"""
Olympiad Service - Business logic for Olympiad operations
Only moderators can create olympiads.
Only monthly subscribers can participate.
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.errors import BadRequestError, NotFoundError, ForbiddenError
from app.models import (
    User, UserRole, AccountStatus,
    StudentProfile, ParentProfile,
    ModeratorProfile, ModeratorRoleType,
    Olympiad, OlympiadQuestion, OlympiadParticipant, OlympiadAnswer,
    OlympiadStatus, OlympiadSubject, ParticipationStatus,
    StudentCoin, CoinTransaction, TransactionType
)


class OlympiadService:
    """Service for olympiad operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================
    # MODERATOR FUNCTIONS (Create, Update, Delete)
    # ============================================================
    
    def create_olympiad(
        self,
        moderator_user_id: UUID,
        title: str,
        description: str,
        subject: OlympiadSubject,
        registration_start: datetime,
        registration_end: datetime,
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int = 30,
        min_age: int = 4,
        max_age: int = 7,
        max_participants: int = 500,
        questions_count: int = 20
    ) -> Dict:
        """
        Create a new olympiad. Only moderators can create.
        """
        # Verify moderator
        user = self.db.query(User).filter(User.id == moderator_user_id).first()
        if not user or user.role != UserRole.moderator:
            raise ForbiddenError("Faqat moderatorlar olimpiada yaratishi mumkin")
        
        # Create olympiad
        olympiad = Olympiad(
            title=title,
            description=description,
            subject=subject,
            registration_start=registration_start,
            registration_end=registration_end,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            min_age=min_age,
            max_age=max_age,
            max_participants=max_participants,
            questions_count=questions_count,
            status=OlympiadStatus.draft,
            created_by=moderator_user_id
        )
        
        self.db.add(olympiad)
        self.db.commit()
        self.db.refresh(olympiad)
        
        return {
            "message": "Olimpiada yaratildi",
            "olympiad_id": str(olympiad.id),
            "title": olympiad.title
        }
    
    def add_questions(
        self,
        moderator_user_id: UUID,
        olympiad_id: UUID,
        questions: List[Dict]
    ) -> Dict:
        """
        Add questions to olympiad.
        questions = [{"text": "...", "options": [...], "correct": 0, "points": 5}, ...]
        """
        # Verify moderator and olympiad
        olympiad = self._get_olympiad_for_moderator(olympiad_id, moderator_user_id)
        
        for i, q in enumerate(questions):
            question = OlympiadQuestion(
                olympiad_id=olympiad_id,
                question_text=q.get("text"),
                question_image=q.get("image"),
                options=q.get("options", []),
                correct_answer=q.get("correct", 0),
                points=q.get("points", 5),
                order=i
            )
            self.db.add(question)
        
        self.db.commit()
        
        return {
            "message": f"{len(questions)} ta savol qo'shildi",
            "olympiad_id": str(olympiad_id)
        }
    
    def publish_olympiad(self, moderator_user_id: UUID, olympiad_id: UUID) -> Dict:
        """
        Publish olympiad (make it visible for registration).
        """
        olympiad = self._get_olympiad_for_moderator(olympiad_id, moderator_user_id)
        
        # Check if questions are added
        if len(olympiad.questions) < 5:
            raise BadRequestError("Kamida 5 ta savol qo'shilishi kerak")
        
        olympiad.status = OlympiadStatus.upcoming
        self.db.commit()
        
        return {"message": "Olimpiada e'lon qilindi", "status": "upcoming"}
    
    def start_olympiad(self, moderator_user_id: UUID, olympiad_id: UUID) -> Dict:
        """
        Start the olympiad (allow participants to take it).
        """
        olympiad = self._get_olympiad_for_moderator(olympiad_id, moderator_user_id)
        
        if olympiad.status != OlympiadStatus.upcoming:
            raise BadRequestError("Olimpiada faqat 'upcoming' holatidan boshlanishi mumkin")
        
        olympiad.status = OlympiadStatus.active
        self.db.commit()
        
        return {"message": "Olimpiada boshlandi", "status": "active"}
    
    def finish_olympiad(self, moderator_user_id: UUID, olympiad_id: UUID) -> Dict:
        """
        Finish olympiad and calculate final rankings.
        """
        olympiad = self._get_olympiad_for_moderator(olympiad_id, moderator_user_id)
        
        if olympiad.status != OlympiadStatus.active:
            raise BadRequestError("Faqat faol olimpiadani tugatish mumkin")
        
        # Calculate rankings
        self._calculate_rankings(olympiad_id)
        
        olympiad.status = OlympiadStatus.finished
        self.db.commit()
        
        return {"message": "Olimpiada tugadi. Natijalar hisoblandi.", "status": "finished"}
    
    # ============================================================
    # STUDENT / PARENT FUNCTIONS
    # ============================================================
    
    def get_upcoming_olympiads(self) -> List[Dict]:
        """
        Get all upcoming and active olympiads.
        """
        olympiads = self.db.query(Olympiad).filter(
            Olympiad.status.in_([OlympiadStatus.upcoming, OlympiadStatus.active])
        ).order_by(Olympiad.start_time).all()
        
        return [
            {
                "id": str(o.id),
                "title": o.title,
                "subject": o.subject.value,
                "status": o.status.value,
                "registration_start": o.registration_start.isoformat(),
                "registration_end": o.registration_end.isoformat(),
                "start_time": o.start_time.isoformat(),
                "min_age": o.min_age,
                "max_age": o.max_age,
                "participants_count": len(o.participants),
                "max_participants": o.max_participants
            }
            for o in olympiads
        ]
    
    def register_student(
        self,
        student_user_id: UUID,
        olympiad_id: UUID
    ) -> Dict:
        """
        Register a student for olympiad.
        Only students with active subscription can participate.
        """
        # Get student profile
        student_profile = self.db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student_profile:
            raise NotFoundError("O'quvchi profili topilmadi")
        
        # Check subscription (via parent)
        if not self._check_student_subscription(student_profile):
            raise ForbiddenError("Olimpiadaga qatnashish uchun oylik obuna kerak")
        
        # Get olympiad
        olympiad = self.db.query(Olympiad).filter(Olympiad.id == olympiad_id).first()
        if not olympiad:
            raise NotFoundError("Olimpiada topilmadi")
        
        if olympiad.status != OlympiadStatus.upcoming:
            raise BadRequestError("Bu olimpiadaga ro'yxatdan o'tish vaqti tugagan")
        
        # Check if already registered
        existing = self.db.query(OlympiadParticipant).filter(
            and_(
                OlympiadParticipant.olympiad_id == olympiad_id,
                OlympiadParticipant.student_id == student_profile.id
            )
        ).first()
        
        if existing:
            raise BadRequestError("Siz allaqachon ro'yxatdan o'tgansiz")
        
        # Check max participants
        if len(olympiad.participants) >= olympiad.max_participants:
            raise BadRequestError("Olimpiadada joy qolmadi")
        
        # Register
        participant = OlympiadParticipant(
            olympiad_id=olympiad_id,
            student_id=student_profile.id,
            status=ParticipationStatus.registered
        )
        
        self.db.add(participant)
        self.db.commit()
        
        return {
            "message": "Olimpiadaga muvaffaqiyatli ro'yxatdan o'tdingiz",
            "olympiad_title": olympiad.title
        }
    
    def start_olympiad_for_student(
        self,
        student_user_id: UUID,
        olympiad_id: UUID
    ) -> Dict:
        """
        Student starts taking the olympiad.
        Returns questions without correct answers.
        """
        participant = self._get_participant(student_user_id, olympiad_id)
        olympiad = participant.olympiad
        
        if olympiad.status != OlympiadStatus.active:
            raise BadRequestError("Olimpiada hali boshlanmagan yoki tugagan")
        
        if participant.status == ParticipationStatus.completed:
            raise BadRequestError("Siz allaqachon olimpiadani tugatgansiz")
        
        # Mark as started
        participant.status = ParticipationStatus.started
        participant.started_at = datetime.utcnow()
        self.db.commit()
        
        # Get questions (without correct answers)
        questions = [
            {
                "id": str(q.id),
                "order": q.order,
                "text": q.question_text,
                "image": q.question_image,
                "options": q.options,
                "points": q.points
            }
            for q in olympiad.questions
        ]
        
        return {
            "olympiad_title": olympiad.title,
            "duration_minutes": olympiad.duration_minutes,
            "questions": questions,
            "started_at": participant.started_at.isoformat()
        }
    
    def submit_answer(
        self,
        student_user_id: UUID,
        olympiad_id: UUID,
        question_id: UUID,
        selected_answer: int
    ) -> Dict:
        """
        Submit answer for a single question.
        """
        participant = self._get_participant(student_user_id, olympiad_id)
        
        if participant.status != ParticipationStatus.started:
            raise BadRequestError("Avval olimpiadani boshlang")
        
        # Check time limit
        time_spent = (datetime.utcnow() - participant.started_at).total_seconds()
        if time_spent > (participant.olympiad.duration_minutes * 60):
            raise BadRequestError("Vaqt tugadi")
        
        # Get question
        question = self.db.query(OlympiadQuestion).filter(
            OlympiadQuestion.id == question_id
        ).first()
        
        if not question or question.olympiad_id != olympiad_id:
            raise NotFoundError("Savol topilmadi")
        
        # Check if already answered
        existing = self.db.query(OlympiadAnswer).filter(
            and_(
                OlympiadAnswer.participant_id == participant.id,
                OlympiadAnswer.question_id == question_id
            )
        ).first()
        
        if existing:
            raise BadRequestError("Bu savolga allaqachon javob bergansiz")
        
        # Check answer
        is_correct = (selected_answer == question.correct_answer)
        points = question.points if is_correct else 0
        
        # Save answer
        answer = OlympiadAnswer(
            participant_id=participant.id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            points_earned=points,
            time_spent_seconds=int(time_spent)
        )
        
        self.db.add(answer)
        
        # Update participant stats
        participant.total_score += points
        if is_correct:
            participant.correct_answers += 1
        else:
            participant.wrong_answers += 1
        
        self.db.commit()
        
        return {
            "is_correct": is_correct,
            "points_earned": points,
            "total_score": participant.total_score
        }
    
    def finish_olympiad_for_student(
        self,
        student_user_id: UUID,
        olympiad_id: UUID
    ) -> Dict:
        """
        Student finishes the olympiad.
        """
        participant = self._get_participant(student_user_id, olympiad_id)
        
        if participant.status != ParticipationStatus.started:
            raise BadRequestError("Avval olimpiadani boshlang")
        
        participant.status = ParticipationStatus.completed
        participant.completed_at = datetime.utcnow()
        participant.time_spent_seconds = int(
            (participant.completed_at - participant.started_at).total_seconds()
        )
        
        self.db.commit()
        
        return {
            "message": "Olimpiada tugatildi",
            "total_score": participant.total_score,
            "correct_answers": participant.correct_answers,
            "wrong_answers": participant.wrong_answers,
            "time_spent_seconds": participant.time_spent_seconds
        }
    
    def get_olympiad_results(self, olympiad_id: UUID) -> List[Dict]:
        """
        Get public leaderboard for olympiad.
        """
        olympiad = self.db.query(Olympiad).filter(Olympiad.id == olympiad_id).first()
        if not olympiad:
            raise NotFoundError("Olimpiada topilmadi")
        
        if olympiad.status != OlympiadStatus.finished:
            raise BadRequestError("Olimpiada hali tugamagan")
        
        participants = self.db.query(OlympiadParticipant).filter(
            OlympiadParticipant.olympiad_id == olympiad_id
        ).order_by(OlympiadParticipant.rank).all()
        
        return [
            {
                "rank": p.rank,
                "student_name": p.student.user.first_name,
                "total_score": p.total_score,
                "correct_answers": p.correct_answers,
                "time_spent_seconds": p.time_spent_seconds,
                "coins_earned": p.coins_earned
            }
            for p in participants if p.status == ParticipationStatus.completed
        ]
    
    def get_student_olympiad_history(self, student_user_id: UUID) -> List[Dict]:
        """
        Get student's olympiad participation history.
        For parent dashboard.
        """
        student_profile = self.db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student_profile:
            return []
        
        participations = self.db.query(OlympiadParticipant).filter(
            OlympiadParticipant.student_id == student_profile.id
        ).all()
        
        return [
            {
                "olympiad_title": p.olympiad.title,
                "olympiad_subject": p.olympiad.subject.value,
                "status": p.status.value,
                "rank": p.rank,
                "total_score": p.total_score,
                "coins_earned": p.coins_earned,
                "date": p.olympiad.start_time.isoformat()
            }
            for p in participations
        ]
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _get_olympiad_for_moderator(self, olympiad_id: UUID, moderator_user_id: UUID) -> Olympiad:
        """Get olympiad and verify moderator access."""
        user = self.db.query(User).filter(User.id == moderator_user_id).first()
        if not user or user.role != UserRole.moderator:
            raise ForbiddenError("Faqat moderatorlar uchun")
        
        olympiad = self.db.query(Olympiad).filter(Olympiad.id == olympiad_id).first()
        if not olympiad:
            raise NotFoundError("Olimpiada topilmadi")
        
        return olympiad
    
    def _get_participant(self, student_user_id: UUID, olympiad_id: UUID) -> OlympiadParticipant:
        """Get participant by student user ID."""
        student_profile = self.db.query(StudentProfile).filter(
            StudentProfile.user_id == student_user_id
        ).first()
        
        if not student_profile:
            raise NotFoundError("O'quvchi profili topilmadi")
        
        participant = self.db.query(OlympiadParticipant).filter(
            and_(
                OlympiadParticipant.olympiad_id == olympiad_id,
                OlympiadParticipant.student_id == student_profile.id
            )
        ).first()
        
        if not participant:
            raise NotFoundError("Siz bu olimpiadaga ro'yxatdan o'tmagansiz")
        
        return participant
    
    def _check_student_subscription(self, student_profile: StudentProfile) -> bool:
        """
        Check if student has active subscription via parent.
        """
        if not student_profile.parent_user_id:
            return False
        
        # Get parent profile via parent_user_id (User.id -> ParentProfile.user_id)
        parent_profile = self.db.query(ParentProfile).filter(
            ParentProfile.user_id == student_profile.parent_user_id
        ).first()
        
        if not parent_profile:
            return False
        
        # Check subscription_plan field
        return parent_profile.subscription_plan in ['basic', 'premium', 'trial']
    
    def _calculate_rankings(self, olympiad_id: UUID):
        """
        Calculate final rankings and award coins.
        """
        participants = self.db.query(OlympiadParticipant).filter(
            and_(
                OlympiadParticipant.olympiad_id == olympiad_id,
                OlympiadParticipant.status == ParticipationStatus.completed
            )
        ).order_by(
            OlympiadParticipant.total_score.desc(),
            OlympiadParticipant.time_spent_seconds.asc()
        ).all()
        
        for rank, participant in enumerate(participants, 1):
            participant.rank = rank
            
            # Award coins based on rank
            if rank == 1:
                participant.coins_earned = 500
                self._add_coins(participant.student_id, 500, TransactionType.olympiad_first)
            elif rank == 2:
                participant.coins_earned = 300
                self._add_coins(participant.student_id, 300, TransactionType.olympiad_second)
            elif rank == 3:
                participant.coins_earned = 100
                self._add_coins(participant.student_id, 100, TransactionType.olympiad_third)
            else:
                # Participation bonus
                participant.coins_earned = 10
                self._add_coins(participant.student_id, 10, TransactionType.olympiad_participation)
        
        self.db.commit()
    
    def _add_coins(self, student_id: UUID, amount: int, transaction_type: TransactionType):
        """Add coins to student balance."""
        # Get or create coin balance
        coin_balance = self.db.query(StudentCoin).filter(
            StudentCoin.student_id == student_id
        ).first()
        
        if not coin_balance:
            coin_balance = StudentCoin(student_id=student_id)
            self.db.add(coin_balance)
            self.db.flush()
        
        coin_balance.add_coins(amount, transaction_type)
        
        # Record transaction
        transaction = CoinTransaction(
            student_coin_id=coin_balance.id,
            type=transaction_type,
            amount=amount,
            description=f"Olimpiada mukofoti"
        )
        self.db.add(transaction)
