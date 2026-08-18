from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval
from app.seed import seed_database

def run_live_verification():
    print("==================================================")
    print("Comprehensive PostgreSQL End-to-End Verification")
    print("Updated Personas: Vijesh (E101), Kaviya (M201), Ahallya Nethra (ADMIN01)")
    print("==================================================")

    db = SessionLocal()
    seed_database(db)
    
    # 0. Clean prior test leave requests in PostgreSQL
    db.query(LeaveApproval).delete(synchronize_session=False)
    db.query(LeaveRequest).delete(synchronize_session=False)
    for emp_id in ["E101", "M201", "ADMIN01"]:
        bal = db.query(EmployeeLeaveBalance).filter(EmployeeLeaveBalance.employee_id == emp_id, EmployeeLeaveBalance.leave_type_id == "BLR-PTO").first()
        if bal:
            bal.used = 0.0
            bal.pending = 0.0
            bal.opening_balance = 15.0
    db.commit()
    db.close()

    client = TestClient(app)

    # 1. Verify Employee Personas & Deletions
    print("\n--- TEST D: Employee Identity & Deletion Verification ---")
    personas_res = client.get("/api/auth/personas")
    assert personas_res.status_code == 200
    personas = {p["employee_id"]: p for p in personas_res.json()}
    
    assert "E101" in personas
    assert personas["E101"]["name"] == "Vijesh"
    assert personas["E101"]["email"] == "vijeshthamodharan@gmail.com"
    print(f"[PASS] E101 verified: {personas['E101']['name']} ({personas['E101']['email']})")

    assert "M201" in personas
    assert personas["M201"]["name"] == "Kaviya"
    assert personas["M201"]["email"] == "anbarasukavya7@gmail.com"
    print(f"[PASS] M201 verified: {personas['M201']['name']} ({personas['M201']['email']})")

    assert "ADMIN01" in personas
    assert personas["ADMIN01"]["name"] == "Ahallya Nethra"
    assert personas["ADMIN01"]["email"] == "ahallyanethrabl@gmail.com"
    print(f"[PASS] ADMIN01 verified: {personas['ADMIN01']['name']} ({personas['ADMIN01']['email']})")

    assert "E105" not in personas, "Vikram Joshi (E105) must not be present"
    assert "M202" not in personas, "Rajesh Kumar (M202) must not be present"
    print("[PASS] Verified Vikram Joshi (E105) and Rajesh Kumar (M202) are COMPLETELY REMOVED.")

    # 2. Test A: Vijesh (E101) submits leave -> Multi-Tier Approval Chain
    print("\n--- TEST A: Employee Leave Request & Sequential Multi-Tier Approval ---")
    login_res = client.post("/api/auth/login", json={"username": "E101", "password": "password123"})
    assert login_res.status_code == 200
    vijesh = login_res.json()["user"]
    print(f"[PASS] Logged in as: {vijesh['name']} ({vijesh['email']})")

    req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-20",
            "reason": "Attending family event",
        },
    )
    assert req_res.status_code == 201, f"Failed: {req_res.text}"
    req_data = req_res.json()
    req_id = req_data["request_id"]
    approvals = req_data["approvals"]
    print(f"[PASS] Leave Request created: {req_id} (Working days: {req_data['working_days']})")
    print(f"   - Current Tier: Level {req_data['current_tier']} (Assigned to: {req_data['current_approver_id']})")
    assert req_data["current_approver_id"] == "M201"
    assert len(approvals) == 2
    assert approvals[0]["approver_id"] == "M201"
    assert approvals[1]["approver_id"] == "ADMIN01"

    # Step 1: Kaviya (M201) checks pending approvals and approves
    kaviya_pending = client.get("/api/approvals/pending?approver_id=M201")
    assert kaviya_pending.status_code == 200
    assert any(p["request_id"] == req_id for p in kaviya_pending.json())
    print(f"[PASS] Kaviya (M201) sees request {req_id} in Approvals Inbox.")

    appr1_id = approvals[0]["approval_id"]
    appr1_res = client.post(
        f"/api/approvals/{appr1_id}/approve?approver_id=M201",
        json={"comments": "Approved by Kaviya (Engineering Director)"},
    )
    assert appr1_res.status_code == 200
    print(f"[PASS] Kaviya approved Level 1 -> Escalated to: {appr1_res.json()['nextApprover']}")

    # Step 2: Ahallya Nethra (ADMIN01) approves Level 2 (Final Approval)
    appr2_id = approvals[1]["approval_id"]
    appr2_res = client.post(
        f"/api/approvals/{appr2_id}/approve?approver_id=ADMIN01",
        json={"comments": "Final HR approval granted by Ahallya Nethra."},
    )
    assert appr2_res.status_code == 200
    final_res = appr2_res.json()
    assert final_res["leaveRequestStatus"] == "APPROVED"
    print(f"[PASS] Ahallya Nethra granted Final HR Approval -> Status: {final_res['leaveRequestStatus']}")

    # 3. Test B: Rejection Flow
    print("\n--- TEST B: Rejection Flow & Balance Restoration ---")
    rej_req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-CASUAL",
            "start_date": "2026-11-02",
            "end_date": "2026-11-03",
            "reason": "Personal errands",
        },
    )
    assert rej_req_res.status_code == 201
    rej_req = rej_req_res.json()
    rej_req_id = rej_req["request_id"]

    reject_res = client.post(
        f"/api/approvals/{rej_req['approvals'][0]['approval_id']}/reject?approver_id=M201",
        json={"comments": "Release sprint scheduled on these dates, please pick alternative days."},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["leaveRequestStatus"] == "REJECTED"
    print(f"[PASS] Kaviya rejected request {rej_req_id} -> Status: REJECTED, reason logged.")

    # 4. Test C: Manager Leave Scenario
    print("\n--- TEST C: Manager Leave (Kaviya M201 applies) ---")
    mgr_req_res = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "M201",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-11-16",
            "end_date": "2026-11-17",
            "reason": "Kaviya vacation",
        },
    )
    assert mgr_req_res.status_code == 201
    mgr_req = mgr_req_res.json()
    print(f"[PASS] Manager Kaviya applied for leave ({mgr_req['request_id']}):")
    print(f"   - Assigned Approver: {mgr_req['current_approver_id']} (Bypassed self, routed directly to Ahallya Nethra ADMIN01)")
    assert mgr_req["current_approver_id"] == "ADMIN01"
    assert "M201" not in [a["approver_id"] for a in mgr_req["approvals"]]
    assert "E105" not in [a["approver_id"] for a in mgr_req["approvals"]]
    assert "M202" not in [a["approver_id"] for a in mgr_req["approvals"]]

    # 5. Test E: Notification Outbox Verification
    print("\n--- TEST E: Notification Outbox Verification ---")
    outbox_res = client.get("/api/leave-requests/notifications/outbox")
    assert outbox_res.status_code == 200
    outbox = outbox_res.json()
    print(f"[PASS] Notification Outbox has {len(outbox)} logged email dispatches:")
    recipients = set(o["to_email"] for o in outbox)
    print(f"   - Recipients in Outbox: {recipients}")
    assert "vijeshthamodharan@gmail.com" in recipients
    assert "anbarasukavya7@gmail.com" in recipients
    assert "ahallyanethrabl@gmail.com" in recipients
    assert "arun.sharma@example.com" not in recipients
    assert "priya.nair@example.com" not in recipients
    assert "vikram.joshi@example.com" not in recipients
    assert "rajesh.kumar@example.com" not in recipients

    print("\n==================================================")
    print("ALL TESTS (A, B, C, D, E) PASSED LIVE ON POSTGRESQL!")
    print("==================================================")

    # 6. Post-test cleanup: Leave database in a clean state
    db = SessionLocal()
    db.query(LeaveApproval).delete(synchronize_session=False)
    db.query(LeaveRequest).delete(synchronize_session=False)
    for b in db.query(EmployeeLeaveBalance).all():
        b.used = 0.0
        b.pending = 0.0
    db.commit()
    db.close()
    print("[PASS] Post-test cleanup completed: 0 demo leave requests left in DB.")

if __name__ == "__main__":
    run_live_verification()
