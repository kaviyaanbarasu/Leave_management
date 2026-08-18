from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.approval import (
    PendingApprovalItem,
    LeaveApprovalResponse,
    ApproveTierRequest,
    RejectTierRequest,
    ApprovalDecisionResponse,
)
from app.services.approval_service import approval_service

router = APIRouter(prefix="/approvals", tags=["Approvals Workflow"])


@router.get("/pending", response_model=List[PendingApprovalItem])
def get_pending_approvals(
    approver_id: Optional[str] = Query(None, description="Employee ID of the current approver"),
    is_admin: bool = Query(False, description="Whether to return all company-wide pending requests"),
    db: Session = Depends(get_db),
):
    """
    Returns pending leave requests requiring approval by the authenticated approver.
    """
    return approval_service.get_pending_approvals_for_user(
        approver_id=approver_id, is_admin=is_admin, db=db
    )


@router.get("/history/{leave_request_id}", response_model=List[LeaveApprovalResponse])
def get_approval_history(
    leave_request_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns the complete sequential approval history for a leave request.
    """
    return approval_service.get_approval_history(request_id=leave_request_id, db=db)


@router.post("/{approval_id}/approve", response_model=ApprovalDecisionResponse)
def approve_leave_approval_step(
    approval_id: int,
    payload: Optional[ApproveTierRequest] = None,
    approver_id: str = Query(..., description="Employee ID of acting approver"),
    db: Session = Depends(get_db),
):
    """
    Approves an approval step by approval_id. Advances sequential workflow to next tier or final approval.
    """
    comments = payload.comments if payload else "Approved"
    return approval_service.approve_approval(
        approval_id=approval_id,
        approver_id=approver_id,
        comments=comments,
        db=db,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalDecisionResponse)
def reject_leave_approval_step(
    approval_id: int,
    payload: RejectTierRequest,
    approver_id: str = Query(..., description="Employee ID of acting approver"),
    db: Session = Depends(get_db),
):
    """
    Rejects an approval step by approval_id. Halts workflow, releases reserved days, and notifies requester.
    """
    return approval_service.reject_approval(
        approval_id=approval_id,
        approver_id=approver_id,
        comments=payload.comments,
        db=db,
    )
