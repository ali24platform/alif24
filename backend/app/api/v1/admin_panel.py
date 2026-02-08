"""
Secret Admin Panel API Endpoints

Yashirin admin paneli uchun endpointlar:
- Faqat maxfiy parol bilan kirish mumkin
- /nurali, /hazratqul, /pedagog yo'llaridan foydalanish uchun
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.models import User, UserRole, AccountStatus
from app.models.rbac_models import StudentProfile, TeacherProfile, ParentProfile

router = APIRouter(prefix="/secret", tags=["secret-admin"])


# ============================================================
# SCHEMAS
# ============================================================

class SecretAccessRequest(BaseModel):
    """Maxfiy kirish uchun so'rov"""
    passphrase: str = Field(..., description="Secret passphrase for admin access")


class SecretAccessResponse(BaseModel):
    """Kirish javobi"""
    success: bool
    token: str = None  # Simple session token
    message: str


class UserActivityLog(BaseModel):
    """Foydalanuvchi faoliyat logi"""
    id: str
    user_id: str
    user_email: str
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    details: Optional[Dict[str, Any]]
    timestamp: datetime


class DashboardStats(BaseModel):
    """Dashboard statistikasi"""
    total_users: int
    total_students: int
    total_teachers: int
    total_parents: int
    active_users: int
    new_users_today: int
    new_users_week: int


class SearchResult(BaseModel):
    """Qidiruv natijasi"""
    type: str  # user, game, lesson
    id: str
    title: str
    subtitle: str
    

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def verify_secret_access(passphrase: str) -> bool:
    """Maxfiy parolni tekshirish"""
    return passphrase == settings.ADMIN_SECRET_KEY


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/access", response_model=SecretAccessResponse)
async def secret_access(request: SecretAccessRequest):
    """
    Maxfiy admin paneliga kirish
    
    Parol to'g'ri bo'lsa, session token qaytariladi
    """
    if not verify_secret_access(request.passphrase):
        raise HTTPException(status_code=403, detail="Invalid passphrase")
    
    # Generate simple session token (in production, use proper JWT)
    import secrets
    token = secrets.token_urlsafe(32)
    
    return SecretAccessResponse(
        success=True,
        token=token,
        message="Access granted"
    )


@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Platform statistikasi - Dashboard uchun
    """
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    # Total counts by role
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.role == UserRole.student).scalar() or 0
    total_teachers = db.query(func.count(User.id)).filter(User.role == UserRole.teacher).scalar() or 0
    total_parents = db.query(func.count(User.id)).filter(User.role == UserRole.parent).scalar() or 0
    
    # Active users (logged in within 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(User.id)).filter(
        User.last_login_at >= thirty_days_ago
    ).scalar() or 0
    
    # New users today
    new_users_today = db.query(func.count(User.id)).filter(
        func.date(User.created_at) == today
    ).scalar() or 0
    
    # New users this week
    new_users_week = db.query(func.count(User.id)).filter(
        func.date(User.created_at) >= week_ago
    ).scalar() or 0
    
    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_parents": total_parents,
            "active_users": active_users,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@router.get("/users")
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Barcha foydalanuvchilar ro'yxati
    """
    query = db.query(User)
    
    # Filters
    if role:
        query = query.filter(User.role == UserRole(role))
    if status:
        query = query.filter(User.status == AccountStatus(status))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.phone.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": {
            "users": [u.to_dict() for u in users],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/user/{user_id}")
async def get_user_details(user_id: str, db: Session = Depends(get_db)):
    """
    Foydalanuvchi haqida to'liq ma'lumot
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get role-specific profile
    profile = None
    if user.role == UserRole.student:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    elif user.role == UserRole.teacher:
        profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
    elif user.role == UserRole.parent:
        profile = db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
    
    return {
        "success": True,
        "data": {
            "user": user.to_dict(),
            "profile": profile.to_dict() if profile and hasattr(profile, 'to_dict') else None
        }
    }


@router.get("/search")
async def smart_search(
    q: str = Query(..., min_length=3, description="Search query (min 3 characters)"),
    db: Session = Depends(get_db)
):
    """
    Smart qidiruv - foydalanuvchilar, o'yinlar, darslar
    
    Kamida 3 ta belgi kiritilganda ishlaydi
    """
    results = []
    search_term = f"%{q}%"
    
    # Search users
    users = db.query(User).filter(
        (User.email.ilike(search_term)) |
        (User.first_name.ilike(search_term)) |
        (User.last_name.ilike(search_term)) |
        (User.phone.ilike(search_term))
    ).limit(10).all()
    
    for user in users:
        results.append({
            "type": "user",
            "id": str(user.id),
            "title": f"{user.first_name} {user.last_name}",
            "subtitle": f"{user.role.value} - {user.email or user.phone}"
        })
    
    # TODO: Search games when Game model is available
    # TODO: Search lessons when Lesson model is available
    
    return {
        "success": True,
        "data": {
            "query": q,
            "results": results,
            "total": len(results)
        }
    }


@router.get("/database/tables")
async def get_database_tables(db: Session = Depends(get_db)):
    """
    Ma'lumotlar bazasi jadvallari ro'yxati
    """
    try:
        # Get table names from PostgreSQL
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        return {
            "success": True,
            "data": {
                "tables": tables,
                "count": len(tables)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/table/{table_name}")
async def get_table_data(
    table_name: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Jadval ma'lumotlarini ko'rish (faqat SELECT)
    
    Xavfsizlik: Faqat public schema jadvallariga ruxsat
    """
    # Validate table name (prevent SQL injection)
    allowed_tables_result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """))
    allowed_tables = [row[0] for row in allowed_tables_result.fetchall()]
    
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Invalid table name")
    
    try:
        # Get column names
        columns_result = db.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        columns = [row[0] for row in columns_result.fetchall()]
        
        # Get data with pagination
        # Note: Using text() for table name is safe after validation above
        data_result = db.execute(text(f"""
            SELECT * FROM {table_name}
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip})
        
        rows = []
        for row in data_result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert non-serializable types
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, UUID):
                    value = str(value)
                row_dict[col] = value
            rows.append(row_dict)
        
        # Get total count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total = count_result.scalar()
        
        return {
            "success": True,
            "data": {
                "table": table_name,
                "columns": columns,
                "rows": rows,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_activity_log(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    days: int = 7,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchi faoliyatlari logi
    
    Hozircha placeholder - keyinchalik ActivityLog modeli qo'shiladi
    """
    # TODO: Implement ActivityLog model and tracking
    return {
        "success": True,
        "data": {
            "activities": [],
            "message": "Activity logging will be implemented with ActivityLog model",
            "total": 0
        }
    }
