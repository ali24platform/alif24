"""
Live Quiz API Endpoints
Kahoot/Quizizz style real-time quiz routes.
Maximum 40 students per session.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models import User, UserRole
from app.services.live_quiz_service import LiveQuizService


router = APIRouter(prefix="/live-quiz", tags=["Live Quiz"])


# ============================================================
# SCHEMAS
# ============================================================

class CreateQuizRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    time_per_question: int = Field(default=30, ge=10, le=120)
    shuffle_questions: bool = False
    shuffle_options: bool = False


class QuestionInput(BaseModel):
    text: str
    image: Optional[str] = None
    options: List[str] = Field(..., min_items=2, max_items=6)
    correct: int = Field(..., ge=0)
    points: int = Field(default=100, ge=10, le=1000)
    time_limit: Optional[int] = None


class AddQuestionsRequest(BaseModel):
    questions: List[QuestionInput]


class JoinQuizRequest(BaseModel):
    join_code: str = Field(..., min_length=6, max_length=6)
    display_name: str = Field(..., min_length=1, max_length=50)
    avatar_emoji: str = Field(default="🎮", max_length=10)


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_answer: int = Field(..., ge=0, le=5)
    time_to_answer_ms: int = Field(..., ge=0)


# ============================================================
# TEACHER ENDPOINTS
# ============================================================

@router.post("/create", summary="Create Live Quiz (Teacher)")
async def create_quiz(
    request: CreateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new live quiz session."""
    if current_user.role not in [UserRole.teacher, UserRole.organization, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar uchun")
    
    service = LiveQuizService(db)
    return service.create_quiz(
        teacher_user_id=current_user.id,
        title=request.title,
        description=request.description,
        time_per_question=request.time_per_question,
        shuffle_questions=request.shuffle_questions,
        shuffle_options=request.shuffle_options
    )


@router.post("/{quiz_id}/questions", summary="Add Questions (Teacher)")
async def add_questions(
    quiz_id: UUID,
    request: AddQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add questions to the quiz."""
    service = LiveQuizService(db)
    questions_data = [q.model_dump() for q in request.questions]
    return service.add_questions(current_user.id, quiz_id, questions_data)


@router.post("/{quiz_id}/open-lobby", summary="Open Lobby (Teacher)")
async def open_lobby(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Open quiz lobby for students to join.
    Returns join code and QR data.
    """
    service = LiveQuizService(db)
    return service.open_lobby(current_user.id, quiz_id)


@router.get("/{quiz_id}/lobby-status", summary="Get Lobby Status (Teacher)")
async def get_lobby_status(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current lobby status and participant list."""
    service = LiveQuizService(db)
    return service.get_lobby_status(current_user.id, quiz_id)


@router.post("/{quiz_id}/start", summary="Start Quiz (Teacher)")
async def start_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start the quiz - begin showing questions."""
    service = LiveQuizService(db)
    return service.start_quiz(current_user.id, quiz_id)


@router.get("/{quiz_id}/current-question", summary="Get Current Question (Teacher)")
async def get_current_question(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current question for display on teacher screen."""
    service = LiveQuizService(db)
    return service.get_current_question(current_user.id, quiz_id)


@router.post("/{quiz_id}/next-question", summary="Next Question (Teacher)")
async def next_question(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move to next question."""
    service = LiveQuizService(db)
    return service.next_question(current_user.id, quiz_id)


@router.get("/{quiz_id}/question-results/{question_id}", summary="Get Question Results (Teacher)")
async def get_question_results(
    quiz_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for a specific question."""
    service = LiveQuizService(db)
    return service.get_question_results(current_user.id, quiz_id, question_id)


@router.get("/{quiz_id}/leaderboard", summary="Get Leaderboard (Teacher)")
async def get_leaderboard(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current leaderboard."""
    service = LiveQuizService(db)
    return service.get_leaderboard(current_user.id, quiz_id)


@router.post("/{quiz_id}/end", summary="End Quiz (Teacher)")
async def end_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End the quiz and finalize scores."""
    service = LiveQuizService(db)
    return service.end_quiz(current_user.id, quiz_id)


# ============================================================
# STUDENT ENDPOINTS
# ============================================================

@router.post("/join", summary="Join Quiz (Student)")
async def join_quiz(
    request: JoinQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a quiz using 6-digit code.
    Max 40 students per session.
    """
    service = LiveQuizService(db)
    return service.join_quiz(
        student_user_id=current_user.id,
        join_code=request.join_code,
        display_name=request.display_name,
        avatar_emoji=request.avatar_emoji
    )


@router.get("/{quiz_id}/student/question", summary="Get Question (Student)")
async def get_student_question(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current question (without correct answer)."""
    service = LiveQuizService(db)
    return service.get_student_question(current_user.id, quiz_id)


@router.post("/{quiz_id}/student/answer", summary="Submit Answer (Student)")
async def submit_student_answer(
    quiz_id: UUID,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit answer for current question."""
    service = LiveQuizService(db)
    return service.submit_answer(
        student_user_id=current_user.id,
        quiz_id=quiz_id,
        question_id=request.question_id,
        selected_answer=request.selected_answer,
        time_to_answer_ms=request.time_to_answer_ms
    )


@router.get("/{quiz_id}/student/results", summary="Get Results (Student)")
async def get_student_results(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get final results for student."""
    service = LiveQuizService(db)
    return service.get_student_results(current_user.id, quiz_id)
