from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Holiday(Base):
    __tablename__ = "holidays"

    holiday_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.location_id"), nullable=False)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, index=True)
    type = Column(String(50), nullable=True, default="PUBLIC")
    description = Column(String(255), nullable=True)

    # Relationships
    location = relationship("Location", back_populates="holidays")
