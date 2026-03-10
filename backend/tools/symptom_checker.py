SYMPTOM_CONDITIONS = {
    "fever": ["viral infection", "flu", "covid-like illness"],
    "cough": ["common cold", "bronchitis", "respiratory infection"],
    "headache": ["dehydration", "migraine", "stress-related headache"],
    "chest pain": ["cardiac issue", "acid reflux", "muscle strain"],
    "fatigue": ["anemia", "poor sleep", "viral illness"],
}


def possible_conditions(symptoms: list[str]) -> list[str]:
    matched_conditions = []
    for symptom in symptoms:
        for condition in SYMPTOM_CONDITIONS.get(symptom.strip().lower(), []):
            if condition not in matched_conditions:
                matched_conditions.append(condition)
    return matched_conditions


def risk_level(symptoms: list[str]) -> str:
    normalized = {symptom.strip().lower() for symptom in symptoms}
    high_risk_triggers = {"chest pain", "shortness of breath", "confusion"}
    moderate_risk_triggers = {"fever", "persistent cough", "fatigue"}

    if normalized & high_risk_triggers:
        return "high"
    if normalized & moderate_risk_triggers:
        return "moderate"
    return "low"


def analyze_symptoms(symptoms: list[str]) -> dict[str, str | list[str]]:
    if not symptoms:
        raise ValueError("At least one symptom is required.")

    return {
        "symptoms": [symptom.strip().lower() for symptom in symptoms if symptom.strip()],
        "possible_conditions": possible_conditions(symptoms),
        "risk_level": risk_level(symptoms),
        "note": "This is not a diagnosis. Seek medical care for urgent symptoms.",
    }
