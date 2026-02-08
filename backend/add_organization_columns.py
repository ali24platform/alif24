from sqlalchemy import text
from app.core.database import engine

def add_column_if_not_exists(table, column, type_def):
    with engine.connect() as conn:
        try:
            # Check if column exists using PRAGMA
            result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            columns = [row[1] for row in result] # row[1] is name
            if column not in columns:
                print(f"Adding {column} to {table}...")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"))
                conn.commit()
                print(f"Added {column} to {table}.")
            else:
                print(f"Column {column} already exists in {table}.")
        except Exception as e:
            print(f"Error adding column to {table}: {e}")

if __name__ == "__main__":
    print("Adding organization_id columns...")
    # Using CHAR(36) for UUID in SQLite
    add_column_if_not_exists("teacher_profiles", "organization_id", "CHAR(36)")
    add_column_if_not_exists("student_profiles", "organization_id", "CHAR(36)")
    add_column_if_not_exists("crm_leads", "organization_id", "CHAR(36)")
    print("Done.")
