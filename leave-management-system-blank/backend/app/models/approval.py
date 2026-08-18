from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class LeaveApproval(Base):
    __tablename__ = "leave_approvals"

    approval_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    request_id = Column(String(50), ForeignKey("leave_requests.request_id"), nullable=False, index=True)
    tier_level = Column(Integer, nullable=False, default=1)  # 1, 2, 3... (Sequential level)
    tier_name = Column(String(100), nullable=False, default="Manager Review")
    approver_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED, SKIPPED, CANCELLED
    decision_at = Column(DateTime, nullable=True)
    comments = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("request_id", "tier_level", name="uq_leave_request_tier"),
        Index("ix_leave_approvals_approver_status", "approver_id", "status"),
    )

    # Relationships
    leave_request = relationship("LeaveRequest", back_populates="approvals")
    approver = relationship("Employee", foreign_keys=[approver_id])

    # Compatibility Property Aliases
    @property
    def id(self) -> int:
        return self.approval_id

    @property
    def leave_request_id(self) -> str:
        return self.request_id

    @property
    def approval_level(self) -> int:
        return self.tier_level

    @property
    def actioned_at(self):
        return self.decision_at
