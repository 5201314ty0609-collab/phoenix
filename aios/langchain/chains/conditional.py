"""
Conditional chain implementation.

Executes different steps based on conditions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from ..core import Config, ExecutionResult, Logger
from .base import Chain, ChainStep, StepResult, StepStatus


@dataclass(frozen=True)
class Condition:
    """
    Condition for conditional chain branching.

    Attributes:
        name: Condition name
        predicate: Function that returns True if condition is met
        chain: Chain to execute if condition is met
        priority: Priority (higher = checked first)
    """
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    chain: Chain
    priority: int = 0


class ConditionalChain(Chain):
    """
    Conditional chain that executes different paths based on conditions.

    Evaluates conditions in priority order and executes the first matching chain.

    Example:
        chain = ConditionalChain("router")

        chain.add_condition(Condition(
            name="is_english",
            predicate=lambda ctx: ctx.get("language") == "en",
            chain=english_chain,
            priority=10,
        ))

        chain.add_condition(Condition(
            name="is_spanish",
            predicate=lambda ctx: ctx.get("language") == "es",
            chain=spanish_chain,
            priority=5,
        ))

        chain.set_default(default_chain)

        result = chain.invoke({"language": "en", "text": "hello"})
    """

    def __init__(self, name: str, config: Optional[Config] = None):
        super().__init__(name, config)
        self._conditions: List[Condition] = []
        self._default_chain: Optional[Chain] = None
        self._logger = Logger(f"ConditionalChain.{name}")

    def add_condition(self, condition: Condition) -> ConditionalChain:
        """
        Add a condition.

        Args:
            condition: Condition to add

        Returns:
            Self for method chaining
        """
        self._conditions.append(condition)
        self._conditions.sort(key=lambda c: c.priority, reverse=True)
        self._logger.debug(f"Added condition: {condition.name}")
        return self

    def set_default(self, chain: Chain) -> ConditionalChain:
        """
        Set default chain to execute when no conditions match.

        Args:
            chain: Default chain

        Returns:
            Self for method chaining
        """
        self._default_chain = chain
        return self

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute chain based on conditions.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult with output from matching chain
        """
        start_time = time.time()
        context = input_data.copy()

        self._logger.info(f"Starting conditional chain: {self._name}")

        # Evaluate conditions
        for condition in self._conditions:
            try:
                if condition.predicate(context):
                    self._logger.info(f"Condition matched: {condition.name}")
                    result = condition.chain.invoke(context)

                    duration = time.time() - start_time
                    self._track_execution(duration)

                    return ExecutionResult.success_result(
                        data=result.data,
                        duration=duration,
                        metadata={
                            "matched_condition": condition.name,
                            "chain_result": result,
                        },
                    )
            except Exception as e:
                self._logger.warning(
                    f"Condition '{condition.name}' evaluation failed: {e}"
                )

        # Execute default chain
        if self._default_chain:
            self._logger.info("No conditions matched, executing default chain")
            result = self._default_chain.invoke(context)

            duration = time.time() - start_time
            self._track_execution(duration)

            return ExecutionResult.success_result(
                data=result.data,
                duration=duration,
                metadata={"matched_condition": "default", "chain_result": result},
            )

        # No matching condition and no default
        duration = time.time() - start_time
        self._track_execution(duration)

        return ExecutionResult.error_result(
            error="No matching condition and no default chain set",
            duration=duration,
        )

    def get_conditions(self) -> List[Condition]:
        """Get all conditions."""
        return self._conditions.copy()

    def remove_condition(self, condition_name: str) -> bool:
        """
        Remove a condition by name.

        Args:
            condition_name: Name of condition to remove

        Returns:
            True if removed, False if not found
        """
        for i, condition in enumerate(self._conditions):
            if condition.name == condition_name:
                self._conditions.pop(i)
                self._logger.debug(f"Removed condition: {condition_name}")
                return True
        return False

    def __repr__(self) -> str:
        """String representation."""
        condition_names = [c.name for c in self._conditions]
        return (
            f"ConditionalChain(name='{self._name}', "
            f"conditions={condition_names}, "
            f"has_default={self._default_chain is not None})"
        )


def conditional(
    name: str,
    conditions: List[Condition],
    default: Optional[Chain] = None,
) -> ConditionalChain:
    """
    Create a conditional chain.

    Args:
        name: Chain name
        conditions: List of conditions
        default: Default chain

    Returns:
        ConditionalChain

    Example:
        chain = conditional(
            "router",
            [
                Condition("is_english", lambda ctx: ctx["lang"] == "en", english_chain),
                Condition("is_spanish", lambda ctx: ctx["lang"] == "es", spanish_chain),
            ],
            default=default_chain,
        )
    """
    chain = ConditionalChain(name)
    for condition in conditions:
        chain.add_condition(condition)
    if default:
        chain.set_default(default)
    return chain


def switch(
    name: str,
    key_fn: Callable[[Dict[str, Any]], str],
    branches: Dict[str, Chain],
    default: Optional[Chain] = None,
) -> ConditionalChain:
    """
    Create a switch-style conditional chain.

    Args:
        name: Chain name
        key_fn: Function to extract switch key
        branches: Dict mapping keys to chains
        default: Default chain

    Returns:
        ConditionalChain

    Example:
        chain = switch(
            "router",
            key_fn=lambda ctx: ctx["action"],
            branches={
                "search": search_chain,
                "create": create_chain,
                "update": update_chain,
            },
            default=error_chain,
        )
    """
    conditions = []
    for key, branch_chain in branches.items():
        condition = Condition(
            name=f"is_{key}",
            predicate=lambda ctx, k=key: key_fn(ctx) == k,
            chain=branch_chain,
        )
        conditions.append(condition)

    return conditional(name, conditions, default)


class RouterChain(Chain):
    """
    Router chain that dynamically selects chains based on input.

    Uses a router function to determine which chain to execute.

    Example:
        def router(ctx):
            if ctx["type"] == "question":
                return qa_chain
            elif ctx["type"] == "command":
                return command_chain
            return default_chain

        chain = RouterChain("router", router)
        result = chain.invoke({"type": "question", "input": "..."})
    """

    def __init__(
        self,
        name: str,
        router_fn: Callable[[Dict[str, Any]], Chain],
        config: Optional[Config] = None,
    ):
        super().__init__(name, config)
        self._router_fn = router_fn
        self._logger = Logger(f"RouterChain.{name}")

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Route and execute chain.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult from selected chain
        """
        start_time = time.time()
        context = input_data.copy()

        self._logger.info(f"Starting router chain: {self._name}")

        try:
            # Select chain
            selected_chain = self._router_fn(context)
            self._logger.info(f"Selected chain: {selected_chain.name}")

            # Execute selected chain
            result = selected_chain.invoke(context)

            duration = time.time() - start_time
            self._track_execution(duration)

            return ExecutionResult.success_result(
                data=result.data,
                duration=duration,
                metadata={"selected_chain": selected_chain.name},
            )
        except Exception as e:
            duration = time.time() - start_time
            self._track_execution(duration)

            return ExecutionResult.error_result(
                error=f"Router chain failed: {e}",
                duration=duration,
            )
