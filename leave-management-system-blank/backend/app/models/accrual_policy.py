from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class AccrualPolicy(Base):
    """Define an accrual policy for leave accrual calculations."""
    __tablename__ = "accrual_policies"

    policy_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.location_id"), nullable=False)
    leave_type_id = Column(String(50), ForeignKey("leave_types.leave_type_id"), nullable=False)
    grade = Column(String(50), nullable=True)  # None means applies to all grades unless specific grade exists
    tenure_from_months = Column(Integer, default=0, nullable=False)
    monthly_accrual = Column(Float, nullable=False)
    max_balance = Column(Float, nullable=False)
    carry_forward_limit = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="accrual_policies")
    leave_type = relationship("LeaveType", back_populates="accrual_policies")


class AccrualRecord(Base):
    """Record an employee's leave accrual for a specific month and year."""
    __tablename__ = "accrual_records"

    record_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    leave_type_id = Column(String(50), ForeignKey("leave_types.leave_type_id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("accrual_policies.policy_id"), nullable=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    accrued_amount = Column(Float, nullable=False)
    accrued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Ensure idempotency: an employee cannot accrue for the same leave type in the same month twice
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", "year", "month", name="uq_employee_leave_year_month"),
    )

    # Relationships
    employee = relationship("Employee", back_populates="accrual_records")
    leave_type = relationship("LeaveType")
    policy = relationship("AccrualPolicy")
