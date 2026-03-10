MEDICAL_INFORMATION = {
    "hypertension": {
        "summary": "Hypertension is persistently elevated blood pressure that increases cardiovascular risk.",
        "guidelines": "Lifestyle changes and blood pressure monitoring are first-line for many patients.",
        "treatments": ["Exercise regularly", "Reduce sodium intake", "Use prescribed antihypertensives"],
    },
    "diabetes": {
        "summary": "Diabetes affects blood glucose regulation and requires long-term monitoring.",
        "guidelines": "Track HbA1c, follow nutrition guidance, and monitor medication adherence.",
        "treatments": ["Nutrition planning", "Physical activity", "Glucose-lowering medication"],
    },
    "asthma": {
        "summary": "Asthma is a chronic inflammatory airway disease that can cause wheezing and breathlessness.",
        "guidelines": "Use controller therapy when prescribed and avoid known triggers.",
        "treatments": ["Inhaled corticosteroids", "Rescue inhaler", "Trigger avoidance"],
    },
}


def search_medical_information(topic: str) -> dict[str, str]:
    key = topic.strip().lower()
    info = MEDICAL_INFORMATION.get(key)
    if not info:
        return {"topic": key, "summary": "No local reference found for this topic."}

    return {"topic": key, "summary": info["summary"]}


def latest_guidelines(topic: str) -> str:
    key = topic.strip().lower()
    info = MEDICAL_INFORMATION.get(key)
    if not info:
        return "No guideline summary is available for this topic."
    return info["guidelines"]


def treatment_options(topic: str) -> list[str]:
    key = topic.strip().lower()
    info = MEDICAL_INFORMATION.get(key)
    if not info:
        return ["No treatment options are available for this topic."]
    return info["treatments"]
