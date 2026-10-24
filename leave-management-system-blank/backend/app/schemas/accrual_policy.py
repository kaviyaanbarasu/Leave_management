from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class AccrualPolicyBase(BaseModel):
    """Define the base accrual policy fields.

    Args:
        grade (Optional[str]): Optional grade identifier.
        tenure_from_months (int): Minimum tenure in months required for the policy (must be >= 0).
        monthly_accrual (float): Amount of leave accrued each month (must be > 0).
        max_balance (float): Maximum leave balance allowed (must be > 0).
        carry_forward_limit (float): Maximum amount that can be carried forward (must be >= 0).
        is_active (bool): Flag indicating whether the policy is active (default True).
    """
    grade: Optional[str] = Field(None)
    tenure_from_months: int = Field(default=0, ge=0)
    monthly_accrual: float = Field(..., gt=0)
    max_balance: float = Field(..., gt=0)
    carry_forward_limit: float = Field(default=0.0, ge=0)
    is_active: bool = Field(default=True)


class AccrualPolicyCreate(AccrualPolicyBase):
    """Create a new accrual policy with required location and leave type identifiers.

    Args:
        grade (Optional[str]): Optional grade identifier.
        tenure_from_months (int): Minimum tenure in months required for the policy (must be >= 0).
        monthly_accrual (float): Amount of leave accrued each month (must be > 0).
        max_balance (float): Maximum leave balance allowed (must be > 0).
        carry_forward_limit (float): Maximum amount that can be carried forward (must be >= 0).
        is_active (bool): Flag indicating whether the policy is active (default True).
        location_id (str): Identifier of the location to which the policy applies (must be non‑empty).
        leave_type_id (str): Identifier of the leave type to which the policy applies (must be non‑empty).
    """
    location_id: str = Field(..., min_length=1)
    leave_type_id: str = Field(..., min_length=1)


class AccrualPolicyUpdate(BaseModel):
    """Update an existing accrual policy with optional fields.

    Args:
        grade (Optional[str]): New grade identifier, if updating.
        tenure_from_months (Optional[int]): Updated minimum tenure in months.
        monthly_accrual (Optional[float]): Updated monthly accrual amount.
        max_balance (Optional[float]): Updated maximum balance.
        carry_forward_limit (Optional[float]): Updated carry‑forward limit.
        is_active (Optional[bool]): Updated active flag.
    """
    grade: Optional[str] = None
    tenure_from_months: Optional[int] = None
    monthly_accrual: Optional[float] = None
    max_balance: Optional[float] = None
    carry_forward_limit: Optional[float] = None
    is_active: Optional[bool] = None


class AccrualPolicyResponse(AccrualPolicyBase):
    """Represent an accrual policy returned by the API.

    Args:
        grade (Optional[str]): Optional grade identifier.
        tenure_from_months (int): Minimum tenure in months required for the policy.
        monthly_accrual (float): Amount of leave accrued each month.
        max_balance (float): Maximum leave balance allowed.
        carry_forward_limit (float): Maximum amount that can be carried forward.
        is_active (bool): Indicates whether the policy is active.
        policy_id (int): Unique identifier of the policy.
        location_id (str): Identifier of the location associated with the policy.
        leave_type_id (str): Identifier of the leave type associated with the policy.
    """
    policy_id: int
    location_id: str
    leave_type_id: str

    model_config = ConfigDict(from_attributes=True)


class AccrualRunRequest(BaseModel):
    """Specify the year and month for an accrual run.

    Args:
        year (Optional[int]): Year for which to run accruals.
        month (Optional[int]): Month for which to run accruals (1‑12).
    """
    year: Optional[int] = None
    month: Optional[int] = Field(None, ge=1, le=12)


class AccrualRecordResponse(BaseModel):
    """Represent a single accrual record returned by the API.

    Args:
        record_id (int): Unique identifier of the accrual record.
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        policy_id (Optional[int]): Identifier of the policy applied, if any.
        year (int): Year of the accrual.
        month (int): Month of the accrual.
        accrued_amount (float): Amount of leave accrued.
        accrued_at (datetime): Timestamp when the accrual was recorded.
    """
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
    """Represent the accrual calculation details for a single employee.

    Args:
        employee_id (str): Identifier of the employee.
        employee_name (Optional[str]): Human‑readable name of the employee.
        leave_type_id (str): Identifier of the leave type.
        leave_type_name (Optional[str]): Name of the leave type.
        grade (Optional[str]): Grade of the employee.
        policy_id (Optional[int]): Identifier of the policy used for accrual.
        policy_name (Optional[str]): Name of the policy.
        policy_grade (Optional[str]): Grade associated with the policy.
        monthly_accrual (float): Standard monthly accrual amount from the policy.
        max_balance (float): Maximum allowed balance from the policy.
        current_balance (float): Employee's current leave balance before accrual.
        actual_accrual (float): Accrual amount actually applied after caps.
        accrued_amount (float): Alias for actual_accrual for compatibility with tests.
        previous_balance (float): Balance before this accrual run.
        new_balance (float): Balance after applying the accrual.
        status (str): Result status (e.g., "ACCRUED", "SKIPPED_ALREADY_ACCRUED", "CAPPED_AT_MAX", "NO_POLICY").
        reason (Optional[str]): Optional explanation for the status.
    """
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
    """Summarize the result of an accrual run operation.

    Args:
        year (int): Year of the accrual run.
        month (int): Month of the accrual run.
        total_processed (int): Number of employee records processed.
        total_accrued (int): Number of records where leave was actually accrued.
        details (List[AccrualRunItem]): List of per‑employee accrual details.
    """
    year: int
    month: int
    total_processed: int
    total_accrued: int
    details: List[AccrualRunItem]
