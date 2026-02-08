from fastapi import APIRouter
from app.api.v1 import auth, users, students, lessons, games, profiles, avatars, teacher_tests, rbac_endpoints
from app.api.v1 import verification

from app.api.v1.endpoints import testai, notification, organization_structure, schedule, olympiad, coins, live_quiz

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(students.router, prefix="/students", tags=["students"])
router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
router.include_router(games.router, prefix="/games", tags=["games"])
router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
router.include_router(avatars.router, prefix="/avatars", tags=["avatars"])
router.include_router(teacher_tests.router, prefix="/teacher-tests", tags=["teacher-tests"])
router.include_router(testai.router, prefix="/testai", tags=["testai"])
router.include_router(notification.router, prefix="/notifications", tags=["notifications"])

# Phone Verification via Telegram
router.include_router(verification.router)

# RBAC Routers
router.include_router(rbac_endpoints.parent_router)
router.include_router(rbac_endpoints.teacher_router)
router.include_router(rbac_endpoints.organization_router)

# SmartKids Routers
from app.smartkids import story_router, file_reader_router
router.include_router(story_router.router, prefix="/smartkids", tags=["smartkids"])
router.include_router(file_reader_router.router, prefix="/smartkids", tags=["smartkids"])

# Organization Routers
router.include_router(organization_structure.router, prefix="/organization-structure", tags=["organization-structure"])
router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])

# NEW: Olympiad, Coins, Live Quiz Routers
router.include_router(olympiad.router)
router.include_router(coins.router)
router.include_router(live_quiz.router)

# SECRET: Admin Panel (yashirin admin panel)
# SECRET: Admin Panel (yashirin admin panel)
from app.api.v1 import admin_panel
router.include_router(admin_panel.router)

# DEBUG: Database Info
from app.api.v1.endpoints import debug
router.include_router(debug.router, prefix="/debug", tags=["debug"])
