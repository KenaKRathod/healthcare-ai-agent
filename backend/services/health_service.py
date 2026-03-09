def validate_health_data(data):

    if data["heart_rate"] < 30 or data["heart_rate"] > 200:

        raise ValueError("Invalid heart rate")

    if data["blood_pressure"] == "":
        raise ValueError("Blood pressure missing")

    return True