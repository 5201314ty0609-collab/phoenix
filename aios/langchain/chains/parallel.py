"""
Parallel chain implementation.

Executes multiple steps in parallel and aggregates results.
"""

from __future__ import annotations

import time
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional

from ..core import Config, ExecutionResult, Logger
from .base import Chain, ChainStep, StepResult, StepStatus


class ParallelChain(Chain):
    """
    Parallel chain that executes steps concurrently.

    All steps receive the same input and execute in parallel.
    Results are collected and optionally aggregated.

    Example:
        chain = ParallelChain("analysis")
        chain.add_step(ChainStep("sentiment", analyze_sentiment))
        chain.add_step(ChainStep("keywords", extract_keywords))
        chain.add_step(ChainStep("summary", generate_summary))

        result = chain.invoke({"text": "..."})
        # result.data = {"sentiment": ..., "keywords": ..., "summary": ...}
    """

    def __init__(
        self,
        name: str,
        config: Optional[Config] = None,
        max_workers: Optional[int] = None,
    ):
        super().__init__(name, config)
        self._max_workers = max_workers
        self._logger = Logger(f"ParallelChain.{name}")
        self._aggregator: Optional[Callable[[Dict[str, Any]], Any]] = None

    @property
    def max_workers(self) -> Optional[int]:
        """Get maximum worker count."""
        return self._max_workers

    def set_aggregator(
        self, aggregator: Callable[[Dict[str, Any]], Any]
    ) -> ParallelChain:
        """
        Set aggregation function for combining results.

        Args:
            aggregator: Function that takes dict of results and returns combined result

        Returns:
            Self for method chaining
        """
        self._aggregator = aggregator
        return self

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute steps in parallel.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult with aggregated output
        """
        start_time = time.time()
        context = input_data.copy()
        step_results: List[StepResult] = []
        results: Dict[str, Any] = {}

        self._logger.info(f"Starting parallel chain: {self._name}")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers
        ) as executor:
            # Submit all steps
            future_to_step = {}
            for step in self._steps:
                future = executor.submit(self._execute_step_safe, step, context)
                future_to_step[future] = step

            # Collect results
            for future in concurrent.futures.as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    result = future.result()
                    step_results.append(result)

                    if result.status == StepStatus.COMPLETED:
                        results[step.name] = result.data
                    elif step.required:
                        # Required step failed
                        duration = time.time() - start_time
                        self._track_execution(duration)
                        return ExecutionResult.error_result(
                            error=f"Required step '{step.name}' failed: {result.error}",
                            duration=duration,
                            metadata={"step_results": step_results},
                        )
                except Exception as e:
                    step_results.append(
                        StepResult.error(step.name, str(e))
                    )

        duration = time.time() - start_time
        self._track_execution(duration)

        # Aggregate results
        if self._aggregator:
            try:
                final_output = self._aggregator(results)
            except Exception as e:
                return ExecutionResult.error_result(
                    error=f"Aggregation failed: {e}",
                    duration=duration,
                    metadata={"step_results": step_results, "partial_results": results},
                )
        else:
            final_output = results

        self._logger.info(
            f"Parallel chain completed: {self._name} in {duration:.3f}s"
        )

        return ExecutionResult.success_result(
            data=final_output,
            duration=duration,
            metadata={"step_results": step_results},
        )

    def _execute_step_safe(
        self, step: ChainStep, context: Dict[str, Any]
    ) -> StepResult:
        """Execute a step with error handling."""
        try:
            return self._execute_step_with_retry(step, context)
        except Exception as e:
            return StepResult.error(step.name, str(e))

    def add_step(self, step: ChainStep) -> ParallelChain:
        """
        Add a step to the chain.

        Args:
            step: ChainStep to add

        Returns:
            Self for method chaining
        """
        self._steps.append(step)
        self._logger.debug(f"Added step: {step.name}")
        return self

    def add_branch(
        self,
        name: str,
        branch_fn: Callable[[Dict[str, Any]], Any],
        **kwargs: Any,
    ) -> ParallelChain:
        """
        Add a branch step.

        Args:
            name: Branch name
            branch_fn: Branch function
            **kwargs: Additional step parameters

        Returns:
            Self for method chaining
        """
        step = ChainStep(name=name, function=branch_fn, **kwargs)
        return self.add_step(step)

    def __add__(self, other: Chain) -> Chain:
        """
        Combine with another chain.

        Parallel chain runs first, then the other chain.

        Args:
            other: Another chain

        Returns:
            Combined chain
        """
        from .sequential import SequentialChain

        combined = SequentialChain(
            name=f"{self._name}+{other._name}",
            config=self._config,
        )
        combined.add_step(
            ChainStep(
                name=f"parallel_{self._name}",
                function=lambda ctx: self.invoke(ctx).data,
            )
        )
        for step in other.steps:
            combined.add_step(step)
        return combined

    def __len__(self) -> int:
        """Get number of steps."""
        return len(self._steps)

    def __repr__(self) -> str:
        """String representation."""
        step_names = [s.name for s in self._steps]
        return f"ParallelChain(name='{self._name}', steps={step_names})"


def parallel(
    name: str,
    *functions: Callable[[Dict[str, Any]], Any],
    max_workers: Optional[int] = None,
) -> ParallelChain:
    """
    Create a parallel chain from functions.

    Args:
        name: Chain name
        *functions: Functions to execute in parallel
        max_workers: Maximum worker count

    Returns:
        ParallelChain

    Example:
        chain = parallel(
            "analysis",
            lambda ctx: analyze_sentiment(ctx["text"]),
            lambda ctx: extract_keywords(ctx["text"]),
        )
    """
    chain = ParallelChain(name, max_workers=max_workers)
    for i, func in enumerate(functions):
        step = ChainStep(name=f"branch_{i}", function=func)
        chain.add_step(step)
    return chain


def fan_out_fan_in(
    name: str,
    fan_out_fn: Callable[[Any], List[Any]],
    worker_fns: List[Callable[[Any], Any]],
    fan_in_fn: Callable[[List[Any]], Any],
) -> Chain:
    """
    Create a fan-out/fan-in pattern.

    Args:
        name: Chain name
        fan_out_fn: Function to split input
        worker_fns: List of worker functions
        fan_in_fn: Function to combine results

    Returns:
        Chain implementing fan-out/fan-in
    """
    from .sequential import SequentialChain

    chain = SequentialChain(name)

    # Fan out
    chain.add_step(
        ChainStep(
            name="fan_out",
            function=lambda ctx: fan_out_fn(ctx["input"]),
        )
    )

    # Parallel workers
    def parallel_workers(ctx: Dict[str, Any]) -> List[Any]:
        items = ctx["fan_out"]
        results = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for i, (item, worker_fn) in enumerate(
                zip(items, worker_fns[:len(items)])
            ):
                futures.append(executor.submit(worker_fn, item))

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        return results

    chain.add_step(
        ChainStep(name="parallel_workers", function=parallel_workers)
    )

    # Fan in
    chain.add_step(
        ChainStep(
            name="fan_in",
            function=lambda ctx: fan_in_fn(ctx["parallel_workers"]),
        )
    )

    return chain
