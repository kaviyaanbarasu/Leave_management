import os
from sqlalchemy import text
from app.database import engine

def migrate_v3():
    """Run v3 migration for notifications table in PostgreSQL."""
    print("Running v3 migration for notifications table in PostgreSQL...")
    with engine.connect() as conn:
        # Add body_text if missing
        conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS body_text TEXT;"))
        # Add error_message if missing
        conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS error_message TEXT;"))
        conn.commit()
    print("[OK] v3 migration completed successfully.")

if __name__ == "__main__":
    migrate_v3()
