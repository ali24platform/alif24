from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid
from app.core.database import Base

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # List of strings ["Option A", "Option B", ...]
    correct_option_index = Column(Integer, nullable=False)  # 0, 1, 2...
    coins_reward = Column(Integer, default=10)
    category = Column(String, default="General")  # Math, English, Logic
    difficulty = Column(String, default="Medium")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("QuizAttempt", back_populates="question")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id = Column(PG_UUID(as_uuid=True), ForeignKey("quiz_questions.id"), nullable=False)
    chosen_option_index = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    coins_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("QuizQuestion", back_populates="attempts")
