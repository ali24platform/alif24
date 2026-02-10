from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services.lesson_service import LessonService
from app.middleware.deps import get_current_active_user
from app.models import User, UserRole

router = APIRouter()

@router.get("/", response_model=dict)
async def get_lessons(
    skip: int = 0,
    limit: int = 100,
    subject_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get all lessons with optional filtering"""
    service = LessonService(db)
    filters = {}
    if subject_id:
        filters["subject_id"] = subject_id
    
    lessons = service.find_all(filters=filters, limit=limit, offset=skip)
    return {"success": True, "data": lessons}

@router.get("/{lesson_id}", response_model=dict)
async def get_lesson(
    lesson_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific lesson by ID with prerequisite check for students"""
    service = LessonService(db)
    lesson = service.find_by_id(str(lesson_id))
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    # Student Prerequisite Check
    if current_user.role == UserRole.student:
        # 1. Get Student Profile
        from app.models import StudentProfile, Progress, ProgressStatus, Lesson
        student = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        
        if student and lesson.order > 1:
            # 2. Find previous lesson
            prev_lesson = db.query(Lesson).filter(
                Lesson.subject_id == lesson.subject_id,
                Lesson.order == lesson.order - 1
            ).first()
            
            if prev_lesson:
                # 3. Check completion
                progress = db.query(Progress).filter(
                    Progress.student_id == student.id,
                    Progress.lesson_id == prev_lesson.id,
                    Progress.status == ProgressStatus.COMPLETED
                ).first()
                
                if not progress:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"You must complete lesson '{prev_lesson.title}' first."
                    )

    return {"success": True, "data": lesson}

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_lesson(
    title: str = Form(...),
    title_uz: str = Form(...),
    title_ru: str = Form(...),
    subject_id: uuid.UUID = Form(...),
    description: str = Form(None),
    level: int = Form(1),
    current_user: User = Depends(deps.require_verified_teacher),
    db: Session = Depends(get_db)
):
    """
    Create a new lesson (Verified Teachers Only)
    """
    service = LessonService(db)
    lesson_data = {
        "title": title,
        "title_uz": title_uz,
        "title_ru": title_ru,
        "subject_id": subject_id,
        "description": description,
        "level": level,
        "created_by_id": current_user.id # Assuming current_user has an id
    }
    lesson = service.create(lesson_data)
    db.commit()
    return {"success": True, "data": lesson}

@router.put("/{lesson_id}")
async def update_lesson(
    lesson_id: UUID,
    lesson_data: dict,
    current_user: User = Depends(deps.get_current_active_user), # Changed to deps.get_current_active_user
    db: Session = Depends(get_db)
):
    """Update lesson (Admin/Teacher only)"""
    if current_user.role not in [UserRole.organization, UserRole.moderator, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    service = LessonService(db)
    lesson = service.update(str(lesson_id), lesson_data)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.commit()
    return {"success": True, "data": lesson}

@router.delete("/{lesson_id}")
def delete_lesson(
    lesson_id: uuid.UUID,
    current_user: User = Depends(deps.require_verified_teacher), # SECURED
    db: Session = Depends(get_db)
):
    """Delete lesson (Admin only)"""
    if current_user.role not in [UserRole.organization, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    service = LessonService(db)
    success = service.delete(str(lesson_id))
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.commit()
    return {"success": True, "message": "Lesson deleted"}
