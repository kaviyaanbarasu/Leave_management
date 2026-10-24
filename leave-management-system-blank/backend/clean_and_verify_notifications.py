import sys
import os
from datetime import date, timedelta
from app.database import SessionLocal, engine
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.models.approval import LeaveApproval
from app.models.notification import Notification
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.schemas.leave_request import LeaveRequestCreate
from app.services.leave_service import leave_service
from app.services.approval_service import approval_service
from app.services.notification_service import notification_service
from app.services.email_service import email_service


def clean_and_verify():
    """Clean and verify the notification system and employee data.

    Returns:
        None

    Raises:
        AssertionError: If any of the required employees (E101, M201, ADMIN01) are missing or have incorrect manager relationships.
    """
    print("=================================================================")
    print("     CLEAN & VERIFY: GMAIL SMTP + SEQUENTIAL APPROVAL OUTBOX     ")
    print("=================================================================")

    db = SessionLocal()
    try:
        # 1. Clean outbox notifications
        print("\n--- 1. Cleaning Outbox Notifications in Database ---")
        deleted_count = db.query(Notification).delete()
        db.commit()
        notification_service.clear_outbox()
        print(f"Cleared {deleted_count} stale notifications from PostgreSQL.")

        # 2. Verify Key Employees
        print("\n--- 2. Verifying Key Employees ---")
        vijesh = db.query(Employee).filter(Employee.employee_id == "E101").first()
        kaviya = db.query(Employee).filter(Employee.employee_id == "M201").first()
        ahallya = db.query(Employee).filter(Employee.employee_id == "ADMIN01").first()

        assert vijesh is not None, "Employee E101 (Vijesh) missing!"
        assert kaviya is not None, "Manager M201 (Kaviya) missing!"
        assert ahallya is not None, "HR Admin ADMIN01 (Ahallya) missing!"

        print(f"  Requester:  {vijesh.name} ({vijesh.employee_id}) -> {vijesh.email}, Manager: {vijesh.manager_id}")
        print(f"  Manager:    {kaviya.name} ({kaviya.employee_id}) -> {kaviya.email}, Manager: {kaviya.manager_id}")
        print(f"  HR Admin:   {ahallya.name} ({ahallya.employee_id}) -> {ahallya.email}, Manager: {ahallya.manager_id}")

        assert vijesh.manager_id == "M201", f"Expected Vijesh's manager to be M201, got {vijesh.manager_id}"
        assert kaviya.manager_id == "ADMIN01", f"Expected Kaviya's manager to be ADMIN01, got {kaviya.manager_id}"

        # 3. Test Full Multi-Tier Approval Flow
        print("\n--- 3. Testing Sequential Approval Flow & Email Notification Routing ---")
        
        # Ensure Vijesh has balance for BLR-PTO
        bal = db.query(EmployeeLeaveBalance).filter(
            EmployeeLeaveBalance.employee_id == "E101",
            EmployeeLeaveBalance.leave_type_id == "BLR-PTO"
        ).first()
        if not bal:
            bal = EmployeeLeaveBalance(
                employee_id="E101",
                leave_type_id="BLR-PTO",
                opening_balance=0.0,
                accrued=25.0,
                used=0.0,
                pending=0.0,
            )
            db.add(bal)
            db.commit()
        else:
            bal.accrued = max(bal.accrued, 25.0)
            db.commit()

        # Step 3.1: Vijesh creates a leave request
        start_d = date(2026, 11, 2)
        end_d = date(2026, 11, 4)
        print(f"Submitting leave request for {vijesh.name}: {start_d} to {end_d}...")

        req = leave_service.create_leave_request(
            payload=LeaveRequestCreate(
                employee_id="E101",
                leave_type_id="BLR-PTO",
                start_date=start_d,
                end_date=end_d,
                reason="Annual Family Vacation",
            ),
            db=db,
        )
        print(f"Leave Request Created: ID={req.request_id}, Status={req.status}, Current Approver={req.current_approver_id}")

        # Check Step 1 Notification: Should be sent to Kaviya ONLY
        kaviya_notifs = notification_service.get_user_outbox_logs(recipient_employee_id="M201", db=db)
        vijesh_notifs = notification_service.get_user_outbox_logs(recipient_employee_id="E101", db=db)
        ahallya_notifs = notification_service.get_user_outbox_logs(recipient_employee_id="ADMIN01", db=db)

        print(f"  Notifications count: Kaviya={len(kaviya_notifs)}, Vijesh={len(vijesh_notifs)}, Ahallya={len(ahallya_notifs)}")
        assert len(kaviya_notifs) == 1, f"Expected 1 notification for Kaviya, got {len(kaviya_notifs)}"
        assert len(vijesh_notifs) == 0, f"Expected 0 notifications for Vijesh at step 1, got {len(vijesh_notifs)}"
        assert len(ahallya_notifs) == 0, f"Expected 0 notifications for Ahallya at step 1, got {len(ahallya_notifs)}"
        assert kaviya_notifs[0]["recipient_employee_id"] == "M201"
        assert kaviya_notifs[0]["to_email"] == "anbarasukavya7@gmail.com"
        print(f"  [OK] Step 1 Email correctly routed to Kaviya ONLY: Subject='{kaviya_notifs[0]['subject']}'")

        # Step 3.2: Kaviya approves (Level 1)
        print("\nKaviya approving Level 1...")
        approval_service.approve_tier(
            request_id=req.request_id,
            approver_id="M201",
            comments="Looks good to me, approved.",
            db=db,
        )

        # Check Step 2 Notification: Should be sent to Ahallya Nethra ONLY
        kaviya_notifs_2 = notification_service.get_user_outbox_logs(recipient_employee_id="M201", db=db)
        vijesh_notifs_2 = notification_service.get_user_outbox_logs(recipient_employee_id="E101", db=db)
        ahallya_notifs_2 = notification_service.get_user_outbox_logs(recipient_employee_id="ADMIN01", db=db)

        print(f"  Notifications count: Kaviya={len(kaviya_notifs_2)}, Vijesh={len(vijesh_notifs_2)}, Ahallya={len(ahallya_notifs_2)}")
        assert len(kaviya_notifs_2) == 1, f"Kaviya should still have 1 notification, got {len(kaviya_notifs_2)}"
        assert len(ahallya_notifs_2) == 1, f"Ahallya should have received 1 notification, got {len(ahallya_notifs_2)}"
        assert len(vijesh_notifs_2) == 0, f"Vijesh should have 0 notifications before final approval, got {len(vijesh_notifs_2)}"
        assert ahallya_notifs_2[0]["recipient_employee_id"] == "ADMIN01"
        assert ahallya_notifs_2[0]["to_email"] == "ahallyanethrabl@gmail.com"
        print(f"  [OK] Step 2 Email correctly routed to Ahallya Nethra ONLY: Subject='{ahallya_notifs_2[0]['subject']}'")

        # Step 3.3: Ahallya approves (Final Tier)
        print("\nAhallya Nethra approving Final Tier...")
        approval_service.approve_tier(
            request_id=req.request_id,
            approver_id="ADMIN01",
            comments="Final approval granted.",
            db=db,
        )

        # Check Step 3 Notification: Final approval should be sent to Vijesh ONLY
        kaviya_notifs_3 = notification_service.get_user_outbox_logs(recipient_employee_id="M201", db=db)
        vijesh_notifs_3 = notification_service.get_user_outbox_logs(recipient_employee_id="E101", db=db)
        ahallya_notifs_3 = notification_service.get_user_outbox_logs(recipient_employee_id="ADMIN01", db=db)

        print(f"  Notifications count: Kaviya={len(kaviya_notifs_3)}, Vijesh={len(vijesh_notifs_3)}, Ahallya={len(ahallya_notifs_3)}")
        assert len(kaviya_notifs_3) == 1, f"Kaviya should have 1 notification, got {len(kaviya_notifs_3)}"
        assert len(ahallya_notifs_3) == 1, f"Ahallya should have 1 notification, got {len(ahallya_notifs_3)}"
        assert len(vijesh_notifs_3) == 1, f"Vijesh should have 1 final approval notification, got {len(vijesh_notifs_3)}"
        assert vijesh_notifs_3[0]["recipient_employee_id"] == "E101"
        assert vijesh_notifs_3[0]["to_email"] == "vijeshthamodharan@gmail.com"
        print(f"  [OK] Step 3 Final Approval Email correctly routed to Vijesh ONLY: Subject='{vijesh_notifs_3[0]['subject']}'")

        # Step 4: Test Rejection Flow
        print("\n--- 4. Testing Rejection Notification Routing ---")
        req_reject = leave_service.create_leave_request(
            payload=LeaveRequestCreate(
                employee_id="E101",
                leave_type_id="BLR-PTO",
                start_date=date(2026, 12, 1),
                end_date=date(2026, 12, 2),
                reason="Short Trip",
            ),
            db=db,
        )
        print(f"Created request {req_reject.request_id} for rejection test...")
        approval_service.reject_tier(
            request_id=req_reject.request_id,
            approver_id="M201",
            comments="Team has critical release on those dates.",
            db=db,
        )

        vijesh_notifs_rej = notification_service.get_user_outbox_logs(recipient_employee_id="E101", db=db)
        # Vijesh now has 2 notifications (1 final approval from earlier + 1 rejection)
        assert len(vijesh_notifs_rej) == 2, f"Expected 2 notifications for Vijesh, got {len(vijesh_notifs_rej)}"
        assert vijesh_notifs_rej[0]["notification_type"] == "REJECTION"
        assert vijesh_notifs_rej[0]["recipient_employee_id"] == "E101"
        print(f"  [OK] Rejection Email correctly routed to Vijesh ONLY: Subject='{vijesh_notifs_rej[0]['subject']}'")

        # Step 5: Test Manager's Own Leave Routing
        print("\n--- 5. Testing Manager's Own Leave Routing (Kaviya -> Ahallya) ---")
        # Ensure Kaviya has balance
        bal_k = db.query(EmployeeLeaveBalance).filter(
            EmployeeLeaveBalance.employee_id == "M201",
            EmployeeLeaveBalance.leave_type_id == "BLR-PTO"
        ).first()
        if not bal_k:
            bal_k = EmployeeLeaveBalance(
                employee_id="M201",
                leave_type_id="BLR-PTO",
                opening_balance=0.0,
                accrued=25.0,
                used=0.0,
                pending=0.0,
            )
            db.add(bal_k)
            db.commit()

        initial_ahallya_count = len(notification_service.get_user_outbox_logs(recipient_employee_id="ADMIN01", db=db))
        req_mgr = leave_service.create_leave_request(
            payload=LeaveRequestCreate(
                employee_id="M201",
                leave_type_id="BLR-PTO",
                start_date=date(2026, 12, 10),
                end_date=date(2026, 12, 11),
                reason="Manager Personal Leave",
            ),
            db=db,
        )
        print(f"Created request {req_mgr.request_id} for Kaviya...")

        ahallya_notifs_mgr = notification_service.get_user_outbox_logs(recipient_employee_id="ADMIN01", db=db)
        assert len(ahallya_notifs_mgr) == initial_ahallya_count + 1
        assert ahallya_notifs_mgr[0]["recipient_employee_id"] == "ADMIN01"
        print(f"  [OK] Manager's own leave request routed to Ahallya Nethra ONLY.")

        # Step 6: Verify Email Service Status
        print("\n--- 6. Checking Email Service Configuration Status ---")
        status = email_service.get_status()
        print(f"  Status: {status}")

        print("\n=================================================================")
        print(" [ALL TESTS PASSED] Multi-Tier + Outbox + Routing Verified!     ")
        print("=================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    clean_and_verify()
