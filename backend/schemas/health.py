from pydantic import BaseModel, ConfigDict, Field


class HealthDataCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    heart_rate: int
    blood_pressure: str = Field(max_length=15)


class HealthRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: str
    heart_rate: int
    blood_pressure: str


class AgentChatRequest(BaseModel):
    question: str = Field(min_length=3)
    patient_name: str | None = None
    latest_vitals: dict[str, str | int] | None = None
    bmi: float | None = None
    steps: int | None = None
    sleep_hours: float | None = None
    calorie_intake: int | None = None
    medications: list[str] | None = None
    symptoms: list[str] | None = None
    output_format: str = "json"
    output_path: str | None = None


class AgentChatResponse(BaseModel):
    response: str
    report_path: str | None = None
    intent: str | None = None
    selected_tool: str | None = None


class WorkflowResponse(BaseModel):
    parsed_rows: int
    anomaly_count: int
    charts: dict[str, str]
    report_path: str | None = None
    agent_response: str


class HealthReportResponse(BaseModel):
    patient_name: str
    bmi: float | None = None
    trends: dict
    predicted_risk: dict
    recommendations: list[str]
    report_path: str | None = None
    output_format: str | None = None


class HealthAnalyticsResponse(BaseModel):
    risk_summary: list[RiskSummary]
    vitals_chart: VitalsChart


class GoalStatus(BaseModel):
    goal_name: str
    current_value: float
    target_value: float
    progress_percent: float
    recommendation: str


class RiskSummary(BaseModel):
    patient_name: str
    heart_rate: int
    blood_pressure: str
    risk_level: str
    risk_score: float


class VitalsChart(BaseModel):
    title: str
    spec: dict
