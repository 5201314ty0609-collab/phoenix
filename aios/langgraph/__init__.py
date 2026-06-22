"""
PHOENIX AIOS LangGraph-Inspired Agent Orchestration Framework

A stateful, graph-based agent orchestration system inspired by LangGraph's design patterns.
Provides StateGraph construction, conditional routing, parallel execution, and checkpointing.

Core Components:
    - StateGraph: Directed graph with typed state for agent workflows
    - ConditionalRouter: Dynamic routing based on state inspection
    - ParallelExecutor: Fan-out/fan-in concurrent execution
    - CheckpointManager: State persistence and recovery

Usage:
    from aios.langgraph import StateGraph, START, END
    from aios.langgraph.core.state import AgentState
    from aios.langgraph.routing import ConditionalRouter
    from aios.langgraph.checkpoint import CheckpointManager
    from aios.langgraph.parallel import Send, parallel_execute

Example:
    # Define state
    class MyState(AgentState):
        messages: list[dict]
        result: str

    # Build graph
    graph = StateGraph(MyState)
    graph.add_node("process", process_fn)
    graph.add_node("validate", validate_fn)
    graph.add_edge(START, "process")
    graph.add_conditional_edges("process", route_fn, ["validate", END])
    graph.add_edge("validate", END)

    # Compile and run
    compiled = graph.compile()
    result = compiled.invoke({"messages": [], "result": ""})
"""

__version__ = "1.0.0"
__author__ = "PHOENIX AIOS"

from .core.graph import StateGraph, CompiledGraph
from .core.state import AgentState, StateReducer
from .core.types import (
    NodeFn,
    EdgeFn,
    RoutingFn,
    GraphConfig,
    GraphMetadata,
    NodeResult,
    EdgeTarget,
)
from .core.constants import START, END, SELF
from .routing.router import ConditionalRouter, RoutingDecision
from .checkpoint.manager import CheckpointManager, Checkpoint
from .parallel.executor import Send, parallel_execute, FanOutResult

__all__ = [
    # Core
    "StateGraph",
    "CompiledGraph",
    "AgentState",
    "StateReducer",
    "START",
    "END",
    "SELF",
    # Types
    "NodeFn",
    "EdgeFn",
    "RoutingFn",
    "GraphConfig",
    "GraphMetadata",
    "NodeResult",
    "EdgeTarget",
    # Routing
    "ConditionalRouter",
    "RoutingDecision",
    # Checkpoint
    "CheckpointManager",
    "Checkpoint",
    # Parallel
    "Send",
    "parallel_execute",
    "FanOutResult",
]
