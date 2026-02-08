from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
import secrets
import string

from app.core.database import get_db
from app.middleware.deps import only_organization
from app.models.rbac_models import (
    User, TeacherProfile, StudentProfile, OrganizationMaterial, OrganizationSubscription, UserRole, AccountStatus
)
from app.services.notification_service import NotificationService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# --- Schemas ---
class AddTeacherRequest(BaseModel):
    teacher_id: UUID

class InviteStudentRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class MaterialCreate(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: str
    file_type: Optional[str] = None
    category: Optional[str] = None

class MaterialResponse(MaterialCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    created_by_id: Optional[UUID]

# --- Endpoints ---

@router.post("/students/invite")
async def invite_student_to_organization(
    request: InviteStudentRequest,
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """
    Invite a new student to the organization.
    Creates a User and StudentProfile, sends credentials via SMS/Email.
    """
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    # 1. Check if user exists
    existing_user = db.query(User).filter(User.phone == request.phone).first()
    if existing_user:
        # If exists, just check/add profile link
        # For simplicity in this logic: if user exists but isn't a student of this org, we link them.
        # But if they are already a student elsewhere, we might need a pivot table or allow multiple orgs.
        # Current models: StudentProfile has one organization_id (Many-to-One). 
        # So a student belongs to ONE organization primary.
        raise HTTPException(status_code=400, detail="Foydalanuvchi allaqachon mavjud (Telefon raqami band)")

    # 2. Generate Credentials
    password = ''.join(secrets.choice(string.digits) for _ in range(6)) # 6 digit numeric password for ease
    
    # 3. Create User
    new_user = User(
        first_name=request.name.split(" ")[0],
        last_name=" ".join(request.name.split(" ")[1:]) if " " in request.name else "",
        phone=request.phone,
        email=request.email,
        role=UserRole.student,
        status=AccountStatus.active,
        language="uz"
    )
    new_user.set_password(password)
    db.add(new_user)
    db.flush() # Get ID
    
    # 4. Create Student Profile linked to Organization
    student_profile = StudentProfile(
        user_id=new_user.id,
        organization_id=org_profile.id,
        level=1
    )
    db.add(student_profile)
    
    # 5. Send Notification
    notification_service = NotificationService(db)
    message = f"Assalomu alaykum, {request.name}. Siz {org_profile.name} tomonidan Alif24 platformasiga taklif qilindingiz.\nLogin: {request.phone}\nParol: {password}\nIlova: https://alif24.uz"
    
    # Send SMS (priority)
    await notification_service.send_sms(request.phone, message, user_id=new_user.id)
    
    if request.email:
        notification_service.send_email(request.email, "Alif24 Taklifnoma", message, user_id=new_user.id)
        
    db.commit()
    
    return {"message": "Student invited successfully", "user_id": new_user.id}

@router.post("/teachers")
def add_teacher_to_organization(
    request: AddTeacherRequest,
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    """
    Link a teacher to the organization
    """
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")

    teacher = db.query(TeacherProfile).filter(TeacherProfile.id == request.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check limit based on subscription
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == org_profile.id,
        OrganizationSubscription.is_active == True
    ).first()
    
    current_count = db.query(TeacherProfile).filter(TeacherProfile.organization_id == org_profile.id).count()
    limit = subscription.max_teachers if subscription else 5 # Default limit
    
    if current_count >= limit:
        raise HTTPException(status_code=403, detail=f"Teacher limit reached ({limit})")

    teacher.organization_id = org_profile.id
    db.commit()
    return {"message": "Teacher added to organization"}

@router.delete("/teachers/{teacher_id}")
def remove_teacher_from_organization(
    teacher_id: UUID,
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    teacher = db.query(TeacherProfile).filter(
        TeacherProfile.id == teacher_id,
        TeacherProfile.organization_id == org_profile.id
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found in this organization")
    
    teacher.organization_id = None
    db.commit()
    return {"message": "Teacher removed from organization"}

@router.get("/teachers")
def get_organization_teachers(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    teachers = db.query(TeacherProfile).filter(TeacherProfile.organization_id == org_profile.id).all()
    return teachers

# --- Materials (Content Box) ---

@router.post("/materials", response_model=MaterialResponse)
def upload_material(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file_url: str = Form(...), # In real app, handle file upload separately and pass URL
    category: Optional[str] = Form(None),
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    material = OrganizationMaterial(
        organization_id=org_profile.id,
        title=title,
        description=description,
        file_url=file_url,
        category=category,
        created_by_id=current_user.id
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material

@router.get("/materials", response_model=List[MaterialResponse])
def get_materials(
    current_user: User = Depends(only_organization),
    db: Session = Depends(get_db)
):
    org_profile = current_user.organization_profile
    if not org_profile:
        raise HTTPException(status_code=400, detail="Organization profile not found")
    
    materials = db.query(OrganizationMaterial).filter(OrganizationMaterial.organization_id == org_profile.id).all()
    return materials
