from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.rbac_models import User, StudentProfile, UserRole

router = APIRouter()

@router.get("/")
async def get_students(db: Session = Depends(get_db)):
    """Get all students"""
    return {"success": True, "data": []}

@router.get("/me")
async def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current student's profile"""
    profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        return {
            "success": True,
            "data": {
                "id": str(current_user.id),
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "level": 1,
                "points": 0,
                "coins": 0,
                "streak": 0,
            }
        }
    
    return {
        "success": True,
        "data": {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "level": profile.level or 1,
            "points": getattr(profile, 'points', 0) or 0,
            "coins": getattr(profile, 'coins', 0) or 0,
            "streak": getattr(profile, 'streak', 0) or 0,
            "organization_id": str(profile.organization_id) if profile.organization_id else None,
        }
    }

class CreateStudentProfileRequest(BaseModel):
    level: Optional[int] = 1

@router.post("/profile")
async def create_student_profile(
    data: CreateStudentProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create student profile if not exists"""
    existing = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()
    
    if existing:
        return {"success": True, "message": "Profile already exists", "data": {"id": str(existing.id)}}
    
    profile = StudentProfile(
        user_id=current_user.id,
        level=data.level or 1
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {"success": True, "message": "Profile created", "data": {"id": str(profile.id)}}

