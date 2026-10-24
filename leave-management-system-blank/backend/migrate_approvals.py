import psycopg2
from app.config import settings

def migrate():
    """Migrate the PostgreSQL database schema to support multi-tier leave approvals."""
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    try:
        # 1. Update employees table with manager_id
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS manager_id VARCHAR(50) REFERENCES employees(employee_id) ON DELETE SET NULL")
        
        # 2. Update leave_requests table with current_tier & current_approver_id
        cur.execute("ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS current_tier INTEGER DEFAULT 1")
        cur.execute("ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS current_approver_id VARCHAR(50) REFERENCES employees(employee_id) ON DELETE SET NULL")
        
        # 3. Create leave_approvals table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leave_approvals (
                approval_id SERIAL PRIMARY KEY,
                request_id VARCHAR(50) NOT NULL REFERENCES leave_requests(request_id) ON DELETE CASCADE,
                tier_level INTEGER NOT NULL DEFAULT 1,
                tier_name VARCHAR(100) NOT NULL DEFAULT 'Manager Review',
                approver_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                decision_at TIMESTAMP WITH TIME ZONE,
                comments VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            ALTER TABLE leave_approvals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            CREATE INDEX IF NOT EXISTS ix_leave_approvals_request_id ON leave_approvals(request_id);
            CREATE INDEX IF NOT EXISTS ix_leave_approvals_approver_id ON leave_approvals(approver_id);
            CREATE INDEX IF NOT EXISTS ix_leave_approvals_approver_status ON leave_approvals(approver_id, status);
        """)
        
        conn.commit()
        print("PostgreSQL database successfully migrated for multi-tier approvals.")
    except Exception as e:
        print("Migration error:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
