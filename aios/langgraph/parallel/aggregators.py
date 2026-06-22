"""
Result aggregators for parallel execution in the PHOENIX AIOS LangGraph framework.

Provides strategies for combining results from parallel node executions.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Callable

from ..core.state import StateReducer, merge_dicts, append_reducer

logger = logging.getLogger(__name__)


# ============================================================================
# Aggregate Strategy
# ============================================================================

class AggregateStrategy(Enum):
    """Strategies for aggregating parallel results.

    Attributes:
        MERGE: Deep merge all results.
        APPEND: Append all results to lists.
        FIRST: Use first successful result.
        LAST: Use last successful result.
        CUSTOM: Use custom aggregation function.
    """

    MERGE = "merge"
    APPEND = "append"
    FIRST = "first"
    LAST = "last"
    CUSTOM = "custom"


# ============================================================================
# Aggregation Functions
# ============================================================================

def aggregate_results(
    results: list[dict[str, Any]],
    strategy: AggregateStrategy = AggregateStrategy.MERGE,
    custom_fn: Callable[[list[dict]], dict] | None = None,
) -> dict[str, Any]:
    """Aggregate results from parallel execution.

    Args:
        results: List of state dicts from parallel nodes.
        strategy: Aggregation strategy.
        custom_fn: Custom aggregation function (for CUSTOM strategy).

    Returns:
        Aggregated state dictionary.

    Raises:
        ValueError: If no results or invalid custom function.
    """
    if not results:
        return {}

    if strategy == AggregateStrategy.MERGE:
        return merge_states(results)

    elif strategy == AggregateStrategy.APPEND:
        return append_states(results)

    elif strategy == AggregateStrategy.FIRST:
        return results[0]

    elif strategy == AggregateStrategy.LAST:
        return results[-1]

    elif strategy == AggregateStrategy.CUSTOM:
        if custom_fn is None:
            raise ValueError("Custom aggregation requires custom_fn")
        return custom_fn(results)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def merge_states(states: list[dict[str, Any]]) -> dict[str, Any]:
    """Deep merge multiple state dictionaries.

    For conflicting keys, later values take precedence.
    For nested dicts, performs recursive merge.

    Args:
        states: List of state dicts to merge.

    Returns:
        Merged state dictionary.
    """
    if not states:
        return {}

    result = {}
    for state in states:
        result = merge_dicts(result, state)

    return result


def append_states(states: list[dict[str, Any]]) -> dict[str, Any]:
    """Append values from multiple states into lists.

    For each key, collects values into a list.
    If value is already a list, extends it.

    Args:
        states: List of state dicts.

    Returns:
        State dict with values collected into lists.
    """
    if not states:
        return {}

    result: dict[str, list] = {}

    for state in states:
        for key, value in state.items():
            if key not in result:
                result[key] = []

            if isinstance(value, list):
                result[key].extend(value)
            else:
                result[key].append(value)

    return result


def reduce_results(
    results: list[dict[str, Any]],
    reducers: dict[str, Callable[[Any, Any], Any]],
) -> dict[str, Any]:
    """Reduce results using per-key reducer functions.

    Args:
        results: List of state dicts.
        reducers: Map of state keys to reducer functions.

    Returns:
        Reduced state dictionary.
    """
    if not results:
        return {}

    result = {}
    for state in results:
        for key, value in state.items():
            if key in result and key in reducers:
                result[key] = reducers[key](result[key], value)
            else:
                result[key] = value

    return result


# ============================================================================
# Specialized Aggregators
# ============================================================================

def aggregate_messages(
    results: list[dict[str, Any]],
    message_key: str = "messages",
) -> list[dict[str, Any]]:
    """Aggregate messages from multiple results.

    Collects all messages into a single sorted list.

    Args:
        results: List of state dicts.
        message_key: Key containing messages.

    Returns:
        Aggregated message list.
    """
    all_messages = []

    for state in results:
        messages = state.get(message_key, [])
        if isinstance(messages, list):
            all_messages.extend(messages)
        else:
            all_messages.append(messages)

    return all_messages


def aggregate_scores(
    results: list[dict[str, Any]],
    score_key: str = "score",
    strategy: str = "max",
) -> float | None:
    """Aggregate scores from multiple results.

    Args:
        results: List of state dicts.
        score_key: Key containing score.
        strategy: Aggregation strategy ("max", "min", "avg", "sum").

    Returns:
        Aggregated score, or None if no scores found.
    """
    scores = []
    for state in results:
        score = state.get(score_key)
        if score is not None:
            try:
                scores.append(float(score))
            except (ValueError, TypeError):
                pass

    if not scores:
        return None

    if strategy == "max":
        return max(scores)
    elif strategy == "min":
        return min(scores)
    elif strategy == "avg":
        return sum(scores) / len(scores)
    elif strategy == "sum":
        return sum(scores)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def aggregate_errors(
    results: list[dict[str, Any]],
    error_key: str = "error",
) -> list[dict[str, Any]]:
    """Aggregate errors from multiple results.

    Args:
        results: List of state dicts.
        error_key: Key containing error.

    Returns:
        List of error dictionaries.
    """
    errors = []

    for i, state in enumerate(results):
        error = state.get(error_key)
        if error is not None:
            if isinstance(error, dict):
                errors.append(error)
            else:
                errors.append({
                    "index": i,
                    "error": str(error),
                })

    return errors


def aggregate_metadata(
    results: list[dict[str, Any]],
    metadata_key: str = "metadata",
) -> dict[str, Any]:
    """Aggregate metadata from multiple results.

    Deep merges all metadata dictionaries.

    Args:
        results: List of state dicts.
        metadata_key: Key containing metadata.

    Returns:
        Merged metadata dictionary.
    """
    metadata_list = []
    for state in results:
        metadata = state.get(metadata_key)
        if metadata and isinstance(metadata, dict):
            metadata_list.append(metadata)

    return merge_states(metadata_list) if metadata_list else {}


# ============================================================================
# Result Filter
# ============================================================================

def filter_results(
    results: list[dict[str, Any]],
    predicate: Callable[[dict], bool],
) -> list[dict[str, Any]]:
    """Filter results based on a predicate.

    Args:
        results: List of state dicts.
        predicate: Function that returns True for valid results.

    Returns:
        Filtered list of results.
    """
    return [r for r in results if predicate(r)]


def partition_results(
    results: list[dict[str, Any]],
    predicate: Callable[[dict], bool],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Partition results into two groups.

    Args:
        results: List of state dicts.
        predicate: Function that returns True for first group.

    Returns:
        Tuple of (matching, non_matching) results.
    """
    matching = []
    non_matching = []

    for result in results:
        if predicate(result):
            matching.append(result)
        else:
            non_matching.append(result)

    return matching, non_matching
