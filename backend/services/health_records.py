from sqlalchemy.orm import Session

from backend.models import HealthData
from backend.ml.health_prediction import calculate_idrs
from backend.schemas.health import HealthDataCreate
from backend.services.health_validator import validate_health_data


def create_health_record(db: Session, payload: HealthDataCreate) -> HealthData:
    validate_health_data(payload.heart_rate, payload.blood_pressure)
    idrs = None
    if (
        payload.age is not None
        and payload.waist_cm is not None
        and payload.activity is not None
        and payload.family_diabetic is not None
    ):
        idrs = calculate_idrs(
            age=payload.age,
            waist_cm=payload.waist_cm,
            activity=payload.activity,
            family_diabetic=payload.family_diabetic,
            sex=payload.sex or "male",
        )

    record = HealthData(
        patient_name=payload.patient_name,
        heart_rate=payload.heart_rate,
        blood_pressure=payload.blood_pressure,
        age=payload.age,
        sex=payload.sex,
        waist_cm=payload.waist_cm,
        activity=payload.activity,
        family_diabetic=payload.family_diabetic,
        fasting_blood_sugar=payload.fasting_blood_sugar,
        postprandial_blood_sugar=payload.postprandial_blood_sugar,
        idrs_score=int(idrs["score"]) if idrs else None,
        idrs_risk_level=str(idrs["risk_level"]) if idrs else None,
    )
    db.add(record)
    
    # Run alerts check
    from backend.services.alerts import check_and_trigger_alerts
    check_and_trigger_alerts(
        db=db,
        patient_name=payload.patient_name,
        heart_rate=payload.heart_rate,
        blood_pressure=payload.blood_pressure,
        fasting_blood_sugar=payload.fasting_blood_sugar,
        postprandial_blood_sugar=payload.postprandial_blood_sugar,
    )
    
    db.commit()
    db.refresh(record)
    return record


def list_health_records(db: Session, limit: int = 20, patient_name: str | None = None) -> list[HealthData]:
    query = db.query(HealthData).order_by(HealthData.id.desc())
    if patient_name:
        query = query.filter(HealthData.patient_name == patient_name)
    return query.limit(limit).all()
