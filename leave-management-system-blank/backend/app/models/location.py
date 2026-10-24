from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Location(Base):
    """Represent a physical location with its details and related entities."""
    __tablename__ = "locations"

    location_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False)
    # Stored as JSON list of weekday integers (0=Monday, ..., 5=Saturday, 6=Sunday)
    # Default is [5, 6] (Saturday and Sunday)
    weekend_days = Column(JSON, nullable=False, default=list)

    # Relationships
    employees = relationship("Employee", back_populates="location", cascade="all, delete-orphan")
    leave_types = relationship("LeaveType", back_populates="location", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="location", cascade="all, delete-orphan")
    accrual_policies = relationship("AccrualPolicy", back_populates="location", cascade="all, delete-orphan")
