import psycopg2
from app.config import settings

def migrate():
    """Migrate the database schema by adding role and password columns to the employees table."""
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'EMPLOYEE'")
        cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS password VARCHAR(255) DEFAULT 'password123'")
        conn.commit()
        print("PostgreSQL employees table updated with role and password columns.")
    except Exception as e:
        print("Error during migration:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
