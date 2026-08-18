from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    grade = Column(String(50), nullable=False)
    location_id = Column(String(50), ForeignKey("locations.location_id"), nullable=False)
    joining_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")

    # Relationships
    location = relationship("Location", back_populates="employees")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")
    balances = relationship("EmployeeLeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    accrual_records = relationship("AccrualRecord", back_populates="employee", cascade="all, delete-orphan")
