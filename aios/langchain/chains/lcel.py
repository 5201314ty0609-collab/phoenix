"""
LCEL (LangChain Expression Language) chain implementation.

Provides composable chain operations using the pipe operator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from ..core import BaseComponent, Config, ExecutionResult, Logger
from .base import Chain, ChainStep, StepResult, StepStatus


@dataclass(frozen=True)
class LCELStep:
    """
    A step in an LCEL chain.

    Attributes:
        name: Step name
        function: Transformation function
        description: Step description
    """
    name: str
    function: Callable[[Any], Any]
    description: str = ""

    def invoke(self, input_data: Any) -> Any:
        """Execute the step."""
        return self.function(input_data)


class LCELChain(BaseComponent):
    """
    LCEL-style chain with pipe operator support.

    Enables composable chain construction using the | operator.

    Example:
        chain = (
            LCELChain("transform")
            | step1
            | step2
            | step3
        )

        result = chain.invoke({"input": "hello"})
    """

    def __init__(self, name: str, config: Optional[Config] = None):
        super().__init__(config)
        self._name = name
        self._steps: List[LCELStep] = []
        self._logger = Logger(f"LCELChain.{name}")

    @property
    def name(self) -> str:
        """Get chain name."""
        return self._name

    @property
    def steps(self) -> List[LCELStep]:
        """Get chain steps."""
        return self._steps.copy()

    def __or__(self, other: Union[LCELStep, Callable[[Any], Any]]) -> LCELChain:
        """
        Pipe operator for composing chains.

        Args:
            other: LCELStep or callable to add

        Returns:
            New LCELChain with added step
        """
        if callable(other) and not isinstance(other, LCELStep):
            # Wrap callable in LCELStep
            step = LCELStep(
                name=f"step_{len(self._steps)}",
                function=other,
            )
        elif isinstance(other, LCELStep):
            step = other
        else:
            raise TypeError(f"Cannot pipe {type(other)}")

        # Create new chain (immutable)
        new_chain = LCELChain(self._name, self._config)
        new_chain._steps = self._steps + [step]
        return new_chain

    def __ror__(self, other: Union[LCELStep, Callable[[Any], Any]]) -> LCELChain:
        """
        Reverse pipe operator.

        Args:
            other: LCELStep or callable to add

        Returns:
            New LCELChain with added step
        """
        if callable(other) and not isinstance(other, LCELStep):
            step = LCELStep(
                name=f"step_0",
                function=other,
            )
        elif isinstance(other, LCELStep):
            step = other
        else:
            raise TypeError(f"Cannot pipe {type(other)}")

        new_chain = LCELChain(self._name, self._config)
        new_chain._steps = [step] + self._steps
        return new_chain

    def invoke(self, input_data: Any) -> ExecutionResult:
        """
        Execute the chain with given input.

        Args:
            input_data: Input data (any type)

        Returns:
            ExecutionResult with final output
        """
        start_time = time.time()
        current_data = input_data
        step_results: List[StepResult] = []

        self._logger.info(f"Starting LCEL chain execution: {self._name}")

        for step in self._steps:
            self._logger.debug(f"Executing step: {step.name}")
            step_start = time.time()

            try:
                current_data = step.invoke(current_data)
                step_duration = time.time() - step_start
                step_results.append(
                    StepResult.success(step.name, current_data, step_duration)
                )
            except Exception as e:
                step_duration = time.time() - step_start
                step_results.append(
                    StepResult.error(step.name, str(e), step_duration)
                )
                duration = time.time() - start_time
                self._track_execution(duration)
                return ExecutionResult.error_result(
                    error=f"Step '{step.name}' failed: {e}",
                    duration=duration,
                    metadata={"step_results": step_results},
                )

        duration = time.time() - start_time
        self._track_execution(duration)

        self._logger.info(
            f"LCEL chain execution completed: {self._name} in {duration:.3f}s"
        )

        return ExecutionResult.success_result(
            data=current_data,
            duration=duration,
            metadata={"step_results": step_results},
        )

    def batch(self, inputs: List[Any]) -> List[ExecutionResult]:
        """
        Execute chain with multiple inputs.

        Args:
            inputs: List of inputs

        Returns:
            List of ExecutionResult
        """
        return [self.invoke(input_data) for input_data in inputs]

    def stream(self, input_data: Any):
        """
        Stream execution results.

        Args:
            input_data: Input data

        Yields:
            Intermediate results
        """
        current_data = input_data

        for step in self._steps:
            self._logger.debug(f"Streaming step: {step.name}")
            try:
                current_data = step.invoke(current_data)
                yield {"step": step.name, "data": current_data}
            except Exception as e:
                yield {"step": step.name, "error": str(e)}
                return

    def __len__(self) -> int:
        """Get number of steps."""
        return len(self._steps)

    def __repr__(self) -> str:
        """String representation."""
        step_names = [s.name for s in self._steps]
        return f"LCELChain(name='{self._name}', steps={step_names})"


def pipe(*functions: Callable[[Any], Any]) -> LCELChain:
    """
    Create an LCEL chain from functions.

    Args:
        *functions: Functions to chain

    Returns:
        LCELChain

    Example:
        chain = pipe(
            lambda x: x + 1,
            lambda x: x * 2,
            lambda x: str(x),
        )
        result = chain.invoke(5)  # "12"
    """
    chain = LCELChain("pipe")
    for i, func in enumerate(functions):
        step = LCELStep(name=f"step_{i}", function=func)
        chain = chain | step
    return chain


def parallel(*chains: LCELChain) -> ParallelLCELChain:
    """
    Create a parallel chain from multiple LCEL chains.

    Args:
        *chains: Chains to run in parallel

    Returns:
        ParallelLCELChain
    """
    return ParallelLCELChain(list(chains))


class ParallelLCELChain(BaseComponent):
    """
    Parallel execution of multiple LCEL chains.

    Runs multiple chains on the same input and collects results.
    """

    def __init__(self, chains: List[LCELChain], config: Optional[Config] = None):
        super().__init__(config)
        self._chains = chains
        self._logger = Logger("ParallelLCELChain")

    def invoke(self, input_data: Any) -> ExecutionResult:
        """
        Execute all chains in parallel.

        Args:
            input_data: Input data

        Returns:
            ExecutionResult with list of results
        """
        import concurrent.futures

        start_time = time.time()
        results: List[ExecutionResult] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(chain.invoke, input_data): chain
                for chain in self._chains
            }

            for future in concurrent.futures.as_completed(futures):
                chain = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(
                        ExecutionResult.error_result(
                            error=f"Chain '{chain.name}' failed: {e}"
                        )
                    )

        duration = time.time() - start_time
        self._track_execution(duration)

        return ExecutionResult.success_result(
            data=[r.data for r in results],
            duration=duration,
            metadata={"chain_results": results},
        )

    def __or__(self, other: Union[LCELStep, Callable]) -> LCELChain:
        """Pipe to sequential execution."""
        # Convert to sequential after parallel
        chain = LCELChain("parallel_then_sequential")
        chain._steps = [LCELStep(name="parallel", function=lambda x: self.invoke(x).data)]
        return chain | other
