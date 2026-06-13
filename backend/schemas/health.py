from pydantic import BaseModel, ConfigDict, Field


class HealthDataCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    heart_rate: int
    blood_pressure: str = Field(max_length=15)
    age: int | None = None
    sex: str | None = Field(default=None, max_length=20)
    waist_cm: float | None = None
    activity: str | None = Field(default=None, max_length=50)
    family_diabetic: str | None = Field(default=None, max_length=50)
    fasting_blood_sugar: float | None = None
    postprandial_blood_sugar: float | None = None


class HealthRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_name: str
    heart_rate: int
    blood_pressure: str
    fasting_blood_sugar: float | None = None
    postprandial_blood_sugar: float | None = None
    age: int | None = None
    sex: str | None = None
    waist_cm: float | None = None
    activity: str | None = None
    family_diabetic: str | None = None
    idrs_score: int | None = None
    idrs_risk_level: str | None = None


class AgentChatRequest(BaseModel):
    question: str = Field(min_length=3)
    patient_name: str | None = None
    conversation_id: int | None = None
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
    predictive_summary: dict = {}
    journey_summary: dict = {}
    conversation_id: int | None = None
    message_id: int | None = None
    rag_sources: list[dict] = []
    llm_used: bool = False
    intent_router_used: str | None = None


class WorkflowResponse(BaseModel):
    parsed_rows: int
    anomaly_count: int
    charts: dict[str, str]
    report_path: str | None = None
    agent_response: str
    goal_statuses: list["GoalStatus"] = []
    interactions: list[dict[str, str]] = []
    insights: list[str] = []
    predictive_summary: dict = {}
    journey_summary: dict = {}


class HealthReportResponse(BaseModel):
    patient_name: str
    bmi: float | None = None
    trends: dict
    predicted_risk: dict
    recommendations: list[str]
    goal_statuses: list["GoalStatus"] = []
    interactions: list[dict[str, str]] = []
    insights: list[str] = []
    journey_summary: dict = {}
    report_path: str | None = None
    output_format: str | None = None


class HealthAnalyticsResponse(BaseModel):
    risk_summary: list["RiskSummary"]
    vitals_chart: "VitalsChart"


class GoalStatus(BaseModel):
    goal_id: int | None = None
    patient_name: str | None = None
    goal_name: str
    current_value: float
    target_value: float
    unit: str = ""
    progress_percent: float
    recommendation: str


class HealthGoalCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    goal_name: str = Field(min_length=1, max_length=100)
    target_value: float = Field(gt=0)
    unit: str = Field(default="", max_length=30)


class HealthGoalUpdate(BaseModel):
    target_value: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=30)


class RiskSummary(BaseModel):
    patient_name: str
    heart_rate: int
    blood_pressure: str
    risk_level: str
    risk_score: float


class VitalsChart(BaseModel):
    title: str
    spec: dict


class JourneySummaryResponse(BaseModel):
    patient_name: str
    snapshot_count: int
    latest_risk_level: str
    average_heart_rate: float
    average_steps: float
    average_sleep_hours: float
    average_bmi: float
    risk_trend: str
    latest_risk_score: float | None = None


WorkflowResponse.model_rebuild()
HealthReportResponse.model_rebuild()
HealthAnalyticsResponse.model_rebuild()
