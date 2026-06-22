"""
State management for the PHOENIX AIOS LangGraph framework.

Provides typed state definitions, reducers, and state manipulation utilities.
Inspired by LangGraph's Annotated type system with operator.add reducers.
"""

from __future__ import annotations

import copy
import operator
from dataclasses import dataclass, field
from typing import (
    Annotated,
    Any,
    Callable,
    Generic,
    TypeVar,
    get_type_hints,
)
from datetime import datetime

from .types import ReducerFunction

# Type variable for generic state
StateT = TypeVar("StateT", bound=dict)


# ============================================================================
# Built-in Reducers
# ============================================================================

def append_reducer(current: list[Any], update: list[Any]) -> list[Any]:
    """Append update items to current list.

    This is the most common reducer for message lists and logs.

    Args:
        current: Current list value.
        update: New items to append.

    Returns:
        New list with update items appended.
    """
    if current is None:
        current = []
    if update is None:
        return current
    return current + update


def replace_reducer(current: Any, update: Any) -> Any:
    """Replace current value with update value.

    This is the default behavior when no reducer is specified.

    Args:
        current: Current value (ignored).
        update: New value.

    Returns:
        The update value.
    """
    return update


def merge_reducer(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Deep merge update dict into current dict.

    For nested dicts, performs recursive merge.
    For other types, replaces current with update.

    Args:
        current: Current dict value.
        update: Dict to merge in.

    Returns:
        Merged dict.
    """
    if current is None:
        current = {}
    if update is None:
        return current

    result = current.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_reducer(result[key], value)
        else:
            result[key] = value
    return result


def max_reducer(current: float, update: float) -> float:
    """Keep the maximum of current and update values.

    Useful for tracking scores, priorities, or thresholds.

    Args:
        current: Current numeric value.
        update: New numeric value.

    Returns:
        Maximum of current and update.
    """
    if current is None:
        return update
    if update is None:
        return current
    return max(current, update)


def min_reducer(current: float, update: float) -> float:
    """Keep the minimum of current and update values.

    Useful for tracking best scores or minimum thresholds.

    Args:
        current: Current numeric value.
        update: New numeric value.

    Returns:
        Minimum of current and update.
    """
    if current is None:
        return update
    if update is None:
        return current
    return min(current, update)


def union_reducer(current: set[Any], update: set[Any]) -> set[Any]:
    """Union of two sets.

    Args:
        current: Current set value.
        update: Set to union with.

    Returns:
        Union of current and update sets.
    """
    if current is None:
        current = set()
    if update is None:
        return current
    return current | update


def increment_reducer(current: int, update: int) -> int:
    """Add update to current value.

    Useful for counters and accumulators.

    Args:
        current: Current integer value.
        update: Value to add.

    Returns:
        Sum of current and update.
    """
    if current is None:
        current = 0
    if update is None:
        return current
    return current + update


# ============================================================================
# State Reducer Registry
# ============================================================================

class StateReducer:
    """Registry for state value reducers.

    Manages reducer functions for state keys, enabling automatic
    merge behavior during state updates.

    Example:
        reducer = StateReducer()
        reducer.register("messages", append_reducer)
        reducer.register("score", max_reducer)

        state = {"messages": ["hello"], "score": 0.5}
        update = {"messages": ["world"], "score": 0.8}
        merged = reducer.apply(state, update)
        # Result: {"messages": ["hello", "world"], "score": 0.8}
    """

    def __init__(self) -> None:
        """Initialize empty reducer registry."""
        self._reducers: dict[str, ReducerFunction] = {}
        self._default_reducer: ReducerFunction = replace_reducer

    def register(self, key: str, reducer: ReducerFunction) -> None:
        """Register a reducer for a state key.

        Args:
            key: State key to register reducer for.
            reducer: Reducer function for combining values.
        """
        self._reducers[key] = reducer

    def unregister(self, key: str) -> None:
        """Unregister a reducer for a state key.

        Args:
            key: State key to unregister reducer for.
        """
        self._reducers.pop(key, None)

    def get(self, key: str) -> ReducerFunction:
        """Get the reducer for a state key.

        Args:
            key: State key to get reducer for.

        Returns:
            Reducer function (default if not registered).
        """
        return self._reducers.get(key, self._default_reducer)

    def set_default(self, reducer: ReducerFunction) -> None:
        """Set the default reducer for unregistered keys.

        Args:
            reducer: Default reducer function.
        """
        self._default_reducer = reducer

    def apply(self, current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        """Apply reducers to merge state update.

        For each key in update:
        - If a reducer is registered, use it to combine values
        - Otherwise, use the default reducer (replace)

        Args:
            current: Current state dict.
            update: State update dict.

        Returns:
            Merged state dict.
        """
        result = current.copy()
        for key, value in update.items():
            if key in result:
                reducer = self.get(key)
                result[key] = reducer(result[key], value)
            else:
                result[key] = value
        return result

    def keys(self) -> list[str]:
        """Get all registered reducer keys.

        Returns:
            List of registered state keys.
        """
        return list(self._reducers.keys())

    def clear(self) -> None:
        """Clear all registered reducers."""
        self._reducers.clear()


# ============================================================================
# Agent State Definition
# ============================================================================

@dataclass
class AgentState:
    """Base state class for agent workflows.

    Provides common state fields and utilities for agent execution.
    Extend this class to define custom state for specific workflows.

    Attributes:
        messages: List of conversation messages.
        current_node: Name of currently executing node.
        execution_history: History of node executions.
        error: Current error state, if any.
        metadata: Additional state metadata.
        created_at: State creation timestamp.
        updated_at: Last update timestamp.
    """

    messages: list[dict[str, Any]] = field(default_factory=list)
    current_node: str = ""
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary.

        Returns:
            State as a plain dictionary.
        """
        return {
            "messages": self.messages,
            "current_node": self.current_node,
            "execution_history": self.execution_history,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentState:
        """Create state from dictionary.

        Args:
            data: State dictionary.

        Returns:
            AgentState instance.
        """
        state = cls()
        state.messages = data.get("messages", [])
        state.current_node = data.get("current_node", "")
        state.execution_history = data.get("execution_history", [])
        state.error = data.get("error")
        state.metadata = data.get("metadata", {})

        if "created_at" in data:
            if isinstance(data["created_at"], str):
                state.created_at = datetime.fromisoformat(data["created_at"])
            elif isinstance(data["created_at"], datetime):
                state.created_at = data["created_at"]

        if "updated_at" in data:
            if isinstance(data["updated_at"], str):
                state.updated_at = datetime.fromisoformat(data["updated_at"])
            elif isinstance(data["updated_at"], datetime):
                state.updated_at = data["updated_at"]

        return state

    def update(self, **kwargs: Any) -> AgentState:
        """Create a new state with updated values.

        Follows immutability principle - returns new instance.

        Args:
            **kwargs: Fields to update.

        Returns:
            New AgentState with updated values.
        """
        data = self.to_dict()
        data.update(kwargs)
        data["updated_at"] = datetime.now().isoformat()
        return AgentState.from_dict(data)

    def add_message(self, role: str, content: str, **kwargs: Any) -> AgentState:
        """Add a message to the state.

        Args:
            role: Message role (user, assistant, system, tool).
            content: Message content.
            **kwargs: Additional message fields.

        Returns:
            New state with message added.
        """
        message = {"role": role, "content": content, **kwargs}
        return self.update(messages=self.messages + [message])

    def record_execution(self, node_name: str, result: dict[str, Any]) -> AgentState:
        """Record a node execution in history.

        Args:
            node_name: Name of executed node.
            result: Execution result.

        Returns:
            New state with execution recorded.
        """
        execution = {
            "node": node_name,
            "timestamp": datetime.now().isoformat(),
            "result": result,
        }
        return self.update(
            execution_history=self.execution_history + [execution],
            current_node=node_name,
        )

    def set_error(self, error: Exception) -> AgentState:
        """Set error state.

        Args:
            error: Exception that occurred.

        Returns:
            New state with error set.
        """
        error_data = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        return self.update(error=error_data)

    def clear_error(self) -> AgentState:
        """Clear error state.

        Returns:
            New state with error cleared.
        """
        return self.update(error=None)


# ============================================================================
# State Utilities
# ============================================================================

def merge_dicts(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Creates a new dictionary with values from both dicts.
    For conflicting keys, update values take precedence.
    For nested dicts, performs recursive merge.

    Args:
        current: Current dictionary.
        update: Dictionary to merge in.

    Returns:
        New merged dictionary.
    """
    result = current.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def apply_reducer(
    current: dict[str, Any],
    update: dict[str, Any],
    reducers: dict[str, ReducerFunction],
) -> dict[str, Any]:
    """Apply reducers to merge state update.

    Args:
        current: Current state dict.
        update: State update dict.
        reducers: Map of state keys to reducer functions.

    Returns:
        Merged state dict.
    """
    result = current.copy()
    for key, value in update.items():
        if key in result and key in reducers:
            result[key] = reducers[key](result[key], value)
        else:
            result[key] = value
    return result


def validate_state(state: dict[str, Any], schema: type) -> list[str]:
    """Validate state against a schema.

    Args:
        state: State dict to validate.
        schema: State schema class (TypedDict or dataclass).

    Returns:
        List of validation error messages (empty if valid).
    """
    errors = []

    # Get expected fields from schema
    if hasattr(schema, "__annotations__"):
        expected_fields = schema.__annotations__
    elif hasattr(schema, "__dataclass_fields__"):
        expected_fields = {f: field.type for f, field in schema.__dataclass_fields__.items()}
    else:
        return ["Invalid schema type"]

    # Check for missing required fields
    for field_name in expected_fields:
        if field_name not in state:
            errors.append(f"Missing required field: {field_name}")

    return errors


def create_default_reducer() -> StateReducer:
    """Create a StateReducer with common defaults.

    Returns:
        StateReducer with append_reducer for list fields.
    """
    reducer = StateReducer()
    # Common patterns
    reducer.register("messages", append_reducer)
    reducer.register("history", append_reducer)
    reducer.register("errors", append_reducer)
    reducer.register("logs", append_reducer)
    reducer.register("results", append_reducer)
    return reducer
