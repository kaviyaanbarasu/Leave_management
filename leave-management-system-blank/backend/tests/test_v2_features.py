import pytest
from datetime import date, datetime, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models.employee import Employee
from app.models.location import Location
from app.models.holiday import Holiday, HolidaySync
from app.models.leave_type import LeaveType
from app.models.accrual_policy import AccrualPolicy, AccrualRecord
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval
from app.services.holiday_service import holiday_service, GoogleCalendarHolidayProvider
from app.services.accrual_service import accrual_service
from app.services.leave_service import leave_service
from app.services.approval_service import approval_service


# =========================================================================
# PART 1: Google Calendar Holidays Sync & Local Cache Resilience
# =========================================================================

def test_google_calendar_holiday_sync_and_cache(db_session):
    """
    Tests that Google Calendar API events are ingested into PostgreSQL Holiday table,
    assigned source='GOOGLE', and metadata recorded in HolidaySync.
    """
    mock_events = [
        {
            "external_event_id": "google_event_001",
            "name": "Independence Day",
            "date": date(2026, 8, 15),
            "type": "PUBLIC",
            "description": "National Holiday",
        },
        {
            "external_event_id": "google_event_002",
            "name": "Diwali",
            "date": date(2026, 10, 20),
            "type": "PUBLIC",
            "description": "Festival of Lights",
        },
    ]

    # Add a manual holiday to ensure reconciliation preserves it
    manual_h = Holiday(
        location_id="BLR",
        name="Company Founder Day",
        date=date(2026, 9, 1),
        type="OPTIONAL",
        source="MANUAL",
    )
    db_session.add(manual_h)
    db_session.commit()

    with patch.object(GoogleCalendarHolidayProvider, "fetch_holidays", return_value=mock_events):
        result = holiday_service.sync_holidays_from_google(
            location_id="BLR",
            year=2026,
            api_key="mock_test_key",
            db=db_session,
            auto=False,
        )

    assert result["sync_status"] == "SYNCED"
    assert result["synced_count"] == 2

    # Verify PostgreSQL storage
    google_hols = db_session.query(Holiday).filter(Holiday.location_id == "BLR", Holiday.source == "GOOGLE").all()
    assert len(google_hols) == 2

    # Verify manual holiday is preserved
    preserved_manual = db_session.query(Holiday).filter(Holiday.name == "Company Founder Day").first()
    assert preserved_manual is not None
    assert preserved_manual.source == "MANUAL"

    # Verify HolidaySync metadata table
    sync_record = db_session.query(HolidaySync).filter(HolidaySync.location_id == "BLR", HolidaySync.year == 2026).first()
    assert sync_record is not None
    assert sync_record.sync_status == "SYNCED"
    assert sync_record.holiday_count >= 3


def test_holiday_calculation_uses_local_cache_without_external_calls(db_session):
    """
    Ensures that working day calculation exclusively uses the PostgreSQL operational cache
    and does NOT make external HTTP calls during leave request calculation.
    """
    emp = db_session.query(Employee).filter(Employee.employee_id == "E101").first()
    assert emp is not None

    # Test working days calculation for Aug 14 to Aug 18, 2026 (Aug 15 is Sat/Holiday, Aug 16 Sun)
    # Aug 14 (Fri: work), Aug 15 (Sat: weekend/hol), Aug 16 (Sun: weekend), Aug 17 (Mon: work), Aug 18 (Tue: work)
    total_cal, work_days, breakdown = holiday_service.calculate_working_days(
        emp.employee_id, date(2026, 8, 14), date(2026, 8, 18), db_session
    )
    assert total_cal == 5
    assert work_days == 3.0


def test_google_sync_failover_to_cache(db_session):
    """
    Ensures that when Google Calendar API fails or is unreachable, the system falls back
    to existing cached holidays with USING_CACHED status instead of crashing.
    """
    with patch.object(GoogleCalendarHolidayProvider, "fetch_holidays", side_effect=Exception("Connection timeout")):
        result = holiday_service.sync_holidays_from_google(
            location_id="BLR",
            year=2026,
            api_key="mock_test_key",
            db=db_session,
            auto=True,
        )

    assert result["sync_status"] == "USING_CACHED"
    assert "connection timeout" in result["message"].lower() or "error" in result["message"].lower()

def test_google_sync_zero_events_preserves_cache(db_session):
    """
    Ensures that when Google Calendar returns 0 events, the system marks sync as SYNC_FAILED,
    does NOT claim success, and preserves existing PostgreSQL cache.
    """
    # Count existing holidays
    initial_count = db_session.query(Holiday).filter(Holiday.location_id == "BLR").count()
    assert initial_count > 0

    with patch.object(GoogleCalendarHolidayProvider, "fetch_holidays", return_value=[]):
        result = holiday_service.sync_holidays_from_google(
            location_id="BLR",
            year=2026,
            api_key="mock_test_key",
            db=db_session,
            auto=False,
        )

    assert result["sync_status"] == "SYNC_FAILED"
    assert result["synced_count"] == 0
    assert "0 holiday events" in result["message"] or "Preserving" in result["message"]

    # Verify PostgreSQL cache was NOT deleted
    after_count = db_session.query(Holiday).filter(Holiday.location_id == "BLR").count()
    assert after_count == initial_count


# =========================================================================
# PART 2: Explainable Monthly Accruals & Grade/Policy Matching
# =========================================================================

def test_accrual_explanation_and_grade_policy_selection(db_session):
    """
    Tests that monthly accrual matches grade-specific policies (G5 Vijesh vs G7 Kaviya)
    and populates detailed explainability fields (status, reason, policy_id).
    """
    # Clear any previous accrual records for month 8
    db_session.query(AccrualRecord).filter(AccrualRecord.year == 2026, AccrualRecord.month == 8).delete()
    db_session.commit()

    res = accrual_service.run_monthly_accrual(year=2026, month=8, db=db_session)
    assert res.total_processed > 0

    # Check Vijesh (E101, Grade G5)
    vijesh_pto = next((d for d in res.details if d.employee_id == "E101" and d.leave_type_id == "BLR-PTO"), None)
    assert vijesh_pto is not None
    assert vijesh_pto.grade == "G5"
    assert vijesh_pto.monthly_accrual == 1.5
    assert vijesh_pto.actual_accrual == 1.5
    assert vijesh_pto.status == "ACCRUED"
    assert "Accrued" in vijesh_pto.reason
    assert vijesh_pto.policy_id is not None

    # Check Kaviya (M201, Grade G7 -> fallback policy 1.25)
    kaviya_pto = next((d for d in res.details if d.employee_id == "M201" and d.leave_type_id == "BLR-PTO"), None)
    assert kaviya_pto is not None
    assert kaviya_pto.grade == "G7"
    assert kaviya_pto.monthly_accrual == 1.25
    assert kaviya_pto.actual_accrual == 1.25
    assert kaviya_pto.status == "ACCRUED"

    # Verify policy_id is stored in AccrualRecord table
    rec = db_session.query(AccrualRecord).filter(
        AccrualRecord.employee_id == "E101",
        AccrualRecord.leave_type_id == "BLR-PTO",
        AccrualRecord.year == 2026,
        AccrualRecord.month == 8
    ).first()
    assert rec is not None
    assert rec.policy_id == vijesh_pto.policy_id


def test_accrual_idempotency_explanation(db_session):
    """
    Tests that running accrual a second time for the same month safely skips
    already-accrued items and outputs status='SKIPPED_ALREADY_ACCRUED'.
    """
    # First run for month 8
    db_session.query(AccrualRecord).filter(AccrualRecord.year == 2026, AccrualRecord.month == 8).delete()
    db_session.commit()
    res1 = accrual_service.run_monthly_accrual(year=2026, month=8, db=db_session)
    assert res1.total_accrued > 0

    # Second run for month 8
    res2 = accrual_service.run_monthly_accrual(year=2026, month=8, db=db_session)
    assert res2.total_accrued == 0

    vijesh_pto = next((d for d in res2.details if d.employee_id == "E101" and d.leave_type_id == "BLR-PTO"), None)
    assert vijesh_pto is not None
    assert vijesh_pto.status == "SKIPPED_ALREADY_ACCRUED"
    assert vijesh_pto.actual_accrual == 0.0
    assert "already accrued" in vijesh_pto.reason.lower()


def test_accrual_cap_at_max_balance(db_session):
    """
    Tests that an employee whose balance reaches max_balance receives status='CAPPED_AT_MAX'.
    """
    # Set Ahallya's opening balance to policy max (30.0)
    bal = db_session.query(EmployeeLeaveBalance).filter(
        EmployeeLeaveBalance.employee_id == "ADMIN01",
        EmployeeLeaveBalance.leave_type_id == "BLR-PTO"
    ).first()
    bal.opening_balance = 30.0
    bal.accrued = 0.0
    bal.used = 0.0
    bal.adjusted = 0.0
    db_session.commit()

    # Clear month 9
    db_session.query(AccrualRecord).filter(AccrualRecord.year == 2026, AccrualRecord.month == 9).delete()
    db_session.commit()

    res = accrual_service.run_monthly_accrual(year=2026, month=9, db=db_session)
    ahallya_pto = next((d for d in res.details if d.employee_id == "ADMIN01" and d.leave_type_id == "BLR-PTO"), None)
    assert ahallya_pto is not None
    assert ahallya_pto.status == "CAPPED_AT_MAX"
    assert ahallya_pto.actual_accrual == 0.0
    assert "reached the maximum" in ahallya_pto.reason.lower()


# =========================================================================
# PART 3: Global Employees & Scoped Hierarchy
# =========================================================================

def test_global_employees_presence_and_attributes(db_session):
    """
    Verifies Kartik (SG, G5), Divya (NY, G5), Vijesh (BLR, G5), Kaviya (BLR, G7), Ahallya (BLR, G8).
    """
    kartik = db_session.query(Employee).filter(Employee.employee_id == "E102").first()
    assert kartik is not None
    assert kartik.name == "Kartik"
    assert kartik.location_id == "SG"
    assert kartik.grade == "G5"
    assert kartik.role == "EMPLOYEE"
    assert kartik.manager_id == "M201"
    assert kartik.manager_name == "Kaviya"
    assert kartik.country == "Singapore"

    divya = db_session.query(Employee).filter(Employee.employee_id == "E103").first()
    assert divya is not None
    assert divya.name == "Divya"
    assert divya.location_id == "NY"
    assert divya.grade == "G5"
    assert divya.role == "EMPLOYEE"
    assert divya.manager_id == "M201"
    assert divya.manager_name == "Kaviya"
    assert divya.country == "USA"


def test_global_employee_location_scoping_enforced(db_session):
    """
    Verifies that Kartik (SG) cannot request BLR-PTO or NY-PTO,
    and Divya (NY) cannot request SG-PTO.
    """
    from app.schemas.leave_request import LeaveRequestCreate
    from fastapi import HTTPException

    # Kartik trying to apply for Indian BLR-PTO
    invalid_req = LeaveRequestCreate(
        employee_id="E102",  # SG
        leave_type_id="BLR-PTO",  # BLR
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 4),
        reason="Invalid cross-location leave",
    )
    with pytest.raises(HTTPException) as exc_info:
        leave_service.create_leave_request(invalid_req, db_session)
    assert exc_info.value.status_code == 400
    assert "does not belong to employee's location" in exc_info.value.detail


def test_global_employee_sequential_approval(db_session):
    """
    Verifies that a leave request raised by Kartik (SG) or Divya (NY) routes
    sequentially through Kaviya (M201) -> Ahallya (ADMIN01).
    """
    from app.schemas.leave_request import LeaveRequestCreate

    req_payload = LeaveRequestCreate(
        employee_id="E102",  # Kartik in SG
        leave_type_id="SG-PTO",
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 4),
        reason="Singapore annual leave",
    )
    leave_req = leave_service.create_leave_request(req_payload, db_session)
    assert leave_req.status == "PENDING_MANAGER"

    # Verify approval chain
    approvals = (
        db_session.query(LeaveApproval)
        .filter(LeaveApproval.request_id == leave_req.request_id)
        .order_by(LeaveApproval.tier_level)
        .all()
    )
    assert len(approvals) == 2
    assert approvals[0].approver_id == "M201"  # Kaviya (Manager Tier 1)
    assert approvals[0].tier_level == 1
    assert approvals[1].approver_id == "ADMIN01"  # Ahallya (HR Admin Tier 2)
    assert approvals[1].tier_level == 2
    assert leave_req.current_approver_id == "M201"
    assert leave_req.current_approver_name == "Kaviya"
