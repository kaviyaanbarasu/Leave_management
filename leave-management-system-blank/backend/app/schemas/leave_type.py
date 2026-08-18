from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class LeaveTypeBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_paid: bool = Field(default=True)
    is_accruable: bool = Field(default=True)
    is_active: bool = Field(default=True)


class LeaveTypeCreate(LeaveTypeBase):
    leave_type_id: str = Field(..., min_length=1)
    location_id: str = Field(..., min_length=1)


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_paid: Optional[bool] = None
    is_accruable: Optional[bool] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(LeaveTypeBase):
    leave_type_id: str
    location_id: str

    model_config = ConfigDict(from_attributes=True)
