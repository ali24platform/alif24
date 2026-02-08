from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.notification_service import NotificationService
from pydantic import BaseModel

router = APIRouter()

class SMSRequest(BaseModel):
    phone: str
    message: str

class TelegramRequest(BaseModel):
    chat_id: Optional[str] = None
    message: Optional[str] = None

class EmailRequest(BaseModel):
    email: str
    subject: str
    content: str

@router.post("/send-sms")
async def send_sms(request: SMSRequest, db: Session = Depends(get_db)):
    service = NotificationService(db)
    success = await service.send_sms(request.phone, request.message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send SMS")
    return {"status": "success", "message": "SMS sent"}

@router.post("/send-telegram")
async def send_telegram(request: TelegramRequest = None, db: Session = Depends(get_db)):
    """
    Send Telegram message.
    If request body is provided, uses that.
    If not, uses hardcoded default Chat ID from settings.
    """
    service = NotificationService(db)
    
    # Defaults
    chat_id = settings.TELEGRAM_CHAT_ID
    message = "Test message from Alif24 Platform"

    if request:
        chat_id = request.chat_id or chat_id
        message = request.message or message

    if not chat_id:
         raise HTTPException(status_code=400, detail="Chat ID not provided and no default set")

    success = await service.send_telegram(chat_id, message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send Telegram message")
    return {"status": "success", "message": "Telegram message sent", "recipient": chat_id}

@router.post("/send-email")
def send_email(request: EmailRequest, db: Session = Depends(get_db)):
    service = NotificationService(db)
    # Simple synchronous send
    success = service.send_email(request.email, request.subject, request.content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send Email")
    return {"status": "success", "message": "Email sent"}
