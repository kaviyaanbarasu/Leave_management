from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


from app.schemas.approval import LeaveApprovalResponse


class LeaveRequestCreate(BaseModel):
    """Create a leave request model.

    Args:
        employee_id (str): Identifier of the employee submitting the request. Must be non-empty.
        leave_type_id (str): Identifier of the leave type being requested. Must be non-empty.
        start_date (date): First day of the requested leave.
        end_date (date): Last day of the requested leave.
        reason (str): Reason for the leave request. Must be non-empty.
    """
    employee_id: str = Field(..., min_length=1)
    leave_type_id: str = Field(..., min_length=1)
    start_date: date = Field(...)
    end_date: date = Field(...)
    reason: str = Field(..., min_length=1)


class LeaveRequestResponse(BaseModel):
    """Represent a leave request response.

    Args:
        request_id (str): Unique identifier of the leave request.
        employee_id (str): Identifier of the employee who made the request.
        employee_name (Optional[str]): Full name of the employee, if available.
        leave_type_id (str): Identifier of the leave type.
        start_date (date): Start date of the leave.
        end_date (date): End date of the leave.
        total_calendar_days (int): Total number of calendar days between start and end dates inclusive.
        working_days (float): Number of working days calculated for the leave period.
        reason (str): Reason provided for the leave.
        status (str): Current status of the request (e.g., pending, approved, rejected).
        current_tier (Optional[int]): Current approval tier, defaults to 1.
        current_approver_id (Optional[str]): Identifier of the user currently responsible for approval.
        current_approver_name (Optional[str]): Name of the current approver.
        applied_on (datetime): Timestamp when the request was submitted.
        reserved_days (Optional[float]): Number of days reserved from the employee's balance.
        remaining_available_balance (Optional[float]): Balance remaining after reservation.
        approvals (Optional[List[LeaveApprovalResponse]]): List of approval records associated with the request.
    """
    request_id: str
    employee_id: str
    employee_name: Optional[str] = None
    leave_type_id: str
    start_date: date
    end_date: date
    total_calendar_days: int
    working_days: float
    reason: str
    status: str
    current_tier: Optional[int] = 1
    current_approver_id: Optional[str] = None
    current_approver_name: Optional[str] = None
    applied_on: datetime
    reserved_days: Optional[float] = None
    remaining_available_balance: Optional[float] = None
    approvals: Optional[List[LeaveApprovalResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class LeaveCalculationPreviewRequest(BaseModel):
    """Create a request to preview leave calculation.

    Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        start_date (date): Proposed start date of the leave.
        end_date (date): Proposed end date of the leave.
    """
    employee_id: str = Field(...)
    leave_type_id: str = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)


class LeaveCalculationPreviewResponse(BaseModel):
    """Represent the result of a leave calculation preview.

    Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        total_calendar_days (int): Total calendar days in the requested period.
        working_days (float): Calculated working days for the period.
        current_available_balance (float): Employee's current available leave balance.
        projected_remaining_balance (float): Balance that would remain after applying the requested leave.
        is_valid (bool): Indicates whether the leave request satisfies balance and policy constraints.
        message (Optional[str]): Additional information or error message when the request is invalid.
    """
    employee_id: str
    leave_type_id: str
    total_calendar_days: int
    working_days: float
    current_available_balance: float
    projected_remaining_balance: float
    is_valid: bool
    message: Optional[str] = None


class BalanceItemResponse(BaseModel):
    """Represent a balance item for a leave type.

    Args:
        leave_type_id (str): Identifier of the leave type.
        leave_type_name (str): Human-readable name of the leave type.
        opening_balance (float): Balance at the start of the period.
        accrued (float): Days accrued during the period.
        used (float): Days already used.
        pending (float): Days pending approval.
        adjusted (float): Days manually adjusted.
        available (float): Currently available balance.
    """
    leave_type_id: str
    leave_type_name: str
    opening_balance: float
    accrued: float
    used: float
    pending: float
    adjusted: float
    available: float


class EmployeeBalanceResponse(BaseModel):
    """Represent an employee's leave balances.

    Args:
        employee_id (str): Identifier of the employee.
        employee_name (Optional[str]): Full name of the employee, if provided.
        location_id (Optional[str]): Identifier of the employee's location.
        balances (List[BalanceItemResponse]): List of balance items for each leave type.
    """
    employee_id: str
    employee_name: Optional[str] = None
    location_id: Optional[str] = None
    balances: List[BalanceItemResponse]


class BalanceAdjustmentRequest(BaseModel):
    """Create a request to adjust leave balance.

    Args:
        leave_type_id (str): Identifier of the leave type to adjust. Must be non-empty.
        adjustment_days (float): Number of days to adjust; positive values add days, negative values deduct days.
        reason (Optional[str]): Audit reason for the adjustment; defaults to "Manual balance adjustment".
    """
    leave_type_id: str = Field(..., min_length=1)
    adjustment_days: float = Field(..., description="Positive to add days, negative to deduct days")
    reason: Optional[str] = Field("Manual balance adjustment", description="Audit reason for adjustment")
