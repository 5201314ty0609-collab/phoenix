"""
Conditional router for the PHOENIX AIOS LangGraph framework.

Provides intelligent routing based on state inspection,
supporting complex routing patterns and strategies.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
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

from ..core.constants import END

logger = logging.getLogger(__name__)

# Type variables
StateT = TypeVar("StateT", bound=dict)
T = TypeVar("T")


# ============================================================================
# Routing Strategy Protocol
# ============================================================================

@runtime_checkable
class RoutingStrategy(Protocol[StateT]):
    """Protocol for routing strategies.

    A routing strategy determines which node to execute next
    based on the current state and available targets.
    """

    def select(
        self,
        state: StateT,
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select next node from available targets.

        Args:
            state: Current graph state.
            targets: List of possible target nodes.
            context: Optional routing context.

        Returns:
            Selected target node name.
        """
        ...


# ============================================================================
# Routing Decision
# ============================================================================

@dataclass(frozen=True)
class RoutingDecision:
    """Represents a routing decision.

    Attributes:
        source: Source node name.
        target: Selected target node name.
        reason: Reason for the routing decision.
        confidence: Confidence score (0.0 to 1.0).
        alternatives: List of alternative targets considered.
        metadata: Additional decision metadata.
    """

    source: str
    target: str
    reason: str = ""
    confidence: float = 1.0
    alternatives: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_end(self) -> bool:
        """Check if routing decision is to END."""
        return self.target == END

    def with_target(self, target: str) -> RoutingDecision:
        """Create a new decision with a different target.

        Args:
            target: New target node name.

        Returns:
            New RoutingDecision with updated target.
        """
        return RoutingDecision(
            source=self.source,
            target=target,
            reason=self.reason,
            confidence=self.confidence,
            alternatives=self.alternatives,
            metadata=self.metadata,
        )


# ============================================================================
# Routing Rule
# ============================================================================

@dataclass
class RoutingRule:
    """A rule for conditional routing.

    Attributes:
        name: Rule name for identification.
        condition: Function that evaluates state.
        target: Target node if condition is true.
        priority: Rule priority (higher = checked first).
        description: Human-readable description.
    """

    name: str
    condition: Callable[[dict], bool]
    target: str
    priority: int = 0
    description: str = ""

    def evaluate(self, state: dict[str, Any]) -> bool:
        """Evaluate the rule against state.

        Args:
            state: Current graph state.

        Returns:
            True if condition is met.
        """
        try:
            return self.condition(state)
        except Exception as e:
            logger.warning(f"Rule '{self.name}' evaluation failed: {e}")
            return False


# ============================================================================
# Conditional Router
# ============================================================================

class ConditionalRouter:
    """Router for conditional edge evaluation.

    Manages routing rules and strategies to determine the next
    node in a graph execution based on state inspection.

    Features:
        - Rule-based routing with priorities
        - Multiple routing strategies
        - Fallback behavior
        - Decision logging and history

    Example:
        router = ConditionalRouter()
        router.add_rule(
            name="has_error",
            condition=lambda s: s.get("error") is not None,
            target="error_handler",
            priority=10,
        )
        router.add_rule(
            name="needs_review",
            condition=lambda s: s.get("needs_review", False),
            target="reviewer",
            priority=5,
        )

        decision = router.route(state, ["error_handler", "reviewer", "end"])
    """

    def __init__(
        self,
        default_target: str = END,
        strategy: RoutingStrategy | None = None,
    ) -> None:
        """Initialize the conditional router.

        Args:
            default_target: Default target when no rules match.
            strategy: Optional routing strategy for disambiguation.
        """
        self._default_target = default_target
        self._strategy = strategy
        self._rules: list[RoutingRule] = []
        self._history: list[RoutingDecision] = []
        self._custom_routes: dict[str, Callable[[dict], str]] = {}

    @property
    def rules(self) -> list[RoutingRule]:
        """Get all routing rules."""
        return self._rules.copy()

    @property
    def history(self) -> list[RoutingDecision]:
        """Get routing decision history."""
        return self._history.copy()

    def add_rule(
        self,
        name: str,
        condition: Callable[[dict], bool],
        target: str,
        priority: int = 0,
        description: str = "",
    ) -> None:
        """Add a routing rule.

        Rules are evaluated in priority order (highest first).
        The first matching rule determines the routing target.

        Args:
            name: Unique rule name.
            condition: Function that evaluates state.
            target: Target node if condition is true.
            priority: Rule priority (higher = checked first).
            description: Human-readable description.
        """
        rule = RoutingRule(
            name=name,
            condition=condition,
            target=target,
            priority=priority,
            description=description,
        )
        self._rules.append(rule)
        # Sort by priority (descending)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, name: str) -> bool:
        """Remove a routing rule by name.

        Args:
            name: Rule name to remove.

        Returns:
            True if rule was removed, False if not found.
        """
        original_count = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < original_count

    def add_custom_route(
        self,
        source: str,
        route_fn: Callable[[dict], str],
    ) -> None:
        """Add a custom route function for a specific source node.

        Args:
            source: Source node name.
            route_fn: Routing function (state -> target).
        """
        self._custom_routes[source] = route_fn

    def route(
        self,
        state: dict[str, Any],
        targets: list[str],
        source: str = "",
    ) -> RoutingDecision:
        """Determine the next node based on state.

        Evaluates rules in priority order and returns the first match.
        Falls back to default target if no rules match.

        Args:
            state: Current graph state.
            targets: List of valid target nodes.
            source: Source node name (for logging).

        Returns:
            RoutingDecision with selected target.
        """
        # Check for custom route
        if source in self._custom_routes:
            target = self._custom_routes[source](state)
            decision = RoutingDecision(
                source=source,
                target=target,
                reason="custom_route",
                confidence=1.0,
                alternatives=targets,
            )
            self._history.append(decision)
            return decision

        # Evaluate rules
        for rule in self._rules:
            if rule.evaluate(state):
                if rule.target in targets or rule.target == END:
                    decision = RoutingDecision(
                        source=source,
                        target=rule.target,
                        reason=f"rule:{rule.name}",
                        confidence=1.0,
                        alternatives=targets,
                        metadata={"rule_priority": rule.priority},
                    )
                    self._history.append(decision)
                    return decision
                else:
                    logger.warning(
                        f"Rule '{rule.name}' target '{rule.target}' not in targets"
                    )

        # Use strategy if available
        if self._strategy and targets:
            target = self._strategy.select(state, targets)
            decision = RoutingDecision(
                source=source,
                target=target,
                reason="strategy",
                confidence=0.5,
                alternatives=targets,
            )
            self._history.append(decision)
            return decision

        # Default fallback
        decision = RoutingDecision(
            source=source,
            target=self._default_target,
            reason="default",
            confidence=0.0,
            alternatives=targets,
        )
        self._history.append(decision)
        return decision

    def clear_history(self) -> None:
        """Clear routing decision history."""
        self._history.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get routing statistics.

        Returns:
            Dictionary with routing statistics.
        """
        if not self._history:
            return {"total_decisions": 0}

        target_counts: dict[str, int] = {}
        reason_counts: dict[str, int] = {}

        for decision in self._history:
            target_counts[decision.target] = target_counts.get(decision.target, 0) + 1
            reason_counts[decision.reason] = reason_counts.get(decision.reason, 0) + 1

        return {
            "total_decisions": len(self._history),
            "target_distribution": target_counts,
            "reason_distribution": reason_counts,
            "average_confidence": sum(
                d.confidence for d in self._history
            ) / len(self._history),
        }


# ============================================================================
# Multi-Target Router (for parallel execution)
# ============================================================================

class MultiTargetRouter:
    """Router that supports multiple target selection for parallel execution.

    Extends conditional routing to return multiple targets that
    should execute concurrently.

    Example:
        router = MultiTargetRouter()
        router.add_parallel_route(
            name="process_all",
            condition=lambda s: len(s.get("items", [])) > 0,
            targets=["processor_1", "processor_2", "processor_3"],
        )

        targets = router.route_parallel(state, available_targets)
    """

    def __init__(self) -> None:
        """Initialize multi-target router."""
        self._parallel_rules: list[dict[str, Any]] = []
        self._history: list[list[str]] = []

    def add_parallel_route(
        self,
        name: str,
        condition: Callable[[dict], bool],
        targets: list[str],
        priority: int = 0,
    ) -> None:
        """Add a parallel routing rule.

        Args:
            name: Rule name.
            condition: State condition.
            targets: List of targets to execute in parallel.
            priority: Rule priority.
        """
        self._parallel_rules.append({
            "name": name,
            "condition": condition,
            "targets": targets,
            "priority": priority,
        })
        self._parallel_rules.sort(key=lambda r: r["priority"], reverse=True)

    def route_parallel(
        self,
        state: dict[str, Any],
        available_targets: list[str],
    ) -> list[str]:
        """Select multiple targets for parallel execution.

        Args:
            state: Current graph state.
            available_targets: List of valid target nodes.

        Returns:
            List of target nodes to execute in parallel.
        """
        for rule in self._parallel_rules:
            try:
                if rule["condition"](state):
                    # Filter to available targets
                    targets = [
                        t for t in rule["targets"]
                        if t in available_targets
                    ]
                    if targets:
                        self._history.append(targets)
                        return targets
            except Exception as e:
                logger.warning(f"Parallel rule '{rule['name']}' failed: {e}")

        # Default: return all available targets
        self._history.append(available_targets)
        return available_targets

    @property
    def history(self) -> list[list[str]]:
        """Get routing history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear routing history."""
        self._history.clear()
