from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.holiday import Holiday
from app.models.location import Location
from app.schemas.holiday import (
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse,
    HolidaySyncStatusResponse,
)
from app.services.holiday_service import (
    holiday_service,
    GOOGLE_CALENDAR_MAP,
    GOOGLE_CALENDAR_NAMES,
)

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
        source=payload.source or "MANUAL",
        external_event_id=payload.external_event_id,
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.get("", response_model=List[HolidayResponse])
def list_holidays(
    location_id: Optional[str] = Query(None, description="Filter holidays by Location ID"),
    year: Optional[int] = Query(None, description="Filter holidays by Year"),
    auto_sync: bool = Query(True, description="Attempt automatic Google sync if not synced yet"),
    db: Session = Depends(get_db),
):
    target_year = year or date.today().year

    # Check or auto-sync from Google Calendar in background/inline if needed
    if location_id and auto_sync:
        holiday_service.check_or_auto_sync(location_id, target_year, db)

    query = db.query(Holiday)
    if location_id:
        query = query.filter(Holiday.location_id == location_id)
    if year:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        query = query.filter(Holiday.date >= start_date, Holiday.date <= end_date)

    return query.order_by(Holiday.date).all()


@router.get("/sync-status", response_model=HolidaySyncStatusResponse)
def get_holiday_sync_status(
    location_id: str = Query(..., description="Location ID to check"),
    year: Optional[int] = Query(None, description="Year to check (default: current year)"),
    db: Session = Depends(get_db),
):
    """
    Returns the Google Calendar holiday synchronization metadata and status for a location.
    """
    target_year = year or date.today().year
    try:
        return holiday_service.get_sync_status(location_id, target_year, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


class GoogleHolidaySyncRequest(BaseModel):
    location_id: str
    year: Optional[int] = None
    api_key: Optional[str] = None


@router.get("/google-status")
def get_google_status():
    """
    Returns Google Calendar API integration status and supported feeds.
    """
    from app.config import settings
    return {
        "has_api_key": bool(settings.GOOGLE_CALENDAR_API_KEY),
        "supported_locations": list(GOOGLE_CALENDAR_MAP.keys()),
        "feed_names": GOOGLE_CALENDAR_NAMES,
        "description": "Google Calendar API v3 Public Holidays integration",
    }


@router.post("/sync-google")
def sync_google_holidays(payload: GoogleHolidaySyncRequest, db: Session = Depends(get_db)):
    """
    Force-syncs official public holidays from Google Calendar API v3 for a given location and year into PostgreSQL.
    """
    target_year = payload.year or date.today().year
    try:
        result = holiday_service.sync_holidays_from_google(
            location_id=payload.location_id,
            year=target_year,
            api_key=payload.api_key,
            db=db,
            auto=False,
        )
        return {
            "status": result.get("status", "success"),
            "message": result.get("message", "Google Calendar synchronization completed."),
            "data": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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

    if payload.date and payload.date != holiday.date:
        existing = (
            db.query(Holiday)
            .filter(
                Holiday.location_id == holiday.location_id,
                Holiday.date == payload.date,
                Holiday.holiday_id != holiday_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another holiday already configured on {payload.date} for location '{holiday.location_id}'",
            )
        holiday.date = payload.date

    if payload.name is not None:
        holiday.name = payload.name
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
