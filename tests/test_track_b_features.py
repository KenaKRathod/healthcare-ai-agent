from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_ai_health_chat_supports_research_tool_and_predictive_summary():
    response = client.post(
        "/ai-health-chat",
        json={
            "question": "Show research guidance and treatment options for diabetes",
            "patient_name": "Research User",
            "latest_vitals": {"heart_rate": 90, "blood_pressure": "132/86"},
            "steps": 6200,
            "sleep_hours": 6.4,
            "bmi": 29.1,
            "output_format": "json",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "research"
    assert payload["selected_tool"] == "research_tool"
    assert payload["predictive_summary"]["projected_health_risks"]["diabetes_risk_label"] in {
        "low",
        "moderate",
        "high",
    }


def test_workflow_persists_health_journey_and_exposes_analytics(tmp_path: Path):
    csv_path = tmp_path / "journey.csv"
    csv_path.write_text(
        "\n".join(
            [
                "date,heart_rate,blood_pressure,steps,sleep_hours,calorie_intake,weight_kg,height_m",
                "2026-03-01,84,126/82,7800,6.8,2050,74,1.75",
                "2026-03-02,96,138/90,4300,5.6,2250,74,1.75",
            ]
        ),
        encoding="utf-8",
    )

    workflow_response = client.post(
        "/health-workflow",
        data={"question": "Analyze my overall health risk", "patient_name": "Journey User"},
        files={"file": ("journey.csv", csv_path.read_bytes(), "text/csv")},
    )
    assert workflow_response.status_code == 200
    workflow_payload = workflow_response.json()
    assert workflow_payload["predictive_summary"]["future_cardiovascular_risk"] in {"low", "moderate", "high"}

    journey_response = client.get("/health-journey", params={"patient_name": "Journey User"})
    assert journey_response.status_code == 200
    journey_payload = journey_response.json()
    assert journey_payload["snapshot_count"] >= 1
    assert journey_payload["risk_trend"] in {"stable", "improving", "worsening", "insufficient_data"}


def test_health_report_includes_journey_summary(tmp_path: Path):
    client.post(
        "/health-data",
        params={
            "patient_name": "Report Journey User",
            "heart_rate": 86,
            "blood_pressure": "128/84",
        },
    )

    csv_path = tmp_path / "report_journey.csv"
    csv_path.write_text(
        "\n".join(
            [
                "date,heart_rate,blood_pressure,steps,sleep_hours,calorie_intake,weight_kg,height_m",
                "2026-03-01,86,128/84,8000,7.2,2100,73,1.74",
                "2026-03-02,88,130/85,8400,7.1,2080,73,1.74",
            ]
        ),
        encoding="utf-8",
    )
    client.post(
        "/health-workflow",
        data={"question": "Build my longitudinal summary", "patient_name": "Report Journey User"},
        files={"file": ("report_journey.csv", csv_path.read_bytes(), "text/csv")},
    )

    response = client.get("/health-report", params={"patient_name": "Report Journey User"})
    assert response.status_code == 200
    assert response.json()["journey_summary"]["snapshot_count"] >= 1
