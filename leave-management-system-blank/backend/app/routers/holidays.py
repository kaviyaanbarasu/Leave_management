from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.holiday import Holiday
from app.models.location import Location
from app.schemas.holiday import HolidayCreate, HolidayUpdate, HolidayResponse

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(payload: HolidayCreate, db: Session = Depends(get_db)):
    # Verify location exists
    location = db.query(Location).filter(Location.location_id == payload.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{payload.location_id}' not found",
        )

    # Check duplicate holiday on same date for same location
    existing = (
        db.query(Holiday)
        .filter(Holiday.location_id == payload.location_id, Holiday.date == payload.date)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Holiday already configured on {payload.date} for location '{payload.location_id}'",
        )

    holiday = Holiday(
        location_id=payload.location_id,
        name=payload.name,
        date=payload.date,
        type=payload.holiday_type,
        description=payload.description,
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.get("", response_model=List[HolidayResponse])
def list_holidays(
    location_id: Optional[str] = Query(None, description="Filter holidays by Location ID"),
    year: Optional[int] = Query(None, description="Filter holidays by Year"),
    db: Session = Depends(get_db),
):
    query = db.query(Holiday)
    if location_id:
        query = query.filter(Holiday.location_id == location_id)
    if year:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        query = query.filter(Holiday.date >= start_date, Holiday.date <= end_date)
    return query.order_by(Holiday.date).all()


@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday(holiday_id: int, db: Session = Depends(get_db)):
    holiday = db.query(Holiday).filter(Holiday.holiday_id == holiday_id).first()
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holiday '{holiday_id}' not found",
        )
    return holiday


@router.put("/{holiday_id}", response_model=HolidayResponse)
def update_holiday(holiday_id: int, payload: HolidayUpdate, db: Session = Depends(get_db)):
    holiday = db.query(Holiday).filter(Holiday.holiday_id == holiday_id).first()
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holiday '{holiday_id}' not found",
        )

    if payload.name is not None:
        holiday.name = payload.name
    if payload.date is not None:
        holiday.date = payload.date
    if payload.holiday_type is not None:
        holiday.type = payload.holiday_type
    if payload.description is not None:
        holiday.description = payload.description

    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(holiday_id: int, db: Session = Depends(get_db)):
    holiday = db.query(Holiday).filter(Holiday.holiday_id == holiday_id).first()
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holiday '{holiday_id}' not found",
        )
    db.delete(holiday)
    db.commit()
    return None
