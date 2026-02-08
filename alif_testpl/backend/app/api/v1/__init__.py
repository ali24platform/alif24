from fastapi import APIRouter
from app.api.v1 import auth, users, students, lessons, games, profiles, avatars, teacher_tests, rbac_endpoints

from app.api.v1.endpoints import testai

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

# RBAC Routers
router.include_router(rbac_endpoints.parent_router)
router.include_router(rbac_endpoints.teacher_router)
router.include_router(rbac_endpoints.organization_router)

# SmartKids Routers
from app.smartkids import story_router, file_reader_router, image_reader_router, speech_token_router
router.include_router(story_router.router, prefix="/smartkids", tags=["smartkids"])
router.include_router(story_router.router, prefix="/story", tags=["story"])
router.include_router(file_reader_router.router, prefix="/smartkids", tags=["smartkids"])
router.include_router(image_reader_router.router, prefix="/smartkids", tags=["smartkids"])
router.include_router(speech_token_router.router, prefix="/smartkids", tags=["smartkids"])

# MathKids Routers
from app.mathkids import math_image_router, math_solver_router
router.include_router(math_image_router.router, prefix="/mathkids", tags=["mathkids"])
router.include_router(math_solver_router.router, prefix="/mathkids", tags=["mathkids"])

# Harf Routers
from app.harf.router import router as harf_router
router.include_router(harf_router, prefix="/harf", tags=["harf"])

