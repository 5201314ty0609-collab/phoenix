"""
Sequential chain implementation.

Executes steps in sequence, passing output to next step.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from ..core import Config, ExecutionResult, Logger
from .base import Chain, ChainStep, StepResult, StepStatus


class SequentialChain(Chain):
    """
    Sequential chain that executes steps one after another.

    Each step receives the output of the previous step as input.

    Example:
        chain = SequentialChain("transform")
        chain.add_step(ChainStep("uppercase", lambda ctx: ctx["input"].upper()))
        chain.add_step(ChainStep("add_prefix", lambda ctx: f"Result: {ctx['uppercase']}"))

        result = chain.invoke({"input": "hello"})
        # result.data = "Result: HELLO"
    """

    def __init__(self, name: str, config: Optional[Config] = None):
        super().__init__(name, config)
        self._logger = Logger(f"SequentialChain.{name}")

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute steps sequentially.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult with final output
        """
        start_time = time.time()
        context = input_data.copy()
        step_results: List[StepResult] = []
        current_data = None

        self._logger.info(f"Starting sequential chain: {self._name}")

        for step in self._steps:
            self._logger.debug(f"Executing step: {step.name}")

            # Prepare step context
            step_context = {
                **context,
                "current_data": current_data,
                "previous_results": step_results,
            }

            # Execute step
            result = self._execute_step_with_retry(step, step_context)
            step_results.append(result)

            if result.status == StepStatus.FAILED and step.required:
                duration = time.time() - start_time
                self._track_execution(duration)
                return ExecutionResult.error_result(
                    error=f"Step '{step.name}' failed: {result.error}",
                    duration=duration,
                    metadata={"step_results": step_results},
                )

            if result.status == StepStatus.COMPLETED:
                current_data = result.data
                context[step.name] = result.data

        duration = time.time() - start_time
        self._track_execution(duration)

        # Final output
        final_output = current_data if current_data is not None else context

        self._logger.info(
            f"Sequential chain completed: {self._name} in {duration:.3f}s"
        )

        return ExecutionResult.success_result(
            data=final_output,
            duration=duration,
            metadata={"step_results": step_results, "final_context": context},
        )

    def add_step(
        self,
        step: ChainStep,
        position: Optional[int] = None,
    ) -> SequentialChain:
        """
        Add a step to the chain.

        Args:
            step: ChainStep to add
            position: Position to insert (None = append)

        Returns:
            Self for method chaining
        """
        if position is not None:
            self._steps.insert(position, step)
        else:
            self._steps.append(step)
        self._logger.debug(f"Added step: {step.name}")
        return self

    def add_transform(
        self,
        name: str,
        transform_fn: Callable[[Any], Any],
        **kwargs: Any,
    ) -> SequentialChain:
        """
        Add a transformation step.

        Args:
            name: Step name
            transform_fn: Transformation function
            **kwargs: Additional step parameters

        Returns:
            Self for method chaining
        """
        step = ChainStep(
            name=name,
            function=lambda ctx: transform_fn(ctx.get("current_data")),
            **kwargs,
        )
        return self.add_step(step)

    def add_filter(
        self,
        name: str,
        filter_fn: Callable[[Any], bool],
        **kwargs: Any,
    ) -> SequentialChain:
        """
        Add a filter step.

        If filter returns False, chain execution stops.

        Args:
            name: Step name
            filter_fn: Filter function
            **kwargs: Additional step parameters

        Returns:
            Self for method chaining
        """
        def filter_step(ctx: Dict[str, Any]) -> Any:
            data = ctx.get("current_data")
            if filter_fn(data):
                return data
            raise ValueError(f"Filter '{name}' rejected data")

        step = ChainStep(name=name, function=filter_step, **kwargs)
        return self.add_step(step)

    def add_aggregator(
        self,
        name: str,
        aggregate_fn: Callable[[List[Any]], Any],
        **kwargs: Any,
    ) -> SequentialChain:
        """
        Add an aggregator step.

        Collects all previous results and aggregates them.

        Args:
            name: Step name
            aggregate_fn: Aggregation function
            **kwargs: Additional step parameters

        Returns:
            Self for method chaining
        """
        def aggregate_step(ctx: Dict[str, Any]) -> Any:
            previous_results = ctx.get("previous_results", [])
            data = [
                r.data for r in previous_results
                if r.status == StepStatus.COMPLETED
            ]
            return aggregate_fn(data)

        step = ChainStep(name=name, function=aggregate_step, **kwargs)
        return self.add_step(step)

    def __add__(self, other: SequentialChain) -> SequentialChain:
        """
        Combine two sequential chains.

        Args:
            other: Another SequentialChain

        Returns:
            Combined chain
        """
        combined = SequentialChain(
            name=f"{self._name}+{other._name}",
            config=self._config,
        )
        combined._steps = self._steps + other._steps
        return combined

    def __len__(self) -> int:
        """Get number of steps."""
        return len(self._steps)

    def __repr__(self) -> str:
        """String representation."""
        step_names = [s.name for s in self._steps]
        return f"SequentialChain(name='{self._name}', steps={step_names})"


def sequential(
    name: str,
    *functions: Callable[[Dict[str, Any]], Any],
) -> SequentialChain:
    """
    Create a sequential chain from functions.

    Args:
        name: Chain name
        *functions: Functions to execute in sequence

    Returns:
        SequentialChain

    Example:
        chain = sequential(
            "transform",
            lambda ctx: ctx["input"].upper(),
            lambda ctx: f"Result: {ctx['step_0']}",
        )
    """
    chain = SequentialChain(name)
    for i, func in enumerate(functions):
        step = ChainStep(name=f"step_{i}", function=func)
        chain.add_step(step)
    return chain
