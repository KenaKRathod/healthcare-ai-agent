def categorize_blood_pressure(blood_pressure: str) -> str:
    systolic_text, diastolic_text = blood_pressure.split("/", maxsplit=1)
    systolic = int(systolic_text)
    diastolic = int(diastolic_text)

    if systolic >= 140 or diastolic >= 90:
        return "high blood pressure"
    if systolic >= 120 or diastolic >= 80:
        return "elevated blood pressure"
    return "normal blood pressure"


def summarize_vitals(latest_vitals: dict[str, str | int] | None) -> str:
    if not latest_vitals:
        return "No recent vitals are available."

    heart_rate = int(latest_vitals["heart_rate"])
    blood_pressure = str(latest_vitals["blood_pressure"])
    blood_pressure_status = categorize_blood_pressure(blood_pressure)
    return (
        f"Heart rate is {heart_rate} bpm and blood pressure is {blood_pressure} "
        f"({blood_pressure_status})."
    )
