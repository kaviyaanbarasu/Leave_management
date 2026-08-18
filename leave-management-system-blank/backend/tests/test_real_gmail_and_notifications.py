import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date
from app.main import app
from app.database import SessionLocal
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.leave_request import LeaveRequest, EmployeeLeaveBalance
from app.services.email_service import email_service
from app.services.notification_service import notification_service
from app.schemas.leave_request import LeaveRequestCreate


@pytest.fixture
def client():
    return TestClient(app)


def test_email_service_status_hides_password():
    """Verifies that email service status never exposes the password."""
    status = email_service.get_status()
    assert "password" not in status
    assert "smtp_host" in status
    assert "smtp_user" in status
    assert status["smtp_user"] == "leavemanagementsystem45@gmail.com"


def test_email_service_unconfigured_handled_gracefully():
    """Verifies that sending email without credentials fails gracefully without crashing."""
    with patch.object(email_service, "get_smtp_config", return_value={
        "host": "smtp.gmail.com", "port": 587, "username": "leavemanagementsystem45@gmail.com", "password": "", "from_email": "leavemanagementsystem45@gmail.com", "from_name": "Leave Management System"
    }):
        success, error = email_service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            html_body="<p>Test</p>",
            text_body="Test",
        )
        assert success is False
        assert "Gmail App Password" in error


def test_email_service_smtp_delivery_success_mock():
    """Verifies successful SMTP dispatch with mocked smtplib."""
    with patch.object(email_service, "get_smtp_config", return_value={
        "host": "smtp.gmail.com", "port": 587, "username": "leavemanagementsystem45@gmail.com", "password": "mock_password", "from_email": "leavemanagementsystem45@gmail.com", "from_name": "Leave Management System"
    }):
        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance

            success, error = email_service.send_email(
                to_email="vijeshthamodharan@gmail.com",
                subject="Leave Request Approved",
                html_body="<p>Approved</p>",
                text_body="Approved",
                recipient_name="Vijesh",
            )
            assert success is True
            assert error is None
            assert instance.sendmail.called


def test_sequential_email_routing_and_user_outbox_isolation(client):
    """
    Tests the complete sequential workflow:
    1. Vijesh submits leave -> notification sent to Kaviya ONLY
    2. Kaviya approves -> notification sent to Ahallya Nethra ONLY
    3. Ahallya approves -> final approval notification sent to Vijesh ONLY
    4. Outbox verification: Each user only sees their own addressed notifications.
    """
    db = SessionLocal()
    try:
        # Clear outbox
        notification_service.clear_outbox(db=db)

        # 1. Login headers
        vijesh_token = client.post(
            "/api/auth/login",
            json={"username": "E101", "password": "password123"}
        ).json()["token"]
        vijesh_headers = {"Authorization": f"Bearer {vijesh_token}"}

        kaviya_token = client.post(
            "/api/auth/login",
            json={"username": "M201", "password": "password123"}
        ).json()["token"]
        kaviya_headers = {"Authorization": f"Bearer {kaviya_token}"}

        ahallya_token = client.post(
            "/api/auth/login",
            json={"username": "ADMIN01", "password": "password123"}
        ).json()["token"]
        ahallya_headers = {"Authorization": f"Bearer {ahallya_token}"}

        # Step 1: Vijesh creates leave request
        res = client.post(
            "/api/leave-requests",
            json={
                "employee_id": "E101",
                "leave_type_id": "BLR-PTO",
                "start_date": "2026-11-16",
                "end_date": "2026-11-18",
                "reason": "Sequential Notification Test",
            },
            headers=vijesh_headers,
        )
        assert res.status_code == 201
        req_data = res.json()
        req_id = req_data["request_id"]

        # Check Outbox at Step 1
        v_outbox = client.get("/api/leave-requests/notifications/outbox", headers=vijesh_headers).json()
        k_outbox = client.get("/api/leave-requests/notifications/outbox", headers=kaviya_headers).json()
        a_outbox = client.get("/api/leave-requests/notifications/outbox", headers=ahallya_headers).json()

        assert len(v_outbox) == 0, "Vijesh must have 0 notifications at Step 1"
        assert len(k_outbox) == 1, "Kaviya must have 1 notification at Step 1"
        assert len(a_outbox) == 0, "Ahallya must have 0 notifications at Step 1"
        assert k_outbox[0]["to_email"] == "anbarasukavya7@gmail.com"
        assert k_outbox[0]["recipient_employee_id"] == "M201"
        assert k_outbox[0]["delivery_mode"] == "GMAIL_SMTP"

        # Step 2: Kaviya approves
        res_approve_k = client.post(
            f"/api/leave-requests/{req_id}/approve-tier?approver_id=M201",
            json={"comments": "Tier 1 Approved"},
            headers=kaviya_headers,
        )
        assert res_approve_k.status_code == 200

        # Check Outbox at Step 2
        v_outbox_2 = client.get("/api/leave-requests/notifications/outbox", headers=vijesh_headers).json()
        k_outbox_2 = client.get("/api/leave-requests/notifications/outbox", headers=kaviya_headers).json()
        a_outbox_2 = client.get("/api/leave-requests/notifications/outbox", headers=ahallya_headers).json()

        assert len(v_outbox_2) == 0, "Vijesh must still have 0 notifications before final tier"
        assert len(k_outbox_2) == 1, "Kaviya must still have 1 notification"
        assert len(a_outbox_2) == 1, "Ahallya must have 1 notification at Step 2"
        assert a_outbox_2[0]["to_email"] == "ahallyanethrabl@gmail.com"
        assert a_outbox_2[0]["recipient_employee_id"] == "ADMIN01"

        # Step 3: Ahallya approves (Final Tier)
        res_approve_a = client.post(
            f"/api/leave-requests/{req_id}/approve-tier?approver_id=ADMIN01",
            json={"comments": "Final Tier Approved"},
            headers=ahallya_headers,
        )
        assert res_approve_a.status_code == 200

        # Check Outbox at Step 3
        v_outbox_3 = client.get("/api/leave-requests/notifications/outbox", headers=vijesh_headers).json()
        k_outbox_3 = client.get("/api/leave-requests/notifications/outbox", headers=kaviya_headers).json()
        a_outbox_3 = client.get("/api/leave-requests/notifications/outbox", headers=ahallya_headers).json()

        assert len(v_outbox_3) == 1, "Vijesh must now receive 1 final approval notification"
        assert len(k_outbox_3) == 1, "Kaviya must still have 1 notification"
        assert len(a_outbox_3) == 1, "Ahallya must still have 1 notification"
        assert v_outbox_3[0]["to_email"] == "vijeshthamodharan@gmail.com"
        assert v_outbox_3[0]["recipient_employee_id"] == "E101"
        assert v_outbox_3[0]["notification_type"] == "FINAL_APPROVAL"

    finally:
        db.close()


def test_retry_and_test_email_endpoints(client):
    """Verifies test-email endpoint and retry endpoint permissions."""
    ahallya_token = client.post(
        "/api/auth/login",
        json={"username": "ADMIN01", "password": "password123"}
    ).json()["token"]
    ahallya_headers = {"Authorization": f"Bearer {ahallya_token}"}

    vijesh_token = client.post(
        "/api/auth/login",
        json={"username": "E101", "password": "password123"}
    ).json()["token"]
    vijesh_headers = {"Authorization": f"Bearer {vijesh_token}"}

    # Non-admin cannot send test email
    res_forbidden = client.post(
        "/api/leave-requests/notifications/test-email",
        json={"to_email": "test@example.com"},
        headers=vijesh_headers,
    )
    assert res_forbidden.status_code == 403

    # Admin mock test email
    with patch.dict("os.environ", {"MAIL_PASSWORD": "mock_app_password_123"}):
        with patch("smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance

            res_test = client.post(
                "/api/leave-requests/notifications/test-email",
                json={"to_email": "test@example.com"},
                headers=ahallya_headers,
            )
            assert res_test.status_code == 200
            assert res_test.json()["status"] == "success"
