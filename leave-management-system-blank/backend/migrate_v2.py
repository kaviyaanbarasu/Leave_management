"""
Migration script to ensure all new columns and tables exist in PostgreSQL.
"""
from sqlalchemy import text
from app.database import engine, Base
from app.models import (
    Location, Employee, LeaveType, Holiday, HolidaySync,
    AccrualPolicy, AccrualRecord, LeaveRequest, EmployeeLeaveBalance,
    LeaveApproval, Notification
)

def run_migration():
    print("Creating any newly declared tables...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        print("Checking/adding columns on existing tables...")
        
        # 1. Holidays columns
        try:
            conn.execute(text("ALTER TABLE holidays ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'MANUAL' NOT NULL;"))
            conn.execute(text("ALTER TABLE holidays ADD COLUMN IF NOT EXISTS external_event_id VARCHAR(255);"))
            print("[OK] holidays columns updated")
        except Exception as e:
            print(f"[ERR] holidays columns update notice: {e}")

        # 2. Accrual records column
        try:
            conn.execute(text("ALTER TABLE accrual_records ADD COLUMN IF NOT EXISTS policy_id INTEGER REFERENCES accrual_policies(policy_id);"))
            print("[OK] accrual_records columns updated")
        except Exception as e:
            print(f"[ERR] accrual_records columns update notice: {e}")

        conn.commit()

    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
