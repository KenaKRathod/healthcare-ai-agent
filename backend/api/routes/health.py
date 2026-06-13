from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User
from backend.schemas.health import HealthDataCreate, HealthRecordRead
from backend.services.health_records import create_health_record, list_health_records
from backend.services.audit_service import log_audit_event

router = APIRouter()


@router.post("/health-data")
def add_health_data(
    patient_name: str,
    heart_rate: int,
    blood_pressure: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    age: int | None = None,
    sex: str | None = None,
    waist_cm: float | None = None,
    activity: str | None = None,
    family_diabetic: str | None = None,
    fasting_blood_sugar: float | None = None,
    postprandial_blood_sugar: float | None = None,
):
    # Enforce RBAC: Patients can only submit health data for themselves
    if current_user.role == "patient" and current_user.username != patient_name:
        log_audit_event(
            db,
            username=current_user.username,
            role=current_user.role,
            action="WRITE",
            resource=f"HealthData:{patient_name}",
            status="DENIED"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only permitted to upload health data for yourself."
        )

    payload = HealthDataCreate(
        patient_name=patient_name,
        heart_rate=heart_rate,
        blood_pressure=blood_pressure,
        age=age,
        sex=sex,
        waist_cm=waist_cm,
        activity=activity,
        family_diabetic=family_diabetic,
        fasting_blood_sugar=fasting_blood_sugar,
        postprandial_blood_sugar=postprandial_blood_sugar,
    )
    record = create_health_record(db, payload)
    
    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"HealthData:{patient_name}",
        status="SUCCESS"
    )
    
    response = {"message": "Health data stored"}
    if record.idrs_score is not None:
        response["idrs_score"] = record.idrs_score
        response["idrs_risk_level"] = record.idrs_risk_level
    return response


@router.get("/health-data", response_model=list[HealthRecordRead])
def get_health_data(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    # Enforce RBAC: Patients can only view their own records
    patient_filter = None
    if current_user.role == "patient":
        patient_filter = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"HealthData:{patient_filter if patient_filter else 'all'}",
        status="SUCCESS"
    )

    return list_health_records(db, limit=limit, patient_name=patient_filter)
