from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, UserRole, Lesson
from app.services.student_service import StudentService

router = APIRouter()

@router.post("/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: UUID,
    answers: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a lesson as completed.
    If the lesson has an attached quiz, answers must be provided.
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only students can complete lessons"
        )

    service = StudentService(db)
    try:
        result = service.complete_lesson(current_user.id, lesson_id, answers or {})
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{lesson_id}/quiz")
async def get_lesson_quiz(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the quiz associated with a lesson (without correct answers).
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not a student"
        )

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    if not lesson.quiz:
        raise HTTPException(status_code=404, detail="No quiz for this lesson")
        
    # Filter out correct answers
    safe_questions = []
    for q in lesson.quiz.questions:
        safe_q = q.copy()
        safe_q.pop("correct_answer", None)
        safe_questions.append(safe_q)
        
    return {
        "id": str(lesson.quiz.id),
        "title": lesson.quiz.title,
        "description": lesson.quiz.description,
        "questions": safe_questions,
        "total_points": lesson.quiz.total_points,
        "time_limit_minutes": lesson.quiz.time_limit_minutes
    }
