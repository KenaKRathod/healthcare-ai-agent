DRUG_INTERACTIONS = {
    ("ibuprofen", "warfarin"): "Increased bleeding risk.",
    ("aspirin", "ibuprofen"): "Higher gastrointestinal bleeding risk.",
    ("alcohol", "metformin"): "May increase lactic acidosis risk.",
    ("lisinopril", "potassium"): "May increase potassium to unsafe levels.",
}


def check_interactions(medications: list[str]) -> list[dict[str, str]]:
    normalized = [item.strip().lower() for item in medications if item.strip()]
    findings = []

    for left_index, left_item in enumerate(normalized):
        for right_item in normalized[left_index + 1 :]:
            pair = tuple(sorted((left_item, right_item)))
            warning = DRUG_INTERACTIONS.get(pair)
            if warning:
                findings.append(
                    {
                        "medication_1": pair[0],
                        "medication_2": pair[1],
                        "warning": warning,
                    }
                )

    return findings


def schedule_medication(
    medication_name: str,
    times_per_day: int,
    start_time: str = "08:00",
) -> dict[str, str | int | list[str]]:
    if not medication_name.strip() or times_per_day <= 0:
        raise ValueError("Medication name is required and times_per_day must be positive.")

    hour_text, minute_text = start_time.split(":", maxsplit=1)
    hour = int(hour_text)
    minute = int(minute_text)
    interval = max(1, 24 // times_per_day)

    schedule = []
    for dose_number in range(times_per_day):
        scheduled_hour = (hour + (dose_number * interval)) % 24
        schedule.append(f"{scheduled_hour:02d}:{minute:02d}")

    return {
        "medication_name": medication_name,
        "times_per_day": times_per_day,
        "schedule": schedule,
    }


def dosage_reminder(medication_name: str, scheduled_time: str, dosage: str) -> str:
    if not medication_name.strip() or not scheduled_time.strip() or not dosage.strip():
        raise ValueError("Medication name, scheduled_time, and dosage are required.")

    return f"Reminder: Take {dosage} of {medication_name} at {scheduled_time}."
