def validate_health_data(data):
    if not isinstance(data, dict):
        raise ValueError("Health data must be a dictionary.")

    heart_rate = data.get("heart_rate")
    blood_pressure = data.get("blood_pressure")

    if heart_rate is None:
        raise ValueError("Heart rate is required.")

    if not isinstance(heart_rate, int):
        raise ValueError("Heart rate must be an integer.")

    if heart_rate < 30 or heart_rate > 200:

        raise ValueError("Invalid heart rate")

    if not isinstance(blood_pressure, str) or blood_pressure.strip() == "":
        raise ValueError("Blood pressure missing")

    return True
