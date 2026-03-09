from langgraph.graph import StateGraph

def health_agent(state):

    question = state["question"]

    response = "AI health assistant response"

    return {"response":response}