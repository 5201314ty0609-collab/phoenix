"""
Routing strategies for the PHOENIX AIOS LangGraph framework.

Provides multiple routing strategies for different use cases:
- Priority-based routing
- Round-robin routing
- Random routing
- Weighted routing
- State-based routing
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ============================================================================
# Base Strategy
# ============================================================================

class BaseRoutingStrategy(ABC):
    """Base class for routing strategies."""

    @abstractmethod
    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select a target from available options.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Selected target node name.
        """
        ...


# ============================================================================
# Priority Router
# ============================================================================

class PriorityRouter(BaseRoutingStrategy):
    """Routes based on target priorities.

    Each target has a fixed priority, and the highest priority
    target is always selected.

    Example:
        router = PriorityRouter({
            "critical_handler": 100,
            "normal_handler": 50,
            "fallback": 0,
        })
        target = router.select(state, ["critical_handler", "normal_handler"])
    """

    def __init__(self, priorities: dict[str, int] | None = None) -> None:
        """Initialize priority router.

        Args:
            priorities: Map of target names to priority values.
        """
        self._priorities: dict[str, int] = priorities or {}

    def set_priority(self, target: str, priority: int) -> None:
        """Set priority for a target.

        Args:
            target: Target node name.
            priority: Priority value (higher = preferred).
        """
        self._priorities[target] = priority

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select highest priority target.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Highest priority target.
        """
        if not targets:
            raise ValueError("No targets available")

        # Get priorities for available targets
        prioritized = [
            (t, self._priorities.get(t, 0))
            for t in targets
        ]

        # Sort by priority (descending)
        prioritized.sort(key=lambda x: x[1], reverse=True)

        return prioritized[0][0]


# ============================================================================
# Round Robin Router
# ============================================================================

class RoundRobinRouter(BaseRoutingStrategy):
    """Routes in round-robin fashion.

    Cycles through targets sequentially, distributing load evenly.

    Example:
        router = RoundRobinRouter()
        target1 = router.select(state, ["a", "b", "c"])  # "a"
        target2 = router.select(state, ["a", "b", "c"])  # "b"
        target3 = router.select(state, ["a", "b", "c"])  # "c"
        target4 = router.select(state, ["a", "b", "c"])  # "a" (cycles)
    """

    def __init__(self) -> None:
        """Initialize round-robin router."""
        self._index: int = 0
        self._target_history: list[str] = []

    @property
    def current_index(self) -> int:
        """Get current index."""
        return self._index

    @property
    def history(self) -> list[str]:
        """Get target selection history."""
        return self._target_history.copy()

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select next target in round-robin order.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Next target in sequence.
        """
        if not targets:
            raise ValueError("No targets available")

        # Ensure index is within bounds
        self._index = self._index % len(targets)

        # Select target
        target = targets[self._index]
        self._target_history.append(target)

        # Advance index
        self._index = (self._index + 1) % len(targets)

        return target

    def reset(self) -> None:
        """Reset the round-robin counter."""
        self._index = 0


# ============================================================================
# Random Router
# ============================================================================

class RandomRouter(BaseRoutingStrategy):
    """Routes randomly.

    Selects a random target from available options.
    Useful for load balancing when order doesn't matter.

    Example:
        router = RandomRouter(seed=42)
        target = router.select(state, ["a", "b", "c"])
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize random router.

        Args:
            seed: Optional random seed for reproducibility.
        """
        self._rng = random.Random(seed)
        self._target_history: list[str] = []

    @property
    def history(self) -> list[str]:
        """Get target selection history."""
        return self._target_history.copy()

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select a random target.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Randomly selected target.
        """
        if not targets:
            raise ValueError("No targets available")

        target = self._rng.choice(targets)
        self._target_history.append(target)
        return target


# ============================================================================
# Weighted Router
# ============================================================================

class WeightedRouter(BaseRoutingStrategy):
    """Routes based on weights.

    Selects targets probabilistically based on assigned weights.
    Higher weight = higher probability of selection.

    Example:
        router = WeightedRouter({
            "fast_path": 0.7,
            "slow_path": 0.2,
            "fallback": 0.1,
        })
        target = router.select(state, ["fast_path", "slow_path", "fallback"])
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        """Initialize weighted router.

        Args:
            weights: Map of target names to weights.
        """
        self._weights: dict[str, float] = weights or {}
        self._target_history: list[str] = []

    def set_weight(self, target: str, weight: float) -> None:
        """Set weight for a target.

        Args:
            target: Target node name.
            weight: Weight value (higher = more likely).
        """
        self._weights[target] = weight

    @property
    def history(self) -> list[str]:
        """Get target selection history."""
        return self._target_history.copy()

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select target based on weights.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Weight-selected target.
        """
        if not targets:
            raise ValueError("No targets available")

        # Get weights for available targets
        available_weights = [
            self._weights.get(t, 1.0)
            for t in targets
        ]

        # Normalize weights
        total = sum(available_weights)
        if total == 0:
            # All weights are 0, select randomly
            target = random.choice(targets)
        else:
            # Weighted random selection
            r = random.random() * total
            cumulative = 0.0
            target = targets[-1]  # Default to last

            for i, w in enumerate(available_weights):
                cumulative += w
                if r <= cumulative:
                    target = targets[i]
                    break

        self._target_history.append(target)
        return target


# ============================================================================
# State-Based Router
# ============================================================================

class StateBasedRouter(BaseRoutingStrategy):
    """Routes based on state evaluation.

    Uses custom functions to evaluate state and select targets.
    Each target has an associated scoring function.

    Example:
        router = StateBasedRouter()
        router.add_scorer(
            "fast_handler",
            lambda s: 1.0 if s.get("complexity", 0) < 0.5 else 0.0,
        )
        router.add_scorer(
            "thorough_handler",
            lambda s: 1.0 if s.get("complexity", 0) >= 0.5 else 0.0,
        )
        target = router.select(state, ["fast_handler", "thorough_handler"])
    """

    def __init__(self) -> None:
        """Initialize state-based router."""
        self._scorers: dict[str, Callable[[dict], float]] = {}
        self._target_history: list[str] = []

    def add_scorer(
        self,
        target: str,
        scorer: Callable[[dict], float],
    ) -> None:
        """Add a scoring function for a target.

        Args:
            target: Target node name.
            scorer: Function that returns a score (0.0 to 1.0).
        """
        self._scorers[target] = scorer

    @property
    def history(self) -> list[str]:
        """Get target selection history."""
        return self._target_history.copy()

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select target based on state evaluation.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Highest-scoring target.
        """
        if not targets:
            raise ValueError("No targets available")

        # Score each target
        scores: list[tuple[str, float]] = []
        for target in targets:
            if target in self._scorers:
                try:
                    score = self._scorers[target](state)
                    scores.append((target, score))
                except Exception as e:
                    logger.warning(f"Scorer for '{target}' failed: {e}")
                    scores.append((target, 0.0))
            else:
                # Default score for unscored targets
                scores.append((target, 0.5))

        # Select highest scoring target
        scores.sort(key=lambda x: x[1], reverse=True)
        target = scores[0][0]

        self._target_history.append(target)
        return target


# ============================================================================
# Composite Router
# ============================================================================

class CompositeRouter(BaseRoutingStrategy):
    """Combines multiple routing strategies.

    Tries strategies in order until one succeeds.
    Useful for fallback patterns.

    Example:
        router = CompositeRouter([
            StateBasedRouter(),
            PriorityRouter({"default": 0}),
            RoundRobinRouter(),
        ])
        target = router.select(state, ["a", "b", "c"])
    """

    def __init__(self, strategies: list[BaseRoutingStrategy]) -> None:
        """Initialize composite router.

        Args:
            strategies: List of strategies to try in order.
        """
        self._strategies = strategies
        self._target_history: list[str] = []

    @property
    def history(self) -> list[str]:
        """Get target selection history."""
        return self._target_history.copy()

    def select(
        self,
        state: dict[str, Any],
        targets: list[str],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Select target using composite strategy.

        Tries each strategy in order until one succeeds.

        Args:
            state: Current graph state.
            targets: List of possible targets.
            context: Optional routing context.

        Returns:
            Selected target.
        """
        if not targets:
            raise ValueError("No targets available")

        for strategy in self._strategies:
            try:
                target = strategy.select(state, targets, context)
                self._target_history.append(target)
                return target
            except Exception as e:
                logger.warning(f"Strategy {type(strategy).__name__} failed: {e}")
                continue

        # Fallback to first target
        target = targets[0]
        self._target_history.append(target)
        return target
