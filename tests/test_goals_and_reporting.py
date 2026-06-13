import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_goals_create_update_and_progress():
    from backend.database import SessionLocal
    from backend.models import HealthGoal
    session = SessionLocal()
    try:
        session.query(HealthGoal).filter(HealthGoal.patient_name == "Alice").delete()
        session.commit()
    finally:
        session.close()

    initial = client.get(
        "/health-goals",
        params={"patient_name": "Alice", "steps": 8500, "sleep_hours": 7.5},
    )

    assert initial.status_code == 200
    initial_payload = initial.json()
    assert len(initial_payload) == 3
    assert initial_payload[0]["goal_name"] == "daily_steps"

    created = client.post(
        "/health-goals",
        json={
            "patient_name": "Alice",
            "goal_name": "hydration_liters",
            "target_value": 3,
            "unit": "liters",
        },
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["goal_name"] == "hydration_liters"
    assert created_payload["unit"] == "liters"

    updated = client.put(
        f"/health-goals/{created_payload['goal_id']}",
        json={"target_value": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["target_value"] == 4.0


def test_health_report_contains_goal_statuses_interactions_and_insights(tmp_path: Path):
    client.post(
        "/health-data",
        params={
            "patient_name": "Alice",
            "heart_rate": 92,
            "blood_pressure": "135/88",
        },
    )

    report_path = tmp_path / "alice_report.json"
    response = client.get(
        "/health-report",
        params={
            "patient_name": "Alice",
            "steps": 9000,
            "sleep_hours": 7,
            "weight_loss_progress_kg": 2,
            "medications": "warfarin, ibuprofen",
            "output_path": str(report_path),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["goal_statuses"]
    assert payload["interactions"]
    assert payload["insights"]
    assert Path(payload["report_path"]).exists()

    saved_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_payload["interactions"][0]["warning"] == "Increased bleeding risk."
