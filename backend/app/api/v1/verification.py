"""
Phone Verification API Endpoints

Telefon raqamini Telegram orqali tasdiqlash uchun API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.services.telegram_bot_service import TelegramBotService

router = APIRouter(prefix="/verification", tags=["verification"])


# ============================================================
# SCHEMAS
# ============================================================

class SendCodeRequest(BaseModel):
    """Request to send verification code"""
    phone: str = Field(..., description="Phone number in format +998XXXXXXXXX")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+998901234567"
            }
        }


class VerifyCodeRequest(BaseModel):
    """Request to verify code"""
    phone: str = Field(..., description="Phone number")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+998901234567",
                "code": "123456"
            }
        }


class VerificationResponse(BaseModel):
    """Verification response"""
    success: bool
    message: str
    expires_in: Optional[int] = None  # Seconds until code expires


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/send-code", response_model=VerificationResponse)
async def send_verification_code(
    request: SendCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Send verification code to user's Telegram
    
    The user must have previously started the Telegram bot and linked their phone number.
    A 6-digit code will be sent via Telegram message.
    """
    import re
    
    # Validate phone format
    phone = re.sub(r'\s+', '', request.phone)
    if not re.match(r'^\+998\d{9}$', phone):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in format +998XXXXXXXXX"
        )
    
    service = TelegramBotService(db)
    result = await service.send_verification_code(phone)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return VerificationResponse(**result)


@router.post("/verify-code", response_model=VerificationResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Verify the code sent to user's Telegram
    
    User has 5 attempts to enter the correct code.
    Code expires after 5 minutes.
    """
    import re
    
    # Validate phone format
    phone = re.sub(r'\s+', '', request.phone)
    if not re.match(r'^\+998\d{9}$', phone):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in format +998XXXXXXXXX"
        )
    
    # Validate code format
    if not request.code.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Verification code must contain only digits"
        )
    
    service = TelegramBotService(db)
    result = service.verify_code(phone, request.code)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return VerificationResponse(**result)


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Telegram webhook endpoint
    
    Receives updates from Telegram and processes them.
    Set this URL as webhook in Telegram: 
    https://api.telegram.org/bot{TOKEN}/setWebhook?url={YOUR_URL}/api/v1/verification/telegram/webhook
    """
    try:
        update = await request.json()
        service = TelegramBotService(db)
        await service.process_update(update)
        return {"ok": True}
    except Exception as e:
        # Log error but return OK to Telegram (they will retry otherwise)
        import logging
        logging.error(f"Telegram webhook error: {e}")
        return {"ok": True}


@router.get("/telegram/set-webhook")
async def set_telegram_webhook(
    webhook_url: str,
    db: Session = Depends(get_db)
):
    """
    Set Telegram webhook URL
    
    Call this once to set up the webhook for your server.
    Example: /api/v1/verification/telegram/set-webhook?webhook_url=https://your-domain.com/api/v1/verification/telegram/webhook
    """
    service = TelegramBotService(db)
    success = await service.set_webhook(webhook_url)
    
    if success:
        return {"success": True, "message": f"Webhook set to {webhook_url}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to set webhook")


@router.get("/telegram/bot-info")
async def get_bot_info(db: Session = Depends(get_db)):
    """Get Telegram bot information"""
    service = TelegramBotService(db)
    info = await service.get_bot_info()
    return {"success": True, "data": info}
