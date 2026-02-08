import logging
import emails
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
        self.sender = (settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL)

    def render_email_template(self, *, template_name: str, context: dict[str, Any]) -> str:
        template_path = Path(__file__).parent.parent / "email-templates" / "build" / template_name
        template_str = template_path.read_text()
        html_content = Template(template_str).render(context)
        return html_content

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

        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=self.sender,
        )
        
        smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
            
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD

        response = message.send(to=email_to, smtp=smtp_options)
        logger.info(f"Send email result: {response}")

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
