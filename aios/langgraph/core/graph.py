"""
StateGraph implementation for the PHOENIX AIOS LangGraph framework.

Provides the core graph construction and execution engine,
inspired by LangGraph's StateGraph API.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Generic,
    Sequence,
    TypeVar,
    Union,
)

from .constants import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_CHECKPOINT_INTERVAL,
    DEFAULT_MAX_CONCURRENT_NODES,
    END,
    SELF,
    START,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
)
from .state import AgentState, StateReducer, merge_dicts, create_default_reducer
from .types import (
    CompiledEdge,
    CompiledNode,
    EdgeFunction,
    GraphConfig,
    GraphExecution,
    GraphMetadata,
    NodeExecution,
    NodeFunction,
    NodeResult,
    RoutingFunction,
)

# Type variable for state
StateT = TypeVar("StateT", bound=dict)

logger = logging.getLogger(__name__)


# ============================================================================
# StateGraph
# ============================================================================

class StateGraph(Generic[StateT]):
    """Directed graph for stateful agent workflows.

    StateGraph provides a fluent API for constructing execution graphs
    where nodes are functions that transform state, and edges define
    the flow between nodes.

    Features:
        - Typed state with reducers for automatic merge behavior
        - Conditional routing based on state inspection
        - Parallel execution via fan-out/fan-in patterns
        - Checkpointing for state persistence and recovery

    Example:
        class MyState(TypedDict):
            messages: Annotated[list[dict], operator.add]
            result: str

        graph = StateGraph(MyState)
        graph.add_node("process", process_fn)
        graph.add_node("validate", validate_fn)
        graph.add_edge(START, "process")
        graph.add_conditional_edges("process", route_fn, ["validate", END])
        graph.add_edge("validate", END)

        compiled = graph.compile()
        result = compiled.invoke({"messages": [], "result": ""})
    """

    def __init__(
        self,
        state_schema: type | None = None,
        reducer: StateReducer | None = None,
        config: GraphConfig | None = None,
    ) -> None:
        """Initialize a new StateGraph.

        Args:
            state_schema: Optional state schema (TypedDict or dataclass).
            reducer: Optional state reducer for merge behavior.
            config: Optional graph configuration.
        """
        self._state_schema = state_schema
        self._reducer = reducer or create_default_reducer()
        self._config = config or GraphConfig()

        # Graph structure
        self._nodes: dict[str, Callable[[dict], dict]] = {}
        self._edges: dict[str, str] = {}  # source -> target (simple edges)
        self._conditional_edges: dict[str, tuple[Callable, list[str]]] = {}
        # source -> (routing_fn, possible_targets)

        # Entry and exit points
        self._entry_point: str | None = None
        self._exit_nodes: set[str] = set()

        # Metadata
        self._name: str = "unnamed"
        self._description: str = ""

    @property
    def name(self) -> str:
        """Get graph name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set graph name."""
        self._name = value

    @property
    def description(self) -> str:
        """Get graph description."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """Set graph description."""
        self._description = value

    def add_node(self, name: str, fn: Callable[[dict], dict]) -> None:
        """Add a node to the graph.

        A node is a function that receives the current state and returns
        a partial state update. The update is merged into the state.

        Args:
            name: Unique node name.
            fn: Node function (state -> state_update).

        Raises:
            ValueError: If node name is reserved or already exists.
        """
        if name in (START, END, SELF):
            raise ValueError(f"Node name '{name}' is reserved")
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already exists")
        self._nodes[name] = fn

    def add_edge(self, source: str, target: str) -> None:
        """Add a simple directed edge.

        Creates a deterministic edge from source to target node.

        Args:
            source: Source node name (or START sentinel).
            target: Target node name (or END sentinel).

        Raises:
            ValueError: If source or target node doesn't exist.
        """
        # Handle START sentinel
        if source == START:
            if target not in self._nodes and target != END:
                raise ValueError(f"Target node '{target}' not found")
            self._entry_point = target
            return

        # Handle END sentinel
        if target == END:
            if source not in self._nodes:
                raise ValueError(f"Source node '{source}' not found")
            self._exit_nodes.add(source)
            return

        # Validate nodes exist
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' not found")
        if target not in self._nodes:
            raise ValueError(f"Target node '{target}' not found")

        # Handle SELF sentinel
        if target == SELF:
            self._edges[source] = source
        else:
            self._edges[source] = target

    def add_conditional_edges(
        self,
        source: str,
        condition: Callable[[dict], str],
        targets: list[str],
    ) -> None:
        """Add conditional edges from a source node.

        The condition function inspects state and returns the name of
        the next node to execute. This enables dynamic routing.

        Args:
            source: Source node name.
            condition: Routing function (state -> node_name).
            targets: List of possible target node names.

        Raises:
            ValueError: If source node doesn't exist or targets are invalid.
        """
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' not found")

        for target in targets:
            if target not in self._nodes and target != END:
                raise ValueError(f"Target node '{target}' not found")

        self._conditional_edges[source] = (condition, targets)

    def add_parallel_edges(
        self,
        source: str,
        targets: list[str],
    ) -> None:
        """Add edges for parallel execution (fan-out).

        Creates edges from source to multiple targets that execute concurrently.
        State updates from parallel nodes are merged using reducers.

        Args:
            source: Source node name.
            targets: List of target node names.

        Raises:
            ValueError: If source node doesn't exist or targets are invalid.
        """
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' not found")

        for target in targets:
            if target not in self._nodes:
                raise ValueError(f"Target node '{target}' not found")

        # Store as conditional edge that returns all targets
        self._conditional_edges[source] = (
            lambda state: targets,
            targets,
        )

    def set_entry_point(self, node_name: str) -> None:
        """Set the graph entry point.

        Args:
            node_name: Name of the entry node.

        Raises:
            ValueError: If node doesn't exist.
        """
        if node_name not in self._nodes:
            raise ValueError(f"Node '{node_name}' not found")
        self._entry_point = node_name

    def set_finish_point(self, node_name: str) -> None:
        """Mark a node as a finish point (connects to END).

        Args:
            node_name: Name of the finish node.

        Raises:
            ValueError: If node doesn't exist.
        """
        if node_name not in self._nodes:
            raise ValueError(f"Node '{node_name}' not found")
        self._exit_nodes.add(node_name)

    def compile(self) -> CompiledGraph:
        """Compile the graph into an executable form.

        Validates the graph structure and creates an optimized
        execution plan.

        Returns:
            CompiledGraph ready for execution.

        Raises:
            ValueError: If graph is invalid (no entry point, unreachable nodes, etc.).
        """
        self._validate()
        return CompiledGraph(
            nodes=self._nodes.copy(),
            edges=self._edges.copy(),
            conditional_edges=self._conditional_edges.copy(),
            entry_point=self._entry_point,
            exit_nodes=self._exit_nodes.copy(),
            reducer=self._reducer,
            config=self._config,
            metadata=self._build_metadata(),
        )

    def _validate(self) -> None:
        """Validate graph structure.

        Raises:
            ValueError: If graph is invalid.
        """
        if not self._nodes:
            raise ValueError("Graph has no nodes")

        if self._entry_point is None:
            raise ValueError("Graph has no entry point (use add_edge(START, ...) or set_entry_point)")

        if not self._exit_nodes and END not in [
            t for _, t in self._edges.items()
        ]:
            # Check conditional edges for END
            has_end = False
            for _, (_, targets) in self._conditional_edges.items():
                if END in targets:
                    has_end = True
                    break
            if not has_end:
                raise ValueError("Graph has no exit point (use add_edge(..., END) or set_finish_point)")

        # Check for unreachable nodes
        reachable = self._find_reachable_nodes()
        unreachable = set(self._nodes.keys()) - reachable
        if unreachable:
            logger.warning(f"Unreachable nodes: {unreachable}")

    def _find_reachable_nodes(self) -> set[str]:
        """Find all nodes reachable from the entry point.

        Returns:
            Set of reachable node names.
        """
        if self._entry_point is None:
            return set()

        reachable = set()
        queue = [self._entry_point]

        while queue:
            node = queue.pop(0)
            if node in reachable:
                continue
            reachable.add(node)

            # Follow simple edges
            if node in self._edges:
                target = self._edges[node]
                if target not in reachable:
                    queue.append(target)

            # Follow conditional edges
            if node in self._conditional_edges:
                _, targets = self._conditional_edges[node]
                for target in targets:
                    if target not in reachable and target != END:
                        queue.append(target)

        return reachable

    def _build_metadata(self) -> GraphMetadata:
        """Build graph metadata.

        Returns:
            GraphMetadata with graph statistics.
        """
        edge_count = len(self._edges)
        for _, (_, targets) in self._conditional_edges.items():
            edge_count += len(targets)

        return GraphMetadata(
            name=self._name,
            description=self._description,
            node_count=len(self._nodes),
            edge_count=edge_count,
            has_conditional_edges=len(self._conditional_edges) > 0,
            has_parallel_nodes=any(
                len(targets) > 1
                for _, (_, targets) in self._conditional_edges.items()
            ),
        )


# ============================================================================
# CompiledGraph
# ============================================================================

class CompiledGraph:
    """Compiled, executable graph.

    Created by calling StateGraph.compile(). Provides methods
    to invoke the graph with state and stream execution.

    Attributes:
        nodes: Compiled node map.
        edges: Compiled edge map.
        metadata: Graph metadata.
    """

    def __init__(
        self,
        nodes: dict[str, Callable[[dict], dict]],
        edges: dict[str, str],
        conditional_edges: dict[str, tuple[Callable, list[str]]],
        entry_point: str | None,
        exit_nodes: set[str],
        reducer: StateReducer,
        config: GraphConfig,
        metadata: GraphMetadata,
    ) -> None:
        """Initialize compiled graph.

        Args:
            nodes: Node function map.
            edges: Simple edge map.
            conditional_edges: Conditional edge map.
            entry_point: Entry node name.
            exit_nodes: Set of exit node names.
            reducer: State reducer.
            config: Graph configuration.
            metadata: Graph metadata.
        """
        self._nodes = nodes
        self._edges = edges
        self._conditional_edges = conditional_edges
        self._entry_point = entry_point
        self._exit_nodes = exit_nodes
        self._reducer = reducer
        self._config = config
        self._metadata = metadata

        # Execution state
        self._execution_count = 0
        self._last_execution: GraphExecution | None = None

    @property
    def metadata(self) -> GraphMetadata:
        """Get graph metadata."""
        return self._metadata

    @property
    def last_execution(self) -> GraphExecution | None:
        """Get the last execution record."""
        return self._last_execution

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the graph with the given state.

        Runs the graph from entry point to completion, following
        edges and applying node functions to transform state.

        Args:
            state: Initial state dictionary.

        Returns:
            Final state after graph execution.

        Raises:
            RuntimeError: If execution fails or exceeds limits.
        """
        execution = GraphExecution(
            graph_name=self._metadata.name,
            final_state=state.copy(),
            start_time=datetime.now(),
            status=STATUS_RUNNING,
        )

        try:
            result = self._execute(state, execution)
            execution.final_state = result
            execution.status = STATUS_COMPLETED
            execution.end_time = datetime.now()
            execution.total_duration_ms = (
                execution.end_time - execution.start_time
            ).total_seconds() * 1000
            self._last_execution = execution
            self._execution_count += 1
            return result
        except Exception as e:
            execution.status = STATUS_FAILED
            execution.error = e
            execution.end_time = datetime.now()
            execution.total_duration_ms = (
                execution.end_time - execution.start_time
            ).total_seconds() * 1000
            self._last_execution = execution
            raise

    def _execute(
        self,
        state: dict[str, Any],
        execution: GraphExecution,
    ) -> dict[str, Any]:
        """Execute the graph internally.

        Args:
            state: Initial state.
            execution: Execution record.

        Returns:
            Final state.

        Raises:
            RuntimeError: If execution fails.
        """
        if self._entry_point is None:
            raise RuntimeError("No entry point defined")

        current_node = self._entry_point
        current_state = state.copy()
        iterations = 0

        while current_node != END:
            # Check iteration limit
            iterations += 1
            if iterations > self._config.max_iterations:
                raise RuntimeError(
                    f"Exceeded maximum iterations ({self._config.max_iterations})"
                )

            # Check timeout
            elapsed = (datetime.now() - execution.start_time).total_seconds()
            if elapsed > self._config.timeout_seconds:
                raise RuntimeError(
                    f"Execution timed out after {elapsed:.1f}s"
                )

            # Execute current node
            if current_node not in self._nodes:
                raise RuntimeError(f"Node '{current_node}' not found")

            node_start = time.time()
            try:
                node_fn = self._nodes[current_node]
                state_update = node_fn(current_state)
                current_state = self._reducer.apply(current_state, state_update)

                # Record execution
                node_exec = NodeExecution(
                    node_name=current_node,
                    input_state=state.copy(),
                    output_state=current_state.copy(),
                    duration_ms=(time.time() - node_start) * 1000,
                )
                execution.executions.append(node_exec)

                if self._config.debug:
                    logger.debug(
                        f"Node '{current_node}' executed in {node_exec.duration_ms:.1f}ms"
                    )

            except Exception as e:
                node_exec = NodeExecution(
                    node_name=current_node,
                    input_state=state.copy(),
                    output_state=current_state.copy(),
                    duration_ms=(time.time() - node_start) * 1000,
                    error=e,
                )
                execution.executions.append(node_exec)

                if self._config.raise_on_error:
                    raise

                logger.error(f"Node '{current_node}' failed: {e}")
                # Try to continue with error state
                current_state["error"] = {
                    "node": current_node,
                    "type": type(e).__name__,
                    "message": str(e),
                }

            # Determine next node
            current_node = self._get_next_node(current_node, current_state)

        return current_state

    def _get_next_node(self, current_node: str, state: dict[str, Any]) -> str:
        """Determine the next node to execute.

        Args:
            current_node: Current node name.
            state: Current state.

        Returns:
            Next node name or END.
        """
        # Check for exit nodes
        if current_node in self._exit_nodes:
            return END

        # Check conditional edges first
        if current_node in self._conditional_edges:
            condition_fn, targets = self._conditional_edges[current_node]
            next_node = condition_fn(state)
            if next_node in targets or next_node == END:
                return next_node
            logger.warning(
                f"Conditional edge returned '{next_node}' which is not in targets {targets}"
            )
            return END

        # Check simple edges
        if current_node in self._edges:
            return self._edges[current_node]

        # No edge found, go to END
        logger.warning(f"No edge from node '{current_node}', going to END")
        return END

    def stream(self, state: dict[str, Any]):
        """Stream graph execution, yielding state after each node.

        Args:
            state: Initial state dictionary.

        Yields:
            State dict after each node execution.
        """
        if self._entry_point is None:
            raise RuntimeError("No entry point defined")

        current_node = self._entry_point
        current_state = state.copy()
        iterations = 0

        while current_node != END:
            iterations += 1
            if iterations > self._config.max_iterations:
                raise RuntimeError(
                    f"Exceeded maximum iterations ({self._config.max_iterations})"
                )

            if current_node not in self._nodes:
                raise RuntimeError(f"Node '{current_node}' not found")

            # Execute node
            node_fn = self._nodes[current_node]
            state_update = node_fn(current_state)
            current_state = self._reducer.apply(current_state, state_update)

            yield {
                "node": current_node,
                "state": current_state.copy(),
                "iteration": iterations,
            }

            # Get next node
            current_node = self._get_next_node(current_node, current_state)

    def get_graph_visualization(self) -> str:
        """Get a text representation of the graph structure.

        Returns:
            String representation of the graph.
        """
        lines = [f"Graph: {self._metadata.name}"]
        lines.append(f"Nodes: {self._metadata.node_count}")
        lines.append(f"Edges: {self._metadata.edge_count}")
        lines.append("")

        # Entry point
        lines.append(f"Entry: {self._entry_point}")
        lines.append("")

        # Nodes
        lines.append("Nodes:")
        for name in sorted(self._nodes.keys()):
            marker = " *" if name in self._exit_nodes else ""
            lines.append(f"  - {name}{marker}")

        lines.append("")

        # Simple edges
        lines.append("Edges:")
        for source, target in sorted(self._edges.items()):
            lines.append(f"  {source} -> {target}")

        # Conditional edges
        for source, (_, targets) in sorted(self._conditional_edges.items()):
            targets_str = ", ".join(targets)
            lines.append(f"  {source} -> [{targets_str}] (conditional)")

        # Exit nodes
        if self._exit_nodes:
            lines.append("")
            lines.append(f"Exit nodes: {', '.join(sorted(self._exit_nodes))}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export graph structure as dictionary.

        Returns:
            Graph structure as dict.
        """
        return {
            "name": self._metadata.name,
            "description": self._metadata.description,
            "entry_point": self._entry_point,
            "exit_nodes": list(self._exit_nodes),
            "nodes": list(self._nodes.keys()),
            "edges": [
                {"source": s, "target": t}
                for s, t in self._edges.items()
            ],
            "conditional_edges": [
                {"source": s, "targets": t}
                for s, (_, t) in self._conditional_edges.items()
            ],
            "config": {
                "max_iterations": self._config.max_iterations,
                "timeout_seconds": self._config.timeout_seconds,
            },
        }
