from datetime import date as dt_date, datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class HolidayBase(BaseModel):
    """Define the base holiday schema.

    Args:
        name (str): Name of the holiday, minimum length 1.
        date (date): Date of the holiday.
        holiday_type (Optional[str]): Type of the holiday, defaults to "PUBLIC".
        description (Optional[str]): Optional description of the holiday.
    """
    name: str = Field(..., min_length=1)
    date: dt_date = Field(...)
    holiday_type: Optional[str] = Field("PUBLIC", alias="type")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidayCreate(HolidayBase):
    """Create a holiday record.

    Args:
        name (str): Name of the holiday, minimum length 1.
        date (date): Date of the holiday.
        holiday_type (Optional[str]): Type of the holiday, defaults to "PUBLIC".
        description (Optional[str]): Optional description of the holiday.
        location_id (str): Identifier of the location, minimum length 1.
        source (Optional[str]): Source of the holiday, defaults to "MANUAL".
        external_event_id (Optional[str]): External event identifier, if any.
    """
    location_id: str = Field(..., min_length=1)
    source: Optional[str] = "MANUAL"
    external_event_id: Optional[str] = None


class HolidayUpdate(BaseModel):
    """Update an existing holiday.

    Args:
        name (Optional[str]): New name for the holiday.
        date (Optional[date]): New date for the holiday.
        holiday_type (Optional[str]): New type for the holiday.
        description (Optional[str]): New description for the holiday.
    """
    name: Optional[str] = None
    date: Optional[dt_date] = None
    holiday_type: Optional[str] = Field(None, alias="type")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidayResponse(HolidayBase):
    """Represent a holiday response.

    Args:
        name (str): Name of the holiday.
        date (date): Date of the holiday.
        holiday_type (Optional[str]): Type of the holiday.
        description (Optional[str]): Optional description of the holiday.
        holiday_id (int): Unique identifier of the holiday.
        location_id (str): Identifier of the location.
        source (str): Source of the holiday, defaults to "MANUAL".
        external_event_id (Optional[str]): External event identifier, if any.
    """
    holiday_id: int
    location_id: str
    source: str = "MANUAL"
    external_event_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidaySyncStatusResponse(BaseModel):
    """Provide sync status for holidays of a location.

    Args:
        location_id (str): Identifier of the location.
        location_name (Optional[str]): Name of the location.
        year (int): Year of the calendar.
        calendar_id (str): Identifier of the calendar.
        last_synced_at (Optional[datetime]): Timestamp of the last synchronization.
        sync_status (str): Synchronization status, defaults to "UNKNOWN".
        holiday_count (int): Number of holidays, defaults to 0.
        has_api_key (bool): Indicates if an API key is available, defaults to False.
        calendar_name (Optional[str]): Name of the calendar.
        error_message (Optional[str]): Error message if synchronization failed.
    """
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
