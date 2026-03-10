from dataclasses import dataclass


def _parse_blood_pressure(blood_pressure: str) -> tuple[int, int]:
    normalized = str(blood_pressure).strip()
    if "/" in normalized:
        systolic_text, diastolic_text = normalized.split("/", maxsplit=1)
        return int(systolic_text), int(diastolic_text)

    if normalized.isdigit():
        return int(normalized), 80

    return 120, 80


@dataclass
class RiskModel:
    def predict(self, heart_rate: int, blood_pressure: str) -> dict[str, str | float]:
        systolic, diastolic = _parse_blood_pressure(blood_pressure)

        risk_score = 0.0
        risk_score += min(abs(heart_rate - 72) / 90, 1.0) * 0.4
        risk_score += min(max(systolic - 120, 0) / 80, 1.0) * 0.35
        risk_score += min(max(diastolic - 80, 0) / 40, 1.0) * 0.25

        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.35:
            risk_level = "moderate"
        else:
            risk_level = "low"

        return {"risk_score": round(risk_score, 2), "risk_level": risk_level}


risk_model = RiskModel()
