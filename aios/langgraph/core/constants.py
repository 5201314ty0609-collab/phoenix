"""
Constants for the PHOENIX AIOS LangGraph framework.

Defines sentinel values for graph construction and execution.
"""

from typing import Final

# Sentinel node names for graph construction
START: Final[str] = "__start__"
"""Entry point sentinel. Used as source in add_edge to mark graph entry."""

END: Final[str] = "__end__"
"""Exit point sentinel. Used as target in add_edge to mark graph termination."""

SELF: Final[str] = "__self__"
"""Self-loop sentinel. Used to create edges back to the current node."""

# Separator for hierarchical node names (e.g., "subgraph.node_name")
NODE_SEPARATOR: Final[str] = "."

# Default configuration values
DEFAULT_MAX_ITERATIONS: Final[int] = 100
"""Maximum iterations before graph execution is terminated to prevent infinite loops."""

DEFAULT_CHECKPOINT_INTERVAL: Final[int] = 10
"""Number of node executions between automatic checkpoints."""

DEFAULT_TIMEOUT_SECONDS: Final[float] = 300.0
"""Default timeout for graph execution in seconds."""

DEFAULT_MAX_CONCURRENT_NODES: Final[int] = 10
"""Maximum number of nodes that can execute concurrently in parallel mode."""

# State reducer types
REDUCER_APPEND: Final[str] = "append"
REDUCER_REPLACE: Final[str] = "replace"
REDUCER_MERGE: Final[str] = "merge"
REDUCER_CUSTOM: Final[str] = "custom"

# Execution status
STATUS_PENDING: Final[str] = "pending"
STATUS_RUNNING: Final[str] = "running"
STATUS_COMPLETED: Final[str] = "completed"
STATUS_FAILED: Final[str] = "failed"
STATUS_CANCELLED: Final[str] = "cancelled"
STATUS_PAUSED: Final[str] = "paused"

# Checkpoint types
CHECKPOINT_AUTO: Final[str] = "auto"
CHECKPOINT_MANUAL: Final[str] = "manual"
CHECKPOINT_BEFORE_NODE: Final[str] = "before_node"
CHECKPOINT_AFTER_NODE: Final[str] = "after_node"
CHECKPOINT_ON_ERROR: Final[str] = "on_error"
