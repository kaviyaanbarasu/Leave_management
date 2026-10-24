from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class LocationBase(BaseModel):
    """Define the base attributes of a location.

    Args:
        name (str): Name of the location.
        city (str): City where the location is situated.
        state (Optional[str]): State of the location, if applicable.
        country (str): Country of the location.
        weekend_days (List[int]): List of weekday indices representing weekend days, where 0=Monday and 6=Sunday. Defaults to [5, 6].
    """
    name: str = Field(...)
    city: str = Field(...)
    state: Optional[str] = Field(None)
    country: str = Field(...)
    weekend_days: List[int] = Field(default_factory=lambda: [5, 6], description="0=Monday, 6=Sunday")


class LocationCreate(LocationBase):
    """Create a new location record.

    Args:
        location_id (str): Unique identifier for the location.

    Inherits all fields from LocationBase.
    """
    location_id: str = Field(...)


class LocationUpdate(BaseModel):
    """Update location fields partially.

    Args:
        name (Optional[str]): New name of the location.
        city (Optional[str]): New city.
        state (Optional[str]): New state.
        country (Optional[str]): New country.
        weekend_days (Optional[List[int]]): New list of weekend day indices.
    """
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    weekend_days: Optional[List[int]] = None


class LocationResponse(LocationBase):
    """Represent a location in API responses.

    Args:
        location_id (str): Unique identifier of the location.

    Inherits all fields from LocationBase.
    """
    location_id: str

    model_config = ConfigDict(from_attributes=True)
