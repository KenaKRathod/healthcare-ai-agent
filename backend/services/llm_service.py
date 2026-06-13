import json
import logging

from backend.core.llm_config import llm_settings
from backend.services.medical_rag_service import format_rag_context

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = """You are AuraHealth AI, a healthcare support assistant.

Rules:
- Provide educational, supportive guidance only. Never claim to diagnose or prescribe.
- Use patient context, tool outputs, and retrieved medical references when available.
- If information is uncertain or outside scope, say so and recommend consulting a licensed clinician.
- Do not invent vitals, lab values, or medication names not present in the provided context.
- Keep responses concise, empathetic, and actionable.
- For emergencies, direct the user to local emergency services immediately.
"""


def _history_to_messages(history: list[dict]) -> list[dict]:
    messages = []
    for item in history[-llm_settings.max_history_messages :]:
        role = item.get("role", "user")
        if role not in {"user", "assistant", "system"}:
            role = "user"
        content = str(item.get("content", "")).strip()
        if content:
            messages.append({"role": role, "content": content})
    return messages


def build_user_prompt(
    question: str,
    patient_name: str,
    tool_context: dict,
    rag_chunks: list[dict],
    latest_vitals: dict | None,
    health_context: dict | None = None,
) -> str:
    payload = {
        "patient_alias": patient_name,
        "question": question,
        "latest_vitals": latest_vitals or {},
        "stored_health_context": health_context or {},
        "tool_outputs": tool_context,
        "retrieved_medical_references": format_rag_context(rag_chunks),
    }
    return (
        "Use the following JSON context to answer the patient question.\n"
        f"{json.dumps(payload, ensure_ascii=True, indent=2)}"
    )


def generate_llm_response(
    question: str,
    patient_name: str,
    tool_context: dict,
    rag_chunks: list[dict],
    conversation_history: list[dict],
    latest_vitals: dict | None = None,
    health_context: dict | None = None,
) -> str | None:
    """Call configured LLM provider. Returns None when LLM is disabled or unavailable."""
    if not llm_settings.enabled or not llm_settings.api_key:
        return None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            api_key=llm_settings.api_key,
            base_url=llm_settings.base_url,
            model=llm_settings.model,
            temperature=llm_settings.temperature,
            max_tokens=llm_settings.max_tokens,
        )

        history_messages = _history_to_messages(conversation_history)
        prompt = build_user_prompt(
            question=question,
            patient_name=patient_name,
            tool_context=tool_context,
            rag_chunks=rag_chunks,
            latest_vitals=latest_vitals,
            health_context=health_context,
        )

        messages = [SystemMessage(content=SAFETY_SYSTEM_PROMPT)]
        for item in history_messages:
            if item["role"] == "assistant":
                from langchain_core.messages import AIMessage

                messages.append(AIMessage(content=item["content"]))
            elif item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
        messages.append(HumanMessage(content=prompt))

        response = llm.invoke(messages)
        text = getattr(response, "content", None)
        if isinstance(text, list):
            text = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in text
            )
        return str(text).strip() if text else None
    except Exception:
        logger.exception("LLM generation failed; falling back to template response.")
        return None
