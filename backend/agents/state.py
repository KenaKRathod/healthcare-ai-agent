from typing import TypedDict


class HealthAgentState(TypedDict, total=False):
    question: str
    patient_name: str
    latest_vitals: dict[str, str | int] | None
    bmi: float
    steps: int
    sleep_hours: float
    calorie_intake: int
    medications: list[str]
    symptoms: list[str]
    topic: str
    output_format: str
    output_path: str
    intent: str
    selected_tool: str
    tool_result: dict | list | str
    vital_summary: str
    recommendations: list[str]
    insights: list[str]
    goal_statuses: list[dict]
    interactions: list[dict[str, str]]
    journey_summary: dict
    predictive_summary: dict
    research_summary: dict[str, str | list[str]]
    prediction: dict[str, str | float]
    ml_prediction: dict[str, str | float | dict]
    report: dict
    report_path: str
    response: str
