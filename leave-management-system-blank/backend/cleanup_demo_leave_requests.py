from app.database import SessionLocal
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval
from app.services.notification_service import notification_service

def cleanup_demo_requests():
    print("==================================================")
    print("  CLEANING DEMO LEAVE REQUESTS & RESETTING BALANCES")
    print("==================================================")
    db = SessionLocal()
    try:
        # 1. Delete all approvals associated with demo leave requests
        deleted_approvals = db.query(LeaveApproval).delete(synchronize_session=False)
        print(f"[+] Deleted {deleted_approvals} demo LeaveApproval records.")

        # 2. Delete all demo leave requests
        deleted_requests = db.query(LeaveRequest).delete(synchronize_session=False)
        print(f"[+] Deleted {deleted_requests} demo LeaveRequest records.")

        # 3. Reset all employee balance reservations & usages (used=0, pending=0)
        balances = db.query(EmployeeLeaveBalance).all()
        for b in balances:
            b.used = 0.0
            b.pending = 0.0
        print(f"[+] Reset usage and pending reservations for {len(balances)} employee balance records.")

        # 4. Clear in-memory notification outbox logs
        notification_service.outbox_logs.clear()
        print("[+] Cleared notification outbox logs.")

        db.commit()
        print("\n[SUCCESS] Database is now clean of demo leave requests!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Cleanup failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_demo_requests()
