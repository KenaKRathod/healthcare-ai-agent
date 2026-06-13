from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User, MedicationSchedule, MedicationAdherence
from backend.services.audit_service import log_audit_event

router = APIRouter()


class ScheduleCreate(BaseModel):
    patient_name: str = Field(..., min_length=1)
    drug_name: str = Field(..., min_length=1)
    dosage: str = Field(...)
    timing: str = Field(..., description="e.g. Morning, Afternoon, Evening, Night")
    drug_type: str = Field(default="Allopathic", description="Allopathic or Ayurvedic")


class AdherenceLog(BaseModel):
    patient_name: str
    drug_name: str
    date: str  # YYYY-MM-DD
    status: str  # Taken or Missed


@router.get("/medication-schedule")
def get_schedules(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_name: str = "Unknown",
):
    target_patient = patient_name
    if current_user.role == "patient":
        target_patient = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"MedicationSchedule:{target_patient}",
        status="SUCCESS"
    )

    return (
        db.query(MedicationSchedule)
        .filter(MedicationSchedule.patient_name == target_patient)
        .all()
    )


@router.post("/medication-schedule")
def create_schedule(
    payload: ScheduleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role == "patient" and current_user.username != payload.patient_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own medication schedules."
        )

    schedule = MedicationSchedule(
        patient_name=payload.patient_name,
        drug_name=payload.drug_name,
        dosage=payload.dosage,
        timing=payload.timing,
        drug_type=payload.drug_type,
        status="Active",
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"MedicationSchedule:{payload.patient_name}:{payload.drug_name}",
        status="SUCCESS"
    )
    return schedule


@router.get("/medication-adherence")
def get_adherence(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_name: str = "Unknown",
):
    target_patient = patient_name
    if current_user.role == "patient":
        target_patient = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"MedicationAdherence:{target_patient}",
        status="SUCCESS"
    )

    return (
        db.query(MedicationAdherence)
        .filter(MedicationAdherence.patient_name == target_patient)
        .order_by(MedicationAdherence.id.desc())
        .limit(100)
        .all()
    )


@router.post("/medication-adherence")
def log_adherence(
    payload: AdherenceLog,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role == "patient" and current_user.username != payload.patient_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own adherence data."
        )

    # Check if entry already exists for drug and date
    adherence = (
        db.query(MedicationAdherence)
        .filter(
            MedicationAdherence.patient_name == payload.patient_name,
            MedicationAdherence.drug_name == payload.drug_name,
            MedicationAdherence.date == payload.date,
        )
        .first()
    )

    if adherence:
        adherence.status = payload.status
    else:
        adherence = MedicationAdherence(
            patient_name=payload.patient_name,
            drug_name=payload.drug_name,
            date=payload.date,
            status=payload.status,
        )
        db.add(adherence)

    db.commit()
    db.refresh(adherence)

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"MedicationAdherence:{payload.patient_name}:{payload.drug_name}:{payload.date}",
        status="SUCCESS"
    )
    return adherence
