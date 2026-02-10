from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, AccountStatus
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.rbac import ChildLoginRequest
from app.middleware.deps import get_current_child_user
from app.middleware.auth import create_access_token, create_refresh_token

router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., alias="currentPassword")
    new_password: str = Field(..., alias="newPassword")
    
    class Config:
        populate_by_name = True  # Allows both field name and alias

class UpdateProfileRequest(BaseModel):
    """
    Schema for profile updates via PUT /auth/me.
    All fields optional — only provided fields are updated.
    FIX: This schema + endpoint was MISSING (ghost endpoint in frontend).
    """
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    
    class Config:
        populate_by_name = True

@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    data.validate()
    service = AuthService(db)
    result = await service.register(data)
    return {
        "success": True,
        "message": "Registration successful",
        "data": result
    }

@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    service = AuthService(db)
    result = await service.login(data.email, data.password)
    return {
        "success": True,
        "message": "Login successful",
        "data": result
    }

@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    service = AuthService(db)
    result = await service.refresh_token(data.refresh_token)
    return {
        "success": True,
        "message": "Token refreshed",
        "data": result
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user"""
    service = AuthService(db)
    await service.logout(str(current_user.id))
    return {
        "success": True,
        "message": "Logged out successfully"
    }

@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password"""
    service = AuthService(db)
    await service.change_password(
        str(current_user.id),
        data.current_password,
        data.new_password
    )
    return {
        "success": True,
        "message": "Password changed successfully"
    }

@router.post("/child-login")
async def child_login(
    request: ChildLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login for child accounts using username + PIN
    """
    # Authenticate child
    child = await get_current_child_user(request.username, request.pin, db)
    
    # Update last login
    child.last_login_at = datetime.utcnow()
    
    # Generate tokens
    access_token = create_access_token(
        str(child.id),
        child.username,
        child.role.value
    )
    refresh_token = create_refresh_token(str(child.id))
    
    # Save refresh token
    child.refresh_token = refresh_token
    db.commit()
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": child.to_dict(),
            "parent_id": str(child.parent_id) if child.parent_id else None
        }
    }

@router.post("/avatar")
async def upload_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar.
    Currently stores as placeholder — real file upload requires storage service (S3/Supabase Storage).
    """
    # For now, return success with current avatar
    return {
        "success": True,
        "message": "Avatar upload endpoint ready. Connect storage service for file handling.",
        "data": {"avatar": current_user.avatar}
    }

@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    service = AuthService(db)
    profile = await service.get_profile(str(current_user.id))
    return {
        "success": True,
        "data": profile
    }

@router.put("/me")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    FIX: This endpoint was MISSING — frontend called PUT /auth/profile (ghost endpoint).
    Now properly implemented at PUT /auth/me to match GET /auth/me pattern.
    
    Accepts: { firstName, lastName, phone, email } — all optional.
    Only fields actually provided (non-null) are updated.
    """
    service = AuthService(db)
    # Only pass fields that were actually provided (not None)
    updates = data.model_dump(exclude_none=True, by_alias=False)
    profile = await service.update_profile(str(current_user.id), updates)
    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": profile
    }
