from datetime import datetime
from uuid import UUID
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.repositories.student_repository import StudentRepository
from app.services.base_service import BaseService
from app.services.coin_service import CoinService
from app.models import Progress, ProgressStatus, Lesson, TeacherTest, TestResult

class StudentService(BaseService):
    def __init__(self, db: Session):
        repository = StudentRepository(db)
        super().__init__(repository, db)
        self.student_repo = repository
        self.coin_service = CoinService(db)

    def complete_lesson(self, student_user_id: UUID, lesson_id: UUID, answers: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mark a lesson as completed.
        If the lesson has a quiz, grade it first.
        """
        # 1. Get Student Profile
        student = self.student_repo.get_by_user_id(student_user_id)
        if not student:
            raise Exception("Student profile not found")

        # 2. Get Lesson
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise Exception("Lesson not found")

        # 3. Handle Quiz (if exists)
        quiz_result = None
        passed = True
        points_earned = 0

        if lesson.quiz:
            # Create TestResult
            quiz_result = self._grade_quiz(lesson.quiz, student.user_id, answers)
            passed = quiz_result.passed
            if passed:
                points_earned = quiz_result.score # Or fixed amount
        
        if not passed:
             return {
                "success": False,
                "message": "Quiz failed. Try again.",
                "quiz_result": quiz_result
            }

        # 4. Update Progress
        # Check if already completed
        progress = self.db.query(Progress).filter(
            Progress.student_id == student.id,
            Progress.lesson_id == lesson.id
        ).first()

        is_first_completion = False
        
        if not progress:
            progress = Progress(
                student_id=student.id,
                lesson_id=lesson.id,
                status=ProgressStatus.COMPLETED,
                points_earned=points_earned
            )
            self.db.add(progress)
            is_first_completion = True
        elif progress.status != ProgressStatus.COMPLETED:
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = datetime.utcnow()
            progress.points_earned = points_earned
            is_first_completion = True
        
        # 5. Award Coins (Only for first completion)
        coin_reward = 0
        if is_first_completion:
            # Base lesson reward + Quiz points
            base_reward = lesson.points_reward or 10
            total_reward = base_reward
            
            self.coin_service.add_coins_for_lesson(student.user_id, lesson.id)
            coin_reward = total_reward

        self.db.commit()

        return {
            "success": True,
            "message": "Lesson completed!",
            "coins_earned": coin_reward,
            "is_first_completion": is_first_completion,
            "quiz_result": quiz_result
        }

    def _grade_quiz(self, quiz: TeacherTest, student_id: UUID, answers: Dict[str, Any]) -> TestResult:
        """Helper to grade a synchronous quiz submission"""
        score = 0
        max_score = quiz.total_points
        
        # Simply logic: check exact matches
        # answers: {"1": "A", "2": "B"}
        # quiz.questions: [{"id": 1, "correct_answer": "A", "points": 10}, ...]
        
        for q in quiz.questions:
            q_id = str(q.get("id")) # Ensure string key
            submitted = answers.get(q_id)
            correct = q.get("correct_answer")
            points = q.get("points", 1)
            
            if submitted == correct:
                score += points
                
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        passed = percentage >= quiz.passing_score
        
        result = TestResult(
            test_id=quiz.id,
            student_id=student_id,
            answers=answers,
            score=score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
            started_at=datetime.utcnow(), 
            completed_at=datetime.utcnow()
        )
        self.db.add(result)
        return result

