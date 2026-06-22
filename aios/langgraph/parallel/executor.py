"""
Parallel executor for the PHOENIX AIOS LangGraph framework.

Provides fan-out/fan-in patterns for concurrent node execution,
inspired by LangGraph's Send API.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, TypeVar

from ..core.constants import DEFAULT_MAX_CONCURRENT_NODES
from ..core.state import StateReducer, merge_dicts

logger = logging.getLogger(__name__)

# Type variables
StateT = TypeVar("StateT", bound=dict)
T = TypeVar("T")


# ============================================================================
# Send Primitive
# ============================================================================

@dataclass(frozen=True)
class Send:
    """Represents a parallel dispatch to a node.

    Used in fan-out patterns to send work to multiple nodes
    concurrently. Each Send targets a specific node with
    custom input state.

    Attributes:
        node: Target node name.
        state: Input state for the target node.
        metadata: Optional metadata for the dispatch.

    Example:
        def fan_out(state: dict) -> list[Send]:
            return [
                Send("processor_1", {"item": state["items"][0]}),
                Send("processor_2", {"item": state["items"][1]}),
                Send("processor_3", {"item": state["items"][2]}),
            ]
    """

    node: str
    state: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation."""
        return f"Send(node={self.node!r}, state_keys={list(self.state.keys())})"


# ============================================================================
# Fan-Out Result
# ============================================================================

@dataclass
class FanOutResult:
    """Result of a parallel fan-out execution.

    Attributes:
        results: List of (node_name, state_update) tuples.
        errors: List of (node_name, error) tuples for failed nodes.
        duration_ms: Total execution duration in milliseconds.
        success_count: Number of successful node executions.
        failure_count: Number of failed node executions.
    """

    results: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    errors: list[tuple[str, Exception]] = field(default_factory=list)
    duration_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0

    @property
    def all_succeeded(self) -> bool:
        """Check if all nodes succeeded."""
        return self.failure_count == 0

    @property
    def all_failed(self) -> bool:
        """Check if all nodes failed."""
        return self.success_count == 0

    @property
    def has_results(self) -> bool:
        """Check if there are any results."""
        return len(self.results) > 0

    def get_merged_state(self, reducer: StateReducer | None = None) -> dict[str, Any]:
        """Merge all results into a single state.

        Args:
            reducer: Optional state reducer for merge behavior.

        Returns:
            Merged state dictionary.
        """
        if not self.results:
            return {}

        merged = {}
        for _, state_update in self.results:
            if reducer:
                merged = reducer.apply(merged, state_update)
            else:
                merged = merge_dicts(merged, state_update)

        return merged


# ============================================================================
# Parallel Configuration
# ============================================================================

@dataclass
class ParallelConfig:
    """Configuration for parallel execution.

    Attributes:
        max_workers: Maximum number of concurrent workers.
        timeout_seconds: Timeout for parallel execution.
        fail_fast: Stop on first failure.
        collect_errors: Collect errors instead of raising.
    """

    max_workers: int = DEFAULT_MAX_CONCURRENT_NODES
    timeout_seconds: float = 60.0
    fail_fast: bool = False
    collect_errors: bool = True


# ============================================================================
# Parallel Executor
# ============================================================================

class ParallelExecutor:
    """Executor for parallel node execution.

    Manages concurrent execution of multiple nodes, handling
    fan-out dispatch and result aggregation.

    Features:
        - Thread-based parallel execution
        - Configurable concurrency limits
        - Error handling and collection
        - Result aggregation

    Example:
        executor = ParallelExecutor()

        # Define nodes
        def process_a(state):
            return {"result_a": "done"}

        def process_b(state):
            return {"result_b": "done"}

        # Execute in parallel
        sends = [
            Send("process_a", {"input": "data_a"}),
            Send("process_b", {"input": "data_b"}),
        ]
        nodes = {"process_a": process_a, "process_b": process_b}
        result = executor.execute(sends, nodes)
    """

    def __init__(
        self,
        config: ParallelConfig | None = None,
        reducer: StateReducer | None = None,
    ) -> None:
        """Initialize parallel executor.

        Args:
            config: Parallel execution configuration.
            reducer: State reducer for merging results.
        """
        self._config = config or ParallelConfig()
        self._reducer = reducer or StateReducer()
        self._execution_count = 0

    @property
    def config(self) -> ParallelConfig:
        """Get parallel configuration."""
        return self._config

    @property
    def execution_count(self) -> int:
        """Get total executions performed."""
        return self._execution_count

    def execute(
        self,
        sends: list[Send],
        nodes: dict[str, Callable[[dict], dict]],
    ) -> FanOutResult:
        """Execute multiple nodes in parallel.

        Dispatches each Send to its target node concurrently
        and collects results.

        Args:
            sends: List of Send dispatches.
            nodes: Map of node names to node functions.

        Returns:
            FanOutResult with all results and errors.

        Raises:
            ValueError: If target node not found.
            RuntimeError: If fail_fast is True and a node fails.
        """
        if not sends:
            return FanOutResult()

        start_time = time.time()
        result = FanOutResult()

        # Validate all targets exist
        for send in sends:
            if send.node not in nodes:
                raise ValueError(f"Node '{send.node}' not found")

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for send in sends:
                future = executor.submit(
                    self._execute_node,
                    send.node,
                    nodes[send.node],
                    send.state,
                )
                futures[future] = send.node

            # Collect results
            for future in as_completed(
                futures,
                timeout=self._config.timeout_seconds,
            ):
                node_name = futures[future]
                try:
                    state_update = future.result()
                    result.results.append((node_name, state_update))
                    result.success_count += 1
                except Exception as e:
                    result.errors.append((node_name, e))
                    result.failure_count += 1
                    logger.error(f"Node '{node_name}' failed: {e}")

                    if self._config.fail_fast:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        raise RuntimeError(
                            f"Node '{node_name}' failed: {e}"
                        ) from e

        result.duration_ms = (time.time() - start_time) * 1000
        self._execution_count += 1

        return result

    def _execute_node(
        self,
        node_name: str,
        node_fn: Callable[[dict], dict],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single node.

        Args:
            node_name: Node name.
            node_fn: Node function.
            state: Input state.

        Returns:
            State update from node.

        Raises:
            Exception: If node execution fails.
        """
        try:
            return node_fn(state)
        except Exception as e:
            logger.error(f"Node '{node_name}' execution failed: {e}")
            raise


# ============================================================================
# Convenience Function
# ============================================================================

def parallel_execute(
    sends: list[Send],
    nodes: dict[str, Callable[[dict], dict]],
    config: ParallelConfig | None = None,
    reducer: StateReducer | None = None,
) -> dict[str, Any]:
    """Execute nodes in parallel and return merged state.

    Convenience function for parallel execution.

    Args:
        sends: List of Send dispatches.
        nodes: Map of node names to node functions.
        config: Optional parallel configuration.
        reducer: Optional state reducer.

    Returns:
        Merged state from all successful nodes.
    """
    executor = ParallelExecutor(config=config, reducer=reducer)
    result = executor.execute(sends, nodes)
    return result.get_merged_state(reducer)


# ============================================================================
# Fan-Out Decorator
# ============================================================================

def fan_out(
    targets: list[str],
    state_transform: Callable[[dict, str], dict] | None = None,
):
    """Decorator to create a fan-out node.

    Transforms a node function into one that dispatches work
    to multiple target nodes in parallel.

    Args:
        targets: List of target node names.
        state_transform: Optional function to transform state for each target.

    Returns:
        Decorator function.

    Example:
        @fan_out(["processor_1", "processor_2"])
        def dispatch(state):
            # This will be called for each target
            return {"items": state["items"]}
    """
    def decorator(fn: Callable[[dict], dict]) -> Callable[[dict], list[Send]]:
        def wrapper(state: dict[str, Any]) -> list[Send]:
            sends = []
            for target in targets:
                if state_transform:
                    target_state = state_transform(state, target)
                else:
                    target_state = fn(state)
                sends.append(Send(node=target, state=target_state))
            return sends

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator


# ============================================================================
# Map-Reduce Pattern
# ============================================================================

class MapReduceExecutor:
    """Executor for map-reduce patterns.

    Provides a higher-level abstraction over parallel execution
    for map-reduce workflows.

    Example:
        executor = MapReduceExecutor()

        # Define map function
        def process_item(state):
            item = state["item"]
            return {"result": item * 2}

        # Define reduce function
        def combine_results(state):
            return {"total": sum(state["results"])}

        # Execute map-reduce
        items = [1, 2, 3, 4, 5]
        result = executor.execute(
            items=items,
            map_fn=process_item,
            reduce_fn=combine_results,
        )
    """

    def __init__(
        self,
        config: ParallelConfig | None = None,
    ) -> None:
        """Initialize map-reduce executor.

        Args:
            config: Parallel execution configuration.
        """
        self._config = config or ParallelConfig()

    def execute(
        self,
        items: list[Any],
        map_fn: Callable[[dict], dict],
        reduce_fn: Callable[[dict], dict] | None = None,
        item_key: str = "item",
        result_key: str = "result",
    ) -> dict[str, Any]:
        """Execute a map-reduce operation.

        Args:
            items: List of items to process.
            map_fn: Map function (processes each item).
            reduce_fn: Optional reduce function (combines results).
            item_key: State key for input item.
            result_key: State key for output result.

        Returns:
            Final state after map-reduce.
        """
        # Create sends for each item
        sends = []
        for i, item in enumerate(items):
            state = {item_key: item, "index": i}
            sends.append(Send(node="mapper", state=state))

        # Create mapper node
        def mapper_node(state: dict) -> dict:
            result = map_fn(state)
            return {result_key: result.get(result_key, result)}

        nodes = {"mapper": mapper_node}

        # Execute map phase
        executor = ParallelExecutor(config=self._config)
        map_result = executor.execute(sends, nodes)

        # Collect results
        results = [r for _, r in map_result.results]

        # Execute reduce phase if provided
        if reduce_fn and results:
            combined = {f"{result_key}s": [r.get(result_key, r) for r in results]}
            return reduce_fn(combined)

        return {f"{result_key}s": [r.get(result_key, r) for r in results]}
