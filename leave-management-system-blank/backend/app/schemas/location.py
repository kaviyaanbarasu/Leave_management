from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class LocationBase(BaseModel):
    name: str = Field(...)
    city: str = Field(...)
    state: Optional[str] = Field(None)
    country: str = Field(...)
    weekend_days: List[int] = Field(default_factory=lambda: [5, 6], description="0=Monday, 6=Sunday")


class LocationCreate(LocationBase):
    location_id: str = Field(...)


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    weekend_days: Optional[List[int]] = None


class LocationResponse(LocationBase):
    location_id: str

    model_config = ConfigDict(from_attributes=True)
