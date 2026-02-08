import httpx
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.config import settings
from app.models.notification import NotificationLog, NotificationType, NotificationStatus
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    async def send_sms(self, recipient: str, message: str, user_id=None):
        """
        Send SMS via Eskiz.uz
        """
        # Create log entry
        log = NotificationLog(
            user_id=user_id,
            notification_type=NotificationType.SMS,
            recipient=recipient,
            message=message,
            status=NotificationStatus.PENDING
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        try:
            # 1. Get Token (In production, cache this token)
            async with httpx.AsyncClient() as client:
                auth_response = await client.post(
                    "https://notify.eskiz.uz/api/auth/login",
                    data={"email": settings.ESKIZ_EMAIL, "password": settings.ESKIZ_PASSWORD}
                )
                
                if auth_response.status_code != 200:
                    raise Exception(f"Eskiz Auth Failed: {auth_response.text}")
                
                token = auth_response.json()["data"]["token"]

                # 2. Send SMS
                send_response = await client.post(
                    "https://notify.eskiz.uz/api/message/sms/send",
                    headers={"Authorization": f"Bearer {token}"},
                    data={
                        "mobile_phone": recipient.replace("+", "").replace(" ", ""),
                        "message": message,
                        "from": "4546" # Standard Eskiz ID, change if you have a brand name
                    }
                )

                if send_response.status_code != 200:
                    raise Exception(f"Eskiz Send Failed: {send_response.text}")

                # Update log
                log.status = NotificationStatus.SENT
                log.sent_at = datetime.now()
                self.db.commit()
                return True

        except Exception as e:
            logger.error(f"SMS Error: {e}")
            log.status = NotificationStatus.FAILED
            log.error_message = str(e)
            self.db.commit()
            return False

    async def send_telegram(self, chat_id: str, message: str, user_id=None):
        """
        Send Telegram Message
        """
        # Create log entry
        log = NotificationLog(
            user_id=user_id,
            notification_type=NotificationType.TELEGRAM,
            recipient=chat_id,
            message=message,
            status=NotificationStatus.PENDING
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        try:
            if not settings.TELEGRAM_BOT_TOKEN:
                raise Exception("Telegram Bot Token not configured")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": chat_id, "text": message}
                )

                if response.status_code != 200:
                    raise Exception(f"Telegram Send Failed: {response.text}")

                # Update log
                log.status = NotificationStatus.SENT
                log.sent_at = datetime.now()
                self.db.commit()
                return True

        except Exception as e:
            logger.error(f"Telegram Error: {e}")
            log.status = NotificationStatus.FAILED
            log.error_message = str(e)
            self.db.commit()
            return False

    def send_email(self, recipient: str, subject: str, html_content: str, user_id=None):
        """
        Send Email
        """
        log = NotificationLog(
            user_id=user_id,
            notification_type=NotificationType.EMAIL,
            recipient=recipient,
            message=f"Subject: {subject}", # HTML content is too large to log fully
            status=NotificationStatus.PENDING
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        try:
            self.email_service.send_email(
                email_to=recipient,
                subject=subject,
                html_content=html_content
            )
            
            log.status = NotificationStatus.SENT
            log.sent_at = datetime.now()
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Email Error: {e}")
            log.status = NotificationStatus.FAILED
            log.error_message = str(e)
            self.db.commit()
            return False
