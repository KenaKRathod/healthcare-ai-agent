from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_add_health_data_success():
    response = client.post(
        "/health-data",
        params={
            "patient_name": "Alice",
            "heart_rate": 72,
            "blood_pressure": "120/80",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Health data stored"}


def test_add_health_data_rejects_invalid_heart_rate():
    response = client.post(
        "/health-data",
        params={
            "patient_name": "Bob",
            "heart_rate": 250,
            "blood_pressure": "140/90",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Heart rate out of safe range"}


def test_add_health_data_rejects_missing_blood_pressure():
    response = client.post(
        "/health-data",
        params={
            "patient_name": "Chris",
            "heart_rate": 88,
            "blood_pressure": "",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Blood pressure missing"}
