import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api"
VITE_URL = "http://localhost:3000/api"

def test_live_system():
    print("=== TESTING LIVE DYNAMIC PTO & LEAVE MANAGEMENT SYSTEM ===")
    
    with httpx.Client(timeout=10.0) as client:
        # 1. Health Check
        res = client.get(f"{BASE_URL}/health")
        print(f"[1] Health Check: {res.status_code} -> {res.json()}")
        assert res.status_code == 200

        # 2. Locations
        res = client.get(f"{BASE_URL}/locations")
        print(f"[2] Locations ({len(res.json())}): {[l['location_id'] for l in res.json()]}")
        assert len(res.json()) >= 4
        dxb = next(l for l in res.json() if l['location_id'] == 'DXB')
        print(f"    Dubai Weekend Config: {dxb['weekend_days']} (Friday & Saturday)")
        assert dxb['weekend_days'] == [4, 5]

        # 3. Location-Specific Leave Types
        res_blr = client.get(f"{BASE_URL}/leave-types?location_id=BLR")
        res_sg = client.get(f"{BASE_URL}/leave-types?location_id=SG")
        print(f"[3] BLR Leave Types: {[lt['name'] for lt in res_blr.json()]}")
        print(f"    SG Leave Types: {[lt['name'] for lt in res_sg.json()]}")
        assert "CASUAL" in [lt['name'] for lt in res_blr.json()]
        assert "CASUAL" not in [lt['name'] for lt in res_sg.json()]

        # 4. Holidays (2026 Diwali in Bangalore)
        res_hols = client.get(f"{BASE_URL}/holidays?location_id=BLR&year=2026")
        diwali = next(h for h in res_hols.json() if "Diwali" in h['name'])
        print(f"[4] Bangalore Diwali 2026: {diwali['date']} ({diwali['name']})")
        assert diwali['date'] in ["2026-11-08", "2026-10-20"]

        # 5. Employees & Initial Balance
        res_emps = client.get(f"{BASE_URL}/employees")
        print(f"[5] Employees ({len(res_emps.json())}): {[e['name'] + ' (' + e['employee_id'] + ')' for e in res_emps.json()]}")
        
        # Cancel/cleanup any previous pending test requests for E101
        res_existing_reqs = client.get(f"{BASE_URL}/leave-requests?employee_id=E101").json()
        for r in res_existing_reqs:
            client.delete(f"{BASE_URL}/leave-requests/{r['request_id']}")

        res_bal = client.get(f"{BASE_URL}/employees/E101/balance")
        print(f"    E101 (Vijesh) Initial Balances: {json.dumps(res_bal.json()['balances'], indent=2)}")
        initial_pto_available = next(b['available'] for b in res_bal.json()['balances'] if b['leave_type_id'] == 'BLR-PTO')

        # Clean any existing leave requests for E101 in live test
        existing_reqs = client.get(f"{BASE_URL}/leave-requests?employee_id=E101").json()
        for r in existing_reqs:
            client.delete(f"{BASE_URL}/leave-requests/{r['request_id']}")

        # 6. Preview Calculation
        preview_payload = {
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-10-19",
            "end_date": "2026-10-22"
        }
        res_preview = client.post(f"{BASE_URL}/leave-requests/preview", json=preview_payload)
        print(f"[6] Leave Request Preview (Oct 19 to Oct 22, 2026):")
        print(f"    Total Calendar Days: {res_preview.json()['total_calendar_days']}")
        print(f"    Calculated Working Days: {res_preview.json()['working_days']} (Diwali excluded!)")
        print(f"    Current Available: {res_preview.json()['current_available_balance']}")
        print(f"    Projected Remaining: {res_preview.json()['projected_remaining_balance']}")
        assert res_preview.json()['total_calendar_days'] == 4
        assert res_preview.json()['working_days'] == 3.0

        # 7. Create Leave Request (Atomic Pending Reservation)
        create_payload = {
            **preview_payload,
            "reason": "Festival vacation"
        }
        res_create = client.post(f"{BASE_URL}/leave-requests", json=create_payload)
        req = res_create.json()
        print(f"[7] Created Leave Request: {res_create.status_code}")
        print(f"    Request ID: {req['request_id']}")
        print(f"    Status: {req['status']}")
        print(f"    Working Days Reserved: {req['reserved_days']}")
        print(f"    Remaining Available Balance: {req['remaining_available_balance']}")
        assert res_create.status_code == 201
        assert req['status'] in ["PENDING", "PENDING_MANAGER"]
        assert req['reserved_days'] == 3.0
        assert req['remaining_available_balance'] == initial_pto_available - 3.0

        # Verify balance reflects pending reservation
        res_bal_after = client.get(f"{BASE_URL}/employees/E101/balance")
        pto_bal = next(b for b in res_bal_after.json()['balances'] if b['leave_type_id'] == 'BLR-PTO')
        print(f"    Balance after reservation -> Pending: {pto_bal['pending']}, Available: {pto_bal['available']}")
        assert pto_bal['pending'] >= 3.0

        # 8. Cancel Leave Request (Release Pending Reservation)
        res_cancel = client.put(f"{BASE_URL}/leave-requests/{req['request_id']}/cancel")
        print(f"[8] Cancelled Leave Request: {res_cancel.status_code}")
        print(f"    Status: {res_cancel.json()['status']}")
        print(f"    Restored Available Balance: {res_cancel.json()['remaining_available_balance']}")
        assert res_cancel.status_code == 200
        assert res_cancel.json()['status'] == "CANCELLED"

        res_bal_cancel = client.get(f"{BASE_URL}/employees/E101/balance")
        pto_bal_cancel = next(b for b in res_bal_cancel.json()['balances'] if b['leave_type_id'] == 'BLR-PTO')
        print(f"    Balance after cancellation -> Pending: {pto_bal_cancel['pending']}, Available: {pto_bal_cancel['available']}")
        assert pto_bal_cancel['available'] == initial_pto_available

        # 9 & 10. Monthly Accrual & Idempotency
        test_year = 2026
        res_accrual1 = client.post(f"{BASE_URL}/accrual/run", json={"year": test_year, "month": 8})
        print(f"[9] Monthly Accrual Run (Aug 2026): {res_accrual1.json()['total_accrued']} items accrued of {res_accrual1.json()['total_processed']} processed.")
        assert res_accrual1.status_code == 200

        res_accrual2 = client.post(f"{BASE_URL}/accrual/run", json={"year": test_year, "month": 8})
        print(f"[10] Monthly Accrual Idempotency Re-run (Aug 2026): {res_accrual2.json()['total_accrued']} items accrued (all skipped).")
        assert res_accrual2.status_code == 200
        assert res_accrual2.json()['total_accrued'] == 0

        # 11. Test Vite Proxy (Frontend proxy to backend)
        res_vite = client.get(f"{VITE_URL}/health")
        print(f"[11] Vite Frontend Proxy (/api/health): {res_vite.status_code} -> {res_vite.json()}")
        assert res_vite.status_code == 200

    print("\n>>> ALL LIVE INTEGRATION CHECKS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    test_live_system()
