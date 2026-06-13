import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from sqlalchemy import inspect
from backend.database import engine
from backend.models import Base

load_dotenv()

def verify_tables():
    print("Connecting to database:", os.getenv("DATABASE_URL"))
    # Trigger table creation
    Base.metadata.create_all(bind=engine)
    
    # Inspect tables in the database
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables found in database:", tables)
    
    expected_tables = [
        "users", "health_data", "health_goals", "health_journey_snapshots",
        "patient_profiles", "medication_schedules", "medication_adherence",
        "health_insurances", "doctor_consultations", "health_alerts"
    ]
    
    missing = [t for t in expected_tables if t not in tables]
    if missing:
        print("Missing tables:", missing)
    else:
        print("All expected tables are successfully created!")

if __name__ == "__main__":
    verify_tables()
