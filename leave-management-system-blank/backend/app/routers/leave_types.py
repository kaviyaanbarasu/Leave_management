from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.leave_type import LeaveType
from app.models.location import Location
from app.schemas.leave_type import LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse

router = APIRouter(prefix="/leave-types", tags=["Leave Types"])


@router.post("", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
def create_leave_type(payload: LeaveTypeCreate, db: Session = Depends(get_db)):
    # Verify location exists
    """Create a new leave type record in the database.

    Args:
        payload (LeaveTypeCreate): Data for the new leave type.
        db (Session): Database session dependency.

    Returns:
        LeaveType: The newly created leave type.

    Raises:
        HTTPException: If the specified location does not exist (404).
        HTTPException: If a leave type with the given ID already exists (409).
    """
    location = db.query(Location).filter(Location.location_id == payload.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{payload.location_id}' not found",
        )

    # Verify unique leave_type_id
    existing = db.query(LeaveType).filter(LeaveType.leave_type_id == payload.leave_type_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Leave type with ID '{payload.leave_type_id}' already exists",
        )

    leave_type = LeaveType(
        leave_type_id=payload.leave_type_id,
        location_id=payload.location_id,
        name=payload.name,
        description=payload.description,
        is_paid=payload.is_paid,
        is_accruable=payload.is_accruable,
        is_active=payload.is_active,
    )
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    return leave_type


@router.get("", response_model=List[LeaveTypeResponse])
def list_leave_types(
    location_id: Optional[str] = Query(None, description="Filter leave types by Location ID"),
    db: Session = Depends(get_db),
):
    """List leave types, optionally filtered by location ID.

    Args:
        location_id (Optional[str]): Location ID to filter leave types; if None, returns all.
        db (Session): Database session dependency.

    Returns:
        List[LeaveType]: List of leave types ordered by leave_type_id.
    """
    query = db.query(LeaveType)
    if location_id:
        query = query.filter(LeaveType.location_id == location_id)
    return query.order_by(LeaveType.leave_type_id).all()


@router.get("/{leave_type_id}", response_model=LeaveTypeResponse)
def get_leave_type(leave_type_id: str, db: Session = Depends(get_db)):
    """Retrieve a leave type by its ID.

    Args:
        leave_type_id (str): Identifier of the leave type to retrieve.
        db (Session): Database session dependency.

    Returns:
        LeaveType: The matching leave type.

    Raises:
        HTTPException: If no leave type with the given ID is found (404).
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave type '{leave_type_id}' not found",
        )
    return leave_type


@router.put("/{leave_type_id}", response_model=LeaveTypeResponse)
def update_leave_type(leave_type_id: str, payload: LeaveTypeUpdate, db: Session = Depends(get_db)):
    """Update fields of an existing leave type.

    Args:
        leave_type_id (str): Identifier of the leave type to update.
        payload (LeaveTypeUpdate): Fields to update; only non-None values are applied.
        db (Session): Database session dependency.

    Returns:
        LeaveType: The updated leave type.

    Raises:
        HTTPException: If the leave type does not exist (404).
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave type '{leave_type_id}' not found",
        )

    if payload.name is not None:
        leave_type.name = payload.name
    if payload.description is not None:
        leave_type.description = payload.description
    if payload.is_paid is not None:
        leave_type.is_paid = payload.is_paid
    if payload.is_accruable is not None:
        leave_type.is_accruable = payload.is_accruable
    if payload.is_active is not None:
        leave_type.is_active = payload.is_active

    db.commit()
    db.refresh(leave_type)
    return leave_type


@router.delete("/{leave_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_type(leave_type_id: str, db: Session = Depends(get_db)):
    """Delete a leave type by its ID.

    Args:
        leave_type_id (str): Identifier of the leave type to delete.
        db (Session): Database session dependency.

    Returns:
        None: Indicates successful deletion.

    Raises:
        HTTPException: If the leave type does not exist (404).
    """
    leave_type = db.query(LeaveType).filter(LeaveType.leave_type_id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leave type '{leave_type_id}' not found",
        )
    db.delete(leave_type)
    db.commit()
    return None
