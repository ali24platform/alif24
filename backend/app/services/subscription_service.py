"""
Subscription Service
Handles teacher subscription logic, free trials, and payment processing.
"""
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import (
    User, TeacherProfile, TeacherSubscription, SubscriptionTier, 
    Payment, PaymentProvider, PaymentStatus
)
from app.core.errors import BadRequestError, NotFoundError, ConflictError

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_subscription(self, teacher_id: UUID) -> Optional[TeacherSubscription]:
        """Get active subscription for a teacher"""
        teacher = self.db.query(TeacherProfile).filter(TeacherProfile.id == teacher_id).first()
        if not teacher:
            raise NotFoundError("Teacher profile not found")
            
        return self.db.query(TeacherSubscription).filter(
            TeacherSubscription.teacher_id == teacher_id
        ).first()

    def start_free_trial(self, teacher_id: UUID) -> Dict:
        """
        Start a 7-day free trial for a new teacher.
        Usually called upon teacher approval or first login.
        """
        existing = self.get_subscription(teacher_id)
        if existing:
            raise ConflictError("Subscription already exists for this teacher")
            
        # Create Trial Subscription
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)
        
        subscription = TeacherSubscription(
            teacher_id=teacher_id,
            tier=SubscriptionTier.trial,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            auto_renew=False
        )
        
        self.db.add(subscription)
        self.db.commit()
        
        return {
            "message": "7-day Free Trial activated",
            "tier": "TRIAL",
            "expires_at": end_date.isoformat()
        }

    def check_subscription_status(self, teacher_id: UUID) -> Dict:
        """
        Check if teacher has active subscription.
        If TRIAL expired, deactivates it.
        """
        sub = self.get_subscription(teacher_id)
        
        if not sub:
            return {"is_active": False, "tier": None, "message": "No subscription"}
            
        now = datetime.utcnow()
        
        if sub.end_date < now:
            # Expired
            if sub.is_active:
                sub.is_active = False
                self.db.commit()
            return {
                "is_active": False, 
                "tier": sub.tier.value, 
                "message": "Subscription expired",
                "expired_at": sub.end_date.isoformat()
            }
            
        return {
            "is_active": True,
            "tier": sub.tier.value,
            "expires_at": sub.end_date.isoformat(),
            "days_left": (sub.end_date - now).days
        }

    def create_payment(self, user_id: UUID, amount: int, provider: str) -> Dict:
        """
        Initiate a payment (Mock for now)
        """
        if provider not in [p.value for p in PaymentProvider]:
            raise BadRequestError("Invalid payment provider")
            
        payment = Payment(
            user_id=user_id,
            amount=amount,
            provider=provider,
            status=PaymentStatus.pending,
            description="Teacher Subscription Payment"
        )
        
        self.db.add(payment)
        self.db.commit()
        
        return {
            "payment_id": str(payment.id),
            "status": "pending",
            "checkout_url": f"https://checkout.{provider}.uz/{payment.id}" # Mock URL
        }

    def activate_subscription(self, teacher_id: UUID, tier: str, months: int = 1) -> Dict:
        """
        Activate/Renew subscription after successful payment.
        """
        if tier not in [t.value for t in SubscriptionTier]:
            raise BadRequestError("Invalid tier")
            
        sub = self.get_subscription(teacher_id)
        now = datetime.utcnow()
        
        start_date = now
        # If active, extend from current end_date
        if sub and sub.is_active and sub.end_date > now:
            start_date = sub.end_date
            
        end_date = start_date + timedelta(days=30 * months)
        
        if sub:
            sub.tier = tier
            sub.end_date = end_date
            sub.is_active = True
        else:
            sub = TeacherSubscription(
                teacher_id=teacher_id,
                tier=tier,
                start_date=now,
                end_date=end_date,
                is_active=True
            )
            self.db.add(sub)
            
        self.db.commit()
        
        return {
            "message": "Subscription activated",
            "tier": tier,
            "expires_at": end_date.isoformat()
        }
