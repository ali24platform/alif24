"""
Permission Dependencies for RBAC
FastAPI dependencies for role-based access control

FIX: Removed duplicate get_current_user definition.
     Now imports the canonical version from app.middleware.auth which:
     - Handles TokenExpiredError gracefully (frontend can trigger refresh)
     - Checks AccountStatus consistently
     - Uses UnauthorizedError for proper error codes
     
     Previously, deps.py had its own version that:
     - Used generic HTTPException (no TOKEN_EXPIRED code)
     - Didn't check AccountStatus (left to get_current_active_user)
     This caused inconsistent auth behavior between auth routes and RBAC routes.
"""
from typing import Optional, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.rbac_models import User, UserRole, StudentProfile, TeacherProfile, Classroom

# FIX: Import canonical get_current_user from auth.py instead of redefining it
# This is the SINGLE SOURCE OF TRUTH for user authentication
from app.middleware.auth import get_current_user


# Security scheme (kept for any direct usage in this module)
security = HTTPBearer()


# ============================================================
# BASE DEPENDENCIES
# ============================================================

# get_current_user is now imported from app.middleware.auth (see import above)
# It handles: JWT decode, UUID parsing, user lookup, AccountStatus check, TokenExpiredError


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user account is active
    """
    from app.models.rbac_models import AccountStatus
    
    if current_user.status != AccountStatus.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_verified_teacher(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Ensure user is a Teacher AND has Approved status.
    Prevent 'Pending' teachers from creating content.
    """
    # 1. Check Role
    if current_user.role != UserRole.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only teachers can access this resource"
        )

    # 2. Check Teacher Profile Status
    # Note: Using joinedload or simple query since user.teacher_profile might not be loaded
    # But usually relationship is lazy loaded on access if session is active.
    # Safe approach: Query profile directly to be sure.
    from app.models.rbac_models import TeacherProfile, TeacherStatus
    
    teacher_profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()

    if not teacher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Teacher profile not found"
        )

    if teacher_profile.verification_status != TeacherStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Teacher account is pending approval. You cannot create content yet."
        )

    return current_user


# ============================================================
# ROLE-BASED DEPENDENCIES
# ============================================================

def require_roles(*allowed_roles: UserRole):
    """
    Factory function to create role-checking dependency
    Usage: @router.get("/", dependencies=[Depends(require_roles(UserRole.admin))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Shortcut dependencies
async def only_moderator(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Only moderator can access
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access required"
        )
    return current_user



async def only_organization(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Only organization can access
    """
    if current_user.role != UserRole.organization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access required"
        )
    return current_user


async def only_organization_or_moderator(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Organization or moderator can access
    """
    if current_user.role not in [UserRole.moderator, UserRole.organization]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access required"
        )
    return current_user


async def only_teacher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Only verified teacher can access
    """
    from app.models.rbac_models import TeacherStatus
    
    if current_user.role != UserRole.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    
    # Check if teacher is approved
    if current_user.teacher_profile and current_user.teacher_profile.verification_status != TeacherStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher account not verified yet"
        )
    
    return current_user


async def only_parent(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Only parent can access
    """
    if current_user.role != UserRole.parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent access required"
        )
    return current_user


async def only_student(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency: Only student can access
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user


# ============================================================
# OWNERSHIP DEPENDENCIES
# ============================================================

class TeacherOwnershipChecker:
    """
    Dependency class to check if teacher owns a resource
    """
    def __init__(self, resource_type: str = "classroom"):
        self.resource_type = resource_type
    
    async def __call__(
        self,
        resource_id: UUID,
        current_user: User = Depends(only_teacher),
        db: Session = Depends(get_db)
    ) -> User:
        """
        Check if the teacher owns the specified resource
        """
        if self.resource_type == "classroom":
            classroom = db.query(Classroom).filter(Classroom.id == resource_id).first()
            if not classroom:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Classroom not found"
                )
            
            if not current_user.teacher_profile or classroom.teacher_id != current_user.teacher_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't own this classroom"
                )
        
        return current_user


# Create instances for common use
only_teacher_owner_classroom = TeacherOwnershipChecker("classroom")


async def only_teacher_owner(
    classroom_id: UUID,
    current_user: User = Depends(only_teacher),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency: Teacher must own the classroom
    """
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    if not current_user.teacher_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found"
        )
    
    if classroom.teacher_id != current_user.teacher_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage this classroom"
        )
    
    return current_user


# ============================================================
# PARENT-CHILD DEPENDENCIES
# ============================================================

async def only_parent_of_child(
    child_id: UUID,
    current_user: User = Depends(only_parent),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency: Parent can only access their own children's data
    """
    # Get the child user
    child = db.query(User).filter(
        User.id == child_id,
        User.role == UserRole.student
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Check if the child belongs to this parent
    if child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this child's data"
        )
    
    return current_user


async def get_parent_children(
    current_user: User = Depends(only_parent),
    db: Session = Depends(get_db)
) -> List[User]:
    """
    Get all children belonging to the current parent
    """
    children = db.query(User).filter(
        User.parent_id == current_user.id,
        User.role == UserRole.student
    ).all()
    
    return children


# ============================================================
# CHILD/STUDENT AUTH DEPENDENCY
# ============================================================

async def get_current_child_user(
    username: str,
    pin: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate child user with username and PIN
    """
    child = db.query(User).filter(
        User.username == username,
        User.role == UserRole.student
    ).first()
    
    if not child or not child.verify_pin(pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or PIN"
        )
    
    from app.models.rbac_models import AccountStatus
    if child.status != AccountStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    return child


# ============================================================
# COMBINED PERMISSION HELPERS
# ============================================================

def can_access_student_data(
    student_id: UUID,
    current_user: User,
    db: Session
) -> bool:
    """
    Helper function to check if user can access student data
    Returns True if:
    - User is the student themselves
    - User is the parent of the student
    - User is a teacher and student is in their classroom
    - User is admin/super_admin
    """
    if current_user.role in [UserRole.moderator, UserRole.organization]:
        return True
    
    # Student accessing their own data
    if current_user.role == UserRole.student and current_user.id == student_id:
        return True
    
    # Parent accessing their child's data
    if current_user.role == UserRole.parent:
        child = db.query(User).filter(User.id == student_id).first()
        if child and child.parent_id == current_user.id:
            return True
    
    # Teacher accessing their classroom student's data
    if current_user.role == UserRole.teacher and current_user.teacher_profile:
        from app.models.rbac_models import ClassroomStudent
        
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == student_id
        ).first()
        
        if student_profile:
            enrollment = db.query(ClassroomStudent).join(Classroom).filter(
                ClassroomStudent.student_id == student_profile.id,
                Classroom.teacher_id == current_user.teacher_profile.id,
                ClassroomStudent.is_active == True
            ).first()
            
            if enrollment:
                return True
    
    return False


async def verify_student_access(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to verify access to student data
    """
    if not can_access_student_data(student_id, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this student's data"
        )
    return current_user
