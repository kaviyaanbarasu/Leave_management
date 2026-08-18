from datetime import date
from sqlalchemy.orm import Session
from app.models.location import Location
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.holiday import Holiday
from app.models.accrual_policy import AccrualPolicy
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.models.approval import LeaveApproval


def seed_database(db: Session):
    # 1. Locations
    locations_data = [
        {
            "location_id": "BLR",
            "name": "Bangalore Office",
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "India",
            "weekend_days": [5, 6],  # Saturday, Sunday
        },
        {
            "location_id": "SG",
            "name": "Singapore Office",
            "city": "Singapore",
            "state": "Singapore",
            "country": "Singapore",
            "weekend_days": [5, 6],  # Saturday, Sunday
        },
        {
            "location_id": "NY",
            "name": "New York Office",
            "city": "New York",
            "state": "New York",
            "country": "USA",
            "weekend_days": [5, 6],  # Saturday, Sunday
        },
        {
            "location_id": "DXB",
            "name": "Dubai Office",
            "city": "Dubai",
            "state": "Dubai",
            "country": "UAE",
            "weekend_days": [4, 5],  # Friday, Saturday
        },
    ]

    for loc in locations_data:
        existing = db.query(Location).filter(Location.location_id == loc["location_id"]).first()
        if not existing:
            db.add(Location(**loc))
    db.flush()

    # 2. Leave Types (Location specific)
    leave_types_data = [
        # Bangalore
        {"leave_type_id": "BLR-PTO", "location_id": "BLR", "name": "PTO", "description": "Paid Time Off", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "BLR-CASUAL", "location_id": "BLR", "name": "CASUAL", "description": "Casual Leave", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "BLR-SICK", "location_id": "BLR", "name": "SICK", "description": "Sick Leave", "is_paid": True, "is_accruable": True},
        # Singapore
        {"leave_type_id": "SG-PTO", "location_id": "SG", "name": "PTO", "description": "Annual Paid Leave", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "SG-SICK", "location_id": "SG", "name": "SICK", "description": "Medical Leave", "is_paid": True, "is_accruable": True},
        # New York
        {"leave_type_id": "NY-PTO", "location_id": "NY", "name": "PTO", "description": "Paid Vacation", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "NY-SICK", "location_id": "NY", "name": "SICK", "description": "Paid Sick Days", "is_paid": True, "is_accruable": True},
        # Dubai
        {"leave_type_id": "DXB-PTO", "location_id": "DXB", "name": "PTO", "description": "Annual Leave", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "DXB-CASUAL", "location_id": "DXB", "name": "CASUAL", "description": "Casual Leave", "is_paid": True, "is_accruable": True},
        {"leave_type_id": "DXB-SICK", "location_id": "DXB", "name": "SICK", "description": "Sick Leave", "is_paid": True, "is_accruable": True},
    ]

    for lt in leave_types_data:
        existing = db.query(LeaveType).filter(LeaveType.leave_type_id == lt["leave_type_id"]).first()
        if not existing:
            db.add(LeaveType(**lt))
    db.flush()

    # 3. Accrual Policies
    accrual_policies_data = [
        # Bangalore
        {"location_id": "BLR", "leave_type_id": "BLR-PTO", "grade": "G5", "tenure_from_months": 0, "monthly_accrual": 1.5, "max_balance": 30.0, "carry_forward_limit": 15.0},
        {"location_id": "BLR", "leave_type_id": "BLR-PTO", "grade": None, "tenure_from_months": 0, "monthly_accrual": 1.25, "max_balance": 30.0, "carry_forward_limit": 15.0},
        {"location_id": "BLR", "leave_type_id": "BLR-CASUAL", "grade": "G5", "tenure_from_months": 0, "monthly_accrual": 1.0, "max_balance": 12.0, "carry_forward_limit": 0.0},
        {"location_id": "BLR", "leave_type_id": "BLR-CASUAL", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.75, "max_balance": 12.0, "carry_forward_limit": 0.0},
        {"location_id": "BLR", "leave_type_id": "BLR-SICK", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.5, "max_balance": 10.0, "carry_forward_limit": 5.0},
        # Singapore
        {"location_id": "SG", "leave_type_id": "SG-PTO", "grade": None, "tenure_from_months": 0, "monthly_accrual": 1.5, "max_balance": 25.0, "carry_forward_limit": 10.0},
        {"location_id": "SG", "leave_type_id": "SG-SICK", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.5, "max_balance": 14.0, "carry_forward_limit": 0.0},
        # New York
        {"location_id": "NY", "leave_type_id": "NY-PTO", "grade": None, "tenure_from_months": 0, "monthly_accrual": 1.75, "max_balance": 28.0, "carry_forward_limit": 10.0},
        {"location_id": "NY", "leave_type_id": "NY-SICK", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.6, "max_balance": 12.0, "carry_forward_limit": 0.0},
        # Dubai
        {"location_id": "DXB", "leave_type_id": "DXB-PTO", "grade": None, "tenure_from_months": 0, "monthly_accrual": 1.6, "max_balance": 30.0, "carry_forward_limit": 10.0},
        {"location_id": "DXB", "leave_type_id": "DXB-CASUAL", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.8, "max_balance": 10.0, "carry_forward_limit": 0.0},
        {"location_id": "DXB", "leave_type_id": "DXB-SICK", "grade": None, "tenure_from_months": 0, "monthly_accrual": 0.5, "max_balance": 12.0, "carry_forward_limit": 0.0},
    ]

    for ap in accrual_policies_data:
        existing = (
            db.query(AccrualPolicy)
            .filter(
                AccrualPolicy.location_id == ap["location_id"],
                AccrualPolicy.leave_type_id == ap["leave_type_id"],
                AccrualPolicy.grade == ap["grade"],
                AccrualPolicy.tenure_from_months == ap["tenure_from_months"],
            )
            .first()
        )
        if not existing:
            db.add(AccrualPolicy(**ap))
    db.flush()

    # 4. Holidays for 2026
    holidays_data = [
        # India (BLR)
        {"location_id": "BLR", "name": "Republic Day", "date": date(2026, 1, 26), "type": "PUBLIC"},
        {"location_id": "BLR", "name": "Holi", "date": date(2026, 3, 4), "type": "PUBLIC"},
        {"location_id": "BLR", "name": "Independence Day", "date": date(2026, 8, 15), "type": "PUBLIC"},
        {"location_id": "BLR", "name": "Gandhi Jayanti", "date": date(2026, 10, 2), "type": "PUBLIC"},
        {"location_id": "BLR", "name": "Diwali (Deepavali)", "date": date(2026, 10, 20), "type": "PUBLIC", "description": "Festival of Lights"},
        {"location_id": "BLR", "name": "Christmas Day", "date": date(2026, 12, 25), "type": "PUBLIC"},
        # Singapore (SG)
        {"location_id": "SG", "name": "New Year's Day", "date": date(2026, 1, 1), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Chinese New Year Day 1", "date": date(2026, 2, 17), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Chinese New Year Day 2", "date": date(2026, 2, 18), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Good Friday", "date": date(2026, 4, 3), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Labour Day", "date": date(2026, 5, 1), "type": "PUBLIC"},
        {"location_id": "SG", "name": "National Day", "date": date(2026, 8, 9), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Deepavali", "date": date(2026, 11, 8), "type": "PUBLIC"},
        {"location_id": "SG", "name": "Christmas Day", "date": date(2026, 12, 25), "type": "PUBLIC"},
        # New York (NY)
        {"location_id": "NY", "name": "New Year's Day", "date": date(2026, 1, 1), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Martin Luther King Jr. Day", "date": date(2026, 1, 19), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Memorial Day", "date": date(2026, 5, 25), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Juneteenth", "date": date(2026, 6, 19), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Independence Day", "date": date(2026, 7, 4), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Labor Day", "date": date(2026, 9, 7), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Thanksgiving Day", "date": date(2026, 11, 26), "type": "PUBLIC"},
        {"location_id": "NY", "name": "Christmas Day", "date": date(2026, 12, 25), "type": "PUBLIC"},
        # Dubai (DXB)
        {"location_id": "DXB", "name": "New Year's Day", "date": date(2026, 1, 1), "type": "PUBLIC"},
        {"location_id": "DXB", "name": "Eid Al Fitr", "date": date(2026, 3, 20), "type": "PUBLIC"},
        {"location_id": "DXB", "name": "Arafat Day", "date": date(2026, 5, 27), "type": "PUBLIC"},
        {"location_id": "DXB", "name": "Eid Al Adha", "date": date(2026, 5, 28), "type": "PUBLIC"},
        {"location_id": "DXB", "name": "Islamic New Year", "date": date(2026, 6, 16), "type": "PUBLIC"},
        {"location_id": "DXB", "name": "National Day", "date": date(2026, 12, 2), "type": "PUBLIC"},
    ]

    for hol in holidays_data:
        existing = (
            db.query(Holiday)
            .filter(Holiday.location_id == hol["location_id"], Holiday.date == hol["date"])
            .first()
        )
        if not existing:
            db.add(Holiday(**hol))
    db.flush()

    # 5. Employees & Multi-Tier Hierarchy
    # First, safely clean up deleted employees (E105 - Vikram Joshi, M202 - Rajesh Kumar) if present
    deleted_ids = ["E105", "M202"]
    for d_id in deleted_ids:
        # Re-assign any employees that had deleted employee as manager
        db.query(Employee).filter(Employee.manager_id == d_id).update({"manager_id": "M201"})
        # Clean approvals and requests
        db.query(LeaveApproval).filter(LeaveApproval.approver_id == d_id).delete(synchronize_session=False)
        db.query(LeaveApproval).filter(LeaveApproval.request_id.in_(
            db.query(LeaveRequest.request_id).filter(LeaveRequest.employee_id == d_id)
        )).delete(synchronize_session=False)
        db.query(LeaveRequest).filter(LeaveRequest.employee_id == d_id).delete(synchronize_session=False)
        db.query(EmployeeLeaveBalance).filter(EmployeeLeaveBalance.employee_id == d_id).delete(synchronize_session=False)
        db.query(Employee).filter(Employee.employee_id == d_id).delete(synchronize_session=False)
    db.flush()

    employees_data = [
        {
            "employee_id": "E101",
            "name": "Vijesh",
            "email": "vijeshthamodharan@gmail.com",
            "department": "Engineering",
            "designation": "Senior Software Engineer",
            "grade": "G5",
            "location_id": "BLR",
            "joining_date": date(2024, 1, 15),
            "status": "ACTIVE",
            "role": "EMPLOYEE",
            "password": "password123",
            "manager_id": "M201",
            "initial_balances": {"BLR-PTO": 10.0, "BLR-CASUAL": 5.0, "BLR-SICK": 5.0},
        },
        {
            "employee_id": "M201",
            "name": "Kaviya",
            "email": "anbarasukavya7@gmail.com",
            "department": "Engineering",
            "designation": "Director of Engineering",
            "grade": "G7",
            "location_id": "BLR",
            "joining_date": date(2023, 1, 10),
            "status": "ACTIVE",
            "role": "MANAGER",
            "password": "password123",
            "manager_id": "ADMIN01",
            "initial_balances": {"BLR-PTO": 18.0, "BLR-CASUAL": 6.0, "BLR-SICK": 8.0},
        },
        {
            "employee_id": "E102",
            "name": "Kartik",
            "email": "kartik@example.com",
            "department": "Engineering",
            "designation": "Software Engineer",
            "grade": "G5",
            "location_id": "SG",
            "joining_date": date(2024, 6, 1),
            "status": "ACTIVE",
            "role": "EMPLOYEE",
            "password": "password123",
            "manager_id": "M201",
            "initial_balances": {"SG-PTO": 10.0, "SG-SICK": 5.0},
        },
        {
            "employee_id": "E103",
            "name": "Divya",
            "email": "divya@example.com",
            "department": "Engineering",
            "designation": "Software Engineer",
            "grade": "G5",
            "location_id": "NY",
            "joining_date": date(2023, 3, 10),
            "status": "ACTIVE",
            "role": "EMPLOYEE",
            "password": "password123",
            "manager_id": "M201",
            "initial_balances": {"NY-PTO": 12.0, "NY-SICK": 5.0},
        },
        {
            "employee_id": "E104",
            "name": "Fatima Al-Mansoor",
            "email": "fatima.almansoor@example.com",
            "department": "Operations",
            "designation": "Operations Lead",
            "grade": "G5",
            "location_id": "DXB",
            "joining_date": date(2024, 2, 1),
            "status": "ACTIVE",
            "role": "EMPLOYEE",
            "password": "password123",
            "manager_id": "ADMIN01",
            "initial_balances": {"DXB-PTO": 12.0, "DXB-CASUAL": 4.0, "DXB-SICK": 5.0},
        },
        {
            "employee_id": "ADMIN01",
            "name": "Ahallya Nethra",
            "email": "ahallyanethrabl@gmail.com",
            "department": "Human Resources",
            "designation": "Head of People & HR Operations",
            "grade": "G8",
            "location_id": "BLR",
            "joining_date": date(2022, 1, 1),
            "status": "ACTIVE",
            "role": "HR_ADMIN",
            "password": "admin123",
            "manager_id": None,
            "initial_balances": {"BLR-PTO": 25.0, "BLR-CASUAL": 8.0, "BLR-SICK": 10.0},
        },
    ]

    # 5. Employees & Multi-Tier Hierarchy (Pass 1: Insert/Update Employees without manager FK)
    for emp_info in employees_data:
        emp_dict = {k: v for k, v in emp_info.items() if k not in ["initial_balances", "manager_id"]}
        emp = db.query(Employee).filter(Employee.employee_id == emp_dict["employee_id"]).first()
        if not emp:
            emp = Employee(**emp_dict)
            db.add(emp)
            db.flush()
        else:
            emp.name = emp_dict.get("name", emp.name)
            emp.email = emp_dict.get("email", emp.email)
            emp.department = emp_dict.get("department", emp.department)
            emp.designation = emp_dict.get("designation", emp.designation)
            emp.grade = emp_dict.get("grade", emp.grade)
            emp.role = emp_dict.get("role", "EMPLOYEE")
            emp.password = emp_dict.get("password", "password123")
            emp.location_id = emp_dict.get("location_id", emp.location_id)
            emp.status = "ACTIVE"

    db.flush()

    # Pass 2: Set manager_id hierarchy now that all employees exist
    for emp_info in employees_data:
        emp = db.query(Employee).filter(Employee.employee_id == emp_info["employee_id"]).first()
        if emp:
            emp.manager_id = emp_info.get("manager_id")

        # Seed initial balances
        for lt_id, opening in emp_info["initial_balances"].items():
            bal = (
                db.query(EmployeeLeaveBalance)
                .filter(
                    EmployeeLeaveBalance.employee_id == emp.employee_id,
                    EmployeeLeaveBalance.leave_type_id == lt_id,
                )
                .first()
            )
            if not bal:
                bal = EmployeeLeaveBalance(
                    employee_id=emp.employee_id,
                    leave_type_id=lt_id,
                    opening_balance=opening,
                    accrued=0.0,
                    used=0.0,
                    pending=0.0,
                    adjusted=0.0,
                    as_of_date=date.today(),
                )
                db.add(bal)

    db.commit()
