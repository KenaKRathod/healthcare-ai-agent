from sqlalchemy.orm import Session

from backend.models import HealthJourneySnapshot


def _parse_blood_pressure(blood_pressure: str | None) -> tuple[float, float]:
    normalized = str(blood_pressure or "120/80").strip()
    if "/" in normalized:
        systolic_text, diastolic_text = normalized.split("/", maxsplit=1)
        return float(systolic_text), float(diastolic_text)
    if normalized.isdigit():
        return float(normalized), 80.0
    return 120.0, 80.0


def record_journey_snapshot(
    db: Session,
    patient_name: str,
    heart_rate: float,
    blood_pressure: str,
    steps: float,
    sleep_hours: float,
    calorie_intake: float,
    bmi: float,
    risk_level: str,
    risk_score: float,
    anomaly_count: int,
    idrs_score: int | None = None,
    idrs_risk_level: str | None = None,
    fasting_blood_sugar: float = 0.0,
    postprandial_blood_sugar: float = 0.0,
) -> HealthJourneySnapshot:
    systolic_bp, diastolic_bp = _parse_blood_pressure(blood_pressure)
    snapshot = HealthJourneySnapshot(
        patient_name=patient_name,
        heart_rate=float(heart_rate),
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        steps=float(steps),
        sleep_hours=float(sleep_hours),
        calorie_intake=float(calorie_intake),
        bmi=float(bmi),
        risk_level=risk_level,
        risk_score=float(risk_score),
        anomaly_count=int(anomaly_count),
        idrs_score=idrs_score,
        idrs_risk_level=idrs_risk_level,
        fasting_blood_sugar=float(fasting_blood_sugar),
        postprandial_blood_sugar=float(postprandial_blood_sugar),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def build_journey_summary(db: Session, patient_name: str, limit: int = 10) -> dict:
    snapshots = (
        db.query(HealthJourneySnapshot)
        .filter(HealthJourneySnapshot.patient_name == patient_name)
        .order_by(HealthJourneySnapshot.id.desc())
        .limit(limit)
        .all()
    )

    if not snapshots:
        return {
            "patient_name": patient_name,
            "snapshot_count": 0,
            "latest_risk_level": "unknown",
            "average_heart_rate": 0.0,
            "average_steps": 0.0,
            "average_sleep_hours": 0.0,
            "average_bmi": 0.0,
            "risk_trend": "insufficient_data",
        }

    average_heart_rate = sum(item.heart_rate for item in snapshots) / len(snapshots)
    average_steps = sum(item.steps for item in snapshots) / len(snapshots)
    average_sleep_hours = sum(item.sleep_hours for item in snapshots) / len(snapshots)
    average_bmi = sum(item.bmi for item in snapshots) / len(snapshots)

    latest = snapshots[0]
    oldest = snapshots[-1]
    if latest.risk_score > oldest.risk_score + 0.05:
        risk_trend = "worsening"
    elif latest.risk_score < oldest.risk_score - 0.05:
        risk_trend = "improving"
    else:
        risk_trend = "stable"

    return {
        "patient_name": patient_name,
        "snapshot_count": len(snapshots),
        "latest_risk_level": latest.risk_level,
        "latest_risk_score": round(float(latest.risk_score), 2),
        "average_heart_rate": round(float(average_heart_rate), 2),
        "average_steps": round(float(average_steps), 2),
        "average_sleep_hours": round(float(average_sleep_hours), 2),
        "average_bmi": round(float(average_bmi), 2),
        "risk_trend": risk_trend,
    }
