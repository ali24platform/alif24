"""
Olympiad API Endpoints
Routes for olympiad management and participation.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, UserRole, OlympiadSubject
from app.services.olympiad_service import OlympiadService


router = APIRouter(prefix="/olympiad", tags=["Olympiad"])


# ============================================================
# SCHEMAS
# ============================================================

class CreateOlympiadRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    subject: OlympiadSubject = OlympiadSubject.general
    registration_start: datetime
    registration_end: datetime
    start_time: datetime
    end_time: datetime
    duration_minutes: int = Field(default=30, ge=10, le=120)
    min_age: int = Field(default=4, ge=3, le=18)
    max_age: int = Field(default=7, ge=3, le=18)
    max_participants: int = Field(default=500, ge=10, le=10000)
    questions_count: int = Field(default=20, ge=5, le=100)


class QuestionInput(BaseModel):
    text: str
    image: Optional[str] = None
    options: List[str] = Field(..., min_items=2, max_items=6)
    correct: int = Field(..., ge=0)
    points: int = Field(default=5, ge=1, le=20)


class AddQuestionsRequest(BaseModel):
    questions: List[QuestionInput]


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_answer: int = Field(..., ge=0, le=5)


class OlympiadResponse(BaseModel):
    id: str
    title: str
    subject: str
    status: str
    registration_start: str
    registration_end: str
    start_time: str
    min_age: int
    max_age: int
    participants_count: int
    max_participants: int


class LeaderboardEntry(BaseModel):
    rank: int
    student_name: str
    total_score: int
    correct_answers: int
    time_spent_seconds: int
    coins_earned: int


# ============================================================
# MODERATOR ENDPOINTS
# ============================================================

@router.post("/create", summary="Create Olympiad (Moderator Only)")
async def create_olympiad(
    request: CreateOlympiadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new olympiad.
    Only moderators can create olympiads.
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar olimpiada yaratishi mumkin")
    
    service = OlympiadService(db)
    return service.create_olympiad(
        moderator_user_id=current_user.id,
        title=request.title,
        description=request.description,
        subject=request.subject,
        registration_start=request.registration_start,
        registration_end=request.registration_end,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_minutes=request.duration_minutes,
        min_age=request.min_age,
        max_age=request.max_age,
        max_participants=request.max_participants,
        questions_count=request.questions_count
    )


@router.post("/{olympiad_id}/questions", summary="Add Questions (Moderator Only)")
async def add_questions(
    olympiad_id: UUID,
    request: AddQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add questions to an olympiad.
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = OlympiadService(db)
    questions_data = [q.model_dump() for q in request.questions]
    return service.add_questions(current_user.id, olympiad_id, questions_data)


@router.post("/{olympiad_id}/publish", summary="Publish Olympiad (Moderator Only)")
async def publish_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish olympiad for registration.
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = OlympiadService(db)
    return service.publish_olympiad(current_user.id, olympiad_id)


@router.post("/{olympiad_id}/start", summary="Start Olympiad (Moderator Only)")
async def start_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start the olympiad - allow students to take the exam.
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = OlympiadService(db)
    return service.start_olympiad(current_user.id, olympiad_id)


@router.post("/{olympiad_id}/finish", summary="Finish Olympiad (Moderator Only)")
async def finish_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finish olympiad and calculate rankings.
    """
    if current_user.role != UserRole.moderator:
        raise HTTPException(status_code=403, detail="Faqat moderatorlar uchun")
    
    service = OlympiadService(db)
    return service.finish_olympiad(current_user.id, olympiad_id)


# ============================================================
# PUBLIC / STUDENT ENDPOINTS
# ============================================================

@router.get("/list", response_model=List[OlympiadResponse], summary="List Upcoming Olympiads")
async def list_olympiads(db: Session = Depends(get_db)):
    """
    Get all upcoming and active olympiads.
    Public endpoint.
    """
    service = OlympiadService(db)
    return service.get_upcoming_olympiads()


@router.post("/{olympiad_id}/register", summary="Register for Olympiad (Student)")
async def register_for_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register for an olympiad.
    Only students with active monthly subscription can register.
    """
    service = OlympiadService(db)
    return service.register_student(current_user.id, olympiad_id)


@router.post("/{olympiad_id}/begin", summary="Start Taking Olympiad (Student)")
async def begin_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start taking the olympiad exam.
    Returns questions without correct answers.
    """
    service = OlympiadService(db)
    return service.start_olympiad_for_student(current_user.id, olympiad_id)


@router.post("/{olympiad_id}/answer", summary="Submit Answer (Student)")
async def submit_answer(
    olympiad_id: UUID,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answer for a question.
    """
    service = OlympiadService(db)
    return service.submit_answer(
        current_user.id,
        olympiad_id,
        request.question_id,
        request.selected_answer
    )


@router.post("/{olympiad_id}/complete", summary="Complete Olympiad (Student)")
async def complete_olympiad(
    olympiad_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finish taking the olympiad.
    """
    service = OlympiadService(db)
    return service.finish_olympiad_for_student(current_user.id, olympiad_id)


@router.get("/{olympiad_id}/results", response_model=List[LeaderboardEntry], summary="Get Results (Public)")
async def get_results(
    olympiad_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get olympiad leaderboard / results.
    Public endpoint after olympiad is finished.
    """
    service = OlympiadService(db)
    return service.get_olympiad_results(olympiad_id)


@router.get("/my-history", summary="Get My Olympiad History (Student)")
async def get_my_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student's olympiad participation history.
    Used in parent dashboard.
    """
    service = OlympiadService(db)
    return service.get_student_olympiad_history(current_user.id)
