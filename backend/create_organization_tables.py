from app.core.database import Base, engine
from app.models.rbac_models import (
    OrganizationSubscription, 
    OrganizationMaterial, 
    ClassroomSchedule
)

if __name__ == "__main__":
    print("Creating Organization tables (subscriptions, materials, schedules)...")
    Base.metadata.create_all(bind=engine)
    print("Done.")
