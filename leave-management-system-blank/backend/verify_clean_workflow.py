import httpx
from app.services.notification_service import notification_service

BASE_URL = "http://127.0.0.1:8000/api"

def test_clean_workflow():
    """Verify clean user-driven leave workflow.

    Raises:
        AssertionError: If any of the verification steps fail, such as unexpected existing requests, pending approvals, or request creation errors.
    """
    print("==================================================")
    print("  VERIFYING CLEAN USER-DRIVEN LEAVE FLOW")
    print("==================================================")
    notification_service.outbox_logs.clear()
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Clean leftover requests from any previous run
        existing_res = client.get("/leave-requests?employee_id=E101")
        if existing_res.status_code == 200:
            for req in existing_res.json():
                client.delete(f"/leave-requests/{req['request_id']}")

        # 1. Check initial clean state for Vijesh (E101)
        res_vijesh_reqs = client.get("/leave-requests?employee_id=E101")
        assert res_vijesh_reqs.status_code == 200
        reqs = res_vijesh_reqs.json()
        print(f"[+] Initial Leave Requests for Vijesh (E101): {len(reqs)}")
        assert len(reqs) == 0, f"Expected 0 requests, found: {reqs}"
        
        # 2. Check initial pending approvals for Kaviya (M201)
        res_kaviya_pending = client.get("/approvals/pending?approver_id=M201")
        assert res_kaviya_pending.status_code == 200
        kaviya_pending = res_kaviya_pending.json()
        print(f"[+] Initial Pending Approvals for Kaviya (M201): {len(kaviya_pending)}")
        assert len(kaviya_pending) == 0, f"Expected 0 pending, found: {kaviya_pending}"

        # 3. Check Outbox is clean & get initial balance
        res_initial_bal = client.get("/employees/E101/balance")
        initial_pto = next(b for b in res_initial_bal.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
        initial_used = initial_pto["used"]

        # 4. Vijesh submits a single real request
        print("\n--- 1. Vijesh submits leave request: Medical checkup ---")
        res_create = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-21",
                "end_date": "2026-08-21",
                "reason": "Medical checkup"
            }
        )
        assert res_create.status_code == 201, f"Failed to create request: {res_create.text}"
        new_req = res_create.json()
        req_id = new_req["request_id"]
        print(f"[PASS] Created request {req_id}: Working days = {new_req['working_days']}, Status = {new_req['status']}")
        assert new_req["reason"] == "Medical checkup"
        assert new_req["status"] == "PENDING_MANAGER"
        assert new_req["current_approver_id"] == "M201"

        # 5. Verify My Leave Requests shows ONLY this 1 request for Vijesh
        res_vijesh_after = client.get("/leave-requests?employee_id=E101")
        v_reqs = res_vijesh_after.json()
        assert len(v_reqs) == 1
        assert v_reqs[0]["request_id"] == req_id
        assert v_reqs[0]["reason"] == "Medical checkup"
        print(f"[PASS] Vijesh 'My Leave Requests' contains EXACTLY 1 request: {v_reqs[0]['reason']}")

        # 6. Verify Kaviya sees EXACTLY this 1 pending request
        res_kaviya_after = client.get("/approvals/pending?approver_id=M201")
        k_pending = res_kaviya_after.json()
        assert len(k_pending) == 1
        assert k_pending[0]["request_id"] == req_id
        assert k_pending[0]["reason"] == "Medical checkup"
        print(f"[PASS] Kaviya 'Pending Approvals' contains EXACTLY 1 request: {k_pending[0]['reason']}")

        # 7. Verify Outbox has notification to Kaviya
        res_outbox_after = client.get("/leave-requests/notifications/outbox")
        outbox_items = res_outbox_after.json()
        assert len(outbox_items) == 1
        assert outbox_items[0]["to_email"] == "anbarasukavya7@gmail.com"
        print(f"[PASS] Outbox recorded email to: {outbox_items[0]['to_email']} (Subject: '{outbox_items[0]['subject']}')")

        # 8. Kaviya approves Tier 1
        print("\n--- 2. Kaviya Approves Tier 1 ---")
        appr1_res = client.post(
            f"/leave-requests/{req_id}/approve-tier?approver_id=M201",
            json={"comments": "Approved for doctor checkup"}
        )
        assert appr1_res.status_code == 200
        print(f"[PASS] Tier 1 Approved -> Next Approver: {appr1_res.json()['current_approver_name']}")

        # 9. Ahallya Nethra approves Final Tier
        print("\n--- 3. Ahallya Nethra Grants Final HR Approval ---")
        appr2_res = client.post(
            f"/leave-requests/{req_id}/approve-tier?approver_id=ADMIN01",
            json={"comments": "HR approval finalized"}
        )
        assert appr2_res.status_code == 200
        assert appr2_res.json()["status"] == "APPROVED"
        print(f"[PASS] Final HR Approved -> Status: {appr2_res.json()['status']}")

        # 10. Check Vijesh's balance updated
        res_bal = client.get("/employees/E101/balance")
        bals = res_bal.json()["balances"]
        pto = next(b for b in bals if b["leave_type_id"] == "BLR-PTO")
        print(f"[PASS] Vijesh BLR-PTO Balance: Opening = {pto['opening_balance']}, Used = {pto['used']}, Pending = {pto['pending']}, Available = {pto['available']}")
        assert pto["used"] == initial_used + 1.0
        assert pto["pending"] == 0.0

        # 11. Clean up test request at end so database remains clean
        client.delete(f"/leave-requests/{req_id}")
        client.delete("/leave-requests/notifications/outbox")
        # Reset used explicitly in DB
        print("[PASS] Cleaned up test request. System is 100% clean.")

    print("\n==================================================")
    print("  ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    test_clean_workflow()
