import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.seed import seed_database
from app.services.holiday_service import holiday_service
from app.models.location import Location
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_request import EmployeeLeaveBalance
from app.services.accrual_service import accrual_service

# Create in-memory SQLite database with StaticPool for test sharing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database(db)
    yield
    db.close()
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# ==========================================
# 1. Employee Creation & Retrieval Tests
# ==========================================
def test_create_and_get_employee():
    payload = {
        "employee_id": "E999",
        "name": "Test User",
        "email": "test.user@example.com",
        "department": "Engineering",
        "designation": "Software Engineer",
        "grade": "G3",
        "location_id": "BLR",
        "joining_date": "2025-01-01",
        "status": "ACTIVE",
    }
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == "E999"
    assert data["name"] == "Test User"
    assert data["location_id"] == "BLR"

    # Get employee
    get_res = client.get("/api/employees/E999")
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "test.user@example.com"


def test_duplicate_employee_id_rejected():
    payload = {
        "employee_id": "E101",  # Already seeded
        "name": "Duplicate User",
        "email": "duplicate@example.com",
        "department": "HR",
        "designation": "HR Exec",
        "grade": "G2",
        "location_id": "BLR",
        "joining_date": "2025-01-01",
        "status": "ACTIVE",
    }
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 409


# ==========================================
# 2. Location Creation & Weekend Config
# ==========================================
def test_create_location():
    payload = {
        "location_id": "LND",
        "name": "London Office",
        "city": "London",
        "state": "Greater London",
        "country": "UK",
        "weekend_days": [5, 6],
    }
    response = client.post("/api/locations", json=payload)
    assert response.status_code == 201
    assert response.json()["location_id"] == "LND"
    assert response.json()["weekend_days"] == [5, 6]


# ==========================================
# 3. Location-Specific Leave Types
# ==========================================
def test_location_specific_leave_types():
    # Fetch BLR leave types
    blr_res = client.get("/api/leave-types?location_id=BLR")
    assert blr_res.status_code == 200
    blr_types = [lt["name"] for lt in blr_res.json()]
    assert "PTO" in blr_types
    assert "CASUAL" in blr_types
    assert "SICK" in blr_types

    # Fetch SG leave types (only PTO and SICK)
    sg_res = client.get("/api/leave-types?location_id=SG")
    assert sg_res.status_code == 200
    sg_types = [lt["name"] for lt in sg_res.json()]
    assert "PTO" in sg_types
    assert "SICK" in sg_types
    assert "CASUAL" not in sg_types


# ==========================================
# 4. Holiday Detection
# ==========================================
def test_holiday_detection():
    db = TestingSessionLocal()
    # 2026-10-20 is Diwali in BLR
    is_diwali = holiday_service.is_holiday("BLR", date(2026, 10, 20), db)
    assert is_diwali is True

    # 2026-10-21 is not a holiday in BLR
    is_not_hol = holiday_service.is_holiday("BLR", date(2026, 10, 21), db)
    assert is_not_hol is False
    db.close()


# ==========================================
# 5 & 8. Weekend Detection & Different Configs (BLR vs DXB)
# ==========================================
def test_weekend_detection_by_location():
    db = TestingSessionLocal()
    blr = db.query(Location).filter(Location.location_id == "BLR").first()
    dxb = db.query(Location).filter(Location.location_id == "DXB").first()

    # 2026-10-23 is Friday
    # 2026-10-24 is Saturday
    # 2026-10-25 is Sunday
    friday = date(2026, 10, 23)
    saturday = date(2026, 10, 24)
    sunday = date(2026, 10, 25)

    # In Bangalore (Sat/Sun weekend): Friday is working day, Saturday & Sunday are weekend
    assert holiday_service.is_weekend(blr, friday) is False
    assert holiday_service.is_weekend(blr, saturday) is True
    assert holiday_service.is_weekend(blr, sunday) is True

    # In Dubai (Fri/Sat weekend): Friday & Saturday are weekend, Sunday is working day
    assert holiday_service.is_weekend(dxb, friday) is True
    assert holiday_service.is_weekend(dxb, saturday) is True
    assert holiday_service.is_weekend(dxb, sunday) is False
    db.close()


# ==========================================
# 6 & 7. Working-Day Calculation & Diwali Exclusion
# ==========================================
def test_diwali_and_working_day_calculation():
    # Scenario:
    # Employee E101 (Bangalore)
    # Request: 2026-10-19 (Mon) to 2026-10-22 (Thu)
    # Oct 19 -> working
    # Oct 20 -> Diwali holiday
    # Oct 21 -> working
    # Oct 22 -> working
    # Total calendar days = 4, Working days = 3
    preview_res = client.post(
        "/api/leave-requests/preview",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
        },
    )
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["total_calendar_days"] == 4
    assert data["working_days"] == 3.0
    assert data["is_valid"] is True


# ==========================================
# 9. Accrual Calculation
# ==========================================
def test_accrual_policy_matching():
    db = TestingSessionLocal()
    e101 = db.query(Employee).filter(Employee.employee_id == "E101").first()  # G5 grade
    # PTO for G5 in BLR = 1.5 per month
    pto = db.query(LeaveType).filter(LeaveType.leave_type_id == "BLR-PTO").first()

    policy, rate = accrual_service.calculate_accrual(e101, pto, date(2026, 8, 1), db)
    assert policy is not None
    assert rate == 1.5
    db.close()


# ==========================================
# 10. Maximum Balance Cap
# ==========================================
def test_max_balance_cap():
    db = TestingSessionLocal()
    # Set employee balance close to max (29.5 out of 30.0)
    bal = (
        db.query(EmployeeLeaveBalance)
        .filter(EmployeeLeaveBalance.employee_id == "E101", EmployeeLeaveBalance.leave_type_id == "BLR-PTO")
        .first()
    )
    bal.opening_balance = 29.5
    bal.accrued = 0.0
    db.commit()
    db.close()

    # Run accrual for 2026-09 (monthly accrual is 1.5, but max is 30.0, so should only add 0.5)
    run_res = client.post("/api/accrual/run", json={"year": 2026, "month": 9})
    assert run_res.status_code == 200

    bal_res = client.get("/api/employees/E101/balance")
    pto_bal = next(b for b in bal_res.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal["available"] == 30.0  # Capped at max 30.0


# ==========================================
# 11 & 16. Leave Balance & Pending Reservation
# ==========================================
def test_leave_balance_and_pending_reservation():
    # Initial balance for E101 BLR-PTO is 10.0
    bal_res = client.get("/api/employees/E101/balance")
    pto_bal = next(b for b in bal_res.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal["available"] == 10.0
    assert pto_bal["pending"] == 0.0

    # Submit leave request for 3 working days (Oct 19 to Oct 22, 2026)
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
            "reason": "Festival vacation",
        },
    )
    assert req_res.status_code == 201
    req_data = req_res.json()
    assert req_data["status"] == "PENDING"
    assert req_data["working_days"] == 3.0
    assert req_data["reserved_days"] == 3.0
    assert req_data["remaining_available_balance"] == 7.0

    # Verify balance endpoint reflects 3 pending and 7 available
    bal_res2 = client.get("/api/employees/E101/balance")
    pto_bal2 = next(b for b in bal_res2.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal2["pending"] == 3.0
    assert pto_bal2["available"] == 7.0


# ==========================================
# 12 & 17. Leave Cancellation Releases Balance
# ==========================================
def test_leave_cancellation_releases_balance():
    # Submit request for 3 working days
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
            "reason": "Festival vacation",
        },
    )
    req_id = req_res.json()["request_id"]

    # Cancel the request
    cancel_res = client.put(f"/api/leave-requests/{req_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    assert cancel_res.json()["remaining_available_balance"] == 10.0

    # Verify balance is restored
    bal_res = client.get("/api/employees/E101/balance")
    pto_bal = next(b for b in bal_res.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal["pending"] == 0.0
    assert pto_bal["available"] == 10.0


# ==========================================
# 13. Insufficient Balance Rejection
# ==========================================
def test_insufficient_balance_rejection():
    # E101 has 10 days PTO. Requesting 15 working days should fail with 409
    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-02",
            "end_date": "2026-11-20",  # ~15 working days
            "reason": "Long trip",
        },
    )
    assert res.status_code == 409
    assert "Insufficient" in res.json()["detail"]


# ==========================================
# 14. Overlapping Request Rejection
# ==========================================
def test_overlapping_request_rejection():
    # First request: Oct 19 to Oct 22
    client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
            "reason": "Trip 1",
        },
    )

    # Second overlapping request: Oct 21 to Oct 24
    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-21",
            "end_date": "2026-10-24",
            "reason": "Trip 2",
        },
    )
    assert res.status_code == 409
    assert "Overlapping" in res.json()["detail"]


# ==========================================
# 15. Invalid Leave Type for Location Rejection
# ==========================================
def test_invalid_leave_type_for_location_rejection():
    # E101 is in BLR. Trying to request SG-PTO should be rejected with 400
    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "SG-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
            "reason": "Wrong location leave type",
        },
    )
    assert res.status_code == 400
    assert "does not belong" in res.json()["detail"]


# ==========================================
# 18. Monthly Accrual Idempotency
# ==========================================
def test_monthly_accrual_idempotency():
    # First run for August 2026
    res1 = client.post("/api/accrual/run", json={"year": 2026, "month": 8})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total_accrued"] > 0

    # Second run for August 2026 (same month) -> should skip all without double credit
    res2 = client.post("/api/accrual/run", json={"year": 2026, "month": 8})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_accrued"] == 0
    for detail in data2["details"]:
        assert detail["status"] == "SKIPPED_ALREADY_ACCRUED"
        assert detail["accrued_amount"] == 0.0
