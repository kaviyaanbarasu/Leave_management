from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class LeaveRequest(Base):
    """Define a leave request model."""
    __tablename__ = "leave_requests"

    request_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    leave_type_id = Column(String(50), ForeignKey("leave_types.leave_type_id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_calendar_days = Column(Integer, nullable=False)
    working_days = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING_MANAGER, PENDING_HR, APPROVED, REJECTED, CANCELLED
    current_tier = Column(Integer, nullable=False, default=1)
    current_approver_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=True)
    applied_on = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="leave_requests")
    current_approver = relationship("Employee", foreign_keys=[current_approver_id])
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    approvals = relationship("LeaveApproval", back_populates="leave_request", cascade="all, delete-orphan", order_by="LeaveApproval.tier_level")


class EmployeeLeaveBalance(Base):
    """Define an employee leave balance model."""
    __tablename__ = "employee_leave_balances"

    balance_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    leave_type_id = Column(String(50), ForeignKey("leave_types.leave_type_id"), nullable=False, index=True)
    opening_balance = Column(Float, default=0.0, nullable=False)
    accrued = Column(Float, default=0.0, nullable=False)
    used = Column(Float, default=0.0, nullable=False)
    pending = Column(Float, default=0.0, nullable=False)
    adjusted = Column(Float, default=0.0, nullable=False)
    as_of_date = Column(Date, default=date.today, nullable=False)

    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", name="uq_employee_leave_balance"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="balances")
    leave_type = relationship("LeaveType", back_populates="balances")

    @property
    def available_balance(self) -> float:
        """Calculate the available leave balance.

        Returns:
            float: The available balance rounded to two decimal places, never less than zero.
        """
        return max(0.0, round(self.opening_balance + self.accrued + self.adjusted - self.used - self.pending, 2))
