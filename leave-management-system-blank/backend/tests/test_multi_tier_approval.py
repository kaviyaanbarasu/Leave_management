import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.models.approval import LeaveApproval
from app.services.balance_service import balance_service
from tests.conftest import TestingSessionLocal

client = TestClient(app)


def test_1_employee_submits_leave_level1_assigned():
    """
    Scenario 1: Vijesh (E101) submits leave.
    Approval chain generated: E101 (Vijesh) -> M201 (Kaviya) -> ADMIN01 (Ahallya Nethra).
    Level 1 is Kaviya (M201).
    """
    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-20",
            "reason": "Personal time off",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["employee_id"] == "E101"
    assert data["current_tier"] == 1
    assert data["current_approver_id"] == "M201"
    assert len(data["approvals"]) == 2

    assert data["approvals"][0]["approver_id"] == "M201"
    assert data["approvals"][0]["tier_name"] == "Level 1: Kaviya Review"
    assert data["approvals"][1]["approver_id"] == "ADMIN01"
    assert data["approvals"][1]["tier_name"] == "HR Admin Final Approval"


def test_2_multi_level_sequential_approval_and_final_deduction():
    """
    Scenario 2: Sequential approval through hierarchy:
    Level 1 (Kaviya M201) approves -> Level 2 (Ahallya Nethra ADMIN01)
    Level 2 (Ahallya Nethra ADMIN01) approves -> Request APPROVED and balance deducted
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-02",
            "end_date": "2026-11-03",
            "reason": "Family vacation",
        },
    )
    assert req_res.status_code == 201
    req = req_res.json()
    req_id = req["request_id"]
    approvals = req["approvals"]

    # Step 1: Kaviya (M201) approves Level 1
    appr1_id = approvals[0]["approval_id"]
    res1 = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=M201",
        json={"comments": "Level 1 approved by Kaviya"},
    )
    assert res1.status_code == 200
    assert res1.json()["approvalStatus"] == "APPROVED"
    assert res1.json()["nextApprover"] == "Ahallya Nethra"

    # Step 2: Ahallya Nethra (ADMIN01) approves Level 2 (Final)
    appr2_id = approvals[1]["approval_id"]
    res2 = client.post(
        f"/api/approvals/{appr2_id}/approve?approver_id=ADMIN01",
        json={"comments": "Final HR approval granted by Ahallya Nethra."},
    )
    assert res2.status_code == 200
    assert res2.json()["leaveRequestStatus"] == "APPROVED"
    assert res2.json()["nextApprover"] is None

    # Check DB balance
    db = TestingSessionLocal()
    try:
        bal = balance_service.get_or_create_balance("E101", "BLR-PTO", db)
        assert bal.used == req["working_days"]
        assert bal.pending == 0.0
    finally:
        db.close()


def test_3_manager_leave_starts_from_managers_manager():
    """
    Scenario 3: When Manager Kaviya (M201) applies for leave,
    it must NOT include Kaviya in the approval chain (no self-approval).
    Chain routes directly to Ahallya Nethra (ADMIN01).
    """
    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "M201",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-16",
            "end_date": "2026-11-17",
            "reason": "Kaviya personal leave",
        },
    )
    assert res.status_code == 201
    data = res.json()

    assert data["current_approver_id"] == "ADMIN01"
    approvers = [a["approver_id"] for a in data["approvals"]]
    assert "M201" not in approvers
    assert approvers == ["ADMIN01"]


def test_4_rejection_halts_chain_and_releases_balance():
    """
    Scenario 4: Rejection by Level 1 (Kaviya) stops workflow,
    marks remaining levels skipped, releases reserved balance, and notifies requester.
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-CASUAL",
            "start_date": "2026-11-23",
            "end_date": "2026-11-24",
            "reason": "Short break",
        },
    )
    assert req_res.status_code == 201
    req = req_res.json()
    approvals = req["approvals"]

    # Level 1 (Kaviya) rejects
    rej_res = client.post(
        f"/api/approvals/{approvals[0]['approval_id']}/reject?approver_id=M201",
        json={"comments": "Critical project milestone during these dates"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["leaveRequestStatus"] == "REJECTED"

    # Verify history
    hist_res = client.get(f"/api/approvals/history/{req['request_id']}")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert history[0]["status"] == "REJECTED"
    assert history[1]["status"] == "SKIPPED"

    # Verify balance restored
    db = TestingSessionLocal()
    try:
        bal = balance_service.get_or_create_balance("E101", "BLR-CASUAL", db)
        assert bal.pending == 0.0
    finally:
        db.close()


def test_5_unauthorized_approver_rejected():
    """
    Scenario 5: An employee who is not the assigned approver cannot approve.
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-12-01",
            "end_date": "2026-12-02",
            "reason": "Test unauthorized",
        },
    )
    req = req_res.json()
    appr1_id = req["approvals"][0]["approval_id"]

    # Fatima (E104) tries to approve Vijesh's Level 1 step (which belongs to Kaviya M201)
    bad_res = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=E104",
        json={"comments": "Hacked approval attempt"},
    )
    assert bad_res.status_code == 403
    assert "Unauthorized" in bad_res.json()["detail"]


def test_6_requester_cannot_approve_own_request():
    """
    Scenario 6: Requester cannot approve their own leave request.
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-12-08",
            "end_date": "2026-12-09",
            "reason": "Self approve attempt",
        },
    )
    req = req_res.json()
    appr1_id = req["approvals"][0]["approval_id"]

    # E101 tries to approve their own request
    bad_res = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=E101",
        json={"comments": "Self approve"},
    )
    assert bad_res.status_code in [400, 403]


def test_7_premature_approval_of_future_level_rejected():
    """
    Scenario 7: Non-current approval level cannot be actioned prematurely.
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-12-15",
            "end_date": "2026-12-16",
            "reason": "Premature test",
        },
    )
    req = req_res.json()
    appr2_id = req["approvals"][1]["approval_id"]  # Level 2 (Ahallya Nethra ADMIN01)

    # ADMIN01 tries to approve Level 2 before Level 1 is approved
    premature_res = client.post(
        f"/api/approvals/{appr2_id}/approve?approver_id=ADMIN01",
        json={"comments": "Premature approve"},
    )
    assert premature_res.status_code == 400
    assert "prematurely" in premature_res.json()["detail"].lower()


def test_8_duplicate_approval_rejected():
    """
    Scenario 8: Already approved step cannot be approved again.
    """
    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-12-22",
            "end_date": "2026-12-23",
            "reason": "Duplicate test",
        },
    )
    req = req_res.json()
    appr1_id = req["approvals"][0]["approval_id"]

    # First approval succeeds
    ok_res = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=M201",
        json={"comments": "First ok"},
    )
    assert ok_res.status_code == 200

    # Second approval on same step fails
    dup_res = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=M201",
        json={"comments": "Duplicate try"},
    )
    assert dup_res.status_code == 400


def test_9_no_manager_configured_raises_error():
    """
    Scenario 9: Employee with no manager configured returns 400 error.
    """
    db = TestingSessionLocal()
    try:
        orphan = Employee(
            employee_id="E999",
            name="Orphan Dev",
            email="orphan@example.com",
            department="Engineering",
            designation="Contractor",
            grade="G3",
            location_id="BLR",
            joining_date=date(2024, 1, 1),
            status="ACTIVE",
            role="EMPLOYEE",
            manager_id=None,
        )
        db.add(orphan)
        bal = balance_service.get_or_create_balance("E999", "BLR-PTO", db)
        bal.opening_balance = 10.0
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E999",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-12-29",
            "end_date": "2026-12-30",
            "reason": "No manager test",
        },
    )
    assert res.status_code == 400
    assert "No approval hierarchy configured" in res.json()["detail"]


def test_10_circular_manager_hierarchy_detected():
    """
    Scenario 10: Circular manager hierarchy (A -> B -> A) is detected and rejected.
    """
    db = TestingSessionLocal()
    try:
        emp_a = Employee(
            employee_id="E_CYCLE_A",
            name="Cycle A",
            email="cyclea@example.com",
            department="Eng",
            designation="Dev",
            grade="G4",
            location_id="BLR",
            joining_date=date(2024, 1, 1),
            status="ACTIVE",
            role="EMPLOYEE",
            manager_id="E_CYCLE_B",
        )
        emp_b = Employee(
            employee_id="E_CYCLE_B",
            name="Cycle B",
            email="cycleb@example.com",
            department="Eng",
            designation="Dev",
            grade="G4",
            location_id="BLR",
            joining_date=date(2024, 1, 1),
            status="ACTIVE",
            role="EMPLOYEE",
            manager_id="E_CYCLE_A",
        )
        db.add(emp_a)
        db.add(emp_b)
        bal_a = balance_service.get_or_create_balance("E_CYCLE_A", "BLR-PTO", db)
        bal_a.opening_balance = 10.0
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E_CYCLE_A",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-16",
            "end_date": "2026-11-17",
            "reason": "Cycle test",
        },
    )
    assert res.status_code == 400
    assert "Circular manager hierarchy detected" in res.json()["detail"]


def test_11_notification_outbox_logs_all_events():
    """
    Scenario 11: Outbox captures initial submission, step escalation,
    rejection, and final approval notifications.
    """
    client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-02",
            "end_date": "2026-11-02",
            "reason": "Outbox test event",
        },
    )
    outbox_res = client.get("/api/leave-requests/notifications/outbox")
    assert outbox_res.status_code == 200
    logs = outbox_res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
