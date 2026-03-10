from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.schemas.health import HealthDataCreate, HealthRecordRead
from backend.services.health_records import create_health_record, list_health_records

router = APIRouter()


@router.post("/health-data")
def add_health_data(
    patient_name: str,
    heart_rate: int,
    blood_pressure: str,
    db: Annotated[Session, Depends(get_db)],
):
    payload = HealthDataCreate(
        patient_name=patient_name,
        heart_rate=heart_rate,
        blood_pressure=blood_pressure,
    )
    create_health_record(db, payload)
    return {"message": "Health data stored"}


@router.get("/health-data", response_model=list[HealthRecordRead])
def get_health_data(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    return list_health_records(db, limit=limit)
