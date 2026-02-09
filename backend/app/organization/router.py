"""
Organization Dashboard API
Ta’lim tashkiloti paneli uchun
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text, desc
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from app.core.database import get_db
from app.middleware.deps import only_organization
from app.models import User, StudentProfile, TeacherProfile, OrganizationProfile, OrganizationMaterial
from app.crm.models import Lead, Activity, LeadStatus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """
    Get organization dashboard statistics
    Optimized for performance (single query for counts)
    """
    org_id = current_user.organization_profile.id
    
    try:
        # 1. Total Students
        total_students = db.query(func.count(StudentProfile.id))\
            .filter(StudentProfile.organization_id == org_id)\
            .scalar()
            
        # 2. Total Leads
        total_leads = db.query(func.count(Lead.id))\
            .filter(Lead.organization_id == org_id)\
            .scalar()

        # 3. Leads by Status (Group By for Performance)
        # Result: [('new', 10), ('won', 5), ...]
        leads_by_status_result = db.query(Lead.status, func.count(Lead.id))\
            .filter(Lead.organization_id == org_id)\
            .group_by(Lead.status)\
            .all()
        
        # Format for Recharts: [{name: 'new', value: 10}, ...]
        leads_by_status = [
            {"name": status.value, "value": count} 
            for status, count in leads_by_status_result
        ]
        
        # 4. Recent Activities (with Lead info)
        # Using joinedload to avoid N+1
        recent_activities = db.query(Activity)\
            .join(Lead)\
            .filter(Lead.organization_id == org_id)\
            .options(joinedload(Activity.lead))\
            .order_by(desc(Activity.created_at))\
            .limit(5)\
            .all()
            
        formatted_activities = [
            {
                "id": str(a.id),
                "type": a.type.value,
                "summary": a.summary,
                "lead_name": f"{a.lead.first_name} {a.lead.last_name or ''}".strip(),
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in recent_activities
        ]

        # 5. Total Teachers
        total_teachers = db.query(func.count(TeacherProfile.id))\
            .filter(TeacherProfile.organization_id == org_id)\
            .scalar()

        return {
            "total_students": total_students or 0,
            "total_leads": total_leads or 0,
            "total_teachers": total_teachers or 0,
            "leads_by_status": leads_by_status,
            "recent_activities": formatted_activities
        }

    except Exception as e:
        logger.error(f"Error fetching org stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Statistikani yuklashda xatolik yuz berdi")


@router.get("/teachers")
async def get_org_teachers(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """Get all teachers in this organization"""
    org_id = current_user.organization_profile.id
    
    teachers = db.query(TeacherProfile)\
        .filter(TeacherProfile.organization_id == org_id)\
        .options(joinedload(TeacherProfile.user))\
        .all()
        
    return [
        {
            "id": str(t.id),
            "qualification": t.qualification,
            "verification_status": t.verification_status.value,
            "user": {
                "first_name": t.user.first_name,
                "last_name": t.user.last_name,
                "email": t.user.email
            }
        }
        for t in teachers
    ]

@router.get("/materials")
async def get_org_materials(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """Get organization materials"""
    org_id = current_user.organization_profile.id
    
    materials = db.query(OrganizationMaterial)\
        .filter(OrganizationMaterial.organization_id == org_id)\
        .order_by(desc(OrganizationMaterial.created_at))\
        .all()
        
    return [
        {
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "file_url": m.file_url,
            "category": m.category,
            "created_at": m.created_at.isoformat()
        }
        for m in materials
    ]

@router.get("/users")
async def get_org_users(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """
    Get all users linked to this organization (students, teachers)
    """
    org_id = current_user.organization_profile.id
    
    # Fetch teachers
    teachers = db.query(TeacherProfile)\
        .filter(TeacherProfile.organization_id == org_id)\
        .options(joinedload(TeacherProfile.user))\
        .all()
        
    # Fetch students
    students = db.query(StudentProfile)\
        .filter(StudentProfile.organization_id == org_id)\
        .options(joinedload(StudentProfile.user))\
        .all()
        
    users_list = []
    
    for t in teachers:
        users_list.append({
            "id": str(t.user.id),
            "name": f"{t.user.first_name} {t.user.last_name}",
            "email": t.user.email,
            "role": "teacher",
            "is_active": True
        })
        
    for s in students:
        users_list.append({
            "id": str(s.user.id),
            "name": f"{s.user.first_name} {s.user.last_name}",
            "email": s.user.email or s.user.username,
            "role": "student",
            "is_active": True
        })
        
    return {"users": users_list}
