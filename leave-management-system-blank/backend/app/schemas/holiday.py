from datetime import date as dt_date, datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class HolidayBase(BaseModel):
    name: str = Field(..., min_length=1)
    date: dt_date = Field(...)
    holiday_type: Optional[str] = Field("PUBLIC", alias="type")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidayCreate(HolidayBase):
    location_id: str = Field(..., min_length=1)
    source: Optional[str] = "MANUAL"
    external_event_id: Optional[str] = None


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[dt_date] = None
    holiday_type: Optional[str] = Field(None, alias="type")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidayResponse(HolidayBase):
    holiday_id: int
    location_id: str
    source: str = "MANUAL"
    external_event_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidaySyncStatusResponse(BaseModel):
    location_id: str
    location_name: Optional[str] = None
    year: int
    calendar_id: str
    last_synced_at: Optional[datetime] = None
    sync_status: str = "UNKNOWN"  # "SYNCED", "SYNC_FAILED", "USING_CACHED", "NOT_SYNCED"
    holiday_count: int = 0
    has_api_key: bool = False
    calendar_name: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
