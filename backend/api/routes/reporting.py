from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.reports.health_report import generate_health_report
from backend.schemas.health import HealthReportResponse
from backend.services.analytics_service import load_recent_patient_snapshot
from backend.services.goal_service import build_goal_statuses, list_patient_goals
from backend.services.journey_service import build_journey_summary
from backend.tools import check_interactions
from backend.tools import summarize_vitals

router = APIRouter()


@router.get("/health-report", response_model=HealthReportResponse)
def get_health_report(
    db: Annotated[Session, Depends(get_db)],
    patient_name: str = "Unknown",
    bmi: float | None = None,
    steps: int = 0,
    sleep_hours: float = 0.0,
    weight_loss_progress_kg: float = 0.0,
    calorie_intake: int = 0,
    medications: str = "",
    output_format: str = "json",
    output_path: str | None = None,
):
    latest_vitals = load_recent_patient_snapshot(db, patient_name=patient_name)
    goals = list_patient_goals(db, patient_name)
    goal_statuses = build_goal_statuses(
        goals,
        {
            "daily_steps": float(steps),
            "sleep_hours": float(sleep_hours),
            "weight_loss_kg": float(weight_loss_progress_kg),
        },
    )
    medication_list = [item.strip() for item in medications.split(",") if item.strip()]
    interactions = check_interactions(medication_list) if medication_list else []
    insights = [
        f"Daily steps progress is {goal_statuses[0]['progress_percent']:.2f}%." if goal_statuses else "No goals available.",
        f"Sleep goal progress is {goal_statuses[1]['progress_percent']:.2f}%." if len(goal_statuses) > 1 else "Sleep goal not configured.",
        "Potential medication interactions were found." if interactions else "No known medication interactions were found.",
    ]
    journey_summary = build_journey_summary(db, patient_name)
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
        recommendations=[status["recommendation"] for status in goal_statuses] or [
            "Continue monitoring your vitals regularly.",
            "Use the AI health chat for tool-guided recommendations.",
        ],
        goal_statuses=goal_statuses,
        interactions=interactions,
        insights=insights,
        journey_summary=journey_summary,
        output_format=output_format,
        output_path=output_path,
    )
    return HealthReportResponse(**report)
