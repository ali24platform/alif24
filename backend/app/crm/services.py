from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from datetime import datetime
from uuid import UUID

from app.crm.models import Lead, Activity, LeadStatus, ActivityType
from app.crm.schemas import LeadCreate, LeadUpdate, LeadFilter, ActivityCreate, ActivityUpdate
from app.core.errors import NotFoundError, ForbiddenError

class CRMService:
    def __init__(self, db: Session):
        self.db = db

    # --- Lead Operations ---
    def create_lead(self, lead_in: LeadCreate) -> Lead:
        lead = Lead(
            first_name=lead_in.first_name,
            last_name=lead_in.last_name,
            phone=lead_in.phone,
            source=lead_in.source,
            status=lead_in.status,
            notes=lead_in.notes,
            assigned_to_id=lead_in.assigned_to_id
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def get_leads(self, filter_in: LeadFilter, skip: int = 0, limit: int = 100) -> List[Lead]:
        # FIX: N+1 Problem solved with joinedload(Lead.activities)
        query = self.db.query(Lead).options(joinedload(Lead.activities))

        if filter_in.status:
            query = query.filter(Lead.status == filter_in.status)
        
        if filter_in.assigned_to_id:
            query = query.filter(Lead.assigned_to_id == filter_in.assigned_to_id)

        if filter_in.search:
            search = f"%{filter_in.search}%"
            query = query.filter(
                or_(
                    Lead.first_name.ilike(search),
                    Lead.last_name.ilike(search),
                    Lead.phone.ilike(search)
                )
            )
        
        return query.order_by(desc(Lead.created_at)).offset(skip).limit(limit).all()

    def get_lead(self, lead_id: int) -> Lead:
        # FIX: Optimized single lead fetch too
        lead = self.db.query(Lead).options(joinedload(Lead.activities)).filter(Lead.id == lead_id).first()
        if not lead:
            raise NotFoundError("Lead topilmadi")
        return lead

    def update_lead(self, lead_id: int, lead_in: LeadUpdate) -> Lead:
        lead = self.get_lead(lead_id)
        
        update_data = lead_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)

        self.db.commit()
        self.db.refresh(lead)
        return lead

    def delete_lead(self, lead_id: int):
        lead = self.get_lead(lead_id)
        self.db.delete(lead)
        self.db.commit()

    # --- Activity Operations ---
    def create_activity(self, lead_id: int, activity_in: ActivityCreate, user_id: UUID) -> Activity:
        # Check if lead exists
        self.get_lead(lead_id)
        
        activity = Activity(
            lead_id=lead_id,
            type=activity_in.type,
            summary=activity_in.summary,
            description=activity_in.description,
            due_date=activity_in.due_date,
            is_completed=activity_in.is_completed,
            created_by_id=user_id
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def update_activity(self, activity_id: int, activity_in: ActivityUpdate) -> Activity:
        activity = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise NotFoundError("Activity topilmadi")

        update_data = activity_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activity, field, value)

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def delete_activity(self, activity_id: int):
        activity = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise NotFoundError("Activity topilmadi")
        
        self.db.delete(activity)
        self.db.commit()
