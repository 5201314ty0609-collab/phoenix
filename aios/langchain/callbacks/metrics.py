"""
Metrics callback for PHOENIX AIOS LangChain integration.

Provides metrics collection for performance monitoring.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core import Config, Logger
from .base import Callback, CallbackEvent, CallbackEventType


@dataclass
class MetricEntry:
    """
    A single metric entry.

    Attributes:
        name: Metric name
        value: Metric value
        timestamp: Timestamp
        metadata: Additional metadata
    """
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCallback(Callback):
    """
    Metrics callback that collects performance metrics.

    Example:
        callback = MetricsCallback()
        # ... run chain ...
        metrics = callback.get_metrics()
        print(f"Total duration: {metrics['total_duration']}")
    """

    def __init__(self, config: Optional[Config] = None):
        self._config = config or Config()
        self._logger = Logger("MetricsCallback")
        self._metrics: List[MetricEntry] = []
        self._start_times: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}

    @property
    def metrics(self) -> List[MetricEntry]:
        """Get all metrics."""
        return self._metrics.copy()

    def on_chain_start(self, event: CallbackEvent) -> None:
        """Record chain start time."""
        key = f"chain_{event.name}"
        self._start_times[key] = time.time()
        self._increment_counter("chain_starts")

    def on_chain_end(self, event: CallbackEvent) -> None:
        """Record chain duration."""
        key = f"chain_{event.name}"
        if key in self._start_times:
            duration = time.time() - self._start_times.pop(key)
            self._record_metric(f"chain_duration_{event.name}", duration)
            self._increment_counter("chain_completions")

    def on_chain_error(self, event: CallbackEvent) -> None:
        """Record chain error."""
        self._increment_counter("chain_errors")

    def on_step_start(self, event: CallbackEvent) -> None:
        """Record step start time."""
        key = f"step_{event.name}"
        self._start_times[key] = time.time()
        self._increment_counter("step_starts")

    def on_step_end(self, event: CallbackEvent) -> None:
        """Record step duration."""
        key = f"step_{event.name}"
        if key in self._start_times:
            duration = time.time() - self._start_times.pop(key)
            self._record_metric(f"step_duration_{event.name}", duration)
            self._increment_counter("step_completions")

    def on_step_error(self, event: CallbackEvent) -> None:
        """Record step error."""
        self._increment_counter("step_errors")

    def on_tool_start(self, event: CallbackEvent) -> None:
        """Record tool start time."""
        key = f"tool_{event.name}"
        self._start_times[key] = time.time()
        self._increment_counter("tool_starts")

    def on_tool_end(self, event: CallbackEvent) -> None:
        """Record tool duration."""
        key = f"tool_{event.name}"
        if key in self._start_times:
            duration = time.time() - self._start_times.pop(key)
            self._record_metric(f"tool_duration_{event.name}", duration)
            self._increment_counter("tool_completions")

    def on_tool_error(self, event: CallbackEvent) -> None:
        """Record tool error."""
        self._increment_counter("tool_errors")

    def on_llm_start(self, event: CallbackEvent) -> None:
        """Record LLM start time."""
        key = f"llm_{event.name}"
        self._start_times[key] = time.time()
        self._increment_counter("llm_starts")

    def on_llm_end(self, event: CallbackEvent) -> None:
        """Record LLM duration."""
        key = f"llm_{event.name}"
        if key in self._start_times:
            duration = time.time() - self._start_times.pop(key)
            self._record_metric(f"llm_duration_{event.name}", duration)
            self._increment_counter("llm_completions")

    def on_llm_error(self, event: CallbackEvent) -> None:
        """Record LLM error."""
        self._increment_counter("llm_errors")

    def on_llm_token(self, event: CallbackEvent) -> None:
        """Record LLM token."""
        self._increment_counter("llm_tokens")

    def _record_metric(self, name: str, value: float, **metadata: Any) -> None:
        """Record a metric."""
        entry = MetricEntry(
            name=name,
            value=value,
            metadata=metadata,
        )
        self._metrics.append(entry)

    def _increment_counter(self, name: str) -> None:
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        Returns:
            Dictionary of metrics
        """
        # Calculate durations
        durations: Dict[str, List[float]] = {}
        for metric in self._metrics:
            if "duration" in metric.name:
                base_name = metric.name.split("_duration_")[0]
                if base_name not in durations:
                    durations[base_name] = []
                durations[base_name].append(metric.value)

        # Calculate statistics
        stats = {}
        for name, values in durations.items():
            if values:
                stats[f"{name}_count"] = len(values)
                stats[f"{name}_total"] = sum(values)
                stats[f"{name}_avg"] = sum(values) / len(values)
                stats[f"{name}_min"] = min(values)
                stats[f"{name}_max"] = max(values)

        return {
            "counters": self._counters.copy(),
            "durations": stats,
            "total_metrics": len(self._metrics),
        }

    def get_counter(self, name: str) -> int:
        """
        Get counter value.

        Args:
            name: Counter name

        Returns:
            Counter value
        """
        return self._counters.get(name, 0)

    def get_duration_stats(self, prefix: str) -> Dict[str, float]:
        """
        Get duration statistics for a prefix.

        Args:
            prefix: Metric prefix (e.g., "chain", "step")

        Returns:
            Dictionary of statistics
        """
        values = [
            m.value for m in self._metrics
            if m.name.startswith(f"{prefix}_duration_")
        ]

        if not values:
            return {
                "count": 0,
                "total": 0.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        return {
            "count": len(values),
            "total": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._start_times.clear()
        self._counters.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"MetricsCallback(metrics={len(self._metrics)})"
