import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app
from backend.database import SessionLocal
from backend.services.workflow_service import run_health_monitoring_workflow

client = TestClient(app)


def _write_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "date,heart_rate,blood_pressure,steps,sleep_hours,calorie_intake,weight_kg,height_m,medications",
                "2026-03-01,78,120/80,8200,7.0,2100,72,1.75,\"warfarin, ibuprofen\"",
                "2026-03-02,88,130/85,9100,7.5,2050,72,1.75,\"warfarin, ibuprofen\"",
            ]
        ),
        encoding="utf-8",
    )


def _write_json(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "date": "2026-03-01",
                        "heart_rate": 80,
                        "blood_pressure": "121/81",
                        "steps": 8000,
                        "sleep_hours": 7.1,
                        "calorie_intake": 2000,
                    },
                    {
                        "date": "2026-03-02",
                        "heart_rate": 85,
                        "blood_pressure": "126/82",
                        "steps": 9500,
                        "sleep_hours": 7.6,
                        "calorie_intake": 1980,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_xml(path: Path) -> None:
    path.write_text(
        """
<records>
  <record>
    <date>2026-03-01</date>
    <heart_rate>75</heart_rate>
    <blood_pressure>118/79</blood_pressure>
    <steps>7600</steps>
    <sleep_hours>6.9</sleep_hours>
    <calorie_intake>1900</calorie_intake>
  </record>
  <record>
    <date>2026-03-02</date>
    <heart_rate>82</heart_rate>
    <blood_pressure>124/80</blood_pressure>
    <steps>8400</steps>
    <sleep_hours>7.4</sleep_hours>
    <calorie_intake>1950</calorie_intake>
  </record>
</records>
""".strip(),
        encoding="utf-8",
    )


def test_workflow_supports_csv_json_and_xml(tmp_path: Path):
    session = SessionLocal()
    try:
        csv_path = tmp_path / "health.csv"
        json_path = tmp_path / "health.json"
        xml_path = tmp_path / "health.xml"
        _write_csv(csv_path)
        _write_json(json_path)
        _write_xml(xml_path)

        for file_path in (csv_path, json_path, xml_path):
            result = run_health_monitoring_workflow(
                file_path=file_path,
                db=session,
                patient_name="Workflow User",
                output_dir=tmp_path / file_path.stem,
            )
            assert result["parsed_rows"] == 2
            assert result["report_path"]
            assert result["goal_statuses"]
            assert result["insights"]
    finally:
        session.close()


def test_workflow_endpoint_returns_enriched_monitoring_output(tmp_path: Path):
    csv_path = tmp_path / "upload.csv"
    _write_csv(csv_path)

    response = client.post(
        "/health-workflow",
        data={"question": "Review my medication and progress", "patient_name": "Alice"},
        files={"file": ("upload.csv", csv_path.read_bytes(), "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_rows"] == 2
    assert payload["goal_statuses"]
    assert payload["interactions"]
    assert payload["insights"]
    assert "Report generated at:" in payload["agent_response"]
