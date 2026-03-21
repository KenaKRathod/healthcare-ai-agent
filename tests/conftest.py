import os
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB_PATH = Path(tempfile.gettempdir()) / "healthcare_ai_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from backend.database import SessionLocal, engine
from backend.models import Base, HealthData, HealthGoal, HealthJourneySnapshot, User


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.query(HealthData).delete()
        session.query(HealthGoal).delete()
        session.query(HealthJourneySnapshot).delete()
        session.query(User).delete()
        session.commit()
        yield
    finally:
        session.close()
