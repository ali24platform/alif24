import sqlite3
import os

db_path = "alif24.db"

# Drop tables that might exist from partial migrations
tables_to_drop = [
    "live_quiz_answers",
    "prize_redemptions",
    "olympiad_answers",
    "live_quiz_questions",
    "live_quiz_participants",
    "coin_withdrawals",
    "coin_transactions",
    "student_coins",
    "olympiad_participants",
    "live_quizzes",
    "olympiad_questions",
    "olympiads",
    "prizes"
]

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Checking tables...")
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        conn.commit()
        conn.close()
        print("Cleanup check complete.")
    except Exception as e:
        print(f"DB cleanup error: {e}")
else:
    print("DB file not found, skipping cleanup.")
