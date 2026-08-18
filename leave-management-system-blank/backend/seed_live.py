from datetime import date
from app.database import SessionLocal
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval
from app.models.notification import Notification
from app.seed import seed_database

db = SessionLocal()
try:
    # Clear leave requests and approvals from old demo runs in live db
    db.query(Notification).delete()
    db.query(LeaveApproval).delete()
    db.query(LeaveRequest).delete()
    db.query(EmployeeLeaveBalance).delete()
    db.commit()

    seed_database(db)
    print("[OK] Live PostgreSQL database reset and seeded with clean state.")
finally:
    db.close()
