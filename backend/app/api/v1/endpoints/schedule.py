from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.deps import only_organization, only_teacher
from app.models.rbac_models import ClassroomSchedule, Classroom, User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ScheduleCreate(BaseModel):
    classroom_id: UUID
    day_of_week: str
    start_time: str
    end_time: str
    subject: Optional[str] = None
    room_number: Optional[str] = None

class ScheduleResponse(ScheduleCreate):
    id: UUID
    created_at: datetime

@router.post("/", response_model=ScheduleResponse)
def create_schedule(
    request: ScheduleCreate,
    current_user: User = Depends(only_organization), # Only organization can create schedules for now
    db: Session = Depends(get_db)
):
    # Verify organization owns the classroom's teacher? 
    # Or just verify classroom exists and belongs to a teacher in this organization.
    classroom = db.query(Classroom).filter(Classroom.id == request.classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    if not current_user.organization_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    if not classroom.teacher or classroom.teacher.organization_id != current_user.organization_profile.id:
        raise HTTPException(status_code=403, detail="Classroom does not belong to your organization")

    schedule = ClassroomSchedule(
        classroom_id=request.classroom_id,
        day_of_week=request.day_of_week,
        start_time=request.start_time,
        end_time=request.end_time,
        subject=request.subject or classroom.subject,
        room_number=request.room_number
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.get("/classroom/{classroom_id}", response_model=List[ScheduleResponse])
def get_classroom_schedule(
    classroom_id: UUID,
    current_user: User = Depends(only_organization), # Or teacher/student
    db: Session = Depends(get_db)
):
    schedules = db.query(ClassroomSchedule).filter(ClassroomSchedule.classroom_id == classroom_id).all()
    return schedules
