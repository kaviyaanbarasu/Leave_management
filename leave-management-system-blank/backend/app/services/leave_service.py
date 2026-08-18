import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_request import LeaveRequest
from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveCalculationPreviewRequest,
    LeaveCalculationPreviewResponse,
)
from app.services.holiday_service import holiday_service
from app.services.balance_service import balance_service


class LeaveService:
    def preview_leave(
        self, payload: LeaveCalculationPreviewRequest, db: Session
    ) -> LeaveCalculationPreviewResponse:
        employee = db.query(Employee).filter(Employee.employee_id == payload.employee_id).first()
        if not employee:
            return LeaveCalculationPreviewResponse(
                employee_id=payload.employee_id,
                leave_type_id=payload.leave_type_id,
                total_calendar_days=0,
                working_days=0.0,
                current_available_balance=0.0,
                projected_remaining_balance=0.0,
                is_valid=False,
                message=f"Employee {payload.employee_id} not found",
            )

        leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == payload.leave_type_id).first()
        if not leave_type:
            return LeaveCalculationPreviewResponse(
                employee_id=payload.employee_id,
                leave_type_id=payload.leave_type_id,
                total_calendar_days=0,
                working_days=0.0,
                current_available_balance=0.0,
                projected_remaining_balance=0.0,
                is_valid=False,
                message=f"Leave type {payload.leave_type_id} not found",
            )

        if leave_type.location_id != employee.location_id:
            return LeaveCalculationPreviewResponse(
                employee_id=payload.employee_id,
                leave_type_id=payload.leave_type_id,
                total_calendar_days=0,
                working_days=0.0,
                current_available_balance=0.0,
                projected_remaining_balance=0.0,
                is_valid=False,
                message=f"Leave type '{leave_type.name}' is not valid for employee's location '{employee.location_id}'",
            )

        if payload.start_date > payload.end_date:
            return LeaveCalculationPreviewResponse(
                employee_id=payload.employee_id,
                leave_type_id=payload.leave_type_id,
                total_calendar_days=0,
                working_days=0.0,
                current_available_balance=0.0,
                projected_remaining_balance=0.0,
                is_valid=False,
                message="Start date must be before or equal to end date",
            )

        try:
            total_cal, working_days, _ = holiday_service.calculate_working_days(
                employee.employee_id, payload.start_date, payload.end_date, db
            )
        except Exception as e:
            return LeaveCalculationPreviewResponse(
                employee_id=payload.employee_id,
                leave_type_id=payload.leave_type_id,
                total_calendar_days=0,
                working_days=0.0,
                current_available_balance=0.0,
                projected_remaining_balance=0.0,
                is_valid=False,
                message=str(e),
            )

        current_balance = balance_service.get_available_balance(employee.employee_id, leave_type.leave_type_id, db)
        projected_balance = max(0.0, round(current_balance - working_days, 2))

        is_valid = True
        msg = None

        if working_days <= 0:
            is_valid = False
            msg = "Selected date range contains no working days (all weekends or holidays)"
        elif current_balance < working_days:
            is_valid = False
            msg = f"Insufficient balance. Available: {current_balance:.1f} days, requested: {working_days:.1f} days"

        return LeaveCalculationPreviewResponse(
            employee_id=employee.employee_id,
            leave_type_id=leave_type.leave_type_id,
            total_calendar_days=total_cal,
            working_days=working_days,
            current_available_balance=current_balance,
            projected_remaining_balance=projected_balance,
            is_valid=is_valid,
            message=msg,
        )

    def create_leave_request(
        self, payload: LeaveRequestCreate, db: Session
    ) -> LeaveRequestResponse:
        # 1. Find employee
        employee = db.query(Employee).filter(Employee.employee_id == payload.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee '{payload.employee_id}' not found",
            )

        # 2. Find leave type
        leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == payload.leave_type_id).first()
        if not leave_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave type '{payload.leave_type_id}' not found",
            )

        # 3. Verify leave type belongs to employee's location
        if leave_type.location_id != employee.location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave type '{leave_type.name}' does not belong to employee's location '{employee.location_id}'",
            )

        # 4. Validate date range
        if payload.start_date > payload.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before or equal to end date",
            )

        # 5. Calculate working days using employee location holidays and weekends
        try:
            total_calendar_days, working_days, _ = holiday_service.calculate_working_days(
                employee.employee_id, payload.start_date, payload.end_date, db
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # 6. Reject if working days <= 0
        if working_days <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected date range contains no working days (all weekends or holidays)",
            )

        # 7. Check overlapping active/pending requests
        overlapping = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.employee_id == employee.employee_id,
                LeaveRequest.status.in_(["PENDING", "APPROVED"]),
                LeaveRequest.start_date <= payload.end_date,
                LeaveRequest.end_date >= payload.start_date,
            )
            .first()
        )
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Overlapping leave request '{overlapping.request_id}' ({overlapping.start_date} to {overlapping.end_date}) already exists in status '{overlapping.status}'",
            )

        # 8. Check balance & reserve atomically within transaction
        try:
            balance_service.reserve_balance(employee.employee_id, leave_type.leave_type_id, working_days, db)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        # 9. Create LeaveRequest record with status PENDING
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        leave_request = LeaveRequest(
            request_id=request_id,
            employee_id=employee.employee_id,
            leave_type_id=leave_type.leave_type_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            total_calendar_days=total_calendar_days,
            working_days=working_days,
            reason=payload.reason,
            status="PENDING",
            applied_on=datetime.now(timezone.utc),
        )

        db.add(leave_request)
        db.commit()
        db.refresh(leave_request)

        # Get updated balance
        remaining_balance = balance_service.get_available_balance(employee.employee_id, leave_type.leave_type_id, db)

        return LeaveRequestResponse(
            request_id=leave_request.request_id,
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            total_calendar_days=leave_request.total_calendar_days,
            working_days=leave_request.working_days,
            reason=leave_request.reason,
            status=leave_request.status,
            applied_on=leave_request.applied_on,
            reserved_days=working_days,
            remaining_available_balance=remaining_balance,
        )

    def cancel_leave_request(self, request_id: str, db: Session) -> LeaveRequestResponse:
        leave_request = db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request '{request_id}' not found",
            )

        if leave_request.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel leave request in '{leave_request.status}' status. Only PENDING requests can be cancelled.",
            )

        # Release the pending balance reservation
        balance_service.release_reservation(
            leave_request.employee_id, leave_request.leave_type_id, leave_request.working_days, db
        )

        leave_request.status = "CANCELLED"
        db.commit()
        db.refresh(leave_request)

        remaining_balance = balance_service.get_available_balance(
            leave_request.employee_id, leave_request.leave_type_id, db
        )

        return LeaveRequestResponse(
            request_id=leave_request.request_id,
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            total_calendar_days=leave_request.total_calendar_days,
            working_days=leave_request.working_days,
            reason=leave_request.reason,
            status=leave_request.status,
            applied_on=leave_request.applied_on,
            reserved_days=0.0,
            remaining_available_balance=remaining_balance,
        )


leave_service = LeaveService()
