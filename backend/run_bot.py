import asyncio
import logging
import sys
import httpx
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telegram_bot_service import TelegramBotService
from app.core.database import SessionLocal
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_polling():
    """
    Run Telegram bot in polling mode.
    This is necessary for local development where Webhooks are not reachable.
    """
    # Create a temporary service just to get URL
    temp_db = SessionLocal()
    temp_service = TelegramBotService(temp_db)
    api_url = temp_service.api_url
    temp_db.close()
    
    # 1. DELETE WEBHOOK (Required to switch to polling)
    logger.info("Removing webhook to enable polling...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{api_url}/deleteWebhook")
            logger.info(f"Webhook removal response: {resp.json()}")
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
    
    offset = 0
    logger.info("🚀 Bot polling started! You can now use the bot.")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # 2. GET UPDATES
                response = await client.get(
                    f"{api_url}/getUpdates",
                    params={"offset": offset, "timeout": 10}
                )
                
                if response.status_code != 200:
                    logger.error(f"Telegram API Error: {response.text}")
                    await asyncio.sleep(5)
                    continue
                    
                data = response.json()
                if not data.get("ok"):
                    logger.error(f"Error in response: {data}")
                    await asyncio.sleep(5)
                    continue
                
                updates = data.get("result", [])
                
                # 3. PROCESS UPDATES
                for update in updates:
                    update_id = update.get("update_id")
                    logger.info(f"Processing update {update_id}")
                    
                    # Create fresh session for each update
                    db = SessionLocal()
                    service = TelegramBotService(db)
                    
                    try:
                        await service.process_update(update)
                    except Exception as e:
                        logger.error(f"Error processing update: {e}")
                    finally:
                        db.close()
                    
                    # Move offset forward
                    offset = update_id + 1
                
                # Small sleep to prevent CPU spin if no updates (though long polling handles this)
                if not updates:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Polling loop error: {e}")
                await asyncio.sleep(5)



def seed_questions():
    """Add some sample questions if database is empty"""
    try:
        from app.models.quiz import QuizQuestion
        db = SessionLocal()
        
        count = db.query(QuizQuestion).count()
        if count > 0:
            db.close()
            return
            
        logger.info("Seeding sample quiz questions...")
        
        questions = [
            QuizQuestion(
                question_text="2 + 2 * 2 = ?",
                options=["6", "8", "4", "10"],
                correct_option_index=0,
                category="Math",
                coins_reward=15
            ),
            QuizQuestion(
                question_text="'Knowledge' so'zining tarjimasi?",
                options=["O'qish", "Bilim", "Maktab", "Kitob"],
                correct_option_index=1,
                category="English",
                coins_reward=10
            ),
            QuizQuestion(
                question_text="O'zbekiston bayrog'ida nechta yulduz bor?",
                options=["13", "11", "12", "14"],
                correct_option_index=2,
                category="General",
                coins_reward=20
            )
        ]
        
        for q in questions:
            db.add(q)
        
        db.commit()
        db.close()
        logger.info("Seeding complete!")
        
    except Exception as e:
        logger.error(f"Error seeding questions: {e}")

if __name__ == "__main__":
    seed_questions()
    try:
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
