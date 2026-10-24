from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class LeaveApprovalResponse(BaseModel):
    """Represent a leave approval response containing approval details."""
    approval_id: int
    id: Optional[int] = None
    request_id: str
    leave_request_id: Optional[str] = None
    tier_level: int
    approval_level: Optional[int] = None
    tier_name: str
    approver_id: str
    approver_name: Optional[str] = None
    approver_email: Optional[str] = None
    status: str
    decision_at: Optional[datetime] = None
    actioned_at: Optional[datetime] = None
    comments: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApproveTierRequest(BaseModel):
    """Create a request to approve a tier with optional comments."""
    comments: Optional[str] = "Approved"


class RejectTierRequest(BaseModel):
    """Create a request to reject a tier with a required comment."""
    comments: str = Field(..., min_length=1, description="Reason for rejection is required")


class PendingApprovalItem(BaseModel):
    """Represent an item pending approval with detailed leave request and employee information."""
    approval_id: Optional[int] = None
    approvalId: Optional[int] = None
    request_id: str
    leave_request_id: Optional[str] = None
    leaveRequestId: Optional[str] = None
    employee_id: str
    employee_name: str
    employeeName: Optional[str] = None
    employee_email: str
    department: str
    designation: str
    grade: str
    location_id: str
    leave_type_id: str
    leave_type_name: str
    leaveType: Optional[str] = None
    start_date: date
    startDate: Optional[date] = None
    end_date: date
    endDate: Optional[date] = None
    working_days: float
    days: Optional[float] = None
    reason: str
    applied_on: datetime
    current_tier: int
    approval_level: Optional[int] = None
    tier_name: str
    status: str
    current_available_balance: float
    current_balance: Optional[float] = None


class ApprovalDecisionResponse(BaseModel):
    """Represent the response after an approval decision, including status messages."""
    message: str
    approvalStatus: str
    nextApprover: Optional[str] = None
    leaveRequestStatus: str
