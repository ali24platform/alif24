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

# SmartKids - Image Reader and Speech Token
from app.smartkids import image_reader_router, speech_token_router
router.include_router(image_reader_router.router, prefix="/smartkids", tags=["smartkids"])
router.include_router(speech_token_router.router, prefix="/smartkids", tags=["smartkids"])

# MathKids Routers
from app.mathkids import math_image_router, math_solver_router
router.include_router(math_image_router.router, prefix="/mathkids", tags=["mathkids"])
router.include_router(math_solver_router.router, prefix="/mathkids", tags=["mathkids"])

# Harf (Uzbek Letters) Router
from app.harf import router as harf_router
router.include_router(harf_router.router, prefix="/harf", tags=["harf"])

# RHarf (Russian Letters) Router
from app.rharf import router as rharf_router
router.include_router(rharf_router.router, prefix="/rharf", tags=["rharf"])

# Unified Speech Router (Multi-language TTS/STT)
from app.unified import router as unified_router
router.include_router(unified_router.router, prefix="/unified", tags=["unified"])

# Guest Session Router
from app.api.guest import router as guest_router
router.include_router(guest_router)

# Organization Dashboard Router
from app.organization import router as org_dashboard_router
router.include_router(org_dashboard_router.router, prefix="/org-dashboard", tags=["organization"])

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
