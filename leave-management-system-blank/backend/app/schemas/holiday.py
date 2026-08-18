from datetime import date as dt_date
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


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[dt_date] = None
    holiday_type: Optional[str] = Field(None, alias="type")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HolidayResponse(HolidayBase):
    holiday_id: int
    location_id: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
