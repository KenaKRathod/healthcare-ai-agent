from pathlib import Path

import pandas as pd
from langgraph.graph import START, StateGraph

from backend.agents.state import HealthAgentState
from backend.ml import health_risk_predictor, pattern_detector, risk_model
from backend.reports.health_report import generate_health_report
from backend.services.intent_router import intent_to_tool, route_intent
from backend.services.llm_service import generate_llm_response
from backend.services.medical_rag_service import search_medical_context_vector
from backend.tools import (
    analyze_symptoms,
    calorie_analysis,
    calculate_bmi,
    check_interactions,
    latest_guidelines,
    nutrition_recommendation,
    search_medical_information,
    summarize_vitals,
    treatment_options,
    lookup_indian_food,
    lookup_ayurvedic_herb,
    check_drug_herb_interaction,
    lookup_pincode_doctor,
)


def detect_intent(state: HealthAgentState) -> HealthAgentState:
    question = state.get("question", "")
    intent, router_mode = route_intent(
        question,
        conversation_history=state.get("conversation_history", []),
    )
    return {"intent": intent, "intent_router_used": router_mode}


def select_tool(state: HealthAgentState) -> HealthAgentState:
    return {"selected_tool": intent_to_tool(state.get("intent", "general"))}


def retrieve_rag_context(state: HealthAgentState) -> HealthAgentState:
    question = state.get("question", "")
    rag_chunks = state.get("rag_chunks") or search_medical_context_vector(question)
    return {"rag_chunks": rag_chunks}


def _extract_symptoms(question: str) -> list[str]:
    known_symptoms = ["fever", "cough", "headache", "fatigue", "chest pain"]
    lowered = question.lower()
    return [symptom for symptom in known_symptoms if symptom in lowered]


def _extract_research_topic(question: str) -> str:
    known_topics = ["hypertension", "diabetes", "asthma"]
    lowered = question.lower()
    for topic in known_topics:
        if topic in lowered:
            return topic
    return "hypertension"


def run_health_analysis(state: HealthAgentState) -> HealthAgentState:
    selected_tool = state.get("selected_tool", "health_summary")
    question = state.get("question", "")
    latest_vitals = state.get("latest_vitals")
    tool_result: dict | list | str
    recommendations: list[str] = []
    medication_interactions = []

    if selected_tool == "ayurvedic_tool":
        topic = state.get("topic") or question
        tool_result = lookup_ayurvedic_herb(topic)
        recommendations = [
            tool_result.get("diet_lifestyle_recommendations", "Follow standard Ayurvedic guidelines."),
            tool_result.get("yoga_physical_therapy", "Practice pranayama and gentle stretching.")
        ]
    elif selected_tool == "doctor_pincode_tool":
        import re
        pincodes = re.findall(r"\b\d{6}\b", question)
        pincode = pincodes[0] if pincodes else "560034"
        tool_result = lookup_pincode_doctor(pincode)
        recommendations = ["Consult a registered medical professional for symptoms and medical diagnoses."]
    elif selected_tool == "symptom_checker":
        symptoms = state.get("symptoms") or _extract_symptoms(question)
        tool_result = analyze_symptoms(symptoms or ["fatigue"])
        recommendations = [
            "Monitor symptoms closely.",
            "Seek urgent care for severe chest pain, confusion, or breathing difficulty.",
        ]
    elif selected_tool == "medication_tool":
        medications = state.get("medications") or ["warfarin", "ibuprofen"]
        
        # Check standard allopathic interactions
        allopathic_interactions = check_interactions(medications)
        
        # Check drug-herb interactions
        herbs = [m for m in medications if m.lower() in ["ashwagandha", "arjuna", "tulsi", "gudmar", "jamun", "turmeric", "ginger"]]
        drugs = [m for m in medications if m.lower() not in herbs]
        herb_interactions = check_drug_herb_interaction(drugs, herbs)
        
        tool_result = {
            "allopathic_interactions": allopathic_interactions,
            "drug_herb_interactions": herb_interactions
        }
        medication_interactions = allopathic_interactions + herb_interactions
        
        recommendations = [
            "Confirm interaction findings with a licensed clinician or pharmacist.",
            "Keep an up-to-date medication list.",
        ]
        for item in herb_interactions:
            recommendations.append(f"Warning: {item['warning']}")
    elif selected_tool == "nutrition_tool":
        # Check if they asked about a specific food
        food_lookup = None
        for word in question.split():
            clean_word = word.strip("?,.!")
            if len(clean_word) > 3:
                res = lookup_indian_food(clean_word)
                if "error" not in res and "message" not in res:
                    food_lookup = res
                    break
        
        calorie_intake = int(state.get("calorie_intake", 2000))
        tool_result = {
            "calorie_analysis": calorie_analysis(calorie_intake, 2000),
            "recommendations": nutrition_recommendation("maintenance"),
            "indian_food_lookup": food_lookup
        }
        recommendations = nutrition_recommendation("maintenance")
        if food_lookup:
            recommendations.append(
                f"Nutritional facts for {food_lookup['food_name']}: "
                f"{food_lookup['calories_kcal']} kcal, P: {food_lookup['protein_g']}g, "
                f"C: {food_lookup['carbohydrates_g']}g, F: {food_lookup['fats_g']}g."
            )
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
    elif selected_tool == "research_tool":
        topic = state.get("topic") or _extract_research_topic(question)
        tool_result = {
            "topic": topic,
            "summary": search_medical_information(topic),
            "guidelines": latest_guidelines(topic),
            "treatment_options": treatment_options(topic),
        }
        recommendations = [
            "Use evidence summaries to prepare questions for your clinician.",
            "Do not replace professional care with general research guidance.",
        ]
    else:
        tool_result = summarize_vitals(latest_vitals)
        recommendations = ["Maintain regular monitoring and consult a clinician for persistent concerns."]

    return {
        "tool_result": tool_result,
        "vital_summary": summarize_vitals(latest_vitals) if latest_vitals else "No recent vitals are on file.",
        "recommendations": recommendations,
        "research_summary": tool_result if selected_tool == "research_tool" else {},
        "interactions": medication_interactions if selected_tool == "medication_tool" else state.get("interactions", []),
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
    predictive_summary = {
        "baseline_risk_level": risk_prediction["risk_level"],
        "baseline_risk_score": float(risk_prediction["risk_score"]),
        "anomaly_flag": bool(anomaly_result["anomaly_flag"]),
        "anomaly_score": float(anomaly_result["anomaly_score"]),
        "projected_health_risks": prediction_result,
    }

    return {
        "prediction": risk_prediction,
        "ml_prediction": {
            "anomaly_flag": bool(anomaly_result["anomaly_flag"]),
            "anomaly_score": float(anomaly_result["anomaly_score"]),
            "risk_predictions": prediction_result,
        },
        "predictive_summary": predictive_summary,
    }


def build_insights_node(state: HealthAgentState) -> HealthAgentState:
    prediction = state.get("prediction", {})
    predictive_summary = state.get("predictive_summary", {})
    goal_statuses = state.get("goal_statuses", [])
    journey_summary = state.get("journey_summary", {})

    insights = [
        f"Current baseline risk is {prediction.get('risk_level', 'unknown')}.",
        f"Anomaly flag is {'on' if predictive_summary.get('anomaly_flag') else 'off'}.",
    ]
    for goal in goal_statuses[:3]:
        insights.append(f"{goal.get('goal_name', 'goal')} progress is {goal.get('progress_percent', 0):.2f}%.")
    if journey_summary:
        insights.append(
            f"Health journey trend is {journey_summary.get('risk_trend', 'unknown')} across "
            f"{journey_summary.get('snapshot_count', 0)} snapshot(s)."
        )
    if state.get("research_summary"):
        insights.append("Research guidance was included for the requested condition.")
    return {"insights": insights}


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
            "predictive_summary": state.get("predictive_summary", {}),
        },
        recommendations=state.get("recommendations", []),
        goal_statuses=state.get("goal_statuses", []),
        interactions=state.get("interactions", []),
        insights=state.get("insights", []),
        output_format=state.get("output_format", "json"),
        output_path=state.get("output_path"),
    )
    update = {"report": report}
    if report.get("report_path"):
        update["report_path"] = report["report_path"]
    return update


def _build_template_response(state: HealthAgentState) -> str:
    report_path = state.get("report_path")
    selected_tool = state.get("selected_tool", "health_summary")
    tool_result = state.get("tool_result")

    response_parts = [
        f"Intent detected: {state.get('intent', 'general')}.",
        f"Tool used: {selected_tool}.",
        f"Summary: {state.get('vital_summary', 'No vitals available.')}",
        f"Risk: {state.get('prediction', {}).get('risk_level', 'unknown')}.",
        f"Trend: {state.get('journey_summary', {}).get('risk_trend', 'unknown')}.",
        "This is supportive guidance and not a medical diagnosis.",
    ]
    
    # Append Ayurvedic details
    if selected_tool == "ayurvedic_tool" and isinstance(tool_result, dict):
        if "ayurvedic_herbs" in tool_result:
            response_parts.append(
                f"\n[Ayurvedic Recommendation for {tool_result.get('disease')}]:\n"
                f"- Recommended Herbs: {tool_result.get('ayurvedic_herbs')}\n"
                f"- Dosage/Formulation: {tool_result.get('formulation')}\n"
                f"- Calibrated Doshas: {tool_result.get('doshas')}\n"
                f"- Diet & Lifestyle Guidance: {tool_result.get('diet_lifestyle_recommendations')}\n"
                f"- Suggested Yoga & Therapy: {tool_result.get('yoga_physical_therapy')}"
            )
            
    # Append Doctor Pincode details
    elif selected_tool == "doctor_pincode_tool" and isinstance(tool_result, dict):
        doctors_list = tool_result.get("doctors", [])
        if doctors_list:
            doc_lines = [f"  * {d['name']} ({d['specialty']} at {d['clinic']}) - Tel: {d['phone']} Address: {d['address']}" for d in doctors_list]
            doc_str = "\n".join(doc_lines)
            response_parts.append(
                f"\n[Doctor Locator in {tool_result.get('region_detected')} (Pincode {tool_result.get('pincode')}):\n"
                f"{doc_str}"
            )
            
    # Append Indian Food Lookup details
    elif selected_tool == "nutrition_tool" and isinstance(tool_result, dict):
        food_lookup = tool_result.get("indian_food_lookup")
        if food_lookup:
            response_parts.append(
                f"\n[Indian Food Nutritional Details for {food_lookup['food_name']}]:\n"
                f"- Calories: {food_lookup['calories_kcal']} kcal\n"
                f"- Carbohydrates: {food_lookup['carbohydrates_g']}g\n"
                f"- Protein: {food_lookup['protein_g']}g\n"
                f"- Fats: {food_lookup['fats_g']}g\n"
                f"- Fibre: {food_lookup['fibre_g']}g\n"
                f"- Sodium: {food_lookup['sodium_mg']}mg"
            )
            
    # Append Drug-Herb Interactions details
    elif selected_tool == "medication_tool" and isinstance(tool_result, dict):
        herb_interactions = tool_result.get("drug_herb_interactions", [])
        if herb_interactions:
            warnings = [f"  * Warning: {item['warning']}" for item in herb_interactions]
            warnings_str = "\n".join(warnings)
            response_parts.append(f"\n[Drug-Herb Interaction Alerts]:\n{warnings_str}")

    if state.get("research_summary"):
        response_parts.append("Research guidance was added to the response.")
    if report_path:
        response_parts.append(f"Report generated at: {Path(report_path).as_posix()}.")
    return " ".join(response_parts)


def compose_response(state: HealthAgentState) -> HealthAgentState:
    tool_context = {
        "intent": state.get("intent"),
        "selected_tool": state.get("selected_tool"),
        "tool_result": state.get("tool_result"),
        "vital_summary": state.get("vital_summary"),
        "recommendations": state.get("recommendations", []),
        "insights": state.get("insights", []),
        "predictive_summary": state.get("predictive_summary", {}),
        "journey_summary": state.get("journey_summary", {}),
        "interactions": state.get("interactions", []),
    }
    rag_chunks = state.get("rag_chunks", [])
    llm_response = generate_llm_response(
        question=state.get("question", ""),
        patient_name=state.get("patient_name", "Unknown"),
        tool_context=tool_context,
        rag_chunks=rag_chunks,
        conversation_history=state.get("conversation_history", []),
        latest_vitals=state.get("latest_vitals"),
        health_context=state.get("health_context", {}),
    )
    if llm_response:
        return {"response": llm_response, "llm_used": True}
    return {"response": _build_template_response(state), "llm_used": False}


graph = StateGraph(HealthAgentState)
graph.add_node("detect_intent", detect_intent)
graph.add_node("select_tool", select_tool)
graph.add_node("retrieve_rag_context", retrieve_rag_context)
graph.add_node("run_health_analysis", run_health_analysis)
graph.add_node("run_ml_analysis", run_ml_analysis)
graph.add_node("build_insights_node", build_insights_node)
graph.add_node("generate_report_node", generate_report_node)
graph.add_node("compose_response", compose_response)
graph.add_edge(START, "detect_intent")
graph.add_edge("detect_intent", "select_tool")
graph.add_edge("select_tool", "retrieve_rag_context")
graph.add_edge("retrieve_rag_context", "run_health_analysis")
graph.add_edge("run_health_analysis", "run_ml_analysis")
graph.add_edge("run_ml_analysis", "build_insights_node")
graph.add_edge("build_insights_node", "generate_report_node")
graph.add_edge("generate_report_node", "compose_response")
graph.set_finish_point("compose_response")

healthcare_agent = graph.compile()
