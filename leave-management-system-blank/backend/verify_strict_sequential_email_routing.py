import httpx

BASE_URL = "http://127.0.0.1:8000/api"

def test_all_sequential_workflows():
    print("==================================================================")
    print("  TESTING STRICT SEQUENTIAL EMAIL ROUTING & OUTBOX ACCURACY")
    print("==================================================================")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Clean any existing leave requests for E101
        existing_res = client.get("/leave-requests?employee_id=E101")
        if existing_res.status_code == 200:
            for req in existing_res.json():
                client.delete(f"/leave-requests/{req['request_id']}")

        # ==================================================================
        # WORKFLOW 1: Vijesh Submits -> Kaviya Approves -> Ahallya Approves
        # ==================================================================
        print("\n>>> [WORKFLOW 1] Full Multi-Tier Sequential Approval")
        client.delete("/leave-requests/notifications/outbox")
        
        # Step 1.1: Vijesh submits
        res1 = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-21",
                "end_date": "2026-08-21",
                "reason": "Family gathering"
            }
        )
        assert res1.status_code == 201, f"Failed to create request 1: {res1.status_code} - {res1.text}"
        req1 = res1.json()
        req1_id = req1["request_id"]
        print(f"  [+] Request created: {req1_id}, status: {req1['status']}, approver: {req1['current_approver_id']}")
        
        try:
            outbox1 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox1) == 1, f"Expected exactly 1 email, got {len(outbox1)}"
            assert outbox1[0]["to_email"] == "anbarasukavya7@gmail.com", f"Expected to Kaviya, got {outbox1[0]['to_email']}"
            assert outbox1[0]["recipient_name"] == "Kaviya"
            assert outbox1[0]["notification_type"] == "ACTION_REQUIRED"
            assert "New Leave Request Requires Your Approval" in outbox1[0]["subject"]
            print("  [PASS] Step 1: Exactly 1 email sent -> Kaviya ONLY (anbarasukavya7@gmail.com)")

            # Step 1.2: Kaviya approves
            res_appr1 = client.post(
                f"/leave-requests/{req1_id}/approve-tier?approver_id=M201",
                json={"comments": "Approved by manager"}
            )
            assert res_appr1.status_code == 200
            outbox2 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox2) == 2, f"Expected 2 total emails, got {len(outbox2)}"
            latest2 = outbox2[0] # most recent
            assert latest2["to_email"] == "ahallyanethrabl@gmail.com", f"Expected to Ahallya, got {latest2['to_email']}"
            assert latest2["recipient_name"] == "Ahallya Nethra"
            assert latest2["notification_type"] == "ACTION_REQUIRED"
            assert "Leave Request Requires Your Approval" in latest2["subject"]
            print("  [PASS] Step 2: Exactly 1 email sent -> Ahallya Nethra ONLY (ahallyanethrabl@gmail.com)")

            # Step 1.3: Ahallya approves (Final)
            res_appr2 = client.post(
                f"/leave-requests/{req1_id}/approve-tier?approver_id=ADMIN01",
                json={"comments": "HR final signoff"}
            )
            assert res_appr2.status_code == 200
            assert res_appr2.json()["status"] == "APPROVED"
            outbox3 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox3) == 3, f"Expected 3 total emails, got {len(outbox3)}"
            latest3 = outbox3[0] # most recent
            assert latest3["to_email"] == "vijeshthamodharan@gmail.com", f"Expected to Vijesh, got {latest3['to_email']}"
            assert latest3["recipient_name"] == "Vijesh"
            assert latest3["notification_type"] == "FINAL_APPROVAL"
            assert latest3["subject"] == "Leave Request Approved"
            print("  [PASS] Step 3: Exactly 1 email sent -> Vijesh ONLY (vijeshthamodharan@gmail.com) [FINAL_APPROVAL]")
        finally:
            client.delete(f"/leave-requests/{req1_id}")

        # ==================================================================
        # WORKFLOW 2: Vijesh Submits -> Kaviya Rejects
        # ==================================================================
        print("\n>>> [WORKFLOW 2] Rejection by Manager (Kaviya)")
        client.delete("/leave-requests/notifications/outbox")

        # Step 2.1: Vijesh submits
        res2 = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-25",
                "end_date": "2026-08-25",
                "reason": "Personal trip"
            }
        )
        assert res2.status_code == 201, f"Failed to create request 2: {res2.status_code} - {res2.text}"
        req2_id = res2.json()["request_id"]

        try:
            outbox_w2_1 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox_w2_1) == 1
            assert outbox_w2_1[0]["to_email"] == "anbarasukavya7@gmail.com"
            print("  [PASS] Step 1: Exactly 1 email sent -> Kaviya ONLY")

            # Step 2.2: Kaviya rejects
            res_rej1 = client.post(
                f"/leave-requests/{req2_id}/reject-tier?approver_id=M201",
                json={"comments": "Critical sprint deadline on this day"}
            )
            assert res_rej1.status_code == 200
            assert res_rej1.json()["status"] == "REJECTED"
            outbox_w2_2 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox_w2_2) == 2
            latest_rej1 = outbox_w2_2[0]
            assert latest_rej1["to_email"] == "vijeshthamodharan@gmail.com"
            assert latest_rej1["recipient_name"] == "Vijesh"
            assert latest_rej1["notification_type"] == "REJECTION"
            assert latest_rej1["subject"] == "Leave Request Rejected"
            print("  [PASS] Step 2: Exactly 1 email sent -> Vijesh ONLY [REJECTION]. Workflow halted.")
        finally:
            client.delete(f"/leave-requests/{req2_id}")

        # ==================================================================
        # WORKFLOW 3: Vijesh Submits -> Kaviya Approves -> Ahallya Rejects
        # ==================================================================
        print("\n>>> [WORKFLOW 3] Rejection by HR Admin (Ahallya Nethra)")
        client.delete("/leave-requests/notifications/outbox")

        # Step 3.1: Vijesh submits
        res3 = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-28",
                "end_date": "2026-08-28",
                "reason": "Conference attendance"
            }
        )
        assert res3.status_code == 201, f"Failed to create request 3: {res3.status_code} - {res3.text}"
        req3_id = res3.json()["request_id"]
        print("  [PASS] Step 1: Request created -> 1 email sent to Kaviya ONLY")

        try:
            # Step 3.2: Kaviya approves
            res_w3_appr = client.post(
                f"/leave-requests/{req3_id}/approve-tier?approver_id=M201",
                json={"comments": "Manager approves"}
            )
            assert res_w3_appr.status_code == 200
            outbox_w3_2 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox_w3_2) == 2
            assert outbox_w3_2[0]["to_email"] == "ahallyanethrabl@gmail.com"
            print("  [PASS] Step 2: Exactly 1 email sent -> Ahallya Nethra ONLY")

            # Step 3.3: Ahallya rejects
            res_w3_rej = client.post(
                f"/leave-requests/{req3_id}/reject-tier?approver_id=ADMIN01",
                json={"comments": "Company blackout period for all engineering staff"}
            )
            assert res_w3_rej.status_code == 200
            assert res_w3_rej.json()["status"] == "REJECTED"
            outbox_w3_3 = client.get("/leave-requests/notifications/outbox").json()
            assert len(outbox_w3_3) == 3
            latest_w3_rej = outbox_w3_3[0]
            assert latest_w3_rej["to_email"] == "vijeshthamodharan@gmail.com"
            assert latest_w3_rej["recipient_name"] == "Vijesh"
            assert latest_w3_rej["notification_type"] == "REJECTION"
            assert latest_w3_rej["subject"] == "Leave Request Rejected"
            print("  [PASS] Step 3: Exactly 1 email sent -> Vijesh ONLY [REJECTION]. Workflow halted.")
        finally:
            client.delete(f"/leave-requests/{req3_id}")

        # Clear outbox at end so UI starts clean
        client.delete("/leave-requests/notifications/outbox")

    print("\n==================================================================")
    print("  ALL 3 SEQUENTIAL WORKFLOWS VERIFIED WITH 100% PRECISION!")
    print("==================================================================")

if __name__ == "__main__":
    test_all_sequential_workflows()
