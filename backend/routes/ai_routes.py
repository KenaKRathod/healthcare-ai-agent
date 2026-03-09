from fastapi import APIRouter

from backend.health_agent import health_agent

router = APIRouter()


@router.post("/ai-health-chat")
def ai_chat(question: str):
    result = health_agent.invoke({"question": question})
    return {"response": result["response"]}
