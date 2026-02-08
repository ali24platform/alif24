from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.middleware.deps import get_current_active_user, only_organization_or_moderator
from app.models import User
from app.crm import schemas, services

router = APIRouter(prefix="/crm", tags=["CRM"])

# --- Leads ---
@router.post("/leads", response_model=schemas.LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: schemas.LeadCreate,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    # If assigned_to_id is not set, default to current user if Organization?
    # Logic handled in frontend/service usually.
    return service.create_lead(lead_in)

@router.get("/leads", response_model=List[schemas.LeadResponse])
async def get_leads(
    status: schemas.LeadStatus = None,
    search: str = None,
    assigned_to_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    filter_in = schemas.LeadFilter(status=status, search=search, assigned_to_id=assigned_to_id)
    return service.get_leads(filter_in, skip, limit)

@router.get("/leads/{lead_id}", response_model=schemas.LeadResponse)
async def get_lead(
    lead_id: int,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    return service.get_lead(lead_id)

@router.put("/leads/{lead_id}", response_model=schemas.LeadResponse)
async def update_lead(
    lead_id: int,
    lead_in: schemas.LeadUpdate,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    return service.update_lead(lead_id, lead_in)

@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    service.delete_lead(lead_id)

# --- Activities ---
@router.post("/leads/{lead_id}/activities", response_model=schemas.ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    lead_id: int,
    activity_in: schemas.ActivityCreate,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    return service.create_activity(lead_id, activity_in, current_user.id)

@router.put("/activities/{activity_id}", response_model=schemas.ActivityResponse)
async def update_activity(
    activity_id: int,
    activity_in: schemas.ActivityUpdate,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    return service.update_activity(activity_id, activity_in)

@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: User = Depends(only_organization_or_moderator),
    db: Session = Depends(get_db)
):
    service = services.CRMService(db)
    service.delete_activity(activity_id)
