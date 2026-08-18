import httpx

BASE_URL = "http://127.0.0.1:8000/api"

def get_headers(employee_id: str, role: str = "employee") -> dict:
    return {
        "Authorization": f"Bearer session-{employee_id}-{role}",
        "X-Employee-ID": employee_id,
    }

def test_user_specific_outbox_security():
    print("==================================================================")
    print("  TESTING USER-SPECIFIC OUTBOX ACCESS CONTROL & CROSS-USER ISOLATION")
    print("==================================================================")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Clean any existing requests
        existing_res = client.get("/leave-requests?employee_id=E101")
        if existing_res.status_code == 200:
            for req in existing_res.json():
                client.delete(f"/leave-requests/{req['request_id']}")

        # Clear outboxes for all 3 users
        client.delete("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin"))

        # ==============================================================
        # 1. Vijesh submits a leave request
        # ==============================================================
        print("\n>>> Step 1: Vijesh (E101) submits leave request...")
        res_create = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-21",
                "end_date": "2026-08-21",
                "reason": "Family gathering"
            },
            headers=get_headers("E101", "employee")
        )
        assert res_create.status_code == 201
        req1_id = res_create.json()["request_id"]
        print(f"  [+] Request created: {req1_id}")

        try:
            # Check Vijesh's Outbox (Must be empty - email was sent to Kaviya)
            outbox_vijesh_1 = client.get("/leave-requests/notifications/outbox", headers=get_headers("E101", "employee")).json()
            print(f"  [+] Vijesh Outbox Count: {len(outbox_vijesh_1)}")
            assert len(outbox_vijesh_1) == 0, f"Vijesh should see 0 emails, found: {outbox_vijesh_1}"
            print("  [PASS] Vijesh CANNOT see email sent to Kaviya.")

            # Check Kaviya's Outbox (Must have 1 email)
            outbox_kaviya_1 = client.get("/leave-requests/notifications/outbox", headers=get_headers("M201", "manager")).json()
            print(f"  [+] Kaviya Outbox Count: {len(outbox_kaviya_1)}")
            assert len(outbox_kaviya_1) == 1
            assert outbox_kaviya_1[0]["to_email"] == "anbarasukavya7@gmail.com"
            assert outbox_kaviya_1[0]["recipient_name"] == "Kaviya"
            assert outbox_kaviya_1[0]["notification_type"] == "ACTION_REQUIRED"
            print("  [PASS] Kaviya sees EXACTLY 1 email (To: Kaviya).")

            # Check Ahallya's Outbox (Must be empty)
            outbox_ahallya_1 = client.get("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin")).json()
            print(f"  [+] Ahallya Outbox Count: {len(outbox_ahallya_1)}")
            assert len(outbox_ahallya_1) == 0
            print("  [PASS] Ahallya sees 0 emails at Step 1.")

            # Test Malicious attempt: Vijesh requests Kaviya's outbox via query param
            tampered_res = client.get(
                "/leave-requests/notifications/outbox?employee_id=M201",
                headers=get_headers("E101", "employee")
            ).json()
            assert len(tampered_res) == 0, "Security failure: Tampered query parameter leaked other user's data!"
            print("  [PASS] Backend security enforced: Authenticated user cannot access other user's notifications via query parameter tampering.")

            # ==============================================================
            # 2. Kaviya Approves (Advances to Ahallya)
            # ==============================================================
            print("\n>>> Step 2: Kaviya (M201) approves Tier 1...")
            res_appr1 = client.post(
                f"/leave-requests/{req1_id}/approve-tier?approver_id=M201",
                json={"comments": "Manager approval"},
                headers=get_headers("M201", "manager")
            )
            assert res_appr1.status_code == 200

            # Check Vijesh's Outbox (Must still be 0)
            outbox_vijesh_2 = client.get("/leave-requests/notifications/outbox", headers=get_headers("E101", "employee")).json()
            assert len(outbox_vijesh_2) == 0
            print("  [PASS] Vijesh Outbox is still 0 (intermediate notice not sent to requester).")

            # Check Kaviya's Outbox (Must STILL be 1 - Kaviya doesn't get Ahallya's notice)
            outbox_kaviya_2 = client.get("/leave-requests/notifications/outbox", headers=get_headers("M201", "manager")).json()
            assert len(outbox_kaviya_2) == 1
            assert outbox_kaviya_2[0]["to_email"] == "anbarasukavya7@gmail.com"
            print("  [PASS] Kaviya Outbox has ONLY her initial email (cannot see Ahallya's notice).")

            # Check Ahallya's Outbox (Must have 1 email now)
            outbox_ahallya_2 = client.get("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin")).json()
            assert len(outbox_ahallya_2) == 1
            assert outbox_ahallya_2[0]["to_email"] == "ahallyanethrabl@gmail.com"
            assert outbox_ahallya_2[0]["recipient_name"] == "Ahallya Nethra"
            assert outbox_ahallya_2[0]["notification_type"] == "ACTION_REQUIRED"
            print("  [PASS] Ahallya sees EXACTLY 1 email (To: Ahallya Nethra).")

            # ==============================================================
            # 3. Ahallya Approves (Final Approval -> Vijesh)
            # ==============================================================
            print("\n>>> Step 3: Ahallya (ADMIN01) grants final approval...")
            res_appr2 = client.post(
                f"/leave-requests/{req1_id}/approve-tier?approver_id=ADMIN01",
                json={"comments": "HR signoff"},
                headers=get_headers("ADMIN01", "hr_admin")
            )
            assert res_appr2.status_code == 200
            assert res_appr2.json()["status"] == "APPROVED"

            # Check Vijesh's Outbox (Must now have EXACTLY 1 email: FINAL_APPROVAL)
            outbox_vijesh_3 = client.get("/leave-requests/notifications/outbox", headers=get_headers("E101", "employee")).json()
            assert len(outbox_vijesh_3) == 1
            assert outbox_vijesh_3[0]["to_email"] == "vijeshthamodharan@gmail.com"
            assert outbox_vijesh_3[0]["recipient_name"] == "Vijesh"
            assert outbox_vijesh_3[0]["notification_type"] == "FINAL_APPROVAL"
            assert outbox_vijesh_3[0]["subject"] == "Leave Request Approved"
            print("  [PASS] Vijesh sees EXACTLY 1 email (FINAL_APPROVAL - Leave Request Approved).")

            # Check Kaviya's Outbox (Must still have ONLY 1 email)
            outbox_kaviya_3 = client.get("/leave-requests/notifications/outbox", headers=get_headers("M201", "manager")).json()
            assert len(outbox_kaviya_3) == 1
            assert outbox_kaviya_3[0]["to_email"] == "anbarasukavya7@gmail.com"
            print("  [PASS] Kaviya DOES NOT see Vijesh's final approval email.")

            # Check Ahallya's Outbox (Must still have ONLY 1 email)
            outbox_ahallya_3 = client.get("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin")).json()
            assert len(outbox_ahallya_3) == 1
            assert outbox_ahallya_3[0]["to_email"] == "ahallyanethrabl@gmail.com"
            print("  [PASS] Ahallya DOES NOT see Vijesh's final approval email.")
        finally:
            client.delete(f"/leave-requests/{req1_id}")

        # ==============================================================
        # 4. Rejection Workflow Isolation Test
        # ==============================================================
        print("\n>>> Step 4: Testing Rejection Workflow Isolation...")
        client.delete("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin"))

        res_rej_create = client.post(
            "/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-08-25",
                "end_date": "2026-08-25",
                "reason": "Personal errands"
            },
            headers=get_headers("E101", "employee")
        )
        assert res_rej_create.status_code == 201
        rej_req_id = res_rej_create.json()["request_id"]

        try:
            # Kaviya rejects
            res_rej_action = client.post(
                f"/leave-requests/{rej_req_id}/reject-tier?approver_id=M201",
                json={"comments": "Critical sprint deadline"},
                headers=get_headers("M201", "manager")
            )
            assert res_rej_action.status_code == 200

            # Vijesh sees the rejection email
            v_rej_outbox = client.get("/leave-requests/notifications/outbox", headers=get_headers("E101", "employee")).json()
            assert len(v_rej_outbox) == 1
            assert v_rej_outbox[0]["to_email"] == "vijeshthamodharan@gmail.com"
            assert v_rej_outbox[0]["notification_type"] == "REJECTION"
            print("  [PASS] Vijesh sees rejection email.")

            # Kaviya sees ONLY the initial notification (1 email total)
            k_rej_outbox = client.get("/leave-requests/notifications/outbox", headers=get_headers("M201", "manager")).json()
            assert len(k_rej_outbox) == 1
            assert k_rej_outbox[0]["notification_type"] == "ACTION_REQUIRED"
            print("  [PASS] Kaviya does NOT see the rejection notification sent to Vijesh.")

            # Ahallya sees 0 emails
            a_rej_outbox = client.get("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin")).json()
            assert len(a_rej_outbox) == 0
            print("  [PASS] Ahallya sees 0 emails for Kaviya's rejection.")
        finally:
            client.delete(f"/leave-requests/{rej_req_id}")

        # Final clean
        client.delete("/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin"))

    print("\n==================================================================")
    print("  ALL USER-SPECIFIC OUTBOX & SECURITY ISOLATION TESTS PASSED 100%!")
    print("==================================================================")

if __name__ == "__main__":
    test_user_specific_outbox_security()
