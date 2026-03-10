import tempfile
from pathlib import Path

import pandas as pd

from backend.agents.healthcare_agent import healthcare_agent
from backend.analytics.health_visualization import (
    plot_calorie_intake,
    plot_heart_rate_trends,
    plot_sleep_hours,
    plot_steps_over_time,
)
from backend.health_goals import DEFAULT_GOALS, goal_recommendation, progress_percentage
from backend.ml import health_risk_predictor, pattern_detector
from backend.reports.health_report import generate_health_report
from backend.utils.file_parser import parse_csv, parse_json, parse_xml


def _parse_health_file(file_path: str | Path, file_format: str | None = None) -> pd.DataFrame:
    path = Path(file_path)
    format_hint = (file_format or path.suffix.lstrip(".")).lower()

    if format_hint == "json":
        return parse_json(path)
    if format_hint == "csv":
        return parse_csv(path)
    if format_hint == "xml":
        return parse_xml(path)

    raise ValueError("Unsupported file format. Use JSON, CSV, or XML.")


def _ensure_numeric_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for column in columns:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    return normalized


def _enrich_frame(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = _ensure_numeric_columns(
        frame,
        ["heart_rate", "steps", "sleep_hours", "calorie_intake", "bmi", "weight_kg", "height_m"],
    )
    if "date" not in enriched.columns:
        enriched["date"] = pd.date_range("2026-01-01", periods=len(enriched), freq="D")
    if "bmi" not in enriched.columns and {"weight_kg", "height_m"}.issubset(enriched.columns):
        enriched["bmi"] = enriched["weight_kg"] / (enriched["height_m"] ** 2)
    return enriched.dropna(subset=["heart_rate", "steps", "sleep_hours"], how="any")


def _generate_charts(frame: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}

    if {"date", "heart_rate"}.issubset(frame.columns):
        charts["heart_rate"] = plot_heart_rate_trends(frame, output_dir / "heart_rate_trends.png")
    if {"date", "steps"}.issubset(frame.columns):
        charts["steps"] = plot_steps_over_time(frame, output_dir / "steps_over_time.png")
    if {"date", "calorie_intake"}.issubset(frame.columns):
        charts["calories"] = plot_calorie_intake(frame, output_dir / "calorie_intake.png")
    if {"date", "sleep_hours"}.issubset(frame.columns):
        charts["sleep"] = plot_sleep_hours(frame, output_dir / "sleep_hours.png")

    return charts


def run_health_monitoring_workflow(
    file_path: str | Path,
    question: str = "Summarize my health trends and risks.",
    patient_name: str = "Unknown",
    file_format: str | None = None,
    report_format: str = "json",
    output_dir: str | Path | None = None,
) -> dict:
    base_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="healthcare_workflow_"))
    parsed = _parse_health_file(file_path, file_format=file_format)
    frame = _enrich_frame(parsed)

    if frame.empty:
        raise ValueError("No usable health records were found in the uploaded file.")

    anomaly_input = frame[[column for column in ["heart_rate", "sleep_hours", "steps"] if column in frame.columns]]
    anomaly_results = pattern_detector.detect_anomalies(anomaly_input)

    if "bmi" not in frame.columns:
        frame["bmi"] = 24.0
    prediction_input = frame[[column for column in ["bmi", "heart_rate", "steps"] if column in frame.columns]]
    risk_results = health_risk_predictor.predict(prediction_input)

    charts = _generate_charts(frame, base_dir / "charts")

    latest = frame.iloc[-1]
    avg_steps = float(frame["steps"].mean()) if "steps" in frame.columns else 0.0
    avg_sleep = float(frame["sleep_hours"].mean()) if "sleep_hours" in frame.columns else 0.0
    recommendations = [
        goal_recommendation("daily_steps", avg_steps, DEFAULT_GOALS["daily_steps"]),
        goal_recommendation("sleep_hours", avg_sleep, DEFAULT_GOALS["sleep_hours"]),
    ]

    predicted_risk = {
        "anomaly_count": int(anomaly_results["anomaly_flag"].sum()),
        "latest_prediction": risk_results.iloc[-1].to_dict(),
        "step_goal_progress": progress_percentage(avg_steps, DEFAULT_GOALS["daily_steps"]),
        "sleep_goal_progress": progress_percentage(avg_sleep, DEFAULT_GOALS["sleep_hours"]),
    }

    report_suffix = "pdf" if report_format.lower() == "pdf" else "json"
    report_path = base_dir / f"health_report.{report_suffix}"
    report = generate_health_report(
        patient_name=patient_name,
        bmi=float(latest.get("bmi", 0.0)),
        trends={
            "heart_rate": float(latest.get("heart_rate", 0.0)),
            "steps": float(latest.get("steps", 0.0)),
            "sleep_hours": float(latest.get("sleep_hours", 0.0)),
            "calorie_intake": float(latest.get("calorie_intake", 0.0)),
        },
        predicted_risk=predicted_risk,
        recommendations=recommendations,
        output_format=report_format,
        output_path=report_path,
    )

    latest_vitals = {
        "heart_rate": int(latest.get("heart_rate", 72)),
        "blood_pressure": str(latest.get("blood_pressure", "120/80")),
    }
    agent_result = healthcare_agent.invoke(
        {
            "question": question,
            "patient_name": patient_name,
            "latest_vitals": latest_vitals,
            "bmi": float(latest.get("bmi", 24.0)),
            "steps": int(latest.get("steps", 0)),
            "sleep_hours": float(latest.get("sleep_hours", 0.0)),
            "calorie_intake": int(latest.get("calorie_intake", 0)),
            "output_format": report_format,
            "output_path": str(report_path),
        }
    )

    return {
        "parsed_rows": int(len(frame)),
        "anomaly_count": int(anomaly_results["anomaly_flag"].sum()),
        "charts": charts,
        "report_path": report.get("report_path"),
        "agent_response": agent_result["response"],
    }
