from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.reports.health_report import generate_health_report
from backend.schemas.health import HealthReportResponse
from backend.services.analytics_service import load_recent_patient_snapshot
from backend.tools import summarize_vitals

router = APIRouter()


@router.get("/health-report", response_model=HealthReportResponse)
def get_health_report(
    db: Annotated[Session, Depends(get_db)],
    patient_name: str = "Unknown",
    bmi: float | None = None,
    steps: int = 0,
    sleep_hours: float = 0.0,
    calorie_intake: int = 0,
    output_format: str = "json",
    output_path: str | None = None,
):
    latest_vitals = load_recent_patient_snapshot(db, patient_name=patient_name)
    report = generate_health_report(
        patient_name=patient_name,
        bmi=bmi,
        trends={
            "vitals_summary": summarize_vitals(latest_vitals) if latest_vitals else "No recent vitals are on file.",
            "heart_rate": latest_vitals.get("heart_rate") if latest_vitals else None,
            "blood_pressure": latest_vitals.get("blood_pressure") if latest_vitals else None,
            "steps": steps,
            "sleep_hours": sleep_hours,
            "calorie_intake": calorie_intake,
        },
        predicted_risk={},
        recommendations=[
            "Continue monitoring your vitals regularly.",
            "Use the AI health chat for tool-guided recommendations.",
        ],
        output_format=output_format,
        output_path=output_path,
    )
    return HealthReportResponse(**report)
