from langgraph.graph import START, StateGraph

from backend.agents.state import HealthAgentState
from backend.ml.risk_model import risk_model
from backend.tools.health_tools import summarize_vitals


def collect_context(state: HealthAgentState) -> HealthAgentState:
    latest_vitals = state.get("latest_vitals")
    return {
        "vital_summary": summarize_vitals(latest_vitals) if latest_vitals else "No recent vitals are on file.",
    }


def run_risk_model(state: HealthAgentState) -> HealthAgentState:
    latest_vitals = state.get("latest_vitals")
    if not latest_vitals:
        return {"prediction": {"risk_level": "unknown", "risk_score": 0.0}}

    prediction = risk_model.predict(
        heart_rate=int(latest_vitals["heart_rate"]),
        blood_pressure=str(latest_vitals["blood_pressure"]),
    )
    return {"prediction": prediction}


def compose_response(state: HealthAgentState) -> HealthAgentState:
    question = state["question"]
    vital_summary = state.get("vital_summary", "No vitals available.")
    prediction = state.get("prediction", {"risk_level": "unknown", "risk_score": 0.0})
    response = (
        f"Question: {question}. "
        f"Vitals summary: {vital_summary} "
        f"Estimated risk: {prediction['risk_level']} "
        f"({prediction['risk_score']:.2f}). "
        "This is supportive guidance and not a medical diagnosis."
    )
    return {"response": response}


graph = StateGraph(HealthAgentState)
graph.add_node("collect_context", collect_context)
graph.add_node("run_risk_model", run_risk_model)
graph.add_node("compose_response", compose_response)
graph.add_edge(START, "collect_context")
graph.add_edge("collect_context", "run_risk_model")
graph.add_edge("run_risk_model", "compose_response")
graph.set_finish_point("compose_response")

health_agent = graph.compile()
