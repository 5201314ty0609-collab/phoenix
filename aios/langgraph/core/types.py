"""
Type definitions for the PHOENIX AIOS LangGraph framework.

Provides comprehensive type annotations for all framework components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Generic,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    runtime_checkable,
)
from datetime import datetime

# Type variables for generic state
StateT = TypeVar("StateT", bound=dict)
"""Type variable for state dictionaries."""

T = TypeVar("T")
"""General purpose type variable."""


# ============================================================================
# Protocol Definitions
# ============================================================================

@runtime_checkable
class NodeFn(Protocol[StateT]):
    """Protocol for node functions.

    A node function receives the current state and returns a partial state update.
    The update is merged into the current state to produce the next state.

    Example:
        def my_node(state: dict) -> dict:
            return {"messages": state["messages"] + ["processed"]}
    """

    def __call__(self, state: StateT) -> dict[str, Any]:
        """Execute node logic and return state update.

        Args:
            state: Current graph state.

        Returns:
            Partial state update to merge into current state.
        """
        ...


@runtime_checkable
class EdgeFn(Protocol[StateT]):
    """Protocol for edge functions that determine next node.

    An edge function inspects the current state and returns the name
    of the next node to execute, or END to terminate.

    Example:
        def route(state: dict) -> str:
            if state.get("needs_review"):
                return "reviewer"
            return END
    """

    def __call__(self, state: StateT) -> str:
        """Determine next node based on current state.

        Args:
            state: Current graph state.

        Returns:
            Name of next node, or END sentinel.
        """
        ...


@runtime_checkable
class RoutingFn(Protocol[StateT]):
    """Protocol for routing functions used in conditional edges.

    A routing function inspects state and returns a list of target nodes.
    This supports fan-out patterns where multiple nodes execute in parallel.

    Example:
        def fan_out(state: dict) -> list[str]:
            return ["processor_1", "processor_2", "processor_3"]
    """

    def __call__(self, state: StateT) -> Union[str, list[str]]:
        """Determine target nodes based on current state.

        Args:
            state: Current graph state.

        Returns:
            Single node name or list of node names for parallel execution.
        """
        ...


@runtime_checkable
class ReducerFn(Protocol[T]):
    """Protocol for state value reducers.

    Reducers define how state values are combined when merging updates.
    This is critical for parallel execution where multiple nodes may
    update the same state key.

    Example:
        def append_reducer(current: list, update: list) -> list:
            return current + update
    """

    def __call__(self, current: T, update: T) -> T:
        """Combine current value with update value.

        Args:
            current: Current state value.
            update: New value to merge.

        Returns:
            Combined value.
        """
        ...


# ============================================================================
# Data Classes
# ============================================================================

@dataclass(frozen=True)
class GraphConfig:
    """Configuration for graph execution.

    Attributes:
        max_iterations: Maximum node executions before termination.
        timeout_seconds: Maximum execution time in seconds.
        checkpoint_interval: Nodes between automatic checkpoints.
        max_concurrent: Maximum parallel node executions.
        debug: Enable debug logging.
        raise_on_error: Raise exceptions instead of catching.
    """

    max_iterations: int = 100
    timeout_seconds: float = 300.0
    checkpoint_interval: int = 10
    max_concurrent: int = 10
    debug: bool = False
    raise_on_error: bool = False

    def with_overrides(self, **kwargs: Any) -> GraphConfig:
        """Create a new config with overridden values.

        Args:
            **kwargs: Configuration values to override.

        Returns:
            New GraphConfig with updated values.
        """
        import dataclasses
        return dataclasses.replace(self, **kwargs)


@dataclass(frozen=True)
class GraphMetadata:
    """Metadata for a compiled graph.

    Attributes:
        name: Graph name.
        version: Graph version.
        description: Graph description.
        created_at: Creation timestamp.
        node_count: Number of nodes in graph.
        edge_count: Number of edges in graph.
        has_conditional_edges: Whether graph has conditional routing.
        has_parallel_nodes: Whether graph has parallel execution paths.
    """

    name: str = "unnamed"
    version: str = "1.0.0"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    node_count: int = 0
    edge_count: int = 0
    has_conditional_edges: bool = False
    has_parallel_nodes: bool = False


@dataclass
class NodeResult:
    """Result of a node execution.

    Attributes:
        node_name: Name of the executed node.
        state_update: Partial state update from node.
        execution_time_ms: Node execution time in milliseconds.
        error: Exception if node failed, None otherwise.
        metadata: Additional execution metadata.
    """

    node_name: str
    state_update: dict[str, Any]
    execution_time_ms: float = 0.0
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if node execution succeeded."""
        return self.error is None


@dataclass(frozen=True)
class EdgeTarget:
    """Target specification for an edge.

    Attributes:
        source: Source node name.
        target: Target node name or END sentinel.
        condition: Optional condition for conditional edges.
        priority: Edge priority for disambiguation.
    """

    source: str
    target: str
    condition: str | None = None
    priority: int = 0


@dataclass
class CompiledNode:
    """A compiled node in the execution graph.

    Attributes:
        name: Node name.
        fn: Node function.
        is_start: Whether this is the start node.
        is_end: Whether this is an end node.
        metadata: Node metadata.
    """

    name: str
    fn: Callable[[dict], dict]
    is_start: bool = False
    is_end: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompiledEdge:
    """A compiled edge in the execution graph.

    Attributes:
        source: Source node name.
        target: Target node name or callable for conditional routing.
        is_conditional: Whether this is a conditional edge.
        targets: List of possible targets for conditional edges.
    """

    source: str
    target: Union[str, Callable[[dict], str]]
    is_conditional: bool = False
    targets: list[str] = field(default_factory=list)


@dataclass
class NodeExecution:
    """Record of a single node execution.

    Attributes:
        node_name: Name of executed node.
        input_state: State before execution.
        output_state: State after execution.
        timestamp: Execution timestamp.
        duration_ms: Execution duration in milliseconds.
        error: Exception if execution failed.
    """

    node_name: str
    input_state: dict[str, Any]
    output_state: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    error: Exception | None = None


@dataclass
class GraphExecution:
    """Record of a complete graph execution.

    Attributes:
        graph_name: Name of the executed graph.
        executions: List of node executions in order.
        final_state: Final state after execution.
        start_time: Execution start time.
        end_time: Execution end time.
        total_duration_ms: Total execution duration.
        status: Execution status.
        error: Exception if execution failed.
    """

    graph_name: str
    executions: list[NodeExecution] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    total_duration_ms: float = 0.0
    status: str = "pending"
    error: Exception | None = None


# ============================================================================
# Type Aliases
# ============================================================================

# Node function type
NodeFunction = Callable[[dict[str, Any]], dict[str, Any]]

# Edge function type (returns next node name)
EdgeFunction = Callable[[dict[str, Any]], str]

# Routing function type (returns single or multiple targets)
RoutingFunction = Callable[[dict[str, Any]], Union[str, list[str]]]

# State reducer type
ReducerFunction = Callable[[Any, Any], Any]

# Conditional edge mapping: target_name -> condition_function
ConditionalEdgeMap = dict[str, Callable[[dict[str, Any]], bool]]
