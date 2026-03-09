from langgraph.graph import StateGraph


class HealthState(dict):
    question: str
    response: str


def health_analysis(state: HealthState):
    question = state["question"]

    if "heart rate" in question.lower():
        response = "Normal resting heart rate is 60-100 bpm."
    elif "blood pressure" in question.lower():
        response = "Normal blood pressure is around 120/80."
    else:
        response = "Please consult a doctor for accurate advice."

    return {"response": response}


graph = StateGraph(HealthState)
graph.add_node("health_analysis", health_analysis)
graph.set_entry_point("health_analysis")
health_agent = graph.compile()
