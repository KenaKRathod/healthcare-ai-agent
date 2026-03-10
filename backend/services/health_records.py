from sqlalchemy.orm import Session

from backend.models import HealthData
from backend.schemas.health import HealthDataCreate
from backend.services.health_validator import validate_health_data


def create_health_record(db: Session, payload: HealthDataCreate) -> HealthData:
    validate_health_data(payload.heart_rate, payload.blood_pressure)

    record = HealthData(
        patient_name=payload.patient_name,
        heart_rate=payload.heart_rate,
        blood_pressure=payload.blood_pressure,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_health_records(db: Session, limit: int = 20) -> list[HealthData]:
    return (
        db.query(HealthData)
        .order_by(HealthData.id.desc())
        .limit(limit)
        .all()
    )
