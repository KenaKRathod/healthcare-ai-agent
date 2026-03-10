import altair as alt
import pandas as pd
from sqlalchemy.orm import Session

from backend.ml.risk_model import risk_model
from backend.models import HealthData
from backend.schemas.health import RiskSummary, VitalsChart


def _records_to_frame(records: list[HealthData]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "patient_name": record.patient_name,
                "heart_rate": record.heart_rate,
                "blood_pressure": record.blood_pressure,
            }
            for record in records
        ]
    )


def load_recent_patient_snapshot(
    db: Session,
    patient_name: str | None = None,
) -> dict[str, str | int] | None:
    query = db.query(HealthData).order_by(HealthData.id.desc())
    if patient_name:
        query = query.filter(HealthData.patient_name == patient_name)

    record = query.first()
    if not record:
        return None

    return {
        "patient_name": record.patient_name,
        "heart_rate": record.heart_rate,
        "blood_pressure": record.blood_pressure,
    }


def build_risk_summary(db: Session, limit: int = 20) -> list[RiskSummary]:
    records = (
        db.query(HealthData)
        .order_by(HealthData.id.desc())
        .limit(limit)
        .all()
    )

    summaries = []
    for record in records:
        prediction = risk_model.predict(record.heart_rate, record.blood_pressure)
        summaries.append(
            RiskSummary(
                patient_name=record.patient_name,
                heart_rate=record.heart_rate,
                blood_pressure=record.blood_pressure,
                risk_level=str(prediction["risk_level"]),
                risk_score=float(prediction["risk_score"]),
            )
        )
    return summaries


def build_vitals_chart(db: Session, limit: int = 20) -> VitalsChart:
    records = (
        db.query(HealthData)
        .order_by(HealthData.id.desc())
        .limit(limit)
        .all()
    )
    frame = _records_to_frame(records)

    if frame.empty:
        return VitalsChart(title="Recent heart rate readings", spec={})

    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("patient_name:N", title="Patient"),
            y=alt.Y("heart_rate:Q", title="Heart Rate"),
            color=alt.Color("heart_rate:Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["patient_name", "heart_rate", "blood_pressure"],
        )
        .properties(title="Recent heart rate readings")
    )

    return VitalsChart(title="Recent heart rate readings", spec=chart.to_dict())
