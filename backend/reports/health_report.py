import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def build_health_report(
    patient_name: str,
    bmi: float | None,
    trends: dict | None,
    predicted_risk: dict | None,
    recommendations: list[str] | None,
    goal_statuses: list[dict] | None = None,
    interactions: list[dict] | None = None,
    insights: list[str] | None = None,
    journey_summary: dict | None = None,
) -> dict:
    return {
        "patient_name": patient_name,
        "bmi": bmi,
        "trends": trends or {},
        "predicted_risk": predicted_risk or {},
        "recommendations": recommendations or [],
        "goal_statuses": goal_statuses or [],
        "interactions": interactions or [],
        "insights": insights or [],
        "journey_summary": journey_summary or {},
    }


def export_json_report(report: dict, output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(path)


def export_pdf_report(report: dict, output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"Patient: {report.get('patient_name', 'Unknown')}",
        f"BMI: {report.get('bmi', 'N/A')}",
        f"Predicted Risk: {json.dumps(report.get('predicted_risk', {}), indent=2)}",
        f"Trends: {json.dumps(report.get('trends', {}), indent=2)}",
        f"Goal Statuses: {json.dumps(report.get('goal_statuses', []), indent=2)}",
        f"Medication Interactions: {json.dumps(report.get('interactions', []), indent=2)}",
        f"Insights: {json.dumps(report.get('insights', []), indent=2)}",
        f"Journey Summary: {json.dumps(report.get('journey_summary', {}), indent=2)}",
        "Recommendations:",
    ]
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.extend([f"- {item}" for item in recommendations])
    else:
        lines.append("- No recommendations available.")

    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(textwrap.wrap(line, width=90) or [""])

    figure = plt.figure(figsize=(8.27, 11.69))
    figure.patch.set_facecolor("white")
    plt.axis("off")
    plt.text(
        0.05,
        0.98,
        "\n".join(wrapped_lines),
        va="top",
        ha="left",
        fontsize=10,
        family="monospace",
    )
    plt.tight_layout()

    with PdfPages(path) as pdf:
        pdf.savefig(figure, bbox_inches="tight")
    plt.close(figure)
    return str(path)


def generate_health_report(
    patient_name: str,
    bmi: float | None,
    trends: dict | None,
    predicted_risk: dict | None,
    recommendations: list[str] | None,
    goal_statuses: list[dict] | None = None,
    interactions: list[dict] | None = None,
    insights: list[str] | None = None,
    journey_summary: dict | None = None,
    output_format: str = "json",
    output_path: str | Path | None = None,
) -> dict:
    report = build_health_report(
        patient_name=patient_name,
        bmi=bmi,
        trends=trends,
        predicted_risk=predicted_risk,
        recommendations=recommendations,
        goal_statuses=goal_statuses,
        interactions=interactions,
        insights=insights,
        journey_summary=journey_summary,
    )

    report_format = output_format.lower()
    if output_path:
        if report_format == "pdf":
            generated_path = export_pdf_report(report, output_path)
        else:
            generated_path = export_json_report(report, output_path)
        report["report_path"] = generated_path
        report["output_format"] = report_format

    return report
