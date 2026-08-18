from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(Location).filter(Location.location_id == payload.location_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Location with ID '{payload.location_id}' already exists",
        )

    location = Location(
        location_id=payload.location_id,
        name=payload.name,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        weekend_days=payload.weekend_days,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("", response_model=List[LocationResponse])
def list_locations(db: Session = Depends(get_db)):
    return db.query(Location).order_by(Location.location_id).all()


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: str, db: Session = Depends(get_db)):
    location = db.query(Location).filter(Location.location_id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found",
        )
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: str, payload: LocationUpdate, db: Session = Depends(get_db)):
    location = db.query(Location).filter(Location.location_id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found",
        )

    if payload.name is not None:
        location.name = payload.name
    if payload.city is not None:
        location.city = payload.city
    if payload.state is not None:
        location.state = payload.state
    if payload.country is not None:
        location.country = payload.country
    if payload.weekend_days is not None:
        location.weekend_days = payload.weekend_days

    db.commit()
    db.refresh(location)
    return location
