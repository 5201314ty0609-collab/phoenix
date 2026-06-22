"""
Core module for PHOENIX AIOS LangGraph framework.

Provides the fundamental building blocks:
    - StateGraph: Graph construction and compilation
    - State types and reducers
    - Type definitions and constants
"""

from .graph import StateGraph, CompiledGraph
from .state import AgentState, StateReducer, merge_dicts, apply_reducer
from .types import (
    NodeFn,
    EdgeFn,
    RoutingFn,
    GraphConfig,
    GraphMetadata,
    NodeResult,
    EdgeTarget,
    CompiledNode,
    CompiledEdge,
    GraphExecution,
    NodeExecution,
)
from .constants import START, END, SELF, NODE_SEPARATOR

__all__ = [
    "StateGraph",
    "CompiledGraph",
    "AgentState",
    "StateReducer",
    "merge_dicts",
    "apply_reducer",
    "NodeFn",
    "EdgeFn",
    "RoutingFn",
    "GraphConfig",
    "GraphMetadata",
    "NodeResult",
    "EdgeTarget",
    "CompiledNode",
    "CompiledEdge",
    "GraphExecution",
    "NodeExecution",
    "START",
    "END",
    "SELF",
    "NODE_SEPARATOR",
]
