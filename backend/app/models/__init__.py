"""
Alif24 Platform - Model Exports

All core models are consolidated in rbac_models.py.
Legacy files are kept as simple aliases for backward compatibility.
"""

# Re-export everything from rbac_models as primary source of truth
from app.models.rbac_models import (
    User,
    UserRole,
    ModeratorRoleType,
    AccountStatus,
    StudentProfile,
    ParentProfile,
    TeacherProfile,
    TeacherStatus,
    ChildRelationship,
    Classroom,
    ClassroomStudent,
    OrganizationProfile,
    ModeratorProfile,
    TeacherSubscription,
    SubscriptionTier,
    Payment,
    PaymentProvider,
    PaymentStatus,
    OrganizationSubscription,
    OrganizationMaterial,
    ClassroomSchedule
)

# Re-export other feature-specific models
from app.models.subject import Subject
from app.models.lesson import Lesson
from app.models.game import Game
from app.models.progress import Progress, ProgressStatus
from app.models.game_session import GameSession
from app.models.achievement import Achievement
from app.models.student_achievement import StudentAchievement
from app.models.notification import Notification, NotificationLog
from app.models.avatar import Avatar
from app.models.guest_session import GuestSession
from app.models.teacher_lesson import TeacherLesson, TeacherLessonStudent, TeacherLessonType
from app.models.teacher_test import TeacherTest, TestResult, TestType
from app.models.reading_analysis import ReadingAnalysis
from app.crm.models import Lead, Activity, LeadStatus, ActivityType

# NEW: Olympiad Models
from app.models.olympiad import (
    Olympiad,
    OlympiadQuestion,
    OlympiadParticipant,
    OlympiadAnswer,
    OlympiadStatus,
    OlympiadSubject,
    ParticipationStatus
)

# NEW: Phone Verification Models
from app.models.phone_verification import PhoneVerification, TelegramUser

# NEW: Coin Models
from app.models.coin import (
    StudentCoin,
    CoinTransaction,
    CoinWithdrawal,
    Prize,
    PrizeRedemption,
    TransactionType,
    WithdrawalStatus,
    PrizeCategory
)

# NEW: Live Quiz Models
from app.models.live_quiz import (
    LiveQuiz,
    LiveQuizQuestion,
    LiveQuizParticipant,
    LiveQuizAnswer,
    LiveQuizStatus,
    ParticipantState
)

# Language is in user.py (which redirects to rbac_models but adds Language enum)
from app.models.user import Language

# Backward compatibility aliases
Student = StudentProfile
Teacher = TeacherProfile
Parent = ParentProfile
Profile = User
TeacherClassroom = Classroom

__all__ = [
    "User",
    "UserRole",
    "AccountStatus",
    "StudentProfile",
    "ParentProfile",
    "TeacherProfile",
    "TeacherStatus",
    "ChildRelationship",
    "Classroom",
    "ClassroomStudent",
    "Language",
    
    # Logic Aliases
    "Student",
    "Teacher",
    "Parent",
    "Profile",
    "TeacherClassroom",
    
    # Feature models
    "Subject",
    "Lesson",
    "Game",
    "Progress",
    "ProgressStatus",
    "GameSession",
    "Achievement",
    "StudentAchievement",
    "Notification",
    "NotificationLog",
    "Avatar",
    "GuestSession",
    "TeacherLesson",
    "TeacherLessonStudent",
    "TeacherLessonType",
    "TeacherTest",
    "TestResult",
    "TestType",
    "ReadingAnalysis",
    "OrganizationProfile",
    "ModeratorProfile",
    "ModeratorRoleType",
    "SubscriptionTier",
    "PaymentProvider",
    "PaymentStatus",
    "TeacherSubscription",
    "Payment",
    "OrganizationSubscription",
    "OrganizationMaterial",
    "ClassroomSchedule",
    
    # CRM Models
    "Lead",
    "Activity",
    "LeadStatus",
    "ActivityType",
    
    # NEW: Olympiad Models
    "Olympiad",
    "OlympiadQuestion",
    "OlympiadParticipant",
    "OlympiadAnswer",
    "OlympiadStatus",
    "OlympiadSubject",
    "ParticipationStatus",
    
    # NEW: Coin Models
    "StudentCoin",
    "CoinTransaction",
    "CoinWithdrawal",
    "Prize",
    "PrizeRedemption",
    "TransactionType",
    "WithdrawalStatus",
    "PrizeCategory",
    
    # NEW: Live Quiz Models
    "LiveQuiz",
    "LiveQuizQuestion",
    "LiveQuizParticipant",
    "LiveQuizAnswer",
    "LiveQuizStatus",
    "ParticipantState",
    
    # NEW: Phone Verification Models
    "PhoneVerification",
    "TelegramUser",
    
    # NEW: Daily Quiz Models
    "QuizQuestion",
    "QuizAttempt"
]

# NEW: Daily Quiz Models
from app.models.quiz import QuizQuestion, QuizAttempt

