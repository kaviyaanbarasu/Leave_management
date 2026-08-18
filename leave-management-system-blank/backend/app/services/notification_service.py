import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.services.email_service import email_service


class NotificationService:
    def __init__(self):
        # In-memory outbox log for live testing & in-app verification fallback
        self.outbox_logs: List[Dict[str, Any]] = []

    def send_notification(
        self,
        recipient_employee_id: str,
        to_email: str,
        recipient_name: str,
        subject: str,
        html_content: str,
        body_text: str,
        notification_type: str = "GENERAL",
        leave_request_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Tuple[bool, Optional[Notification]]:
        """
        Core notification dispatcher:
        1. Persists notification record with status='PENDING' and delivery_mode='GMAIL_SMTP'.
        2. Dispatches real email via Gmail SMTP through EmailService.
        3. Updates status to 'SENT' on success, or 'FAILED' with detailed error message on failure.
        4. Maintains strict user-specific ownership via recipient_employee_id.
        """
        now = datetime.now(timezone.utc)
        delivery_mode = "GMAIL_SMTP"
        status = "PENDING"
        error_msg = None

        # Step 1: Attempt real Gmail SMTP delivery
        email_sent, smtp_error = email_service.send_email(
            to_email=to_email,
            recipient_name=recipient_name,
            subject=subject,
            html_body=html_content,
            text_body=body_text,
        )

        if email_sent:
            status = "SENT"
        else:
            status = "FAILED"
            error_msg = smtp_error or "Gmail SMTP delivery failed"

        # Step 2: Persist in PostgreSQL database
        notif_record = None
        if db is not None:
            try:
                notif_record = Notification(
                    leave_request_id=leave_request_id,
                    recipient_employee_id=recipient_employee_id,
                    recipient_email=to_email,
                    recipient_name=recipient_name,
                    notification_type=notification_type,
                    subject=subject,
                    html_content=html_content,
                    body_text=body_text,
                    delivery_mode=delivery_mode,
                    status=status,
                    error_message=error_msg,
                    created_at=now,
                    sent_at=now,
                )
                db.add(notif_record)
                db.flush()
            except Exception as ex:
                print(f"[NotificationService] DB save warning: {ex}")

        # Step 3: Maintain in-memory log for test client / fallback queries
        log_entry = {
            "id": notif_record.id if notif_record else (len(self.outbox_logs) + 1),
            "leave_request_id": leave_request_id,
            "recipient_employee_id": recipient_employee_id,
            "to_email": to_email,
            "recipient_name": recipient_name,
            "subject": subject,
            "html_content": html_content,
            "body_text": body_text,
            "notification_type": notification_type,
            "delivery_mode": delivery_mode,
            "status": status,
            "error_message": error_msg,
            "timestamp": now.isoformat(),
        }
        self.outbox_logs.insert(0, log_entry)

        return email_sent, notif_record

    def notify_new_request_to_approver(
        self,
        employee_name: str,
        employee_email: str,
        approver_name: str,
        approver_email: str,
        request_id: str,
        leave_type_name: str,
        start_date: str,
        end_date: str,
        working_days: float,
        reason: str,
        tier_name: str = "Manager Review",
        approver_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Event 1 / New Request: Sent ONLY to the initial pending approver (e.g. Kaviya).
        Subject: New Leave Request Requires Your Approval
        """
        subject = "New Leave Request Requires Your Approval"

        text_body = (
            f"Hello {approver_name},\n\n"
            f"{employee_name} has submitted a leave request that requires your approval.\n\n"
            f"Leave Type: {leave_type_name}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Working Days: {working_days} Days\n"
            f"Reason: {reason}\n"
            f"Workflow Step: {tier_name}\n\n"
            f"Please review and action this request in the Leave Management System.\n\n"
            f"---\n"
            f"Leave Management System\n"
            f"leavemanagementsystem45@gmail.com"
        )

        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 24px; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px;">New Leave Request Requires Your Approval</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">{tier_name}</p>
            </div>
            <div style="padding: 24px; color: #1e293b;">
                <p style="font-size: 15px; margin-top: 0;">Hello <strong>{approver_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569;">
                    <strong>{employee_name}</strong> has submitted a leave request that requires your approval.
                </p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Employee</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{employee_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Leave Type</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4f46e5;">{leave_type_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Start Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{start_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">End Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{end_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Working Days</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #059669;">{working_days} Days</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; color: #64748b; font-size: 13px;">Reason</td>
                        <td style="padding: 10px 16px; font-style: italic;">"{reason}"</td>
                    </tr>
                </table>
                <p style="font-size: 14px; color: #475569;">
                    Please review the request in the Leave Management System.
                </p>
                <div style="margin-top: 24px; text-align: center;">
                    <a href="http://localhost:3000" style="display: inline-block; background: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">Open Approvals Inbox</a>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Enterprise Multi-Tier Leave Management &bull; System Sender: leavemanagementsystem45@gmail.com
            </div>
        </div>
        """

        return self.send_notification(
            recipient_employee_id=approver_id or "",
            to_email=approver_email,
            recipient_name=approver_name,
            subject=subject,
            html_content=html_content,
            body_text=text_body,
            notification_type="ACTION_REQUIRED",
            leave_request_id=request_id,
            db=db,
        )

    def notify_next_approver(
        self,
        employee_name: str,
        employee_email: str,
        next_approver_name: str,
        next_approver_email: str,
        previous_approver_name: str,
        request_id: str,
        leave_type_name: str,
        start_date: str,
        end_date: str,
        working_days: float,
        tier_name: str,
        next_approver_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Event 2 / Intermediate Approval: Sent ONLY to the next approver (e.g. Ahallya Nethra).
        Subject: Leave Request Requires Your Approval
        """
        subject = "Leave Request Requires Your Approval"

        text_body = (
            f"Hello {next_approver_name},\n\n"
            f"{previous_approver_name} has approved {employee_name}'s leave request.\n"
            f"The request now requires your approval.\n\n"
            f"Leave Type: {leave_type_name}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Working Days: {working_days} Days\n"
            f"Previous Approval: {previous_approver_name} — APPROVED\n"
            f"Workflow Step: {tier_name}\n\n"
            f"Please review the request in the Leave Management System.\n\n"
            f"---\n"
            f"Leave Management System\n"
            f"leavemanagementsystem45@gmail.com"
        )

        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 24px; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px;">Leave Request Requires Your Approval</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">{tier_name}</p>
            </div>
            <div style="padding: 24px; color: #1e293b;">
                <p style="font-size: 15px; margin-top: 0;">Hello <strong>{next_approver_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569;">
                    <strong>{previous_approver_name}</strong> has approved <strong>{employee_name}</strong>'s leave request. The request now requires your approval.
                </p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Employee</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{employee_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Leave Type</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #4f46e5;">{leave_type_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Start Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{start_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">End Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{end_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Working Days</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #059669;">{working_days} Days</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Previous Approval</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #059669;">{previous_approver_name} &mdash; APPROVED</td>
                    </tr>
                </table>
                <p style="font-size: 14px; color: #475569;">
                    Please review the request.
                </p>
                <div style="margin-top: 24px; text-align: center;">
                    <a href="http://localhost:3000" style="display: inline-block; background: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">Review & Action</a>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Enterprise Multi-Tier Leave Management &bull; System Sender: leavemanagementsystem45@gmail.com
            </div>
        </div>
        """

        return self.send_notification(
            recipient_employee_id=next_approver_id or "",
            to_email=next_approver_email,
            recipient_name=next_approver_name,
            subject=subject,
            html_content=html_content,
            body_text=text_body,
            notification_type="ACTION_REQUIRED",
            leave_request_id=request_id,
            db=db,
        )

    def notify_rejection_to_employee(
        self,
        employee_name: str,
        employee_email: str,
        request_id: str,
        leave_type_name: str,
        start_date: str,
        end_date: str,
        working_days: float,
        rejector_name: str,
        reason: str,
        employee_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Event 3 / Rejection: Sent ONLY to the requester (e.g. Vijesh).
        Subject: Leave Request Rejected
        """
        subject = "Leave Request Rejected"

        text_body = (
            f"Hello {employee_name},\n\n"
            f"Your leave request has been rejected.\n\n"
            f"Rejected By: {rejector_name}\n"
            f"Reason: {reason}\n\n"
            f"Leave Type: {leave_type_name}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Working Days: {working_days} Days\n"
            f"Status: REJECTED\n\n"
            f"Your reserved pending balance has been restored to your available days.\n\n"
            f"---\n"
            f"Leave Management System\n"
            f"leavemanagementsystem45@gmail.com"
        )

        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: #dc2626; padding: 24px; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px;">Leave Request Rejected</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Status: REJECTED</p>
            </div>
            <div style="padding: 24px; color: #1e293b;">
                <p style="font-size: 15px; margin-top: 0;">Hello <strong>{employee_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569;">
                    Your leave request has been rejected.
                </p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Rejected By</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #dc2626;">{rejector_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Reason</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-style: italic; color: #b91c1c;">"{reason or 'No reason specified'}"</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Leave Type</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{leave_type_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Start Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{start_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">End Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{end_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Working Days</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #dc2626;">{working_days} Days</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; color: #64748b; font-size: 13px;">Status</td>
                        <td style="padding: 10px 16px; font-weight: bold; color: #dc2626;">REJECTED</td>
                    </tr>
                </table>
                <p style="font-size: 14px; color: #475569;">
                    Your reserved pending balance has been restored to your available days.
                </p>
            </div>
            <div style="background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Enterprise Multi-Tier Leave Management &bull; System Sender: leavemanagementsystem45@gmail.com
            </div>
        </div>
        """

        return self.send_notification(
            recipient_employee_id=employee_id or "",
            to_email=employee_email,
            recipient_name=employee_name,
            subject=subject,
            html_content=html_content,
            body_text=text_body,
            notification_type="REJECTION",
            leave_request_id=request_id,
            db=db,
        )

    def notify_final_approval_to_employee(
        self,
        employee_name: str,
        employee_email: str,
        request_id: str,
        leave_type_name: str,
        start_date: str,
        end_date: str,
        working_days: float,
        approvers_list: List[str],
        employee_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Event 4 / Final Approval: Sent ONLY to the requester (e.g. Vijesh).
        Subject: Leave Request Approved
        """
        subject = "Leave Request Approved"

        approvers_text = "\n".join([f"  - {name} — APPROVED" for name in approvers_list])
        text_body = (
            f"Hello {employee_name},\n\n"
            f"Your leave request has been fully approved.\n\n"
            f"Leave Type: {leave_type_name}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Working Days: {working_days} Days\n\n"
            f"Approval History:\n{approvers_text}\n\n"
            f"Status: APPROVED\n\n"
            f"Your leave balance has been updated accordingly in the system ledger.\n\n"
            f"---\n"
            f"Leave Management System\n"
            f"leavemanagementsystem45@gmail.com"
        )

        approvers_html = "".join(
            [
                f"<li style='margin-bottom: 4px; font-weight: 600; color: #059669;'>&bull; {name} &mdash; APPROVED</li>"
                for name in approvers_list
            ]
        )

        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: #059669; padding: 24px; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px;">Leave Request Approved</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Status: APPROVED</p>
            </div>
            <div style="padding: 24px; color: #1e293b;">
                <p style="font-size: 15px; margin-top: 0;">Hello <strong>{employee_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569;">
                    Your leave request has been fully approved.
                </p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Employee</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{employee_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Leave Type</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{leave_type_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Start Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{start_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">End Date</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{end_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Working Days</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #059669;">{working_days} Days</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px; vertical-align: top;">Approval History</td>
                        <td style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0;">
                            <ul style="margin: 0; padding-left: 0; list-style-type: none;">
                                {approvers_html}
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px; color: #64748b; font-size: 13px;">Status</td>
                        <td style="padding: 10px 16px; font-weight: bold; color: #059669;">APPROVED</td>
                    </tr>
                </table>
                <p style="font-size: 14px; color: #475569;">
                    Your leave balance has been updated accordingly in the system ledger.
                </p>
            </div>
            <div style="background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Enterprise Multi-Tier Leave Management &bull; System Sender: leavemanagementsystem45@gmail.com
            </div>
        </div>
        """

        return self.send_notification(
            recipient_employee_id=employee_id or "",
            to_email=employee_email,
            recipient_name=employee_name,
            subject=subject,
            html_content=html_content,
            body_text=text_body,
            notification_type="FINAL_APPROVAL",
            leave_request_id=request_id,
            db=db,
        )

    def retry_notification(self, notification_id: int, db: Session) -> Dict[str, Any]:
        """
        Retries Gmail delivery for a FAILED notification without creating duplicate records.
        """
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            raise ValueError(f"Notification #{notification_id} not found")

        if notif.status == "SENT":
            return {
                "success": True,
                "message": "Notification has already been successfully sent.",
                "notification_id": notif.id,
                "status": "SENT",
            }

        email_sent, smtp_error = email_service.send_email(
            to_email=notif.recipient_email,
            recipient_name=notif.recipient_name,
            subject=notif.subject,
            html_body=notif.html_content or "",
            text_body=notif.body_text or notif.subject,
        )

        now = datetime.now(timezone.utc)
        if email_sent:
            notif.status = "SENT"
            notif.sent_at = now
            notif.error_message = None
            notif.delivery_mode = "GMAIL_SMTP"
            db.commit()
            return {
                "success": True,
                "message": f"Successfully re-sent notification to {notif.recipient_email} via Gmail SMTP.",
                "notification_id": notif.id,
                "status": "SENT",
            }
        else:
            notif.status = "FAILED"
            notif.error_message = smtp_error or "Retry failed"
            db.commit()
            return {
                "success": False,
                "message": f"Retry failed: {notif.error_message}",
                "notification_id": notif.id,
                "status": "FAILED",
            }

    def get_user_outbox_logs(
        self,
        recipient_employee_id: str,
        recipient_email: Optional[str] = None,
        limit: int = 50,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves outbox logs strictly belonging to the specified employee (recipient).
        Guarantees that Vijesh only sees notifications addressed to Vijesh,
        Kaviya only sees notifications addressed to Kaviya,
        and Ahallya only sees notifications addressed to Ahallya.
        """
        if db is not None:
            try:
                emp_id = (recipient_employee_id or "").strip()
                email = (recipient_email or "").strip().lower()
                query = db.query(Notification).filter(
                    (Notification.recipient_employee_id.ilike(emp_id))
                    | (Notification.recipient_email.ilike(email if email else emp_id))
                ).order_by(Notification.created_at.desc())
                db_records = query.limit(limit).all()
                if db_records:
                    return [
                        {
                            "id": r.id,
                            "leave_request_id": r.leave_request_id,
                            "recipient_employee_id": r.recipient_employee_id,
                            "to_email": r.recipient_email,
                            "recipient_name": r.recipient_name or r.recipient_email,
                            "subject": r.subject,
                            "html_content": r.html_content,
                            "body_text": r.body_text,
                            "notification_type": r.notification_type,
                            "delivery_mode": r.delivery_mode,
                            "status": r.status,
                            "error_message": r.error_message,
                            "timestamp": r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat(),
                        }
                        for r in db_records
                    ]
            except Exception as e:
                print(f"[NotificationService] DB query fallback: {e}")

        # In-memory fallback (strictly recipient-filtered)
        emp_id = (recipient_employee_id or "").strip().lower()
        email = (recipient_email or "").strip().lower()
        filtered = [
            log for log in self.outbox_logs
            if (log.get("recipient_employee_id") and log.get("recipient_employee_id").strip().lower() == emp_id)
            or (email and log.get("to_email") and log.get("to_email").strip().lower() == email)
        ]
        return filtered[:limit]

    def get_outbox_logs(
        self,
        limit: int = 50,
        recipient_employee_id: Optional[str] = None,
        recipient_email: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        General retrieval helper with user-specific fallback enforcement.
        """
        if recipient_employee_id or recipient_email:
            return self.get_user_outbox_logs(
                recipient_employee_id=recipient_employee_id or "",
                recipient_email=recipient_email,
                limit=limit,
                db=db,
            )
        return self.outbox_logs[:limit]

    def clear_outbox(
        self,
        recipient_employee_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Clears outbox records. If recipient_employee_id is given, clears only for that recipient.
        """
        if recipient_employee_id:
            emp_id = recipient_employee_id.strip().lower()
            self.outbox_logs = [
                log for log in self.outbox_logs
                if log.get("recipient_employee_id", "").strip().lower() != emp_id
            ]
            if db is not None:
                try:
                    db.query(Notification).filter(
                        Notification.recipient_employee_id.ilike(recipient_employee_id)
                    ).delete(synchronize_session=False)
                    db.commit()
                except Exception as ex:
                    db.rollback()
        else:
            self.outbox_logs.clear()
            if db is not None:
                try:
                    db.query(Notification).delete(synchronize_session=False)
                    db.commit()
                except Exception as ex:
                    db.rollback()


notification_service = NotificationService()
