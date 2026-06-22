"""
Base chain module for PHOENIX AIOS LangChain integration.

Provides abstract base classes for chain components.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

from ..core import BaseComponent, Config, ExecutionResult, Logger

T = TypeVar("T")


class StepStatus(Enum):
    """Status of a chain step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StepResult:
    """
    Result of a single chain step execution.

    Attributes:
        step_name: Name of the step
        status: Execution status
        data: Output data
        error: Error message if failed
        duration: Execution duration in seconds
        metadata: Additional metadata
    """
    step_name: str
    status: StepStatus
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, step_name: str, data: Any, duration: float = 0.0) -> StepResult:
        """Create a successful step result."""
        return cls(
            step_name=step_name,
            status=StepStatus.COMPLETED,
            data=data,
            duration=duration,
        )

    @classmethod
    def error(cls, step_name: str, error: str, duration: float = 0.0) -> StepResult:
        """Create an error step result."""
        return cls(
            step_name=step_name,
            status=StepStatus.FAILED,
            error=error,
            duration=duration,
        )

    @classmethod
    def skipped(cls, step_name: str) -> StepResult:
        """Create a skipped step result."""
        return cls(
            step_name=step_name,
            status=StepStatus.SKIPPED,
        )


@dataclass(frozen=True)
class ChainStep:
    """
    A single step in a chain.

    Attributes:
        name: Step name
        function: Function to execute
        description: Step description
        required: Whether step is required
        retry_count: Number of retries on failure
        timeout: Step timeout in seconds
    """
    name: str
    function: Callable[[Dict[str, Any]], Any]
    description: str = ""
    required: bool = True
    retry_count: int = 0
    timeout: Optional[float] = None

    def execute(self, context: Dict[str, Any]) -> StepResult:
        """
        Execute the step with given context.

        Args:
            context: Execution context

        Returns:
            StepResult with output or error
        """
        start_time = time.time()

        try:
            result = self.function(context)
            duration = time.time() - start_time
            return StepResult.success(self.name, result, duration)
        except Exception as e:
            duration = time.time() - start_time
            return StepResult.error(self.name, str(e), duration)


class Chain(BaseComponent):
    """
    Base chain class for composing operations.

    A chain consists of multiple steps that execute in sequence,
    passing context between them.

    Example:
        chain = Chain("my_chain")
        chain.add_step(ChainStep("step1", lambda ctx: ctx["input"]))
        chain.add_step(ChainStep("step2", lambda ctx: ctx["step1"] + "!"))

        result = chain.invoke({"input": "hello"})
    """

    def __init__(self, name: str, config: Optional[Config] = None):
        super().__init__(config)
        self._name = name
        self._steps: List[ChainStep] = []
        self._logger = Logger(f"Chain.{name}")

    @property
    def name(self) -> str:
        """Get chain name."""
        return self._name

    @property
    def steps(self) -> List[ChainStep]:
        """Get chain steps."""
        return self._steps.copy()

    def add_step(self, step: ChainStep) -> Chain:
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

    def remove_step(self, step_name: str) -> bool:
        """
        Remove a step by name.

        Args:
            step_name: Name of step to remove

        Returns:
            True if removed, False if not found
        """
        for i, step in enumerate(self._steps):
            if step.name == step_name:
                self._steps.pop(i)
                self._logger.debug(f"Removed step: {step_name}")
                return True
        return False

    def clear_steps(self) -> None:
        """Remove all steps from the chain."""
        self._steps.clear()
        self._logger.debug("Cleared all steps")

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the chain with given input.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult with final output
        """
        start_time = time.time()
        context = input_data.copy()
        step_results: List[StepResult] = []

        self._logger.info(f"Starting chain execution: {self._name}")

        for step in self._steps:
            self._logger.debug(f"Executing step: {step.name}")

            # Execute with retries
            result = self._execute_step_with_retry(step, context)
            step_results.append(result)

            if result.status == StepStatus.FAILED and step.required:
                duration = time.time() - start_time
                self._track_execution(duration)
                return ExecutionResult.error_result(
                    error=f"Required step '{step.name}' failed: {result.error}",
                    duration=duration,
                    metadata={"step_results": step_results},
                )

            # Update context with step result
            if result.status == StepStatus.COMPLETED:
                context[step.name] = result.data

        duration = time.time() - start_time
        self._track_execution(duration)

        # Get final output
        final_output = context.get("output", context)

        self._logger.info(
            f"Chain execution completed: {self._name} in {duration:.3f}s"
        )

        return ExecutionResult.success_result(
            data=final_output,
            duration=duration,
            metadata={"step_results": step_results},
        )

    def _execute_step_with_retry(
        self, step: ChainStep, context: Dict[str, Any]
    ) -> StepResult:
        """Execute a step with retry logic."""
        last_result = None

        for attempt in range(step.retry_count + 1):
            if attempt > 0:
                self._logger.debug(
                    f"Retrying step {step.name} (attempt {attempt + 1})"
                )

            result = step.execute(context)
            last_result = result

            if result.status == StepStatus.COMPLETED:
                return result

            if attempt < step.retry_count:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff

        return last_result

    def batch(self, inputs: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """
        Execute chain with multiple inputs.

        Args:
            inputs: List of input data dictionaries

        Returns:
            List of ExecutionResult
        """
        return [self.invoke(input_data) for input_data in inputs]

    def get_step_names(self) -> List[str]:
        """Get list of step names."""
        return [step.name for step in self._steps]

    def get_step(self, step_name: str) -> Optional[ChainStep]:
        """Get a step by name."""
        for step in self._steps:
            if step.name == step_name:
                return step
        return None
