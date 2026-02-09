"""
Admin Router
Temporary administrative endpoints for managing the platform.

CONTEXT: New teachers register with status='pending' and are locked out
because only_teacher() dependency requires status='approved'.
No admin panel exists yet, so this provides a secure API endpoint
for teacher approval until a full admin UI is built.

SECURITY: Protected by a hardcoded admin secret key in the header.
Only requests with the correct X-Admin-Secret header are accepted.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

from app.core.database import get_db
from app.models.rbac_models import User, TeacherProfile, TeacherStatus, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================================
# SECURITY: Hardcoded admin secret key
# In production, move this to environment variables
# For now, this is the only way to call admin endpoints
# ============================================================
ADMIN_SECRET = "alif24-admin-secret-2024"


async def verify_admin_secret(
    x_admin_secret: str = Header(..., alias="X-Admin-Secret")
):
    """
    Verify the admin secret key from request header.
    Usage: curl -H "X-Admin-Secret: alif24-admin-secret-2024" ...
    """
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin secret key"
        )
    return True


# ============================================================
# SCHEMAS
# ============================================================

class ApproveTeacherRequest(BaseModel):
    user_id: str  # UUID as string

class TeacherStatusResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    message: str


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/approve-teacher", response_model=TeacherStatusResponse)
async def approve_teacher(
    data: ApproveTeacherRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)
):
    """
    Approve a pending teacher account.
    
    Requires X-Admin-Secret header.
    
    Usage example:
        curl -X POST https://yourdomain.com/api/v1/admin/approve-teacher \\
             -H "Content-Type: application/json" \\
             -H "X-Admin-Secret: alif24-admin-secret-2024" \\
             -d '{"user_id": "uuid-here"}'
    """
    # Find the user
    try:
        user_uuid = UUID(data.user_id)
    except ValueError:
        raise HTTPException(400, "Invalid user_id format (must be UUID)")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.role != UserRole.teacher:
        raise HTTPException(400, f"User is not a teacher (role: {user.role.value})")
    
    # Find teacher profile
    teacher_profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == user_uuid
    ).first()
    
    if not teacher_profile:
        # Create teacher profile if it doesn't exist
        teacher_profile = TeacherProfile(
            user_id=user_uuid,
            verification_status=TeacherStatus.approved
        )
        db.add(teacher_profile)
    else:
        teacher_profile.verification_status = TeacherStatus.approved
    
    db.commit()
    
    return TeacherStatusResponse(
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status="approved",
        message=f"Teacher {user.first_name or user.email} has been approved"
    )


@router.post("/reject-teacher", response_model=TeacherStatusResponse)
async def reject_teacher(
    data: ApproveTeacherRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)
):
    """Reject a pending teacher account."""
    try:
        user_uuid = UUID(data.user_id)
    except ValueError:
        raise HTTPException(400, "Invalid user_id format")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    teacher_profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == user_uuid
    ).first()
    
    if not teacher_profile:
        raise HTTPException(404, "Teacher profile not found")
    
    teacher_profile.verification_status = TeacherStatus.rejected
    db.commit()
    
    return TeacherStatusResponse(
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status="rejected",
        message=f"Teacher {user.first_name or user.email} has been rejected"
    )


@router.get("/pending-teachers")
async def list_pending_teachers(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_secret)
):
    """
    List all teachers with pending status.
    Useful for reviewing who needs approval.
    """
    pending = db.query(TeacherProfile).filter(
        TeacherProfile.verification_status == TeacherStatus.pending
    ).all()
    
    result = []
    for tp in pending:
        user = db.query(User).filter(User.id == tp.user_id).first()
        if user:
            result.append({
                "user_id": str(user.id),
                "email": user.email,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "status": tp.verification_status.value,
                "created_at": str(user.created_at) if user.created_at else None
            })
    
    return {
        "count": len(result),
        "teachers": result
    }
