from pathlib import Path

import pandas as pd
from langgraph.graph import START, StateGraph

from backend.agents.state import HealthAgentState
from backend.ml import health_risk_predictor, pattern_detector, risk_model
from backend.reports.health_report import generate_health_report
from backend.tools import (
    analyze_symptoms,
    calorie_analysis,
    calculate_bmi,
    check_interactions,
    nutrition_recommendation,
    summarize_vitals,
)


def detect_intent(state: HealthAgentState) -> HealthAgentState:
    question = state.get("question", "").lower()

    if any(keyword in question for keyword in ["symptom", "fever", "pain", "cough", "headache"]):
        intent = "symptom"
    elif any(keyword in question for keyword in ["medication", "drug", "tablet", "interaction"]):
        intent = "medication"
    elif any(keyword in question for keyword in ["diet", "nutrition", "calorie", "meal"]):
        intent = "nutrition"
    elif any(keyword in question for keyword in ["fitness", "bmi", "exercise", "steps", "workout"]):
        intent = "fitness"
    else:
        intent = "general"

    return {"intent": intent}


def select_tool(state: HealthAgentState) -> HealthAgentState:
    tool_map = {
        "symptom": "symptom_checker",
        "medication": "medication_tool",
        "nutrition": "nutrition_tool",
        "fitness": "fitness_tool",
        "general": "health_summary",
    }
    return {"selected_tool": tool_map[state.get("intent", "general")]}


def _extract_symptoms(question: str) -> list[str]:
    known_symptoms = ["fever", "cough", "headache", "fatigue", "chest pain"]
    lowered = question.lower()
    return [symptom for symptom in known_symptoms if symptom in lowered]


def run_health_analysis(state: HealthAgentState) -> HealthAgentState:
    selected_tool = state.get("selected_tool", "health_summary")
    question = state.get("question", "")
    latest_vitals = state.get("latest_vitals")
    tool_result: dict | list | str
    recommendations: list[str] = []

    if selected_tool == "symptom_checker":
        symptoms = state.get("symptoms") or _extract_symptoms(question)
        tool_result = analyze_symptoms(symptoms or ["fatigue"])
        recommendations = [
            "Monitor symptoms closely.",
            "Seek urgent care for severe chest pain, confusion, or breathing difficulty.",
        ]
    elif selected_tool == "medication_tool":
        medications = state.get("medications") or ["warfarin", "ibuprofen"]
        tool_result = check_interactions(medications)
        recommendations = [
            "Confirm interaction findings with a licensed clinician or pharmacist.",
            "Keep an up-to-date medication list.",
        ]
    elif selected_tool == "nutrition_tool":
        calorie_intake = int(state.get("calorie_intake", 2000))
        tool_result = {
            "calorie_analysis": calorie_analysis(calorie_intake, 2000),
            "recommendations": nutrition_recommendation("maintenance"),
        }
        recommendations = nutrition_recommendation("maintenance")
    elif selected_tool == "fitness_tool":
        bmi_value = state.get("bmi")
        if bmi_value is None and state.get("weight_kg") and state.get("height_m"):
            bmi_value = calculate_bmi(float(state["weight_kg"]), float(state["height_m"]))["bmi"]
        tool_result = {
            "bmi": bmi_value,
            "steps": state.get("steps", 0),
            "vitals": summarize_vitals(latest_vitals),
        }
        recommendations = [
            "Aim for regular daily movement.",
            "Track heart rate, steps, and recovery consistently.",
        ]
    else:
        tool_result = summarize_vitals(latest_vitals)
        recommendations = ["Maintain regular monitoring and consult a clinician for persistent concerns."]

    return {
        "tool_result": tool_result,
        "vital_summary": summarize_vitals(latest_vitals) if latest_vitals else "No recent vitals are on file.",
        "recommendations": recommendations,
    }


def run_ml_analysis(state: HealthAgentState) -> HealthAgentState:
    latest_vitals = state.get("latest_vitals") or {}
    heart_rate = int(latest_vitals.get("heart_rate", 72))
    blood_pressure = str(latest_vitals.get("blood_pressure", "120/80"))
    steps = int(state.get("steps", 7000))
    sleep_hours = float(state.get("sleep_hours", 7.0))
    bmi_value = float(state.get("bmi", 24.0))

    risk_prediction = risk_model.predict(heart_rate=heart_rate, blood_pressure=blood_pressure)
    anomaly_frame = pd.DataFrame(
        [{"heart_rate": heart_rate, "sleep_hours": sleep_hours, "steps": steps}]
    )
    anomaly_result = pattern_detector.detect_anomalies(anomaly_frame).iloc[0].to_dict()

    risk_frame = pd.DataFrame([{"bmi": bmi_value, "heart_rate": heart_rate, "steps": steps}])
    prediction_result = health_risk_predictor.predict(risk_frame).iloc[0].to_dict()

    return {
        "prediction": risk_prediction,
        "ml_prediction": {
            "anomaly_flag": bool(anomaly_result["anomaly_flag"]),
            "anomaly_score": float(anomaly_result["anomaly_score"]),
            "risk_predictions": prediction_result,
        },
    }


def generate_report_node(state: HealthAgentState) -> HealthAgentState:
    latest_vitals = state.get("latest_vitals") or {}
    report = generate_health_report(
        patient_name=state.get("patient_name", "Unknown"),
        bmi=state.get("bmi"),
        trends={
            "heart_rate": latest_vitals.get("heart_rate"),
            "steps": state.get("steps"),
            "sleep_hours": state.get("sleep_hours"),
            "calorie_intake": state.get("calorie_intake"),
        },
        predicted_risk={
            "baseline": state.get("prediction", {}),
            "ml_prediction": state.get("ml_prediction", {}),
        },
        recommendations=state.get("recommendations", []),
        output_format=state.get("output_format", "json"),
        output_path=state.get("output_path"),
    )
    update = {"report": report}
    if report.get("report_path"):
        update["report_path"] = report["report_path"]
    return update


def compose_response(state: HealthAgentState) -> HealthAgentState:
    report_path = state.get("report_path")
    response_parts = [
        f"Intent detected: {state.get('intent', 'general')}.",
        f"Tool used: {state.get('selected_tool', 'health_summary')}.",
        f"Summary: {state.get('vital_summary', 'No vitals available.')}",
        f"Risk: {state.get('prediction', {}).get('risk_level', 'unknown')}.",
        "This is supportive guidance and not a medical diagnosis.",
    ]
    if report_path:
        response_parts.append(f"Report generated at: {Path(report_path).as_posix()}.")
    return {"response": " ".join(response_parts)}


graph = StateGraph(HealthAgentState)
graph.add_node("detect_intent", detect_intent)
graph.add_node("select_tool", select_tool)
graph.add_node("run_health_analysis", run_health_analysis)
graph.add_node("run_ml_analysis", run_ml_analysis)
graph.add_node("generate_report_node", generate_report_node)
graph.add_node("compose_response", compose_response)
graph.add_edge(START, "detect_intent")
graph.add_edge("detect_intent", "select_tool")
graph.add_edge("select_tool", "run_health_analysis")
graph.add_edge("run_health_analysis", "run_ml_analysis")
graph.add_edge("run_ml_analysis", "generate_report_node")
graph.add_edge("generate_report_node", "compose_response")
graph.set_finish_point("compose_response")

healthcare_agent = graph.compile()
