from app.core.database import engine, Base
from app.models.quiz import QuizQuestion, QuizAttempt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    logger.info("Creatng Daily Quiz tables...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
        
        # Verify
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "quiz_questions" in tables and "quiz_attempts" in tables:
            logger.info("✅ Verification successful: 'quiz_questions' and 'quiz_attempts' tables exist.")
        else:
            logger.error("❌ Verification failed: Tables not found.")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
