from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.models.approval import LeaveApproval
from app.models.leave_type import LeaveType
from app.schemas.approval import (
    PendingApprovalItem,
    LeaveApprovalResponse,
    ApprovalDecisionResponse,
)
from app.services.balance_service import balance_service
from app.services.notification_service import notification_service


class ApprovalService:
    def create_approval_chain(
        self, leave_request: LeaveRequest, employee: Employee, db: Session
    ):
        """
        Dynamically generates an N-tier approval workflow for a new leave request
        following the employee reporting hierarchy upward.
        """
        return self.generate_approval_chain(leave_request, employee, db)

    def generate_approval_chain(
        self, leave_request: LeaveRequest, employee: Employee, db: Session
    ):
        """
        Builds a sequential N-tier approval chain starting from the requester's direct manager
        and continuing up to top-level HR.
        - Detects circular hierarchy (A -> B -> C -> A) and raises error.
        - Never creates self-approval (if manager requests leave, starts from their manager).
        - If employee has no manager and is not HR -> raises error.
        - Handles inactive managers by advancing to their active manager.
        """
        approvers_chain: List[Employee] = []
        visited = set([employee.employee_id])

        current_mgr_id = employee.manager_id

        # Case 1: Requester is top-level HR Admin with no manager
        if not current_mgr_id and employee.role == "HR_ADMIN":
            # Find another active HR Admin or peer
            alt_hr = (
                db.query(Employee)
                .filter(
                    Employee.role == "HR_ADMIN",
                    Employee.status == "ACTIVE",
                    Employee.employee_id != employee.employee_id,
                )
                .first()
            )
            if alt_hr:
                approvers_chain.append(alt_hr)
            else:
                # Sole top-level admin: auto-approves or self single-tier
                approvers_chain.append(employee)

        # Case 2: Employee has no manager and is not HR
        elif not current_mgr_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No approval hierarchy configured for employee '{employee.name}' ({employee.employee_id}). Please assign a reporting manager.",
            )

        # Case 3: Traverse manager hierarchy
        else:
            while current_mgr_id:
                # Circular hierarchy check
                if current_mgr_id in visited:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Circular manager hierarchy detected involving employee '{current_mgr_id}'.",
                    )
                visited.add(current_mgr_id)

                mgr = db.query(Employee).filter(Employee.employee_id == current_mgr_id).first()
                if not mgr:
                    break

                # If manager is inactive, skip to the inactive manager's manager
                if mgr.status != "ACTIVE":
                    current_mgr_id = mgr.manager_id
                    continue

                approvers_chain.append(mgr)

                # Stop if we reached top-level HR Admin
                if mgr.role == "HR_ADMIN" or not mgr.manager_id:
                    break

                current_mgr_id = mgr.manager_id

        if not approvers_chain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active approvers found in hierarchy for employee '{employee.name}'.",
            )

        # Ensure HR Admin is included at top if not already in chain
        top_approver = approvers_chain[-1]
        if top_approver.role != "HR_ADMIN":
            hr_admin = (
                db.query(Employee)
                .filter(
                    Employee.role == "HR_ADMIN",
                    Employee.status == "ACTIVE",
                    Employee.employee_id != employee.employee_id,
                )
                .first()
            )
            if hr_admin and hr_admin.employee_id not in [a.employee_id for a in approvers_chain]:
                approvers_chain.append(hr_admin)

        # Create sequential LeaveApproval records in DB
        for idx, approver in enumerate(approvers_chain, start=1):
            tier_label = (
                "HR Admin Final Approval"
                if approver.role == "HR_ADMIN"
                else f"Level {idx}: {approver.name} Review"
            )
            approval = LeaveApproval(
                request_id=leave_request.request_id,
                tier_level=idx,
                tier_name=tier_label,
                approver_id=approver.employee_id,
                status="PENDING",
            )
            db.add(approval)

        db.flush()

        # Set initial active tier
        first_approver = approvers_chain[0]
        leave_request.current_tier = 1
        leave_request.current_approver_id = first_approver.employee_id
        leave_request.status = (
            "PENDING_MANAGER" if first_approver.role != "HR_ADMIN" else "PENDING_HR"
        )

        leave_type_name = (
            leave_request.leave_type.name
            if leave_request.leave_type
            else leave_request.leave_type_id
        )

        # Send initial notification email to Level 1 approver
        if first_approver.employee_id != employee.employee_id:
            try:
                notification_service.notify_new_request_to_approver(
                    employee_name=employee.name,
                    employee_email=employee.email,
                    approver_name=first_approver.name,
                    approver_email=first_approver.email,
                    request_id=leave_request.request_id,
                    leave_type_name=leave_type_name,
                    start_date=str(leave_request.start_date),
                    end_date=str(leave_request.end_date),
                    working_days=leave_request.working_days,
                    reason=leave_request.reason,
                    tier_name=f"Level 1: {first_approver.name} Review",
                    approver_id=first_approver.employee_id,
                    db=db,
                )
            except Exception as e:
                print(f"[ApprovalService] Notification dispatch warning: {e}")

    def approve_approval(
        self, approval_id: int, approver_id: str, comments: Optional[str], db: Session
    ) -> ApprovalDecisionResponse:
        """
        Approves an approval step by approval_id with security and sequence validation.
        """
        approval = db.query(LeaveApproval).filter(LeaveApproval.approval_id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval step #{approval_id} not found",
            )

        leave_request = approval.leave_request
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated leave request not found",
            )

        # Security check: Validate approver identity
        acting_user = db.query(Employee).filter(Employee.employee_id == approver_id).first()
        if not acting_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approver '{approver_id}' not found",
            )

        if approval.approver_id != approver_id and acting_user.role != "HR_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: You are not the designated approver for Level {approval.tier_level}",
            )

        # Requester cannot approve their own leave
        if approver_id == leave_request.employee_id and acting_user.role != "HR_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requester cannot approve their own leave request",
            )

        # Status validations
        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve step with status '{approval.status}'. It has already been processed.",
            )

        if leave_request.status in ["APPROVED", "REJECTED", "CANCELLED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve request with overall status '{leave_request.status}'",
            )

        if approval.tier_level != leave_request.current_tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot action Level {approval.tier_level} prematurely. Active step is Level {leave_request.current_tier}.",
            )

        # Mark current step approved
        now = datetime.now(timezone.utc)
        approval.status = "APPROVED"
        approval.decision_at = now
        approval.comments = comments or "Approved"
        approval.approver_id = acting_user.employee_id

        employee = leave_request.employee
        leave_type_name = (
            leave_request.leave_type.name
            if leave_request.leave_type
            else leave_request.leave_type_id
        )

        # Check for next tier in sequence
        next_approval = (
            db.query(LeaveApproval)
            .filter(
                LeaveApproval.request_id == leave_request.request_id,
                LeaveApproval.tier_level > approval.tier_level,
                LeaveApproval.status == "PENDING",
            )
            .order_by(LeaveApproval.tier_level.asc())
            .first()
        )

        if next_approval:
            leave_request.current_tier = next_approval.tier_level
            leave_request.current_approver_id = next_approval.approver_id
            leave_request.status = (
                "PENDING_HR"
                if (next_approval.approver and next_approval.approver.role == "HR_ADMIN")
                else "PENDING_MANAGER"
            )

            next_approver = db.query(Employee).filter(Employee.employee_id == next_approval.approver_id).first()

            db.commit()
            db.refresh(leave_request)

            # Trigger email notification to next approver
            if next_approver:
                try:
                    notification_service.notify_next_approver(
                        employee_name=employee.name,
                        employee_email=employee.email,
                        next_approver_name=next_approver.name,
                        next_approver_email=next_approver.email,
                        previous_approver_name=acting_user.name,
                        request_id=leave_request.request_id,
                        leave_type_name=leave_type_name,
                        start_date=str(leave_request.start_date),
                        end_date=str(leave_request.end_date),
                        working_days=leave_request.working_days,
                        tier_name=next_approval.tier_name,
                        next_approver_id=next_approver.employee_id,
                        db=db,
                    )
                except Exception as e:
                    print(f"[ApprovalService] Notification dispatch warning: {e}")

            return ApprovalDecisionResponse(
                message="Leave request approved successfully",
                approvalStatus="APPROVED",
                nextApprover=next_approver.name if next_approver else next_approval.approver_id,
                leaveRequestStatus=leave_request.status,
            )
        else:
            # Final Tier Approval: Deduct balance from pending -> used
            leave_request.status = "APPROVED"
            leave_request.current_approver_id = None

            balance_service.deduct_balance(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_request.leave_type_id,
                working_days=leave_request.working_days,
                db=db,
            )

            db.commit()
            db.refresh(leave_request)

            # Retrieve all approved approvers for final notification
            approved_steps = (
                db.query(LeaveApproval)
                .filter(
                    LeaveApproval.request_id == leave_request.request_id,
                    LeaveApproval.status == "APPROVED",
                )
                .order_by(LeaveApproval.tier_level.asc())
                .all()
            )
            approvers_list = [
                a.approver.name if a.approver else a.approver_id for a in approved_steps
            ]

            try:
                notification_service.notify_final_approval_to_employee(
                    employee_name=employee.name,
                    employee_email=employee.email,
                    request_id=leave_request.request_id,
                    leave_type_name=leave_type_name,
                    start_date=str(leave_request.start_date),
                    end_date=str(leave_request.end_date),
                    working_days=leave_request.working_days,
                    approvers_list=approvers_list,
                    employee_id=employee.employee_id,
                    db=db,
                )
            except Exception as e:
                print(f"[ApprovalService] Notification dispatch warning: {e}")

            return ApprovalDecisionResponse(
                message="Leave request fully approved",
                approvalStatus="APPROVED",
                nextApprover=None,
                leaveRequestStatus="APPROVED",
            )

    def reject_approval(
        self, approval_id: int, approver_id: str, comments: str, db: Session
    ) -> ApprovalDecisionResponse:
        """
        Rejects an approval step, halts the workflow, releases reserved days, and notifies requester.
        """
        approval = db.query(LeaveApproval).filter(LeaveApproval.approval_id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval step #{approval_id} not found",
            )

        leave_request = approval.leave_request
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated leave request not found",
            )

        acting_user = db.query(Employee).filter(Employee.employee_id == approver_id).first()
        if not acting_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approver '{approver_id}' not found",
            )

        if approval.approver_id != approver_id and acting_user.role != "HR_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You are not the assigned approver for this step",
            )

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject step with status '{approval.status}'",
            )

        if leave_request.status in ["APPROVED", "REJECTED", "CANCELLED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject request with status '{leave_request.status}'",
            )

        if not comments or not comments.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason comment is required",
            )

        now = datetime.now(timezone.utc)
        approval.status = "REJECTED"
        approval.decision_at = now
        approval.comments = comments.strip()
        approval.approver_id = acting_user.employee_id

        # Skip all subsequent pending tiers
        db.query(LeaveApproval).filter(
            LeaveApproval.request_id == leave_request.request_id,
            LeaveApproval.status == "PENDING",
        ).update({"status": "SKIPPED", "decision_at": now})

        leave_request.status = "REJECTED"
        leave_request.current_approver_id = None

        # Release reserved balance back to available
        balance_service.release_balance(
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            working_days=leave_request.working_days,
            db=db,
        )

        db.commit()
        db.refresh(leave_request)

        employee = leave_request.employee
        leave_type_name = (
            leave_request.leave_type.name
            if leave_request.leave_type
            else leave_request.leave_type_id
        )

        try:
            notification_service.notify_rejection_to_employee(
                employee_name=employee.name,
                employee_email=employee.email,
                request_id=leave_request.request_id,
                leave_type_name=leave_type_name,
                start_date=str(leave_request.start_date),
                end_date=str(leave_request.end_date),
                working_days=leave_request.working_days,
                rejector_name=acting_user.name,
                reason=comments.strip(),
                employee_id=employee.employee_id,
                db=db,
            )
        except Exception as e:
            print(f"[ApprovalService] Notification dispatch warning: {e}")

        return ApprovalDecisionResponse(
            message="Leave request rejected",
            approvalStatus="REJECTED",
            nextApprover=None,
            leaveRequestStatus="REJECTED",
        )

    def approve_tier(
        self, request_id: str, approver_id: str, comments: Optional[str], db: Session
    ) -> LeaveRequest:
        """
        Convenience method: Approves by request_id and approver_id.
        """
        leave_request = db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request '{request_id}' not found",
            )

        current_approval = (
            db.query(LeaveApproval)
            .filter(
                LeaveApproval.request_id == request_id,
                LeaveApproval.tier_level == leave_request.current_tier,
                LeaveApproval.status == "PENDING",
            )
            .first()
        )
        if not current_approval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval step found for this request",
            )

        self.approve_approval(
            approval_id=current_approval.approval_id,
            approver_id=approver_id,
            comments=comments,
            db=db,
        )
        db.refresh(leave_request)
        return leave_request

    def reject_tier(
        self, request_id: str, approver_id: str, comments: str, db: Session
    ) -> LeaveRequest:
        """
        Convenience method: Rejects by request_id and approver_id.
        """
        leave_request = db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request '{request_id}' not found",
            )

        current_approval = (
            db.query(LeaveApproval)
            .filter(
                LeaveApproval.request_id == request_id,
                LeaveApproval.tier_level == leave_request.current_tier,
                LeaveApproval.status == "PENDING",
            )
            .first()
        )
        if not current_approval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval step found for this request",
            )

        self.reject_approval(
            approval_id=current_approval.approval_id,
            approver_id=approver_id,
            comments=comments,
            db=db,
        )
        db.refresh(leave_request)
        return leave_request

    def get_approval_history(self, request_id: str, db: Session) -> List[LeaveApprovalResponse]:
        """
        Returns full sequential approval history for a leave request.
        """
        approvals = (
            db.query(LeaveApproval)
            .filter(LeaveApproval.request_id == request_id)
            .order_by(LeaveApproval.tier_level.asc())
            .all()
        )
        responses: List[LeaveApprovalResponse] = []
        for a in approvals:
            approver = a.approver or db.query(Employee).filter(Employee.employee_id == a.approver_id).first()
            responses.append(
                LeaveApprovalResponse(
                    approval_id=a.approval_id,
                    id=a.approval_id,
                    request_id=a.request_id,
                    leave_request_id=a.request_id,
                    tier_level=a.tier_level,
                    approval_level=a.tier_level,
                    tier_name=a.tier_name,
                    approver_id=a.approver_id,
                    approver_name=approver.name if approver else a.approver_id,
                    approver_email=approver.email if approver else "",
                    status=a.status,
                    decision_at=a.decision_at,
                    actioned_at=a.decision_at,
                    comments=a.comments,
                    created_at=a.created_at,
                )
            )
        return responses

    def get_pending_approvals_for_user(
        self, approver_id: Optional[str], is_admin: bool, db: Session
    ) -> List[PendingApprovalItem]:
        """
        Returns actionable pending approval items for an approver.
        """
        query = db.query(LeaveRequest).filter(
            LeaveRequest.status.in_(["PENDING", "PENDING_APPROVAL", "PENDING_MANAGER", "PENDING_HR"])
        )

        if not is_admin:
            if not approver_id:
                return []
            query = query.filter(LeaveRequest.current_approver_id == approver_id)

        pending_requests = query.order_by(LeaveRequest.applied_on.asc()).all()
        items: List[PendingApprovalItem] = []

        for req in pending_requests:
            emp = req.employee
            lt = req.leave_type
            bal = balance_service.get_available_balance(req.employee_id, req.leave_type_id, db)

            current_step = (
                db.query(LeaveApproval)
                .filter(
                    LeaveApproval.request_id == req.request_id,
                    LeaveApproval.tier_level == req.current_tier,
                )
                .first()
            )
            step_id = current_step.approval_id if current_step else None
            tier_name = current_step.tier_name if current_step else f"Level {req.current_tier} Review"

            items.append(
                PendingApprovalItem(
                    approval_id=step_id,
                    approvalId=step_id,
                    request_id=req.request_id,
                    leave_request_id=req.request_id,
                    leaveRequestId=req.request_id,
                    employee_id=req.employee_id,
                    employee_name=emp.name if emp else req.employee_id,
                    employeeName=emp.name if emp else req.employee_id,
                    employee_email=emp.email if emp else "",
                    department=emp.department if emp else "",
                    designation=emp.designation if emp else "",
                    grade=emp.grade if emp else "",
                    location_id=emp.location_id if emp else "",
                    leave_type_id=req.leave_type_id,
                    leave_type_name=lt.name if lt else req.leave_type_id,
                    leaveType=lt.name if lt else req.leave_type_id,
                    start_date=req.start_date,
                    startDate=req.start_date,
                    end_date=req.end_date,
                    endDate=req.end_date,
                    working_days=req.working_days,
                    days=req.working_days,
                    reason=req.reason,
                    applied_on=req.applied_on,
                    current_tier=req.current_tier or 1,
                    approval_level=req.current_tier or 1,
                    tier_name=tier_name,
                    status=req.status,
                    current_available_balance=bal,
                    current_balance=bal,
                )
            )

        return items


approval_service = ApprovalService()
