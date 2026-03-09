from langgraph.graph import StateGraph

def health_agent(state):
    if not isinstance(state, dict):
        raise ValueError("State must be a dictionary.")

    question = state.get("question")
    if not question:
        raise ValueError("Missing question in state.")

    response = "AI health assistant response"

    return {"response": response}
