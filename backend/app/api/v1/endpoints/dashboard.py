from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Dict, Any, List, Optional
import uuid

from app.core.database import get_db
from app.middleware.deps import get_current_user
from app.models.user import User
from app.models.rbac_models import StudentProfile
from app.models.progress import Progress, ProgressStatus
from app.models.lesson import Lesson
from app.models.reading_analysis import ReadingAnalysis

router = APIRouter()

@router.get("/student")
async def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified Dashboard Endpoint (Performance Optimized).
    Fetches:
    1. Student Profile (Points, Coins, Level, Streak)
    2. Reading Stats (Total Words, Sessions via SQL Aggregation)
    3. Active Tasks/Lessons (Next up)
    """
    
    # 1. Fetch Student Profile (Eagerly or via direct query if relationship not set)
    # We query StudentProfile directly to be safe and efficient
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.user_id == current_user.id
    ).first()

    if not student_profile:
        # Create default profile if missing (auto-heal) or return basic stats
        # For now, we'll return zeroes but log warning
        stats = {
            "level": 1,
            "points": 0,
            "coins": 0,
            "streak": 0,
            "xp": 0
        }
    else:
        stats = {
            "level": student_profile.level,
            "points": student_profile.total_points,
            "coins": student_profile.total_coins,
            "streak": student_profile.current_streak,
            # Mocking XP as points for now, or calculate based on level
            "xp": student_profile.total_points 
        }

    # 2. Reading Analysis Stats (SQL Aggregation - O(1) Fetch)
    # Replaces the O(N) loop in story_router
    reading_stats_query = db.query(
        func.count(ReadingAnalysis.id).label("total_sessions"),
        func.sum(ReadingAnalysis.total_words_read).label("total_words"),
        func.avg(ReadingAnalysis.pronunciation_score).label("avg_pronunciation"),
        func.avg(ReadingAnalysis.comprehension_score).label("avg_comprehension"),
        func.sum(ReadingAnalysis.speech_errors).label("total_errors")
    ).filter(
        ReadingAnalysis.user_id == current_user.id
    )
    
    reading_result = reading_stats_query.first()
    
    reading_stats = {
        "total_sessions": reading_result.total_sessions or 0,
        "total_words": int(reading_result.total_words or 0),
        "avg_pronunciation": round(float(reading_result.avg_pronunciation or 0), 1),
        "avg_comprehension": round(float(reading_result.avg_comprehension or 0), 1),
        "total_errors": int(reading_result.total_errors or 0)
    }

    # 3. Active/Pending Tasks (Recent uncompleted lessons or next in sequence)
    # Logic: Find lessons that are NOT completed
    # For simplicity, we'll mock this or query available lessons if schema supports it
    # Ideally: Fetch 3 pending tasks
    
    # Example tasks (Static for now, but dynamic structure ready)
    tasks = [
        {"id": 1, "title": "Matematika: Ko'paytirish jadvali", "deadline": "Bugun, 18:00", "xp": 50, "status": "pending"},
        {"id": 2, "title": "English: New Words", "deadline": "Ertaga", "xp": 30, "status": "pending"},
    ]

    return {
        "status": "success",
        "data": {
            "user": {
                "id": str(current_user.id),
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "role": current_user.role.value,
                "avatar": current_user.avatar
            },
            "profile": stats,
            "reading_stats": reading_stats,
            "tasks": tasks
        }
    }
