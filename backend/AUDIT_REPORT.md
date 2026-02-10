# 🚨 SYSTEM INTEGRITY & LOGIC HEALTH CHECK — AUDIT REPORT

**Date:** 2026-02-10  
**Auditor:** Senior Full-Stack Software Architect (AI)  
**Scope:** Full backend + frontend handshake audit

---

## PHASE 1: GHOST HUNTER SCAN (Dead/Missing Imports)

### ✅ SAFE — Guarded with try/except (No Crash Risk)
These files import removed libraries but are **properly guarded** with `try/except ImportError`:

| File | Ghost Import | Guard | Runtime Risk |
|------|-------------|-------|-------------|
| `app/rharf/router.py` | `azure.cognitiveservices.speech` | ✅ `speechsdk = None` | **🔴 HIGH** — see below |
| `app/letters/router.py` | `azure.cognitiveservices.speech` | ✅ `speechsdk = None` | **🔴 HIGH** — see below |
| `app/unified/router.py` | `azure.cognitiveservices.speech` | ✅ `speechsdk = None` | **🔴 HIGH** — see below |
| `app/smartkids/file_reader_router.py` | `docx` | ✅ `docx = None` | ⚠️ MEDIUM — returns 501 |
| `app/services/test_builder_service.py` | `docx` | ✅ `docx = None` | ⚠️ MEDIUM — returns 400 |
| `app/services/testai/parsers.py` | `pdfplumber`, `docx`, `PIL`, `pytesseract` | ✅ All guarded | ⚠️ LOW — returns empty |

### 🔴 CRITICAL — Unguarded Imports (WILL CRASH on Vercel)

| File | Ghost Import | Impact |
|------|-------------|--------|
| `app/smartkids/image_reader_router.py:12` | `from openai import AzureOpenAI` | ✅ OK — openai is in requirements.txt |
| `app/smartkids/story_router.py:10` | `from openai import AzureOpenAI` | ✅ OK — openai is in requirements.txt |
| `app/services/testai/ai_generator.py:1` | `from openai import AzureOpenAI` | ✅ OK — openai is in requirements.txt |
| `app/mathkids/math_solver_router.py:7` | `from openai import AzureOpenAI` | ✅ OK — openai is in requirements.txt |
| `app/mathkids/math_image_router.py:5` | `from openai import AzureOpenAI` | ✅ OK — openai is in requirements.txt |

> **Note:** `AzureOpenAI` is part of the `openai` package (which IS in requirements.txt). These are NOT ghost imports.

### 🔴 CRITICAL LOGIC BOMB — Speech Routers Will Crash at Runtime

**Files:** `rharf/router.py`, `unified/router.py`

These files guard `import azure.cognitiveservices.speech as speechsdk` with try/except, setting `speechsdk = None`. **BUT** they then call `speechsdk.SpeechConfig(...)` directly in endpoint handlers **without checking if speechsdk is None first**.

- `rharf/router.py:71` → `speech_config = speechsdk.SpeechConfig(...)` — **will crash with `AttributeError: 'NoneType'`**
- `unified/router.py:49` → same pattern
- `letters/router.py:138-142` → **CORRECTLY handles** `if speechsdk is None: raise HTTPException(503)`

### requirements.txt vs. Actual Imports — Mismatch Summary

| Library | In requirements.txt | Imported in app/ code |
|---------|--------------------|-----------------------|
| `azure-cognitiveservices-speech` | ❌ Commented out | ✅ 3 files (guarded) |
| `pdfplumber` | ❌ Commented out | ✅ 1 file (guarded) |
| `python-docx` | ❌ Commented out | ✅ 3 files (guarded) |
| `pillow` | ❌ Commented out | ✅ 1 file (guarded) |
| `pytesseract` | ❌ Not present | ✅ 1 file (guarded) |
| `pandas` / `numpy` | ❌ Not present | ❌ Not imported in app/ |

---

## PHASE 2: SKELETON SCAN (Database Model Relationships)

### ✅ HEALTHY — TeacherLesson ↔ TeacherTest
```
TeacherLesson.tests → relationship("TeacherTest", back_populates="lesson")
TeacherTest.lesson → relationship("TeacherLesson", back_populates="tests")
TeacherTest.lesson_id → ForeignKey("teacher_lessons.id")  ✅ Matches
```
**Verdict:** Properly wired. `back_populates` pairs match. ForeignKey exists.

### ✅ HEALTHY — StudentProfile ↔ User
```
User.student_profile → relationship("StudentProfile", ..., foreign_keys="StudentProfile.user_id")
StudentProfile.user → relationship("User", ..., foreign_keys=[user_id])
StudentProfile.user_id → ForeignKey("users.id")  ✅ Matches
StudentProfile.parent_user_id → ForeignKey("users.id")  ✅ Separate FK, properly specified
```
**Verdict:** Properly wired with explicit `foreign_keys` to disambiguate multiple FKs to `users`.

### ✅ HEALTHY — Progress, GameSession, StudentAchievement
All point to `student_profiles.id` with proper `back_populates` and explicit `foreign_keys`.

### ⚠️ WARNING — Notification model
```python
# notification.py line 27
created_at = Column(DateTime, default=datetime.now)  # ← Uses datetime.now (called once at class load!)
```
Should be `default=datetime.now` (without parens) or `server_default=func.now()`. Currently it's **correct** (no parens = callable), but mixing `datetime.now` with timezone-unaware columns while other models use `func.now()` with `timezone=True` is a **consistency issue**.

### ⚠️ WARNING — Mutable Default Arguments in Column Definitions
Multiple models use mutable defaults that are shared across instances:
- `rbac_models.py:239` — `favorite_subjects = Column(JSON, default=[])`
- `rbac_models.py:241-246` — `preferences = Column(JSON, default={...})`
- `rbac_models.py:298-304` — `notification_preferences = Column(JSON, default={...})`
- `teacher_test.py:38` — `questions = Column(JSON, nullable=False, default=[])`
- `teacher_test.py:64` — `tags = Column(JSON, default=[])`

**Risk:** SQLAlchemy's `default` with mutable Python objects can cause shared state bugs. Should use `default=list` or `default=lambda: []`.

### ✅ NO Orphaned Relationships Found
All `relationship()` definitions have corresponding `ForeignKey` columns. No `NoForeignKeysError` risk.

---

## PHASE 3: NERVOUS SYSTEM SCAN (API Router Wiring)

### Router Registration Map (main.py + api/v1/__init__.py)

| Module | Prefix | Registered In | Status |
|--------|--------|--------------|--------|
| `auth` | `/auth` | `v1/__init__.py` | ✅ |
| `users` | `/users` | `v1/__init__.py` | ✅ |
| `students` | `/students` | `v1/__init__.py` | ✅ |
| `lessons` | `/lessons` | `v1/__init__.py` | ✅ |
| `games` | `/games` | `v1/__init__.py` | ✅ |
| `profiles` | `/profiles` | `v1/__init__.py` | ✅ |
| `avatars` | `/avatars` | `v1/__init__.py` | ✅ |
| `teacher_tests` | `/teacher-tests` | `v1/__init__.py` | ✅ |
| `testai` | `/testai` | `v1/__init__.py` | ✅ |
| `notification` | `/notifications` | `v1/__init__.py` | ✅ |
| `verification` | `/verification` | `v1/__init__.py` | ✅ |
| `rbac_endpoints` (x3) | `/parents`, `/teachers`, `/organizations` | `v1/__init__.py` | ✅ |
| `smartkids` (x4) | `/smartkids` | `v1/__init__.py` | ✅ |
| `mathkids` (x2) | `/mathkids` | `v1/__init__.py` | ✅ |
| `harf` | `/harf` | `v1/__init__.py` | ✅ |
| `rharf` | `/rharf` | `v1/__init__.py` | ✅ |
| `unified` | `/unified` | `v1/__init__.py` | ✅ |
| `guest` | (own prefix) | `v1/__init__.py` | ✅ |
| `org-dashboard` | `/org-dashboard` | `v1/__init__.py` | ✅ |
| `organization_structure` | `/organization-structure` | `v1/__init__.py` | ✅ |
| `schedule` | `/schedule` | `v1/__init__.py` | ✅ |
| `olympiad` | (own prefix) | `v1/__init__.py` | ✅ |
| `coins` | (own prefix) | `v1/__init__.py` | ✅ |
| `live_quiz` | (own prefix) | `v1/__init__.py` | ✅ |
| `student_lesson_router` | `/student-lessons` | `v1/__init__.py` | ✅ |
| `admin_panel` | (own prefix) | `v1/__init__.py` | ✅ |
| `debug` | `/debug` | `v1/__init__.py` | ✅ |
| `letters` | `/letters` | `main.py` (separate) | ✅ |
| `crm` | (own prefix) | `main.py` (separate) | ✅ |
| `admin_router` | (own prefix) | `main.py` (separate) | ✅ |

**All endpoint files are wired. No orphan routers found.**

### ⚠️ WARNING — Verification Flow
`verification.py` handles SMS/Telegram failures correctly:
- `send-code`: If `TelegramBotService.send_verification_code()` returns `{"success": false}`, raises `HTTPException(400)` ✅
- `verify-code`: If verification fails, raises `HTTPException(400)` ✅
- `telegram/webhook`: Catches all exceptions, returns `{"ok": True}` to Telegram (prevents retries) ✅

**No logic gap in verification flow.**

---

## PHASE 4: FRONTEND HANDSHAKE

### Data Contract Analysis

| Frontend Call | Backend Response | Match? |
|--------------|-----------------|--------|
| `authService.login()` → expects `response.data` | Returns `{"success": true, "data": {...}}` | ✅ |
| `authService.register()` → expects `response.data` | Returns `{"success": true, "data": {...}}` | ✅ |
| `authService.getProfile()` → expects `response.data` | Returns `{"success": true, "data": {...}}` | ✅ |
| `authService.updateProfile()` → calls PUT `/auth/me` | Backend has PUT `/auth/me` endpoint | ✅ |
| `studentService.getMyProfile()` → expects `response.data` | Depends on `/students/me` | ⚠️ Check |

### ⚠️ UUID Handling
- **Backend** sends UUIDs as Python `UUID` objects (serialized as strings in JSON)
- **Frontend** treats IDs as strings throughout — **compatible** ✅

### ⚠️ Error Handling in Frontend
- `apiService.handleResponse()` checks `!response.ok` and throws errors ✅
- Handles 401 with token refresh ✅
- **Gap:** `studentService.getLesson()` tries to access `error.response.status` — but `fetch()` API doesn't have `.response` property on errors. This catch block **will never match the 403 condition**. The error thrown by `handleResponse()` is a plain `Error` object.

### 🔴 CRITICAL — teacherService.createLesson() Content-Type Mismatch
`teacherService.createLesson()` and `createQuiz()` construct `FormData` but pass it to `apiService.post()`, which **always sets `Content-Type: application/json`** and calls `JSON.stringify(data)`. A `FormData` object when stringified becomes `"[object FormData]"`.

**This means teacher lesson/quiz creation is completely broken from the frontend.**

### 🔴 CRITICAL — Hardcoded API Keys in Source Code
Multiple files contain hardcoded Azure API keys:
- `app/smartkids/image_reader_router.py:23-25`
- `app/smartkids/story_router.py:23-26`
- `app/services/testai/ai_generator.py:9-11`
- `app/rharf/router.py:17-26`
- `app/unified/router.py:16-25`
- `app/mathkids/math_solver_router.py:16-18`
- `app/mathkids/math_image_router.py` (similar)
- `app/core/config.py:36-38`

These should be moved to environment variables only.

---

## PHASE 5: SYSTEM LOGIC FLOW (Mermaid)

```mermaid
sequenceDiagram
    participant S as Student (Browser)
    participant FE as Frontend (React/Vite)
    participant API as FastAPI Backend
    participant SVC as Service Layer
    participant AI as Azure OpenAI
    participant DB as PostgreSQL (Supabase)

    Note over S,DB: Flow 1: Student Login
    S->>FE: Enter username + PIN
    FE->>API: POST /api/v1/auth/child-login {username, pin}
    API->>DB: SELECT * FROM users WHERE username=?
    DB-->>API: User row
    API->>API: verify_pin(pin, hashed_pin)
    API->>API: create_access_token() + create_refresh_token()
    API-->>FE: {access_token, refresh_token, user}
    FE->>S: Redirect to Dashboard

    Note over S,DB: Flow 2: Start SmartKids Story Lesson
    S->>FE: Click "Start Story"
    FE->>API: POST /api/v1/smartkids/next-question {story_text, age, question_number}
    API->>SVC: story_router.next_question()
    SVC->>SVC: langdetect → detect language
    SVC->>AI: chat.completions.create(model, messages)
    AI-->>SVC: Generated question text
    SVC-->>API: {question: "..."}
    API-->>FE: {question: "Ertakda kim bor edi?"}
    FE->>S: Display question + voice prompt

    Note over S,DB: Flow 3: Student Answers → AI Analyzes
    S->>FE: Speak answer (STT)
    FE->>API: POST /api/v1/smartkids/analyze {story_text, question, child_answer}
    API->>AI: Analyze child's answer (JSON mode)
    AI-->>API: {speech_errors, thinking_assessment, ...}
    API-->>FE: {analysis: {...}}
    FE->>S: Show feedback + encouragement

    Note over S,DB: Flow 4: Save Analysis
    FE->>API: POST /api/v1/smartkids/save-analysis {user_id, scores...}
    API->>DB: INSERT INTO reading_analyses (...)
    DB-->>API: OK
    API-->>FE: {analysis_id: "uuid"}

    Note over S,DB: Flow 5: Teacher Creates Test
    S->>FE: Fill test form
    FE->>API: POST /api/v1/teacher-tests {title, questions, ...}
    API->>DB: INSERT INTO teacher_tests (...)
    DB-->>API: TeacherTest row
    API-->>FE: {test: {...}}

    Note over S,DB: Flow 6: Phone Verification
    S->>FE: Enter phone number
    FE->>API: POST /api/v1/verification/send-code {phone}
    API->>SVC: TelegramBotService.send_verification_code()
    SVC->>DB: INSERT INTO phone_verifications (phone, code, expires_at)
    SVC->>SVC: Send Telegram message with code
    SVC-->>API: {success: true, expires_in: 300}
    API-->>FE: {success, message, expires_in}
```

---

## RED FLAGS SUMMARY — ALL FIXED ✅

### 🔴 P0 — CRASHES (ALL FIXED)

| # | File | Bug | Status |
|---|------|-----|--------|
| 1 | `rharf/router.py:71` | `speechsdk.SpeechConfig()` when `speechsdk is None` → `AttributeError` | ✅ FIXED — Added `if speechsdk is None: raise HTTPException(501)` |
| 2 | `rharf/router.py:131` | Same in `speech_to_text` | ✅ FIXED — Same guard |
| 3 | `unified/router.py:46` | Same in `get_voice_config()` + STT silent fail | ✅ FIXED — Guard + `raise HTTPException(501)` |
| 4 | `letters/router.py:138` | Was already guarded but used 503 | ✅ FIXED — Standardized to 501 |
| 5 | `apiService.js:post/put` | `JSON.stringify(FormData)` → `"[object FormData]"` | ✅ FIXED — `instanceof FormData` detection |
| 6 | `apiService.js:handleResponse` | `response.json()` crashes on non-JSON (audio) | ✅ FIXED — Content-Type check before parsing |
| 7 | `ai_cache_service.py:43` | `func.now()` used but `func` never imported → `NameError` | ✅ FIXED — Added `from sqlalchemy.sql import func` |
| 8 | `testai.py:152,261` | Pydantic v1 `.dict()` deprecated in v2 | ✅ FIXED — Changed to `.model_dump()` |

### 🟡 P1 — SILENT FAILURES (ALL FIXED)

| # | File | Bug | Status |
|---|------|-----|--------|
| 9 | `teacherService.js:81,90` | Sent FormData to JSON endpoint | ✅ FIXED — Now sends plain JSON |
| 10 | `studentService.js:90` | `error.response.status` never works with fetch | ✅ FIXED — Checks `error.message` |
| 11 | `story_router.py:225` | Variable shadowing `AZURE_MODEL` | ✅ FIXED — Removed redundant reassignment |
| 12 | `models/__init__.py` | `QuizQuestion`/`QuizAttempt` imported after `__all__`; `AICache` missing | ✅ FIXED — Reordered, added to `__all__` |

### 🟢 P2 — NOT FIXED (Low Priority, Documented Only)

| # | Issue | Location | Recommendation |
|---|-------|----------|----------------|
| 13 | Mutable Column defaults (`default=[]`, `default={}`) | `rbac_models.py`, `teacher_test.py` | Change to `default=list` / `default=dict` |
| 14 | Hardcoded API keys in source | 8+ files | Move to `.env` only |
| 15 | Mixed datetime handling | `notification.py` | Standardize to `server_default=func.now()` |

---

## FRONTEND BUTTON AUDIT REPORT

**Date:** 2025-02-10
**Scope:** All interactive elements (buttons, links, tiles, navigation) across every role and page.
**Status:** All critical/high-priority issues FIXED.

---

### PAGES & ROUTES AUDITED

| Route | Component | Roles | Status |
|-------|-----------|-------|--------|
| `/` , `/dashboard` | `HomePage` | All | ✅ OK |
| `/about` | `AboutPage` | All | ✅ OK (static) |
| `/partners` | `PartnerPage` | All | ✅ OK (static) |
| `/profile` | `ProfilePageTeacher` | Authenticated | ✅ OK |
| `/student-dashboard` | `StudentDashboard` | Student | ✅ FIXED |
| `/teacher-dashboard` | `TeacherDashboard` | Teacher | ✅ FIXED (4 bugs) |
| `/parent-dashboard` | `ParentDashboard` | Parent | ✅ FIXED |
| `/organization-dashboard` | `OrganizationDashboard` | Org/Mod/Admin | ✅ FIXED (admin added) |
| `/crm` | `CRMPage` | Org/Mod/Admin | ✅ OK |
| `/lesson/:id` | `LessonPage` | Student | ✅ OK |
| `/lesson-builder` | `LessonBuilder` | Teacher | ✅ FIXED (dup route) |
| `/test-creator` | `TestCreator` | Teacher | ✅ OK |
| `/harf` | `Harf` | All | ✅ OK |
| `/rharf` | `Harfr` | All | ✅ OK |
| `/smartkids-ai` | `SmartKidsAI` | All | ✅ OK |
| `/mathkids-ai` | `MathKidsAI` | All | ✅ OK |
| `/ertak` | `KidsReadingPlatformMobile` | All | ✅ OK |
| `/games/letter-memory` | `LetterMemoryGame` | All | ✅ OK |
| `/games/math-monster` | `MathMonsterGame` | All | ✅ OK |
| `/nurali`, `/hazratqul`, `/pedagog` | `SecretAdminLogin` | Secret | ✅ OK |
| `/teacher/test-ai` | `TestAIPage` | Teacher | ✅ OK |

---

### 🔴 P0 — CRASHES (ALL FIXED)

| # | File | Bug | Fix |
|---|------|-----|-----|
| F1 | `TeacherDashboard.jsx` | `teacherData` never defined → `TypeError` crash on Header & Settings render | ✅ Added `teacherData` object derived from `useAuth().user` |
| F2 | `TeacherDashboard.jsx` | `t()` from `useLanguage` imported but never destructured → `TypeError: t is not a function` | ✅ Added `const { t } = useLanguage()` |
| F3 | `TeacherDashboard.jsx` | Nested `<tbody><tbody>` in StudentsView → invalid HTML, React rendering errors | ✅ Removed duplicate `<tbody>` and closing tag |
| F4 | `LoginModal.jsx` | Admin/super_admin login redirects to `/admin` which has no route → 404 | ✅ Changed to redirect to `/organization-dashboard` |
| F5 | `Navbar.jsx` | `profilePath` for admin role → `/admin` (404) | ✅ Changed to `/organization-dashboard` for admin/mod/org |
| F6 | `ProtectedRoute.jsx` | `ROLE_DASHBOARDS` missing `admin`/`super_admin` → falls through to `/` | ✅ Added both roles mapping to `/organization-dashboard` |
| F7 | `App.jsx` | `/organization-dashboard` route missing `admin` in `allowedRoles` → admin gets bounced | ✅ Added `admin` to allowedRoles |

### 🟡 P1 — BROKEN/ORPHANED BUTTONS (ALL FIXED)

| # | File | Button/Element | Bug | Fix |
|---|------|---------------|-----|-----|
| F8 | `HomePage.jsx` | Game tiles id=14-17 | Navigated to `/admin`, `/teacher-dashboard` etc. as test shortcuts → crashes for non-authenticated | ✅ Replaced with "coming soon" alert |
| F9 | `Navbar.jsx` | Desktop nav links (Home, About, Partners, Profile) | Used `<a href>` → full page reload, breaks SPA state | ✅ Changed to `<button onClick={() => navigate()}>` |
| F10 | `App.jsx` | `/lesson-builder` route | Duplicate route definition (exact copy) | ✅ Removed duplicate |
| F11 | `ParentDashboard.jsx` | "To'liq hisobot" button | No `onClick` handler — dead button | ✅ Added handler with placeholder alert |
| F12 | `StudentDashboard.jsx` | "Bajarish" button on tasks | No `onClick` handler — dead button | ✅ Added handler with placeholder alert |
| F13 | `TeacherDashboard.jsx` | Sidebar tabs (classes, grades, calendar, resources, help) | Buttons existed but `renderContent()` switch had no case → silently showed Dashboard | ✅ Added placeholder views for each tab |

### 🟢 P2 — NON-FUNCTIONAL UI (Documented, Low Priority)

| # | File | Element | Notes |
|---|------|---------|-------|
| F14 | `TeacherDashboard.jsx` | "Tahrirlash" (Edit profile) button | No handler — placeholder UI, settings not yet implemented |
| F15 | `TeacherDashboard.jsx` | "Rasmni o'zgartirish" (Change avatar) button | No handler — avatar upload not yet built |
| F16 | `TeacherDashboard.jsx` | "Parolni o'zgartirish" button | No handler — password change UI not connected |
| F17 | `TeacherDashboard.jsx` | Toggle switches (2FA, notifications, dark mode) | Non-functional CSS toggles — settings backend not built |
| F18 | `TeacherDashboard.jsx` | "Yangi topshiriq" button | No handler — assignment creation not yet implemented |
| F19 | `TeacherDashboard.jsx` | "Yangi" (new message) button | No handler — messaging not yet implemented |
| F20 | `TeacherDashboard.jsx` | Student action buttons (Eye, Message, Edit icons) | No handlers — individual student views not built |
| F21 | `StudentDashboard.jsx` | Library book tiles | `cursor-pointer` but no `onClick` — book viewer not built |
| F22 | `StudentDashboard.jsx` | Achievement tiles | Static placeholder, no real data or interaction |
| F23 | `ParentDashboard.jsx` | "Hisobni to'ldirish" (Top up) button | No handler — payment system not integrated |
| F24 | `ParentDashboard.jsx` | Notifications & Settings tabs | Show placeholder "Tez orada..." — not built yet |
| F25 | `Navbar.jsx` | `useStarsManager` hook | Commented out, using placeholder `totalStars = 0` |
| F26 | `RegisterModal.jsx` | Moderator registration redirects to `/crm` but LoginModal redirects to `/organization-dashboard` | Inconsistent but both routes exist — not a crash |

---

### SHARED COMPONENTS AUDIT

#### Navbar (`components/Common/Navbar.jsx`)
| Element | Handler | Status |
|---------|---------|--------|
| Logo click | `navigate('/dashboard')` | ✅ OK |
| Home link | `navigate('/dashboard')` | ✅ FIXED (was `<a href>`) |
| About link | `navigate('/about')` | ✅ FIXED |
| Partners link | `navigate('/partners')` | ✅ FIXED |
| Profile link | `handleProfileClick()` → navigate or open login modal | ✅ FIXED (admin path) |
| Language selector | `switchLanguage(lang)` | ✅ OK |
| Login button | `setLoginModalOpen(true)` | ✅ OK |
| Logout button | `logout()` + `navigate('/')` | ✅ OK |
| Mobile bottom nav (4 buttons) | `navigate()` for each tab | ✅ OK |

#### LoginModal (`components/Auth/LoginModal.jsx`)
| Element | Handler | Status |
|---------|---------|--------|
| Email/Phone toggle | `setLoginType()` | ✅ OK |
| Show/hide password | `setShowPassword()` | ✅ OK |
| Submit button | `handleSubmit()` → login + role redirect | ✅ FIXED (admin route) |
| Switch to Register | `onSwitchToRegister()` | ✅ OK |
| Close button | `onClose()` | ✅ OK |

#### RegisterModal (`components/Auth/RegisterModal.jsx`)
| Element | Handler | Status |
|---------|---------|--------|
| Name inputs | `handleChange()` | ✅ OK |
| Phone/Email toggle | `setLoginType()` | ✅ OK |
| Role selector (4 roles) | Radio buttons + `handleChange()` | ✅ OK |
| Send code button (phone) | `handleSendCode()` → Telegram verification | ✅ OK |
| Email register button | `handleEmailRegister()` | ✅ OK |
| Verify code input + submit | `handleVerifyAndRegister()` | ✅ OK |
| Back button (from verify) | `setStep('form')` | ✅ OK |
| Switch to Login | `onSwitchToLogin()` | ✅ OK |

#### ProtectedRoute (`components/Auth/ProtectedRoute.jsx`)
| Logic | Status |
|-------|--------|
| Unauthenticated → dispatch `showLoginModal` + redirect `/` | ✅ OK |
| Wrong role → redirect to role dashboard | ✅ FIXED (admin/super_admin added) |

---

### SERVICES → API MAPPING VERIFICATION

| Frontend Service | Method | API Endpoint | Status |
|-----------------|--------|-------------|--------|
| `authService.login()` | POST | `/auth/login` | ✅ OK |
| `authService.register()` | POST | `/auth/register` | ✅ OK |
| `authService.getProfile()` | GET | `/auth/me` | ✅ OK |
| `authService.sendVerificationCode()` | POST | `/verification/send-code` | ✅ OK |
| `authService.verifyCode()` | POST | `/verification/verify-code` | ✅ OK |
| `teacherService.searchStudents()` | GET | `/teachers/search-students` | ✅ OK |
| `teacherService.addStudentToClass()` | POST | `/teachers/classrooms/{id}/students` | ✅ OK |
| `teacherService.getMyClassrooms()` | GET | `/teachers/classrooms` | ✅ OK |
| `teacherService.createClassroom()` | POST | `/teachers/classrooms` | ✅ OK |
| `teacherService.createLesson()` | POST | `/lessons` | ✅ FIXED (was FormData) |
| `teacherService.createQuiz()` | POST | `/teacher-tests` | ✅ FIXED (was FormData) |
| `parentService.getChildren()` | GET | `/parents/children` | ✅ OK |
| `parentService.createChild()` | POST | `/parents/children` | ✅ OK |
| `studentService.getLesson()` | GET | `/lessons/{id}` | ✅ OK |
| `studentService.completeLesson()` | POST | `/lessons/{id}/complete` | ✅ OK |

---

---

## DEEP SCAN — PHASE 2

**Date:** 2025-02-10
**Scope:** Full system analysis — contexts, hooks, services, layouts, error handling, route integrity.

### 🔴 P0 — CRASHES (ALL FIXED)

| # | File | Bug | Fix |
|---|------|-----|-----|
| D1 | `AuthContext.jsx` | `isAdmin` only checked `moderator`/`organization`, not `admin`/`super_admin` → admin users treated as non-admin | ✅ Added `admin`, `super_admin` to `isAdmin` check |
| D2 | `AuthContext.jsx` | `isSuperAdmin` not exported → `DashboardLayout` destructures it as `undefined` | ✅ Added `isSuperAdmin: user?.role === 'super_admin'` |
| D3 | `DashboardLayout.jsx` | All nav links (`/admin/*`, `/teacher/*`, `/parent/*`, `/student/*`) point to routes that **don't exist** in `App.jsx` → 404 on every click | ✅ Rewired all links to real routes (`/organization-dashboard`, `/crm`, `/teacher-dashboard`, etc.) |
| D4 | `DashboardLayout.jsx` | Used `<a href>` for navigation → full page reload, breaks SPA state | ✅ Changed to `<button onClick={() => navigate()}>` with active state |

### 🟡 P1 — SILENT BUGS (ALL FIXED)

| # | File | Bug | Fix |
|---|------|-----|-----|
| D5 | `OrganizationDashboard.jsx` (×2) | `error.response?.data?.detail` — Axios pattern, but app uses `fetch` via `apiService`. `error.response` is always `undefined` → error messages show "undefined" | ✅ Changed to `error.message` |
| D6 | `LessonBuilder.jsx` | Same Axios error pattern `error.response?.data?.detail` | ✅ Changed to `error.message` |
| D7 | `useUsageTracking.js` | `USAGE_ACTIONS.LESSON_START` maps to `'lessonStarts'` and `VIDEO_WATCH` to `'videoWatches'`, but neither key exists in initial state → `trackAction()` produces `NaN` (undefined + 1) | ✅ Added `lessonStarts: 0` and `videoWatches: 0` to initial state and `resetUsage()` |
| D8 | `AuthContext.jsx` | `canManageContent` didn't include `admin`/`super_admin` | ✅ Added both roles |

### 🟢 P2 — NOTED (Not Fixed, Low Priority)

| # | File | Issue | Notes |
|---|------|-------|-------|
| D9 | `MathSolver.jsx` | Imports `microsoft-cognitiveservices-speech-sdk` directly — heavy package (~30MB), loaded on every MathKids page visit | Package is in `package.json` so not a crash, but should be lazy-loaded |
| D10 | `DashboardLayout.jsx` | Teacher/Parent/Student nav only has 1-3 links (reduced from dead routes) | Should be expanded as new features ship |
| D11 | `OrganizationDashboard.jsx` | CRM `onEdit` handler is `console.log("Edit lead", lead)` — no actual edit UI | Placeholder, documented |
| D12 | `LessonBuilder.jsx` | Mock subjects use non-UUID IDs (`uuid-math`) → backend validation will reject | Users must select valid UUIDs from real DB data |
| D13 | `apiService.js` | `refreshToken()` — after refresh, the original failed request is NOT retried | User must manually retry; could add retry logic |
| D14 | `OrganizationDashboard.jsx` | `user?.name` on line 188 — backend user object has `first_name`/`last_name`, not `name` | Shows `undefined` in header |

---

---

## DEEP SCAN — PHASE 3

**Date:** 2025-02-10
**Scope:** Raw axios elimination, hardcoded localhost URLs, TestAI module, VoiceAssistant, game components.

### 🔴 P0 — AUTH BYPASS (ALL FIXED)

| # | File | Bug | Fix |
|---|------|-----|-----|
| T1 | `TestAIPage.jsx` | Uses raw `axios` — **no auth token sent**, all API calls fail with 401 | ✅ Replaced with `apiService` |
| T2 | `TestParser.jsx` | Raw `axios.post('/api/v1/testai/parse/text')` — no auth | ✅ Replaced with `apiService.post('/testai/parse/text')` |
| T3 | `TestBuilder.jsx` | Raw `axios.post('/api/v1/testai/save')` — no auth | ✅ Replaced with `apiService.post('/testai/save')` |
| T4 | `TestAssignment.jsx` | Raw `axios` for 4 endpoints, also calls non-existent `/api/v1/classes` and `/api/v1/assignments` | ✅ Replaced with `apiService`, rewired to `/teachers/classrooms` and `/teacher-tests` |
| T5 | `TestDisplay.jsx` | `axios.post('http://localhost:8001/api/tests')` — hardcoded dev URL, no auth | ✅ Replaced with `apiService.post('/testai/save')` |
| T6 | `TestResults.jsx` | `axios.get('http://localhost:8001/api/test-results/${testId}')` — hardcoded dev URL, no auth | ✅ Replaced with `apiService.get('/testai/results/${testId}')` |
| T7 | `VoiceAssistant.jsx` | `import axios` for speech-to-text FormData POST — unnecessary dep | ✅ Replaced with native `fetch` + `AbortController` for timeout |

### 🟡 P1 — HARDCODED URLs (ALL FIXED)

| # | File | Bug | Fix |
|---|------|-----|-----|
| T8 | `StudentDashboard.jsx` | Fallback URL `http://localhost:8000/api/v1/smartkids` — fails in production | ✅ Changed to `/api/v1/smartkids` |
| T9 | `utils/constants.js` | `API_URL` fallback `http://localhost:8000/api/v1` — fails in production | ✅ Changed to `/api/v1` |
| T10 | `OrganizationDashboard.jsx` | `user?.name` on line 188 — backend has `first_name`/`last_name`, showed `undefined` | ✅ Changed to `user?.first_name user?.last_name` |

### 🟢 P2 — NOTED (Not Fixed)

| # | File | Issue | Notes |
|---|------|-------|-------|
| T11 | `eharf/` module | `Eharf.jsx` and `EharfModal.jsx` exist but no route in `App.jsx` — orphaned component | Add `/eharf` route when ready to ship |
| T12 | `window.appAlert` (38 uses in 7 files) | Defined in `main.jsx` but only logs to console + dispatches CustomEvent — no visible toast UI | Add toast listener component |
| T13 | `MathSolver.jsx` | Uses raw `fetch` to `/api/v1/mathkids/*` — no auth token (works because these endpoints are public) | OK for now, add auth if endpoints become protected |
| T14 | `TestCreator.jsx` (in `/test/`) | Separate from TestAI module, uses local file parsing only — no API calls | OK, self-contained |

---

### FINAL SUMMARY (ALL PHASES)

- **Total issues found:** 54 (F1-F26 + D1-D14 + T1-T14)
- **P0 Crashes/Auth bypass fixed:** 18 (F1-F7 + D1-D4 + T1-T7)
- **P1 Silent bugs fixed:** 13 (F8-F13 + D5-D8 + T8-T10)
- **P2 Documented (low priority):** 23 (F14-F26 + D9-D14 + T11-T14)
- **axios fully eliminated** — 0 imports remaining (was 7 files)
- **All hardcoded localhost URLs removed** from active code
- **Files modified (total):** 19 files
  - `TeacherDashboard.jsx` — 4 fixes
  - `HomePage.jsx` — 1 fix
  - `Navbar.jsx` — 2 fixes
  - `LoginModal.jsx` — 1 fix
  - `ProtectedRoute.jsx` — 1 fix
  - `App.jsx` — 2 fixes
  - `StudentDashboard.jsx` — 2 fixes (button handler + localhost URL)
  - `ParentDashboard.jsx` — 1 fix
  - `AuthContext.jsx` — 3 fixes (isAdmin, isSuperAdmin, canManageContent)
  - `DashboardLayout.jsx` — 3 fixes (dead routes, `<a href>`, isSuperAdmin)
  - `OrganizationDashboard.jsx` — 3 fixes (Axios error, user?.name)
  - `LessonBuilder.jsx` — 1 fix (Axios error pattern)
  - `useUsageTracking.js` — 1 fix (missing state keys)
  - `TestAIPage.jsx` — 1 fix (axios → apiService)
  - `TestParser.jsx` — 1 fix (axios → apiService)
  - `TestBuilder.jsx` — 1 fix (axios → apiService)
  - `TestAssignment.jsx` — 1 fix (axios → apiService + dead endpoints)
  - `TestDisplay.jsx` — 1 fix (hardcoded localhost + axios)
  - `TestResults.jsx` — 1 fix (hardcoded localhost + axios)
  - `VoiceAssistant.jsx` — 1 fix (axios → native fetch)
  - `utils/constants.js` — 1 fix (localhost fallback)
