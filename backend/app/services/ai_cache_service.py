import hashlib
import json
from sqlalchemy.orm import Session
from app.models.ai_cache import AICache
from typing import Optional, Dict, Any

class AICacheService:
    @staticmethod
    def generate_hash(prompt: str, context: str = "", model: str = "gpt-4") -> str:
        """Generate SHA256 hash for the prompt configuration"""
        content = f"{model}:{prompt}:{context}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def get_cached_response(db: Session, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if exists"""
        cache_entry = db.query(AICache).filter(AICache.prompt_hash == prompt_hash).first()
        if cache_entry:
            try:
                return json.loads(cache_entry.response_json)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def set_cached_response(
        db: Session, 
        prompt_hash: str, 
        response_data: Dict[str, Any], 
        prompt_text: str = "", 
        model: str = "gpt-4",
        tokens: int = 0
    ):
        """Save response to cache"""
        # Save as string
        response_str = json.dumps(response_data)
        
        # Check if exists (upsert logic if needed, but hash should be unique)
        existing = db.query(AICache).filter(AICache.prompt_hash == prompt_hash).first()
        
        if existing:
            existing.response_json = response_str
            existing.updated_at = func.now()
        else:
            new_cache = AICache(
                prompt_hash=prompt_hash,
                prompt_text=prompt_text[:1000] if prompt_text else "", # Truncate for storage
                response_json=response_str,
                model_name=model,
                tokens_used=tokens
            )
            db.add(new_cache)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Cache Save Error: {e}")
