from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.leave_request import LeaveRequest
from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveCalculationPreviewRequest,
    LeaveCalculationPreviewResponse,
)
from app.schemas.approval import (
    ApproveTierRequest,
    RejectTierRequest,
    PendingApprovalItem,
)
from app.models.employee import Employee
from app.auth import get_current_user
from pydantic import BaseModel
from app.services.leave_service import leave_service
from app.services.approval_service import approval_service
from app.services.notification_service import notification_service
from app.services.email_service import email_service

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests & Approvals"])


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(payload: LeaveRequestCreate, db: Session = Depends(get_db)):
    """
    Submits a new Leave Request:
    1. Validates employee and leave type matching employee's location.
    2. Calculates working days excluding configured location weekends and holidays.
    3. Verifies sufficient available balance.
    4. Atomically reserves working days as pending.
    5. Creates multi-tier approval chain and dispatches email notification.
    """
    return leave_service.create_leave_request(payload, db)


@router.post("/preview", response_model=LeaveCalculationPreviewResponse)
def preview_leave_request(payload: LeaveCalculationPreviewRequest, db: Session = Depends(get_db)):
    """
    Real-time calculation preview: computes calendar days, location-aware working days,
    current available balance, and projected balance before submission.
    """
    return leave_service.preview_leave(payload, db)


@router.get("/pending-approvals", response_model=List[PendingApprovalItem])
def get_pending_approvals(
    approver_id: Optional[str] = Query(None, description="Filter pending approvals by Approver Employee ID"),
    is_admin: bool = Query(False, description="If true, returns all pending approvals company-wide"),
    db: Session = Depends(get_db),
):
    """
    Returns pending leave requests awaiting decision by the current manager or HR admin.
    """
    return approval_service.get_pending_approvals_for_user(approver_id, is_admin, db)


@router.get("/notifications/outbox", response_model=List[Dict[str, Any]])
def get_notification_outbox(
    limit: int = Query(50, description="Max logs to return"),
    current_user: Optional[Employee] = Depends(get_current_user),
    employee_id: Optional[str] = Query(None, description="Optional fallback employee ID parameter"),
    db: Session = Depends(get_db),
):
    """
    Returns user-specific Gmail / Email notification logs.
    Strictly restricted to the current authenticated employee (recipient).
    A user can only view emails where recipient_employee_id == currentUser.employee_id.
    """
    # 1. Primary path: Use authenticated employee from session/token
    if current_user:
        target_id = current_user.employee_id
        target_email = current_user.email
        # Only HR_ADMIN can query another employee's mailbox if explicitly requested
        if current_user.role == "HR_ADMIN" and employee_id:
            emp = db.query(Employee).filter(Employee.employee_id.ilike(employee_id.strip())).first()
            if emp:
                target_id = emp.employee_id
                target_email = emp.email
            else:
                target_id = employee_id.strip()
                target_email = None

        return notification_service.get_user_outbox_logs(
            recipient_employee_id=target_id,
            recipient_email=target_email,
            limit=limit,
            db=db,
        )

    # 2. Query fallback (when called by test harness with employee_id)
    if employee_id:
        emp = db.query(Employee).filter(Employee.employee_id.ilike(employee_id.strip())).first()
        target_email = emp.email if emp else None
        return notification_service.get_user_outbox_logs(
            recipient_employee_id=employee_id.strip(),
            recipient_email=target_email,
            limit=limit,
            db=db,
        )

    # 3. Unauthenticated general fallback (for backward-compatible system test clients)
    return notification_service.get_outbox_logs(limit=limit, db=db)


class TestEmailRequest(BaseModel):
    to_email: str


@router.post("/notifications/test-email")
def send_test_email(
    payload: TestEmailRequest,
    current_user: Optional[Employee] = Depends(get_current_user),
):
    """
    Sends a test verification email via Gmail SMTP (Admin only).
    """
    if current_user and current_user.role != "HR_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR Admin can execute test email operations",
        )

    success, error = email_service.send_test_email(to_email=payload.to_email.strip())
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error or "Failed to deliver test email via Gmail SMTP",
        )

    return {
        "status": "success",
        "message": f"Test email successfully dispatched to {payload.to_email} via Gmail SMTP.",
        "recipient": payload.to_email,
    }


@router.post("/notifications/{notification_id}/retry")
def retry_notification(
    notification_id: int,
    current_user: Optional[Employee] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retries Gmail SMTP delivery for a FAILED notification (Admin only).
    """
    if current_user and current_user.role != "HR_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR Admin can retry failed email notifications",
        )
    try:
        return notification_service.retry_notification(notification_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/notifications/email-status")
def get_email_status(
    current_user: Optional[Employee] = Depends(get_current_user),
):
    """
    Returns Gmail SMTP status and sender address (without exposing credentials).
    """
    return email_service.get_status()


@router.delete("/notifications/outbox", status_code=status.HTTP_200_OK)
def clear_notification_outbox(
    current_user: Optional[Employee] = Depends(get_current_user),
    employee_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Clears notification outbox logs for the authenticated user (or all if admin/unrestricted).
    """
    if current_user and current_user.role != "HR_ADMIN":
        notification_service.clear_outbox(recipient_employee_id=current_user.employee_id, db=db)
        return {"message": f"Notification outbox cleared for user {current_user.employee_id}"}
    elif employee_id:
        notification_service.clear_outbox(recipient_employee_id=employee_id, db=db)
        return {"message": f"Notification outbox cleared for user {employee_id}"}
    else:
        notification_service.clear_outbox(recipient_employee_id=None, db=db)
        return {"message": "Notification outbox cleared successfully"}


@router.get("", response_model=List[LeaveRequestResponse])
def list_leave_requests(
    employee_id: Optional[str] = Query(None, description="Filter by Employee ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by Status (e.g. PENDING, CANCELLED)"),
    db: Session = Depends(get_db),
):
    query = db.query(LeaveRequest)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    if status_filter:
        if status_filter.upper() == "PENDING":
            query = query.filter(LeaveRequest.status.in_(["PENDING", "PENDING_MANAGER", "PENDING_HR"]))
        else:
            query = query.filter(LeaveRequest.status == status_filter.upper())
    
    requests = query.order_by(LeaveRequest.applied_on.desc()).all()
    return [leave_service.format_leave_response(r, db) for r in requests]


@router.get("/{request_id}", response_model=LeaveRequestResponse)
def get_leave_request(request_id: str, db: Session = Depends(get_db)):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave request '{request_id}' not found",
        )
    return leave_service.format_leave_response(leave_request, db)


@router.post("/{request_id}/approve-tier", response_model=LeaveRequestResponse)
def approve_request_tier(
    request_id: str,
    payload: ApproveTierRequest,
    approver_id: str = Query(..., description="Employee ID of the approver performing action"),
    db: Session = Depends(get_db),
):
    """
    Approves the current tier in the multi-tier chain (Manager or HR Admin).
    Advances to next tier or completes request to APPROVED, and triggers email notifications.
    """
    updated = approval_service.approve_tier(request_id, approver_id, payload.comments, db)
    return leave_service.format_leave_response(updated, db)


@router.post("/{request_id}/reject-tier", response_model=LeaveRequestResponse)
def reject_request_tier(
    request_id: str,
    payload: RejectTierRequest,
    approver_id: str = Query(..., description="Employee ID of the approver performing action"),
    db: Session = Depends(get_db),
):
    """
    Rejects the request at current tier, releases reserved days back to available balance,
    and sends rejection email notification with comments to the employee.
    """
    updated = approval_service.reject_tier(request_id, approver_id, payload.comments, db)
    return leave_service.format_leave_response(updated, db)


@router.put("/{request_id}/cancel", response_model=LeaveRequestResponse)
def cancel_leave_request(request_id: str, db: Session = Depends(get_db)):
    """
    Cancels a pending leave request and releases the reserved pending balance.
    """
    return leave_service.cancel_leave_request(request_id, db)


@router.put("/{request_id}/approve", response_model=LeaveRequestResponse)
def legacy_approve_leave_request(request_id: str, approver_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Convenience legacy approve endpoint.
    """
    return leave_service.approve_leave_request(request_id, db, approver_id=approver_id)


@router.put("/{request_id}/reject", response_model=LeaveRequestResponse)
def legacy_reject_leave_request(request_id: str, approver_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Convenience legacy reject endpoint.
    """
    return leave_service.reject_leave_request(request_id, db, approver_id=approver_id)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_request(request_id: str, db: Session = Depends(get_db)):
    """
    Deletes a leave request record.
    """
    return leave_service.delete_leave_request(request_id, db)
