import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.core.llm_config import llm_settings
from backend.models import ChatConversation, ChatFeedback, ChatMessage, HealthGoal, PatientProfile, User


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_health_context(
    db: Session,
    patient_name: str,
    latest_vitals: dict | None = None,
) -> dict:
    """Assemble non-diagnostic health context for follow-up conversations."""
    profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.patient_name == patient_name)
        .first()
    )
    goals = (
        db.query(HealthGoal)
        .filter(HealthGoal.patient_name == patient_name)
        .order_by(HealthGoal.id.desc())
        .limit(5)
        .all()
    )
    return {
        "patient_name": patient_name,
        "latest_vitals": latest_vitals or {},
        "profile": {
            "age": profile.age if profile else None,
            "gender": profile.gender if profile else None,
            "dietary_preference": profile.dietary_preference if profile else None,
            "physical_activity": profile.physical_activity if profile else None,
            "family_history": profile.family_history if profile else None,
        },
        "active_goals": [
            {
                "goal_name": goal.goal_name,
                "target_value": goal.target_value,
                "unit": goal.unit,
            }
            for goal in goals
        ],
    }


def update_conversation_health_context(
    db: Session,
    conversation_id: int,
    health_context: dict,
) -> None:
    conversation = db.query(ChatConversation).filter(ChatConversation.id == conversation_id).first()
    if not conversation:
        return
    conversation.health_context_json = json.dumps(health_context, ensure_ascii=True)
    conversation.updated_at = _now()
    db.commit()


def load_conversation_health_context(conversation: ChatConversation) -> dict:
    raw = conversation.health_context_json
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def get_or_create_conversation(
    db: Session,
    user: User,
    patient_name: str,
    conversation_id: int | None = None,
) -> ChatConversation:
    if conversation_id:
        conversation = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user.id,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found or access denied.")
        return conversation

    title = f"Chat with {patient_name}"
    conversation = ChatConversation(
        user_id=user.id,
        patient_name=patient_name,
        title=title,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def load_conversation_history(db: Session, conversation_id: int, user: User) -> list[dict]:
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user.id,
        )
        .first()
    )
    if not conversation:
        raise ValueError("Conversation not found or access denied.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history = [{"role": message.role, "content": message.content} for message in messages]
    return history[-llm_settings.max_history_messages :]


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    intent: str | None = None,
    selected_tool: str | None = None,
    metadata: dict | None = None,
) -> ChatMessage:
    message = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        intent=intent,
        selected_tool=selected_tool,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=True),
        created_at=_now(),
    )
    db.add(message)
    conversation = db.query(ChatConversation).filter(ChatConversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = _now()
    db.commit()
    db.refresh(message)
    return message


def list_user_conversations(db: Session, user: User, limit: int = 20) -> list[ChatConversation]:
    return (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user.id)
        .order_by(ChatConversation.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_conversation_messages(db: Session, conversation_id: int, user: User) -> list[ChatMessage]:
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user.id,
        )
        .first()
    )
    if not conversation:
        raise ValueError("Conversation not found or access denied.")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )


def _find_user_query_for_assistant_message(db: Session, assistant_message: ChatMessage) -> str | None:
    prior_user_message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == assistant_message.conversation_id,
            ChatMessage.role == "user",
            ChatMessage.id < assistant_message.id,
        )
        .order_by(ChatMessage.id.desc())
        .first()
    )
    return prior_user_message.content if prior_user_message else None


def save_feedback(
    db: Session,
    user: User,
    message_id: int,
    rating: int,
    comment: str | None = None,
) -> ChatFeedback:
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise ValueError("Message not found.")
    if message.role != "assistant":
        raise ValueError("Feedback is only accepted for assistant messages.")

    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == message.conversation_id,
            ChatConversation.user_id == user.id,
        )
        .first()
    )
    if not conversation:
        raise ValueError("You do not have permission to rate this message.")

    user_query = _find_user_query_for_assistant_message(db, message)
    response_text = message.content

    existing = (
        db.query(ChatFeedback)
        .filter(ChatFeedback.message_id == message_id, ChatFeedback.user_id == user.id)
        .first()
    )
    if existing:
        existing.rating = rating
        existing.comment = comment
        existing.query = user_query
        existing.response = response_text
        existing.created_at = _now()
        db.commit()
        db.refresh(existing)
        return existing

    feedback = ChatFeedback(
        message_id=message_id,
        user_id=user.id,
        query=user_query,
        response=response_text,
        rating=rating,
        comment=comment,
        created_at=_now(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
