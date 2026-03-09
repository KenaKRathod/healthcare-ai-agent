def validate_health_data(heart_rate, blood_pressure):
    if heart_rate < 30 or heart_rate > 200:
        raise ValueError("Heart rate out of safe range")

    if blood_pressure == "":
        raise ValueError("Blood pressure missing")

    return True
