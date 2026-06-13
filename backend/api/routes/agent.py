import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User
from backend.schemas.health import AgentChatRequest, AgentChatResponse, WorkflowResponse
from backend.services.analytics_service import load_recent_patient_snapshot
from backend.health_agent import health_agent
from backend.services.workflow_service import run_health_monitoring_workflow
from backend.services.audit_service import log_audit_event
from backend.services.conversation_service import (
    build_health_context,
    get_or_create_conversation,
    load_conversation_health_context,
    load_conversation_history,
    save_message,
    update_conversation_health_context,
)

router = APIRouter()


@router.post("/ai-health-chat", response_model=AgentChatResponse)
def ai_chat(
    payload: AgentChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    target_patient = payload.patient_name
    if current_user.role == "patient":
        target_patient = current_user.username
        payload.patient_name = current_user.username

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="READ",
        resource=f"AIChat:{target_patient}",
        status="SUCCESS",
    )

    try:
        conversation = get_or_create_conversation(
            db,
            user=current_user,
            patient_name=target_patient or current_user.username,
            conversation_id=payload.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    conversation_history = load_conversation_history(db, conversation.id, current_user)

    save_message(
        db,
        conversation_id=conversation.id,
        role="user",
        content=payload.question,
    )

    latest_vitals = payload.latest_vitals or load_recent_patient_snapshot(
        db,
        patient_name=target_patient,
    )
    health_context = build_health_context(db, target_patient or current_user.username, latest_vitals)
    stored_context = load_conversation_health_context(conversation)
    merged_health_context = {**stored_context, **health_context}
    update_conversation_health_context(db, conversation.id, merged_health_context)

    request_payload = payload.model_dump(exclude_none=True)
    request_payload["latest_vitals"] = latest_vitals
    request_payload["conversation_history"] = conversation_history
    request_payload["health_context"] = merged_health_context
    request_payload["patient_name"] = target_patient or current_user.username

    alerts = []
    if latest_vitals and target_patient:
        from backend.services.alerts import check_and_trigger_alerts

        alerts = check_and_trigger_alerts(
            db,
            patient_name=target_patient,
            heart_rate=latest_vitals.get("heart_rate"),
            blood_pressure=latest_vitals.get("blood_pressure"),
            fasting_blood_sugar=latest_vitals.get("fasting_blood_sugar"),
            postprandial_blood_sugar=latest_vitals.get("postprandial_blood_sugar"),
        )

    result = health_agent.invoke(request_payload)
    rag_chunks = result.get("rag_chunks", [])

    response_text = result["response"]
    if alerts:
        response_text = "\n".join(alerts) + "\n\n" + response_text

    assistant_message = save_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        intent=result.get("intent"),
        selected_tool=result.get("selected_tool"),
        metadata={
            "llm_used": bool(result.get("llm_used")),
            "intent_router_used": result.get("intent_router_used"),
            "rag_source_ids": [chunk.get("id") for chunk in rag_chunks],
        },
    )

    return AgentChatResponse(
        response=response_text,
        report_path=result.get("report_path"),
        intent=result.get("intent"),
        selected_tool=result.get("selected_tool"),
        predictive_summary=result.get("predictive_summary", {}),
        journey_summary=result.get("journey_summary", {}),
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        rag_sources=rag_chunks,
        llm_used=bool(result.get("llm_used")),
        intent_router_used=result.get("intent_router_used"),
    )


@router.post("/health-workflow", response_model=WorkflowResponse)
async def run_workflow(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    question: str = Form("Summarize my health trends and risks."),
    patient_name: str = Form("Unknown"),
    report_format: str = Form("json"),
    db: Session = Depends(get_db),
):
    target_patient = patient_name
    if current_user.role == "patient":
        target_patient = current_user.username

    if db is not None:
        log_audit_event(
            db,
            username=current_user.username,
            role=current_user.role,
            action="WRITE",
            resource=f"HealthWorkflow:{target_patient}",
            status="SUCCESS",
        )

    suffix = Path(file.filename or "health_data.csv").suffix or ".csv"
    temp_path = Path(tempfile.gettempdir()) / f"healthcare_upload{suffix}"
    content = await file.read()
    temp_path.write_bytes(content)

    result = run_health_monitoring_workflow(
        file_path=temp_path,
        db=db,
        question=question,
        patient_name=target_patient,
        report_format=report_format,
    )
    return WorkflowResponse(**result)


@router.post("/upload-health-data", response_model=WorkflowResponse)
async def upload_health_data(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    question: str = Form("Summarize my health trends and risks."),
    patient_name: str = Form("Unknown"),
    report_format: str = Form("json"),
    db: Session = Depends(get_db),
):
    return await run_workflow(
        current_user=current_user,
        file=file,
        question=question,
        patient_name=patient_name,
        report_format=report_format,
        db=db,
    )
