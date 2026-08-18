import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(endpoint, data=None, method="GET"):
    url = f"{BASE_URL}{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def verify_scoping():
    print("=== 1. TEST LOGIN VIJESH (INDIA / BLR) ===")
    res_vijesh = make_req("/auth/login", {"username": "E101", "password": "password123"}, "POST")
    user = res_vijesh["user"]
    print(f"Logged in: {user['name']} | ID: {user['employee_id']} | Grade: {user['grade']} | Location: {user['location_id']} | Role: {user['role']}")
    assert user["employee_id"] == "E101"
    assert user["name"] == "Vijesh"
    assert user["location_id"] == "BLR"
    assert user["role"] == "EMPLOYEE"

    print("\n=== 2. VERIFY SCOPED LEAVE TYPES FOR BLR (INDIA) ===")
    lts = make_req(f"/leave-types?location_id={user['location_id']}")
    lt_ids = [lt["leave_type_id"] for lt in lts]
    print(f"Leave Types for {user['location_id']}: {lt_ids}")
    assert all(lt_id.startswith("BLR-") for lt_id in lt_ids), "All leave types must belong to BLR"

    print("\n=== 3. VERIFY SCOPED HOLIDAYS FOR BLR (INDIA) ===")
    hols = make_req(f"/holidays?location_id={user['location_id']}&year=2026")
    hol_names = [h["name"] for h in hols]
    print(f"Holidays in {user['location_id']}: {len(hols)} items -> {hol_names[:3]}...")
    assert all(h["location_id"] == "BLR" for h in hols), "All holidays must belong to BLR"

    print("\n=== 4. VERIFY VIJESH'S PERSONAL BALANCES ===")
    bals = make_req(f"/employees/{user['employee_id']}/balance")
    print(f"Balances for {user['name']}: {[{b['leave_type_id']: b['available']} for b in bals['balances']]}")
    assert len(bals["balances"]) > 0

    print("\n=== 5. TEST PERSONA SWITCH TO MEI LING (SINGAPORE / SG) ===")
    res_sg = make_req("/auth/login", {"username": "E102", "password": "password123"}, "POST")
    user_sg = res_sg["user"]
    print(f"Logged in: {user_sg['name']} | ID: {user_sg['employee_id']} | Location: {user_sg['location_id']}")
    assert user_sg["location_id"] == "SG"
    
    sg_lts = make_req(f"/leave-types?location_id={user_sg['location_id']}")
    sg_lt_ids = [lt["leave_type_id"] for lt in sg_lts]
    print(f"Leave Types for Singapore: {sg_lt_ids}")
    assert all(lt_id.startswith("SG-") for lt_id in sg_lt_ids)

    sg_hols = make_req(f"/holidays?location_id={user_sg['location_id']}&year=2026")
    print(f"Holidays for Singapore: {[h['name'] for h in sg_hols]}")
    assert all(h["location_id"] == "SG" for h in sg_hols)

    print("\n=== 6. TEST LOGIN AS HR ADMIN (GLOBAL SCOPE) ===")
    res_admin = make_req("/auth/login", {"username": "ADMIN01", "password": "admin123"}, "POST")
    user_admin = res_admin["user"]
    print(f"Logged in: {user_admin['name']} | Role: {user_admin['role']}")
    assert user_admin["role"] == "HR_ADMIN"

    all_emps = make_req("/employees")
    print(f"Admin directory view: {len(all_emps)} active employees across all offices.")
    assert len(all_emps) >= 5

    print("\n[SUCCESS] ALL AUTHENTICATION AND SCOPING CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    verify_scoping()
