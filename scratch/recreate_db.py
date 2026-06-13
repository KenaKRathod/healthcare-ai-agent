import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from backend.database import engine
from backend.models import Base

load_dotenv()

def recreate_db():
    print("Re-initializing PostgreSQL tables...")
    print("Database URL:", os.getenv("DATABASE_URL"))
    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)
    print("Successfully dropped all tables.")
    # Create tables with the updated schema
    Base.metadata.create_all(bind=engine)
    print("Successfully created all tables with the updated schemas!")

if __name__ == "__main__":
    recreate_db()
