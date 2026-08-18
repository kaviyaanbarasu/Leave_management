from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class AccrualPolicyBase(BaseModel):
    grade: Optional[str] = Field(None)
    tenure_from_months: int = Field(default=0, ge=0)
    monthly_accrual: float = Field(..., gt=0)
    max_balance: float = Field(..., gt=0)
    carry_forward_limit: float = Field(default=0.0, ge=0)
    is_active: bool = Field(default=True)


class AccrualPolicyCreate(AccrualPolicyBase):
    location_id: str = Field(..., min_length=1)
    leave_type_id: str = Field(..., min_length=1)


class AccrualPolicyUpdate(BaseModel):
    grade: Optional[str] = None
    tenure_from_months: Optional[int] = None
    monthly_accrual: Optional[float] = None
    max_balance: Optional[float] = None
    carry_forward_limit: Optional[float] = None
    is_active: Optional[bool] = None


class AccrualPolicyResponse(AccrualPolicyBase):
    policy_id: int
    location_id: str
    leave_type_id: str

    model_config = ConfigDict(from_attributes=True)


class AccrualRunRequest(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = Field(None, ge=1, le=12)


class AccrualRecordResponse(BaseModel):
    record_id: int
    employee_id: str
    leave_type_id: str
    policy_id: Optional[int] = None
    year: int
    month: int
    accrued_amount: float
    accrued_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccrualRunItem(BaseModel):
    employee_id: str
    employee_name: Optional[str] = None
    leave_type_id: str
    leave_type_name: Optional[str] = None
    grade: Optional[str] = None
    policy_id: Optional[int] = None
    policy_name: Optional[str] = None
    policy_grade: Optional[str] = None
    monthly_accrual: float = 0.0
    max_balance: float = 0.0
    current_balance: float = 0.0
    actual_accrual: float = 0.0
    accrued_amount: float = 0.0  # Alias/compat for tests
    previous_balance: float = 0.0
    new_balance: float = 0.0
    status: str  # "ACCRUED", "SKIPPED_ALREADY_ACCRUED", "CAPPED_AT_MAX", "NO_POLICY"
    reason: Optional[str] = None


class AccrualRunResponse(BaseModel):
    year: int
    month: int
    total_processed: int
    total_accrued: int
    details: List[AccrualRunItem]
