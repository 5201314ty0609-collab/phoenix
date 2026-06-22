"""
Parallel execution module for the PHOENIX AIOS LangGraph framework.

Provides fan-out/fan-in patterns, concurrent node execution,
and result aggregation.
"""

from .executor import (
    Send,
    parallel_execute,
    FanOutResult,
    ParallelConfig,
    ParallelExecutor,
)
from .aggregators import (
    aggregate_results,
    merge_states,
    reduce_results,
    AggregateStrategy,
)

__all__ = [
    "Send",
    "parallel_execute",
    "FanOutResult",
    "ParallelConfig",
    "ParallelExecutor",
    "aggregate_results",
    "merge_states",
    "reduce_results",
    "AggregateStrategy",
]
