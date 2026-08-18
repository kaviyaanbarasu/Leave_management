import pytest
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest
from app.models.notification import Notification

def get_headers(employee_id: str, role: str = "employee") -> dict:
    return {
        "Authorization": f"Bearer session-{employee_id}-{role}",
        "X-Employee-ID": employee_id,
    }

def test_user_specific_outbox_isolation(client):
    """
    Tests that:
    1. When Vijesh submits a leave request, email is routed exclusively to Kaviya.
    2. Vijesh's outbox returns 0 items for this new request.
    3. Kaviya's outbox returns 1 item for this new request.
    4. Ahallya's outbox returns 0 items for this new request.
    """
    # Clean notifications via API endpoint
    client.delete("/api/leave-requests/notifications/outbox")

    # Step 1: Submit request
    res_create = client.post(
        "/api/leave-requests",
        json={
            "employee_id": "E101",
            "leave_type_id": "BLR-PTO",
            "start_date": "2026-08-24",
            "end_date": "2026-08-24",
            "reason": "Personal work",
        },
        headers=get_headers("E101", "employee")
    )
    assert res_create.status_code == 201
    req_id = res_create.json()["request_id"]

    # Vijesh's outbox -> 0
    vijesh_outbox = client.get("/api/leave-requests/notifications/outbox", headers=get_headers("E101", "employee")).json()
    assert len(vijesh_outbox) == 0

    # Kaviya's outbox -> 1
    kaviya_outbox = client.get("/api/leave-requests/notifications/outbox", headers=get_headers("M201", "manager")).json()
    assert len(kaviya_outbox) == 1
    assert kaviya_outbox[0]["to_email"] == "anbarasukavya7@gmail.com"
    assert kaviya_outbox[0]["recipient_employee_id"] == "M201"

    # Ahallya's outbox -> 0
    ahallya_outbox = client.get("/api/leave-requests/notifications/outbox", headers=get_headers("ADMIN01", "hr_admin")).json()
    assert len(ahallya_outbox) == 0
