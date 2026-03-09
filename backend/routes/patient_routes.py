from fastapi import APIRouter

from backend.database import SessionLocal
from backend.models import HealthData
from backend.services.health_validator import validate_health_data

router = APIRouter()


@router.post("/health-data")
def add_health_data(patient_name: str, heart_rate: int, blood_pressure: str):
    validate_health_data(heart_rate, blood_pressure)

    db = SessionLocal()
    try:
        record = HealthData(
            patient_name=patient_name,
            heart_rate=heart_rate,
            blood_pressure=blood_pressure,
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"message": "Health data stored"}
