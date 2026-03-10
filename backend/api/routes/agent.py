import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.schemas.health import AgentChatRequest, AgentChatResponse, WorkflowResponse
from backend.services.analytics_service import load_recent_patient_snapshot
from backend.health_agent import health_agent
from backend.services.workflow_service import run_health_monitoring_workflow

router = APIRouter()


@router.post("/ai-health-chat", response_model=AgentChatResponse)
def ai_chat(
    payload: AgentChatRequest,
    db: Annotated[Session, Depends(get_db)],
):
    latest_vitals = payload.latest_vitals or load_recent_patient_snapshot(
        db,
        patient_name=payload.patient_name,
    )
    request_payload = payload.model_dump(exclude_none=True)
    request_payload["latest_vitals"] = latest_vitals
    result = health_agent.invoke(request_payload)
    return AgentChatResponse(
        response=result["response"],
        report_path=result.get("report_path"),
        intent=result.get("intent"),
        selected_tool=result.get("selected_tool"),
    )


@router.post("/health-workflow", response_model=WorkflowResponse)
async def run_workflow(
    file: UploadFile = File(...),
    question: str = Form("Summarize my health trends and risks."),
    patient_name: str = Form("Unknown"),
    report_format: str = Form("json"),
):
    suffix = Path(file.filename or "health_data.csv").suffix or ".csv"
    temp_path = Path(tempfile.gettempdir()) / f"healthcare_upload{suffix}"
    content = await file.read()
    temp_path.write_bytes(content)

    result = run_health_monitoring_workflow(
        file_path=temp_path,
        question=question,
        patient_name=patient_name,
        report_format=report_format,
    )
    return WorkflowResponse(**result)


@router.post("/upload-health-data", response_model=WorkflowResponse)
async def upload_health_data(
    file: UploadFile = File(...),
    question: str = Form("Summarize my health trends and risks."),
    patient_name: str = Form("Unknown"),
    report_format: str = Form("json"),
):
    return await run_workflow(
        file=file,
        question=question,
        patient_name=patient_name,
        report_format=report_format,
    )
