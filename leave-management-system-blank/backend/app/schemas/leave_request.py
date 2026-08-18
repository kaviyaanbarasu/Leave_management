from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class LeaveRequestCreate(BaseModel):
    employee_id: str = Field(..., min_length=1)
    leave_type_id: str = Field(..., min_length=1)
    start_date: date = Field(...)
    end_date: date = Field(...)
    reason: str = Field(..., min_length=1)


class LeaveRequestResponse(BaseModel):
    request_id: str
    employee_id: str
    leave_type_id: str
    start_date: date
    end_date: date
    total_calendar_days: int
    working_days: float
    reason: str
    status: str
    applied_on: datetime
    reserved_days: Optional[float] = None
    remaining_available_balance: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveCalculationPreviewRequest(BaseModel):
    employee_id: str = Field(...)
    leave_type_id: str = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)


class LeaveCalculationPreviewResponse(BaseModel):
    employee_id: str
    leave_type_id: str
    total_calendar_days: int
    working_days: float
    current_available_balance: float
    projected_remaining_balance: float
    is_valid: bool
    message: Optional[str] = None


class BalanceItemResponse(BaseModel):
    leave_type_id: str
    leave_type_name: str
    opening_balance: float
    accrued: float
    used: float
    pending: float
    adjusted: float
    available: float


class EmployeeBalanceResponse(BaseModel):
    employee_id: str
    employee_name: Optional[str] = None
    location_id: Optional[str] = None
    balances: List[BalanceItemResponse]
