from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.leave_request import LeaveRequest
from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveCalculationPreviewRequest,
    LeaveCalculationPreviewResponse,
)
from app.services.leave_service import leave_service

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(payload: LeaveRequestCreate, db: Session = Depends(get_db)):
    """
    Submits a new Leave Request:
    1. Validates employee and leave type matching employee's location.
    2. Calculates working days excluding configured location weekends and holidays.
    3. Verifies sufficient available balance.
    4. Atomically reserves working days as pending and creates request in PENDING status.
    """
    return leave_service.create_leave_request(payload, db)


@router.post("/preview", response_model=LeaveCalculationPreviewResponse)
def preview_leave_request(payload: LeaveCalculationPreviewRequest, db: Session = Depends(get_db)):
    """
    Real-time calculation preview: computes calendar days, location-aware working days,
    current available balance, and projected balance before submission.
    """
    return leave_service.preview_leave(payload, db)


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
        query = query.filter(LeaveRequest.status == status_filter.upper())
    return query.order_by(LeaveRequest.applied_on.desc()).all()


@router.get("/{request_id}", response_model=LeaveRequestResponse)
def get_leave_request(request_id: str, db: Session = Depends(get_db)):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave request '{request_id}' not found",
        )
    return leave_request


@router.put("/{request_id}/cancel", response_model=LeaveRequestResponse)
def cancel_leave_request(request_id: str, db: Session = Depends(get_db)):
    """
    Cancels a pending leave request and releases the reserved pending balance.
    """
    return leave_service.cancel_leave_request(request_id, db)
