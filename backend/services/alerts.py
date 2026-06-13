from datetime import datetime
from sqlalchemy.orm import Session
from backend.models import HealthAlert

def _parse_blood_pressure(bp_str: str) -> tuple[float, float] | None:
    try:
        normalized = str(bp_str).strip()
        if "/" in normalized:
            sys_t, dia_t = normalized.split("/", maxsplit=1)
            return float(sys_t), float(dia_t)
    except Exception:
        pass
    return None

def check_and_trigger_alerts(
    db: Session,
    patient_name: str,
    heart_rate: int | float | None = None,
    blood_pressure: str | None = None,
    fasting_blood_sugar: float | None = None,
    postprandial_blood_sugar: float | None = None,
) -> list[str]:
    """
    Checks patient vitals against critical thresholds and logs any alerts to the PostgreSQL database.
    Returns a list of warning/alert messages.
    """
    alerts_triggered = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # L-BUG-8 FIX: Heart Rate Check — previously the `heart_rate` parameter was accepted
    # by this function but never evaluated, so dangerous rates produced no alert at all.
    if heart_rate is not None:
        if heart_rate < 40:
            msg = (
                f"CRITICAL ALERT: Severe bradycardia detected — resting heart rate is {heart_rate} BPM. "
                f"This may indicate a cardiac conduction disorder. Lie down, avoid physical exertion, "
                f"and seek immediate medical attention."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="heart_rate",
                value=str(heart_rate),
                risk_level="critical",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)
        elif heart_rate > 140:
            msg = (
                f"CRITICAL ALERT: Severe tachycardia detected — resting heart rate is {heart_rate} BPM. "
                f"This may indicate a cardiac arrhythmia. Rest immediately, avoid caffeine and strenuous activity, "
                f"and contact a medical professional right away."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="heart_rate",
                value=str(heart_rate),
                risk_level="critical",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)
        elif heart_rate > 100:
            msg = (
                f"WARNING: Elevated resting heart rate ({heart_rate} BPM) detected (Tachycardia). "
                f"Monitor your heart rate, stay hydrated, and consult your physician if it persists."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="heart_rate",
                value=str(heart_rate),
                risk_level="warning",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)

    # 1. Blood Pressure Check (Hypertensive Crisis)
    if blood_pressure:
        bp_parsed = _parse_blood_pressure(blood_pressure)
        if bp_parsed:
            systolic, diastolic = bp_parsed
            if systolic > 180 or diastolic > 120:
                msg = (
                    f"EMERGENCY: Critical blood pressure level ({blood_pressure} mmHg) detected. "
                    f"This indicates a Hypertensive Crisis. Sit down, rest, avoid exertion, "
                    f"and contact a medical professional immediately."
                )
                alert = HealthAlert(
                    patient_name=patient_name,
                    vital_type="blood_pressure",
                    value=blood_pressure,
                    risk_level="critical",
                    message=msg,
                    generated_at=timestamp,
                )
                db.add(alert)
                alerts_triggered.append(msg)

    # 2. Fasting Blood Sugar Check
    if fasting_blood_sugar is not None and fasting_blood_sugar > 0:
        if fasting_blood_sugar < 70:
            msg = (
                f"CRITICAL ALERT: Low fasting blood sugar ({fasting_blood_sugar} mg/dL) detected (Hypoglycemia). "
                f"Consume 15g of fast-acting sugar (e.g., fruit juice, honey, or glucose tablets) "
                f"immediately and retest in 15 minutes."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="fasting_blood_sugar",
                value=str(fasting_blood_sugar),
                risk_level="critical",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)
        elif fasting_blood_sugar > 130:
            msg = (
                f"WARNING: Elevated fasting blood sugar ({fasting_blood_sugar} mg/dL) detected (Hyperglycemia). "
                f"Ensure hydration, follow diabetic dietary guidelines, and consult your physician if this persists."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="fasting_blood_sugar",
                value=str(fasting_blood_sugar),
                risk_level="warning",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)

    # 3. Postprandial Blood Sugar Check
    if postprandial_blood_sugar is not None and postprandial_blood_sugar > 0:
        if postprandial_blood_sugar < 70:
            msg = (
                f"CRITICAL ALERT: Low postprandial blood sugar ({postprandial_blood_sugar} mg/dL) detected (Hypoglycemia). "
                f"Consume fast-acting sugar (e.g., fruit juice or glucose tablets) immediately."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="postprandial_blood_sugar",
                value=str(postprandial_blood_sugar),
                risk_level="critical",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)
        elif postprandial_blood_sugar > 180:
            msg = (
                f"WARNING: Elevated postprandial blood sugar ({postprandial_blood_sugar} mg/dL) detected (Hyperglycemia). "
                f"Limit high-glycemic carbohydrates and monitor your readings."
            )
            alert = HealthAlert(
                patient_name=patient_name,
                vital_type="postprandial_blood_sugar",
                value=str(postprandial_blood_sugar),
                risk_level="warning",
                message=msg,
                generated_at=timestamp,
            )
            db.add(alert)
            alerts_triggered.append(msg)

    if alerts_triggered:
        db.commit()

    return alerts_triggered
