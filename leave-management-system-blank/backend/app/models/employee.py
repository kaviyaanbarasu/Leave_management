from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    """Represent an employee record with personal and employment details."""
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
    role = Column(String(50), nullable=False, default="EMPLOYEE")
    password = Column(String(255), nullable=True, default="password123")
    manager_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=True)

    # Relationships
    location = relationship("Location", back_populates="employees")
    manager = relationship("Employee", remote_side=[employee_id], backref="direct_reports")
    leave_requests = relationship("LeaveRequest", foreign_keys="[LeaveRequest.employee_id]", back_populates="employee", cascade="all, delete-orphan")
    balances = relationship("EmployeeLeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    accrual_records = relationship("AccrualRecord", back_populates="employee", cascade="all, delete-orphan")

    @property
    def manager_name(self):
        """Return the manager's name if a manager is assigned, otherwise None.

        Returns:
            str or None: The manager's name or None if no manager is assigned.
        """
        return self.manager.name if self.manager else None

    @property
    def location_name(self):
        """Return the location's name if the employee has an associated location, otherwise return the location identifier.

        Returns:
            str: The location name or the location_id when the location object is not available.
        """
        return self.location.name if self.location else self.location_id

    @property
    def country(self):
        """Return the country of the employee's location if available, otherwise None.

        Returns:
            str or None: The country name or None if the location is not associated.
        """
        return self.location.country if self.location else None
