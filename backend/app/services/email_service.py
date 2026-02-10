import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from jinja2 import Template
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class EmailData:
    html_content: str
    subject: str

class EmailService:
    def __init__(self):
        self.emails_enabled = settings.EMAILS_ENABLED
        self.sender_name = settings.EMAILS_FROM_NAME
        self.sender_email = settings.EMAILS_FROM_EMAIL

    def render_email_template(self, *, template_name: str, context: dict[str, Any]) -> str:
        try:
            template_path = Path(__file__).parent.parent / "email-templates" / "build" / template_name
            if not template_path.exists():
                logger.warning(f"Email template not found: {template_path}")
                return f"<html><body>{str(context)}</body></html>"
            template_str = template_path.read_text()
            html_content = Template(template_str).render(context)
            return html_content
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return ""

    def send_email(
        self,
        *,
        email_to: str,
        subject: str = "",
        html_content: str = "",
    ) -> None:
        if not self.emails_enabled:
            logger.warning("Email sending is disabled in settings.")
            return

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = email_to

            part = MIMEText(html_content, "html")
            message.attach(part)

            if not settings.SMTP_HOST:
                logger.warning("SMTP_HOST not configured, skipping email send.")
                return

            # Connect to SMTP Server
            if settings.SMTP_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
            elif settings.SMTP_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.sendmail(self.sender_email, email_to, message.as_string())
            server.quit()
            logger.info(f"Email sent to {email_to}")

        except Exception as e:
            logger.error(f"Failed to send email to {email_to}: {e}")

    def send_test_email(self, email_to: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Test email"
        html_content = self.render_email_template(
            template_name="test_email.html",
            context={"project_name": "Alif24 Platform", "email": email_to},
        )
        self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
        )

    def send_new_account_email(self, email_to: str, username: str, password: str) -> None:
        subject = f"Alif24 - New account for {username}"
        html_content = self.render_email_template(
            template_name="new_account.html",
            context={
                "project_name": "Alif24 Platform",
                "username": username,
                "password": password,
                "email": email_to,
                "link": "https://alif24.uz", # Replace with actual frontend URL
            },
        )
        self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
        )

    def send_reset_password_email(self, email_to: str, token: str) -> None:
        subject = f"Alif24 - Password recovery"
        link = f"https://alif24.uz/reset-password?token={token}"
        html_content = self.render_email_template(
            template_name="reset_password.html",
            context={
                "project_name": "Alif24 Platform",
                "username": email_to,
                "email": email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
        )
