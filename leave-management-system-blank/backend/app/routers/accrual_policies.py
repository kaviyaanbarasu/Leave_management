from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.accrual_policy import AccrualPolicy
from app.models.location import Location
from app.models.leave_type import LeaveType
from app.schemas.accrual_policy import (
    AccrualPolicyCreate,
    AccrualPolicyUpdate,
    AccrualPolicyResponse,
    AccrualRunRequest,
    AccrualRunResponse,
)
from app.services.accrual_service import accrual_service

router = APIRouter(tags=["Accrual Policies"])


@router.post("/accrual-policies", response_model=AccrualPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_accrual_policy(payload: AccrualPolicyCreate, db: Session = Depends(get_db)):
    # Verify location exists
    location = db.query(Location).filter(Location.location_id == payload.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{payload.location_id}' not found",
        )

    # Verify leave type exists and belongs to location
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == payload.leave_type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave type '{payload.leave_type_id}' not found",
        )

    if leave_type.location_id != payload.location_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave type '{leave_type.name}' does not belong to location '{payload.location_id}'",
        )

    policy = AccrualPolicy(
        location_id=payload.location_id,
        leave_type_id=payload.leave_type_id,
        grade=payload.grade,
        tenure_from_months=payload.tenure_from_months,
        monthly_accrual=payload.monthly_accrual,
        max_balance=payload.max_balance,
        carry_forward_limit=payload.carry_forward_limit,
        is_active=payload.is_active,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/accrual-policies", response_model=List[AccrualPolicyResponse])
def list_accrual_policies(
    location_id: Optional[str] = Query(None, description="Filter by Location ID"),
    leave_type_id: Optional[str] = Query(None, description="Filter by Leave Type ID"),
    db: Session = Depends(get_db),
):
    query = db.query(AccrualPolicy)
    if location_id:
        query = query.filter(AccrualPolicy.location_id == location_id)
    if leave_type_id:
        query = query.filter(AccrualPolicy.leave_type_id == leave_type_id)
    return query.order_by(AccrualPolicy.policy_id).all()


@router.get("/accrual-policies/{policy_id}", response_model=AccrualPolicyResponse)
def get_accrual_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(AccrualPolicy).filter(AccrualPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accrual policy '{policy_id}' not found",
        )
    return policy


@router.put("/accrual-policies/{policy_id}", response_model=AccrualPolicyResponse)
def update_accrual_policy(policy_id: int, payload: AccrualPolicyUpdate, db: Session = Depends(get_db)):
    policy = db.query(AccrualPolicy).filter(AccrualPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accrual policy '{policy_id}' not found",
        )

    if payload.grade is not None:
        policy.grade = payload.grade
    if payload.tenure_from_months is not None:
        policy.tenure_from_months = payload.tenure_from_months
    if payload.monthly_accrual is not None:
        policy.monthly_accrual = payload.monthly_accrual
    if payload.max_balance is not None:
        policy.max_balance = payload.max_balance
    if payload.carry_forward_limit is not None:
        policy.carry_forward_limit = payload.carry_forward_limit
    if payload.is_active is not None:
        policy.is_active = payload.is_active

    db.commit()
    db.refresh(policy)
    return policy


@router.post("/accrual/run", response_model=AccrualRunResponse)
def run_accrual(payload: Optional[AccrualRunRequest] = None, db: Session = Depends(get_db)):
    """
    Manually triggers monthly accrual calculation across all active employees.
    Idempotent operation: running multiple times for the same month will not double credit.
    """
    year = payload.year if payload else None
    month = payload.month if payload else None
    return accrual_service.run_monthly_accrual(year=year, month=month, db=db)
