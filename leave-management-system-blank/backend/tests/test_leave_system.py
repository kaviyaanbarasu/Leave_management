import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.services.holiday_service import holiday_service
from app.models.location import Location
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_request import EmployeeLeaveBalance
from app.services.accrual_service import accrual_service
from tests.conftest import TestingSessionLocal

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
    assert req_data["status"].startswith("PENDING")
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


# ==========================================
# 19. Leave Approval Deducts Balance
# ==========================================
def test_leave_approval_deducts_balance():
    # Submit request for 3 working days
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22",
            "reason": "Approval test vacation",
        },
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["request_id"]

    # Multi-tier approval: Tier 1 (Manager M201 - Kaviya) -> Tier 2 (HR ADMIN01 - Ahallya Nethra)
    client.post(f"/api/leave-requests/{req_id}/approve-tier?approver_id=M201", json={"comments": "Tier 1 Approved by Kaviya"})
    approve_res = client.post(f"/api/leave-requests/{req_id}/approve-tier?approver_id=ADMIN01", json={"comments": "Final HR Approved by Ahallya Nethra"})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # Verify balance: pending is 0, used is 3.0
    bal_res = client.get("/api/employees/E101/balance")
    pto_bal = next(b for b in bal_res.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal["pending"] == 0.0
    assert pto_bal["used"] >= 3.0


# ==========================================
# 20. Leave Rejection Releases Balance
# ==========================================
def test_leave_rejection_releases_balance():
    # Submit request
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-CASUAL",
            "start_date": "2026-11-02",
            "end_date": "2026-11-03",
            "reason": "Rejection test",
        },
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["request_id"]

    # Reject request via Manager M201 (Kaviya)
    reject_res = client.post(f"/api/leave-requests/{req_id}/reject-tier?approver_id=M201", json={"comments": "Rejection reason by Kaviya"})
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"

    # Verify pending balance released
    bal_res = client.get("/api/employees/E101/balance")
    cas_bal = next(b for b in bal_res.json()["balances"] if b["leave_type_id"] == "BLR-CASUAL")
    assert cas_bal["pending"] == 0.0


# ==========================================
# 21. Balance Adjustment Endpoint
# ==========================================
def test_adjust_employee_balance():
    # Add 5 days of PTO
    adj_res = client.post(
        "/api/employees/E101/adjust-balance",
        json={
            "leave_type_id": "BLR-PTO",
            "adjustment_days": 5.0,
            "reason": "Special performance award",
        },
    )
    assert adj_res.status_code == 200
    pto_bal = next(b for b in adj_res.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
    assert pto_bal["adjusted"] >= 5.0


# ==========================================
# 22. Google Calendar Holiday Status
# ==========================================
def test_google_holiday_status():
    res = client.get("/api/holidays/google-status")
    assert res.status_code == 200
    data = res.json()
    assert "supported_locations" in data
    assert "BLR" in data["supported_locations"]
    assert "SG" in data["supported_locations"]
    assert "NY" in data["supported_locations"]
    assert "DXB" in data["supported_locations"]


# ==========================================
# 23. Google Calendar Holiday Sync Mocked
# ==========================================
def test_google_holiday_sync_mock(monkeypatch):
    from app.services.holiday_service import GoogleCalendarHolidayProvider
    from datetime import date

    # Mock Google Calendar fetch to simulate live Google Calendar API
    mock_holidays = [
        {
            "name": "Republic Day (Google Sync)",
            "date": date(2026, 1, 26),
            "type": "PUBLIC",
            "description": "National Holiday synced via Google Calendar API",
        },
        {
            "name": "Independence Day (Google Sync)",
            "date": date(2026, 8, 15),
            "type": "PUBLIC",
            "description": "National Holiday synced via Google Calendar API",
        },
    ]

    monkeypatch.setattr(GoogleCalendarHolidayProvider, "fetch_holidays", lambda cal_id, yr, key: mock_holidays)

    res = client.post(
        "/api/holidays/sync-google",
        json={
            "location_id": "BLR",
            "year": 2026,
            "api_key": "AIzaSyTestKey",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["synced_count"] == 2

    # Verify holidays were saved in database
    hols_res = client.get("/api/holidays?location_id=BLR&year=2026")
    assert hols_res.status_code == 200
    hol_names = [h["name"] for h in hols_res.json()]
    assert "Republic Day (Google Sync)" in hol_names
    assert "Independence Day (Google Sync)" in hol_names


def test_auth_login_employee():
    """Verify regular employee authentication and profile scoping."""
    res = client.post("/api/auth/login", json={"username": "E101", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["employee_id"] == "E101"
    assert data["user"]["name"] == "Vijesh"
    assert data["user"]["email"] == "vijeshthamodharan@gmail.com"
    assert data["user"]["location_id"] == "BLR"
    assert data["user"]["role"] == "EMPLOYEE"
    assert data["token"].startswith("session-E101")


def test_auth_login_admin():
    """Verify HR Admin authentication and role."""
    res = client.post("/api/auth/login", json={"username": "ADMIN01", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["employee_id"] == "ADMIN01"
    assert data["user"]["name"] == "Ahallya Nethra"
    assert data["user"]["email"] == "ahallyanethrabl@gmail.com"
    assert data["user"]["role"] == "HR_ADMIN"


def test_auth_login_invalid():
    """Verify error on invalid employee ID."""
    res = client.post("/api/auth/login", json={"username": "NONEXISTENT", "password": "password123"})
    assert res.status_code == 401
    assert "not found" in res.json()["detail"].lower()


def test_auth_get_personas():
    """Verify personas endpoint returns all location demo personas."""
    res = client.get("/api/auth/personas")
    assert res.status_code == 200
    personas = res.json()
    assert len(personas) >= 5
    emp_ids = [p["employee_id"] for p in personas]
    assert "E101" in emp_ids
    assert "E102" in emp_ids
    assert "E103" in emp_ids
    assert "E104" in emp_ids
    assert "ADMIN01" in emp_ids
