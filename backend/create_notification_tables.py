from app.core.database import Base, engine
from app.models.notification import NotificationLog

if __name__ == "__main__":
    print("Creating Notification tables (notification_logs)...")
    Base.metadata.create_all(bind=engine)
    print("Done.")
