from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
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
    source = Column(String(50), nullable=False, default="MANUAL")  # "GOOGLE" or "MANUAL"
    external_event_id = Column(String(255), nullable=True, index=True)

    # Relationships
    location = relationship("Location", back_populates="holidays")


class HolidaySync(Base):
    __tablename__ = "holiday_syncs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    location_id = Column(String(50), ForeignKey("locations.location_id"), nullable=False)
    year = Column(Integer, nullable=False)
    calendar_id = Column(String(255), nullable=False)
    last_synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sync_status = Column(String(50), default="SYNCED", nullable=False)  # "SYNCED", "SYNC_FAILED", "USING_CACHED"
    holiday_count = Column(Integer, default=0, nullable=False)
    error_message = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint("location_id", "year", name="uq_holiday_sync_loc_year"),
    )

    # Relationships
    location = relationship("Location")
