from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import get_current_user
from backend.models import User
from backend.schemas.conversation import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageRead,
    ConversationSummary,
)
from backend.services.audit_service import log_audit_event
from backend.services.conversation_service import (
    get_conversation_messages,
    list_user_conversations,
    save_feedback,
)

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    conversations = list_user_conversations(db, current_user, limit=limit)
    return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageRead])
def read_conversation_messages(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        messages = get_conversation_messages(db, conversation_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return messages


@router.post("/ai-health-chat/feedback", response_model=ChatFeedbackResponse)
def submit_chat_feedback(
    payload: ChatFeedbackRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        feedback = save_feedback(
            db,
            user=current_user,
            message_id=payload.message_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_audit_event(
        db,
        username=current_user.username,
        role=current_user.role,
        action="WRITE",
        resource=f"ChatFeedback:{payload.message_id}",
        status="SUCCESS",
    )
    return feedback
