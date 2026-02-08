"""
Create Phone Verification and Telegram User Tables

Run this script to create the new tables for phone verification:
    python create_verification_tables.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models.phone_verification import PhoneVerification, TelegramUser


def create_tables():
    """Create phone verification tables"""
    print("Creating phone verification tables...")
    
    try:
        # Create only the new tables
        PhoneVerification.__table__.create(engine, checkfirst=True)
        TelegramUser.__table__.create(engine, checkfirst=True)
        
        print("✅ Tables created successfully:")
        print("   - phone_verifications")
        print("   - telegram_users")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True


def verify_tables():
    """Verify tables exist"""
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required = ["phone_verifications", "telegram_users"]
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"❌ Missing tables: {missing}")
        return False
    
    print("✅ All verification tables exist")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage phone verification tables")
    parser.add_argument("action", choices=["create", "verify"], default="create", nargs="?")
    args = parser.parse_args()
    
    if args.action == "create":
        success = create_tables()
        if success:
            verify_tables()
    elif args.action == "verify":
        verify_tables()
