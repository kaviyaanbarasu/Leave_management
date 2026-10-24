import httpx
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def test_dynamic_postgres():
    """Verify dynamic PostgreSQL employee creation, balance initialization, adjustment, and leave application workflow.

    Raises:
        AssertionError: If any verification step fails.
    """
    print("\n=======================================================")
    print("  COMPREHENSIVE POSTGRESQL DYNAMIC SYSTEM VERIFICATION ")
    print("=======================================================\n")

    with httpx.Client(timeout=10.0) as client:
        # 1. Health & Database Check
        res = client.get(f"{BASE_URL}/health")
        assert res.status_code == 200
        print("[+] 1. Health & Postgres DB: OK")

        # 2. Dynamic Employee Creation & Auto-initialization of Balances
        new_emp_id = "E999"
        # Cleanup if exists
        client.delete(f"{BASE_URL}/employees/{new_emp_id}")

        create_emp_payload = {
            "employee_id": new_emp_id,
            "name": "Alex Rivera",
            "email": "alex.rivera@example.com",
            "department": "Cybernetics",
            "designation": "Staff Engineer",
            "grade": "G5",
            "location_id": "BLR",
            "joining_date": str(date.today()),
            "manager_id": "M201",
            "status": "ACTIVE"
        }
        res_emp = client.post(f"{BASE_URL}/employees", json=create_emp_payload)
        assert res_emp.status_code == 201, f"Failed: {res_emp.text}"
        print(f"[+] 2. Created Employee {new_emp_id} in PostgreSQL: OK")

        # Verify auto-initialized balances
        res_bal = client.get(f"{BASE_URL}/employees/{new_emp_id}/balance")
        balances = res_bal.json()["balances"]
        assert len(balances) >= 3
        print(f"[+] 3. Auto-initialized {len(balances)} Leave Types for {new_emp_id}: OK")

        # 3. Dynamic Manual Balance Adjustment
        res_adj = client.post(
            f"{BASE_URL}/employees/{new_emp_id}/adjust-balance",
            json={
                "leave_type_id": "BLR-PTO",
                "adjustment_days": 5.0,
                "reason": "Sign-on bonus days"
            }
        )
        assert res_adj.status_code == 200
        pto_bal = next(b for b in res_adj.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
        assert pto_bal["adjusted"] == 5.0
        print(f"[+] 4. Adjusted +5.0 Days to BLR-PTO -> Available: {pto_bal['available']}: OK")

        # 4. Apply for Leave with Dynamic Dates
        today = date.today()
        # Find next Monday to Wednesday
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        start_d = today + timedelta(days=days_ahead)
        end_d = start_d + timedelta(days=2)

        res_leave = client.post(
            f"{BASE_URL}/leave-requests",
            json={
                "employee_id": new_emp_id,
                "leave_type_id": "BLR-PTO",
                "start_date": str(start_d),
                "end_date": str(end_d),
                "reason": "Dynamic test vacation"
            }
        )
        assert res_leave.status_code == 201
        req_data = res_leave.json()
        req_id = req_data["request_id"]
        working_days = req_data["working_days"]
        assert req_data["status"] == "PENDING_MANAGER"
        assert req_data["reserved_days"] == working_days
        print(f"[+] 5. Created Leave Request {req_id} (PENDING_MANAGER, {working_days} working days reserved): OK")

        # 5. Approve Request -> Verify multi-tier and used balance incremented
        client.post(f"{BASE_URL}/leave-requests/{req_id}/approve-tier?approver_id=M201", json={"comments": "Tier 1 ok"})
        res_approve = client.post(f"{BASE_URL}/leave-requests/{req_id}/approve-tier?approver_id=ADMIN01", json={"comments": "Final ok"})
        assert res_approve.status_code == 200
        assert res_approve.json()["status"] == "APPROVED"
        
        res_bal_app = client.get(f"{BASE_URL}/employees/{new_emp_id}/balance")
        pto_app = next(b for b in res_bal_app.json()["balances"] if b["leave_type_id"] == "BLR-PTO")
        assert pto_app["pending"] == 0.0
        assert pto_app["used"] == working_days
        print(f"[+] 6. Approved Request {req_id} -> Pending: 0.0, Used: {pto_app['used']}: OK")

        # 6. Apply second leave request and Test Rejection
        start_d2 = start_d + timedelta(days=7)
        end_d2 = start_d2 + timedelta(days=1)
        res_leave2 = client.post(
            f"{BASE_URL}/leave-requests",
            json={
                "employee_id": new_emp_id,
                "leave_type_id": "BLR-CASUAL",
                "start_date": str(start_d2),
                "end_date": str(end_d2),
                "reason": "Rejection test"
            }
        )
        assert res_leave2.status_code == 201
        req_id2 = res_leave2.json()["request_id"]
        
        # Reject via Manager M201
        res_rej = client.post(f"{BASE_URL}/leave-requests/{req_id2}/reject-tier?approver_id=M201", json={"comments": "Busy days"})
        assert res_rej.status_code == 200
        assert res_rej.json()["status"] == "REJECTED"

        res_bal_rej = client.get(f"{BASE_URL}/employees/{new_emp_id}/balance")
        cas_rej = next(b for b in res_bal_rej.json()["balances"] if b["leave_type_id"] == "BLR-CASUAL")
        assert cas_rej["pending"] == 0.0
        print(f"[+] 7. Rejected Request {req_id2} -> Reserved balance released: OK")

        # 7. Clean up test employee
        res_del_emp = client.delete(f"{BASE_URL}/employees/{new_emp_id}")
        assert res_del_emp.status_code == 204
        print(f"[+] 8. Deleted Test Employee {new_emp_id}: OK")

    print("\n=======================================================")
    print("  ALL DYNAMIC POSTGRESQL END-TO-END TESTS SUCCEEDED!  ")
    print("=======================================================\n")

if __name__ == "__main__":
    test_dynamic_postgres()
