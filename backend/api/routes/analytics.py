from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User
from backend.schemas.health import HealthAnalyticsResponse, JourneySummaryResponse, RiskSummary, VitalsChart
from backend.services.analytics_service import build_risk_summary, build_vitals_chart
from backend.services.journey_service import build_journey_summary
from backend.services.audit_service import log_audit_event

router = APIRouter(prefix="/analytics")


@router.get("/risk-summary", response_model=list[RiskSummary])
def risk_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource="RiskSummary:all",
        status="SUCCESS"
    )
    return build_risk_summary(db, limit=limit)


@router.get("/vitals-chart", response_model=VitalsChart)
def vitals_chart(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource="VitalsChart:all",
        status="SUCCESS"
    )
    return build_vitals_chart(db, limit=limit)


health_analytics_router = APIRouter()


@health_analytics_router.get("/health-analytics", response_model=HealthAnalyticsResponse)
def health_analytics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource="HealthAnalytics:all",
        status="SUCCESS"
    )
    return HealthAnalyticsResponse(
        risk_summary=build_risk_summary(db, limit=limit),
        vitals_chart=build_vitals_chart(db, limit=limit),
    )


@health_analytics_router.get("/health-journey", response_model=JourneySummaryResponse)
def health_journey(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_name: str = "Unknown",
    limit: int = 10,
):
    # Enforce RBAC: Patient can only view their own journey
    target_patient = patient_name
    if current_user.role == "patient":
        target_patient = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"HealthJourney:{target_patient}",
        status="SUCCESS"
    )

    return JourneySummaryResponse(**build_journey_summary(db, patient_name=target_patient, limit=limit))
