import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Tuple, Optional, Dict, Any
from app.config import settings


class EmailService:
    """
    Dedicated Email Service for Real Gmail SMTP Delivery.
    Sends multi-part (HTML + Plain Text) emails via smtp.gmail.com with App Passwords.
    Technically originates from the system sender (leavemanagementsystem45@gmail.com)
    while clearly identifying the relevant actors in the message body.
    """

    def __init__(self):
        pass

    def get_smtp_config(self) -> Dict[str, Any]:
        host = os.getenv("MAIL_HOST") or os.getenv("SMTP_HOST") or "smtp.gmail.com"
        port = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT") or 587)
        username = (
            os.getenv("MAIL_USERNAME")
            or os.getenv("SMTP_USER")
            or "leavemanagementsystem45@gmail.com"
        )
        password = os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASSWORD") or ""
        from_email = (
            os.getenv("MAIL_FROM")
            or os.getenv("EMAIL_FROM")
            or username
            or "leavemanagementsystem45@gmail.com"
        )
        from_name = (
            os.getenv("MAIL_FROM_NAME")
            or "Leave Management System"
        )
        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "from_name": from_name,
        }

    def is_configured(self) -> bool:
        cfg = self.get_smtp_config()
        return bool(cfg["username"] and cfg["password"] and cfg["password"].strip())

    def get_status(self) -> Dict[str, Any]:
        cfg = self.get_smtp_config()
        configured = bool(cfg["username"] and cfg["password"] and cfg["password"].strip())
        return {
            "is_configured": configured,
            "smtp_host": cfg["host"],
            "smtp_port": cfg["port"],
            "smtp_user": cfg["username"],
            "from_email": cfg["from_email"],
            "from_name": cfg["from_name"],
            "delivery_mode": "GMAIL_SMTP" if configured else "UNCONFIGURED",
        }

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        recipient_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Sends a multi-part email (HTML + plain text) to the given recipient.
        Returns:
            (success: bool, error_message: Optional[str])
        """
        cfg = self.get_smtp_config()
        if not cfg["password"] or not cfg["password"].strip():
            err = (
                "Gmail SMTP is not configured. Please set MAIL_PASSWORD (Gmail App Password) in backend/.env"
            )
            print(f"[EmailService] {err}")
            return False, err

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((cfg["from_name"], cfg["from_email"]))
            recipient_formatted = formataddr((recipient_name or to_email, to_email))
            msg["To"] = recipient_formatted

            # Attach plain text and HTML versions
            part_text = MIMEText(text_body or "", "plain", "utf-8")
            part_html = MIMEText(html_body or "", "html", "utf-8")
            msg.attach(part_text)
            msg.attach(part_html)

            print(
                f"[EmailService] Connecting to {cfg['host']}:{cfg['port']} as {cfg['username']} to send email to {to_email}..."
            )
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(cfg["username"], cfg["password"].strip())
                server.sendmail(cfg["from_email"], [to_email], msg.as_string())

            print(f"[EmailService] [SUCCESS] Email successfully delivered to {to_email} via Gmail SMTP.")
            return True, None

        except smtplib.SMTPAuthenticationError as auth_err:
            err = f"Gmail SMTP Authentication Failed. Check MAIL_USERNAME and MAIL_PASSWORD in backend/.env. ({auth_err})"
            print(f"[EmailService] [ERROR] {err}")
            return False, err
        except smtplib.SMTPConnectError as conn_err:
            err = f"Failed to connect to Gmail SMTP server {cfg['host']}:{cfg['port']}. ({conn_err})"
            print(f"[EmailService] [ERROR] {err}")
            return False, err
        except Exception as e:
            err = f"Gmail SMTP Delivery Error: {str(e)}"
            print(f"[EmailService] [ERROR] {err}")
            return False, err

    def send_test_email(self, to_email: str) -> Tuple[bool, Optional[str]]:
        """
        Sends a test email to verify Gmail SMTP delivery configuration.
        """
        subject = "Leave Management System — Test Email"
        text_body = (
            "Hello,\n\n"
            "This is a test email from the Leave Management System.\n"
            "Gmail integration and SMTP delivery are working correctly.\n\n"
            "System Sender: leavemanagementsystem45@gmail.com\n"
            "Leave Management System Team"
        )
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 24px; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px;">Leave Management System — Test Email</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Gmail SMTP Integration Verification</p>
            </div>
            <div style="padding: 24px; color: #1e293b;">
                <p style="font-size: 15px; margin-top: 0;">Hello,</p>
                <p style="font-size: 14px; color: #475569;">
                    This is a verification test email sent from the <strong>Leave Management System</strong>.
                </p>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin: 16px 0; color: #166534; font-size: 14px;">
                    <strong>Success:</strong> Real Gmail SMTP integration is operating properly!
                </div>
                <table style="width: 100%; border-collapse: collapse; margin: 16px 0; background: #f8fafc; border-radius: 8px; overflow: hidden; font-size: 13px;">
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Sender Account</td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">leavemanagementsystem45@gmail.com</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #64748b;">Recipient</td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{to_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 12px; color: #64748b;">Delivery Mode</td>
                        <td style="padding: 8px 12px; font-weight: 600; color: #4f46e5;">GMAIL_SMTP (STARTTLS / Port 587)</td>
                    </tr>
                </table>
            </div>
            <div style="background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                Enterprise Multi-Tier Leave Management &bull; Automated System Notification
            </div>
        </div>
        """
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            recipient_name=to_email,
        )


email_service = EmailService()
