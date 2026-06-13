"""LLM-based intent router with rule-based fallback."""

import json
import logging
import re

from backend.core.llm_config import llm_settings

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "ayurveda",
    "doctor_pincode",
    "symptom",
    "medication",
    "nutrition",
    "fitness",
    "research",
    "general",
}

INTENT_TOOL_MAP = {
    "ayurveda": "ayurvedic_tool",
    "doctor_pincode": "doctor_pincode_tool",
    "symptom": "symptom_checker",
    "medication": "medication_tool",
    "nutrition": "nutrition_tool",
    "fitness": "fitness_tool",
    "research": "research_tool",
    "general": "health_summary",
}

ROUTER_SYSTEM_PROMPT = """You are an intent router for AuraHealth AI.
Classify the user health question into exactly one intent label.

Allowed intents:
- ayurveda: herbs, dosha, Ayurvedic remedies
- doctor_pincode: find doctors, clinics, hospitals by pincode/location
- symptom: fever, pain, cough, headache, symptom checking
- medication: drugs, tablets, prescriptions, interactions
- nutrition: diet, calories, meals, Indian food nutrition
- fitness: BMI, exercise, steps, workouts
- research: medical guidelines, treatment options, conditions, PubMed-style questions
- general: health summary, vitals overview, unclear queries

Return ONLY valid JSON:
{"intent":"one_of_allowed_intents","confidence":0.0}
"""


def _rule_based_intent(question: str) -> str:
    lowered = question.lower()
    if any(keyword in lowered for keyword in ["ayur", "herb", "tulsi", "ashwagandha", "remedy", "dosha", "prakriti"]):
        return "ayurveda"
    if any(keyword in lowered for keyword in ["doctor", "clinic", "hospital", "pincode", "pin code"]):
        return "doctor_pincode"
    if any(keyword in lowered for keyword in ["symptom", "fever", "pain", "cough", "headache"]):
        return "symptom"
    if any(keyword in lowered for keyword in ["medication", "drug", "tablet", "interaction"]):
        return "medication"
    if any(keyword in lowered for keyword in ["diet", "nutrition", "calorie", "meal", "food", "roti", "biryani"]):
        return "nutrition"
    if any(keyword in lowered for keyword in ["fitness", "bmi", "exercise", "steps", "workout"]):
        return "fitness"
    if any(keyword in lowered for keyword in ["research", "guideline", "treatment", "condition"]):
        return "research"
    return "general"


def _parse_router_json(text: str) -> str | None:
    try:
        payload = json.loads(text)
        intent = str(payload.get("intent", "")).strip().lower()
        if intent in VALID_INTENTS:
            return intent
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            payload = json.loads(match.group(0))
            intent = str(payload.get("intent", "")).strip().lower()
            if intent in VALID_INTENTS:
                return intent
        except json.JSONDecodeError:
            return None
    return None


def route_intent_with_llm(question: str, conversation_history: list[dict] | None = None) -> str | None:
    if not llm_settings.enabled or not llm_settings.api_key:
        return None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            api_key=llm_settings.api_key,
            base_url=llm_settings.base_url,
            model=llm_settings.router_model,
            temperature=0.0,
            max_tokens=120,
        )
        history_snippet = ""
        if conversation_history:
            recent = conversation_history[-4:]
            history_snippet = "\n".join(
                f"{item.get('role', 'user')}: {str(item.get('content', ''))[:200]}"
                for item in recent
            )

        user_prompt = (
            f"Recent conversation:\n{history_snippet or 'None'}\n\n"
            f"Current question:\n{question}"
        )
        response = llm.invoke(
            [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
        )
        text = getattr(response, "content", "")
        if isinstance(text, list):
            text = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in text
            )
        return _parse_router_json(str(text))
    except Exception:
        logger.exception("LLM intent routing failed; using rule-based fallback.")
        return None


def route_intent(question: str, conversation_history: list[dict] | None = None) -> tuple[str, str]:
    """Return (intent, router_mode) where router_mode is 'llm' or 'rules'."""
    llm_intent = None
    if llm_settings.use_llm_intent_router:
        llm_intent = route_intent_with_llm(question, conversation_history)
    if llm_intent:
        return llm_intent, "llm"
    return _rule_based_intent(question), "rules"


def intent_to_tool(intent: str) -> str:
    return INTENT_TOOL_MAP.get(intent, "health_summary")
