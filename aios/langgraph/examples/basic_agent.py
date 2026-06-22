"""
Basic agent example using PHOENIX AIOS LangGraph framework.

Demonstrates:
- StateGraph construction
- Conditional routing
- Simple agent workflow
"""

from typing import TypedDict, Annotated
import operator
from aios.langgraph import StateGraph, START, END
from aios.langgraph.core.state import AgentState, append_reducer, StateReducer


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """Agent state with message history and result."""
    messages: Annotated[list[dict], operator.add]
    current_node: str
    result: str
    error: str


# ============================================================================
# Node Functions
# ============================================================================

def analyze(state: dict) -> dict:
    """Analyze the input and determine next step."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}

    content = last_message.get("content", "")
    has_question = "?" in content

    return {
        "current_node": "analyze",
        "result": "question" if has_question else "statement",
        "messages": [{"role": "system", "content": f"Analyzed: {len(content)} chars"}],
    }


def answer(state: dict) -> dict:
    """Answer a question."""
    return {
        "current_node": "answer",
        "result": "Here is the answer to your question.",
        "messages": [{"role": "assistant", "content": "Answered question."}],
    }


def acknowledge(state: dict) -> dict:
    """Acknowledge a statement."""
    return {
        "current_node": "acknowledge",
        "result": "I understand your statement.",
        "messages": [{"role": "assistant", "content": "Acknowledged statement."}],
    }


def error_handler(state: dict) -> dict:
    """Handle errors."""
    return {
        "current_node": "error_handler",
        "error": "",
        "messages": [{"role": "system", "content": "Error handled."}],
    }


# ============================================================================
# Routing Function
# ============================================================================

def route_after_analyze(state: dict) -> str:
    """Route based on analysis result."""
    result = state.get("result", "")

    if result == "question":
        return "answer"
    elif result == "statement":
        return "acknowledge"
    else:
        return "error_handler"


# ============================================================================
# Graph Construction
# ============================================================================

def build_agent_graph() -> StateGraph:
    """Build the agent graph.

    Returns:
        Configured StateGraph.
    """
    # Create reducer
    reducer = StateReducer()
    reducer.register("messages", append_reducer)

    # Create graph
    graph = StateGraph(AgentState, reducer=reducer)
    graph.name = "basic_agent"

    # Add nodes
    graph.add_node("analyze", analyze)
    graph.add_node("answer", answer)
    graph.add_node("acknowledge", acknowledge)
    graph.add_node("error_handler", error_handler)

    # Add edges
    graph.add_edge(START, "analyze")
    graph.add_conditional_edges(
        "analyze",
        route_after_analyze,
        ["answer", "acknowledge", "error_handler"],
    )
    graph.add_edge("answer", END)
    graph.add_edge("acknowledge", END)
    graph.add_edge("error_handler", END)

    return graph


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Build and compile graph
    graph = build_agent_graph()
    compiled = graph.compile()

    # Print graph structure
    print(compiled.get_graph_visualization())
    print()

    # Test with a question
    print("=== Question Test ===")
    result = compiled.invoke({
        "messages": [{"role": "user", "content": "What is Python?"}],
        "current_node": "",
        "result": "",
        "error": "",
    })
    print(f"Result: {result['result']}")
    print(f"Messages: {result['messages']}")
    print()

    # Test with a statement
    print("=== Statement Test ===")
    result = compiled.invoke({
        "messages": [{"role": "user", "content": "Python is great."}],
        "current_node": "",
        "result": "",
        "error": "",
    })
    print(f"Result: {result['result']}")
    print(f"Messages: {result['messages']}")
