from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.schemas.health import HealthAnalyticsResponse, JourneySummaryResponse, RiskSummary, VitalsChart
from backend.services.analytics_service import build_risk_summary, build_vitals_chart
from backend.services.journey_service import build_journey_summary

router = APIRouter(prefix="/analytics")


@router.get("/risk-summary", response_model=list[RiskSummary])
def risk_summary(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    return build_risk_summary(db, limit=limit)


@router.get("/vitals-chart", response_model=VitalsChart)
def vitals_chart(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    return build_vitals_chart(db, limit=limit)
health_analytics_router = APIRouter()


@health_analytics_router.get("/health-analytics", response_model=HealthAnalyticsResponse)
def health_analytics(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    return HealthAnalyticsResponse(
        risk_summary=build_risk_summary(db, limit=limit),
        vitals_chart=build_vitals_chart(db, limit=limit),
    )


@health_analytics_router.get("/health-journey", response_model=JourneySummaryResponse)
def health_journey(
    db: Annotated[Session, Depends(get_db)],
    patient_name: str = "Unknown",
    limit: int = 10,
):
    return JourneySummaryResponse(**build_journey_summary(db, patient_name=patient_name, limit=limit))
