"""
Parallel agent example using PHOENIX AIOS LangGraph framework.

Demonstrates:
- Fan-out/fan-in patterns
- Parallel node execution
- Result aggregation
"""

from typing import TypedDict, Annotated
import operator
from aios.langgraph import StateGraph, START, END
from aios.langgraph.core.state import StateReducer, append_reducer
from aios.langgraph.parallel import Send, parallel_execute, ParallelConfig


# ============================================================================
# State Definition
# ============================================================================

class ParallelState(TypedDict):
    """State for parallel processing."""
    task: str
    results: Annotated[list[str], operator.add]
    final_result: str


# ============================================================================
# Node Functions
# ============================================================================

def dispatch(state: dict) -> list[Send]:
    """Dispatch work to parallel processors."""
    task = state.get("task", "")

    return [
        Send("researcher", {"task": task}),
        Send("analyzer", {"task": task}),
        Summarizer("summarizer", {"task": task}),
    ]


def researcher(state: dict) -> dict:
    """Research the task."""
    task = state.get("task", "")
    return {
        "results": [f"Research findings for: {task}"],
    }


def analyzer(state: dict) -> dict:
    """Analyze the task."""
    task = state.get("task", "")
    return {
        "results": [f"Analysis of: {task}"],
    }


def summarizer(state: dict) -> dict:
    """Summarize the task."""
    task = state.get("task", "")
    return {
        "results": [f"Summary of: {task}"],
    }


def aggregate(state: dict) -> dict:
    """Aggregate results from parallel processors."""
    results = state.get("results", [])
    final = " | ".join(results)
    return {
        "final_result": final,
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_parallel_graph() -> StateGraph:
    """Build the parallel processing graph.

    Returns:
        Configured StateGraph with parallel execution.
    """
    # Create reducer
    reducer = StateReducer()
    reducer.register("results", append_reducer)

    # Create graph
    graph = StateGraph(ParallelState, reducer=reducer)
    graph.name = "parallel_agent"

    # Add nodes
    graph.add_node("dispatch", dispatch)
    graph.add_node("researcher", researcher)
    graph.add_node("analyzer", analyzer)
    graph.add_node("summarizer", summarizer)
    graph.add_node("aggregate", aggregate)

    # Add edges
    graph.add_edge(START, "dispatch")
    graph.add_parallel_edges("dispatch", ["researcher", "analyzer", "summarizer"])
    graph.add_edge("researcher", "aggregate")
    graph.add_edge("analyzer", "aggregate")
    graph.add_edge("summarizer", "aggregate")
    graph.add_edge("aggregate", END)

    return graph


# ============================================================================
# Direct Parallel Execution
# ============================================================================

def run_parallel_direct(task: str) -> dict:
    """Run parallel execution directly without graph.

    Args:
        task: Task to process.

    Returns:
        Merged results.
    """
    sends = [
        Send("researcher", {"task": task}),
        Send("analyzer", {"task": task}),
        Send("summarizer", {"task": task}),
    ]

    nodes = {
        "researcher": researcher,
        "analyzer": analyzer,
        "summarizer": summarizer,
    }

    config = ParallelConfig(max_workers=3)
    return parallel_execute(sends, nodes, config=config)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Build and compile graph
    graph = build_parallel_graph()
    compiled = graph.compile()

    # Print graph structure
    print(compiled.get_graph_visualization())
    print()

    # Run with graph
    print("=== Graph Execution ===")
    result = compiled.invoke({
        "task": "Analyze PHOENIX architecture",
        "results": [],
        "final_result": "",
    })
    print(f"Final Result: {result['final_result']}")
    print(f"All Results: {result['results']}")
    print()

    # Run direct parallel
    print("=== Direct Parallel Execution ===")
    result = run_parallel_direct("Design new agent system")
    print(f"Merged Results: {result}")
