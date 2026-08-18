from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_id = Column(String(50), primary_key=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.location_id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_paid = Column(Boolean, default=True, nullable=False)
    is_accruable = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="leave_types")
    accrual_policies = relationship("AccrualPolicy", back_populates="leave_type", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="leave_type")
    balances = relationship("EmployeeLeaveBalance", back_populates="leave_type")
