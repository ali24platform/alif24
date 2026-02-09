import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.models import User, UserRole, StudentProfile, Lesson, TeacherTest, Progress, ProgressStatus
from app.core.database import get_db
from app.middleware.deps import get_current_active_user, get_current_user

class TestStudentLessonFlow(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.client = TestClient(app)
        
        # Mock User (Student)
        self.student_user = MagicMock(spec=User)
        self.student_user.id = uuid4()
        self.student_user.role = UserRole.student
        self.student_user.email = "student@test.com"
        
        self.student_profile = MagicMock(spec=StudentProfile)
        self.student_profile.id = uuid4()
        self.student_profile.user_id = self.student_user.id
        
        # Override Dependencies
        def override_get_db():
            yield self.mock_db
            
        def override_get_current_user():
            return self.student_user
            
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Configure Query Mock
        self.mock_query = MagicMock()
        self.mock_db.query.return_value = self.mock_query
        self.mock_query.filter.return_value = self.mock_query
        self.mock_query.order_by.return_value = self.mock_query

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_lesson_prerequisite_blocked(self):
        """Test accessing Lesson 2 without completing Lesson 1"""
        # Setup Lesson 2
        lesson2 = MagicMock(spec=Lesson)
        lesson2.id = uuid4()
        lesson2.order = 2
        lesson2.subject_id = uuid4()
        lesson2.title = "Lesson 2"

        # Setup Lesson 1
        lesson1 = MagicMock(spec=Lesson)
        lesson1.id = uuid4()
        lesson1.order = 1
        lesson1.subject_id = lesson2.subject_id
        lesson1.title = "Lesson 1"

        # Mock DB Queries
        # 1. Get Student Profile
        # 2. Get Lesson 2 (via Service or direct query)
        # 3. Get Previous Lesson
        # 4. Check Progress
        
        # We need to mock the service call inside get_lesson OR the db query if service does that
        # valid_lesson check:
        # service.find_by_id -> returns lesson2
        # then db query for student -> returns profile
        # then db query for prev_lesson -> returns lesson1
        # then db query for progress -> returns None
        
        # It's hard to mock internal queries of the endpoint without integration test DB or complex side_effects
        # We need to mock the db query results in sequence
        self.mock_query.first.side_effect = [
            lesson2,          # 1. LessonService.find_by_id
            self.student_profile, # 2. StudentProfile
            lesson1,          # 3. Prev Lesson
            None              # 4. Progress (Not found)
        ]
        
        response = self.client.get(f"/api/v1/lessons/{lesson2.id}")
        
        # Expect 403 Forbidden
        self.assertEqual(response.status_code, 403)
        self.assertIn("must complete lesson", response.json()["detail"])

    @patch('app.api.v1.endpoints.student_lesson_router.StudentService')
    def test_complete_lesson_success(self, MockStudentService):
        """Test successfully completing a lesson"""
        lesson_id = uuid4()
        answers = {"1": "A"}
        
        mock_service_instance = MockStudentService.return_value
        mock_service_instance.complete_lesson.return_value = {
            "success": True,
            "message": "Lesson completed!",
            "coins_earned": 10
        }
        
        response = self.client.post(
            f"/api/v1/student-lessons/{lesson_id}/complete",
            json=answers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["coins_earned"], 10)
        mock_service_instance.complete_lesson.assert_called_once()

if __name__ == "__main__":
    unittest.main()
