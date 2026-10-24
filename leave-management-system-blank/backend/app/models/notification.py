from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Notification(Base):
    """Represent a notification record for leave request events."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    leave_request_id = Column(
        String(32),
        ForeignKey("leave_requests.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recipient_employee_id = Column(
        String(32),
        ForeignKey("employees.employee_id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    notification_type = Column(String(50), nullable=False)  # ACTION_REQUIRED, FINAL_APPROVAL, REJECTION, TEST_EMAIL
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    delivery_mode = Column(String(50), default="GMAIL_SMTP")  # GMAIL_SMTP
    status = Column(String(20), default="PENDING")  # PENDING, SENDING, SENT, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    sent_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    employee = relationship("Employee", foreign_keys=[recipient_employee_id])
    leave_request = relationship("LeaveRequest", foreign_keys=[leave_request_id])
