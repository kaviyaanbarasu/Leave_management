from app.database import SessionLocal
from app.seed import seed_database
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval

def sync_db():
    db = SessionLocal()
    print("Syncing PostgreSQL Database with updated employees and hierarchy...")
    try:
        # Re-run seed database which performs cleanup and updates
        seed_database(db)
        
        # Verify employees
        emps = db.query(Employee).all()
        print(f"\nCurrent Active Employees ({len(emps)}):")
        for e in emps:
            print(f" - {e.employee_id}: {e.name} ({e.email}) | Role: {e.role} | Manager: {e.manager_id}")

        # Check for any references to deleted employees
        bad_mgrs = db.query(Employee).filter(Employee.manager_id.in_(["E105", "M202"])).all()
        assert len(bad_mgrs) == 0, f"Found employees pointing to deleted managers: {bad_mgrs}"
        
        bad_approvals = db.query(LeaveApproval).filter(LeaveApproval.approver_id.in_(["E105", "M202"])).all()
        assert len(bad_approvals) == 0, f"Found approvals with deleted approvers: {bad_approvals}"
        
        deleted_exist = db.query(Employee).filter(Employee.employee_id.in_(["E105", "M202"])).all()
        assert len(deleted_exist) == 0, f"Deleted employees still exist: {deleted_exist}"
        
        print("\n[SUCCESS] PostgreSQL Database successfully synchronized and verified!")
    finally:
        db.close()

if __name__ == "__main__":
    sync_db()
