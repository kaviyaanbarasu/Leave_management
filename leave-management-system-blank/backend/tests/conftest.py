import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.seed import seed_database
from app.models import (
    Location,
    Employee,
    LeaveType,
    Holiday,
    AccrualPolicy,
    AccrualRecord,
    LeaveRequest,
    EmployeeLeaveBalance,
    LeaveApproval,
    Notification,
)
from app.main import app

import os

TEST_DATABASE_URL = "sqlite:///./test_temp_db.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create schema once at start
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    # Clean rows before seeding
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()

    db = TestingSessionLocal()
    seed_database(db)
    yield
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


from unittest.mock import patch, MagicMock

@pytest.fixture(scope="function", autouse=True)
def mock_smtp_for_unit_tests():
    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_instance
        yield mock_smtp
