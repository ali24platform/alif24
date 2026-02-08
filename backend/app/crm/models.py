from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from app.core.database import Base

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    TRIAL_LESSON = "trial_lesson"
    NEGOTIATION = "negotiation"
    WON = "won"  # Converted to Student
    LOST = "lost"

class ActivityType(str, enum.Enum):
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"

class Lead(Base):
    __tablename__ = "crm_leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=False, index=True)
    source = Column(String, nullable=True)  # e.g., "Instagram", "Website", "Referral"
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    notes = Column(Text, nullable=True)
    
    # Foreign Keys - Changed to UUID
    # Foreign Keys - Changed to UUID
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization_profiles.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assigned_to = relationship("User", backref="leads")
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "crm_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=False)
    type = Column(Enum(ActivityType), default=ActivityType.NOTE)
    summary = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps - Changed to UUID
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="activities")
    created_by = relationship("User")
