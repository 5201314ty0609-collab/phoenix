"""
Core module for PHOENIX AIOS LangChain integration.

Provides base classes and utilities used across all components.
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

T = TypeVar("T")


class LogLevel(Enum):
    """Logging levels for PHOENIX components."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Config:
    """
    Configuration for PHOENIX LangChain components.

    Attributes:
        name: Component name
        version: Component version
        log_level: Logging level
        max_retries: Maximum retry attempts
        timeout: Operation timeout in seconds
        metadata: Additional metadata
    """
    name: str = "phoenix-langchain"
    version: str = "1.0.0"
    log_level: LogLevel = LogLevel.INFO
    max_retries: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_override(self, **kwargs: Any) -> Config:
        """Create a new config with overridden values."""
        from dataclasses import replace
        return replace(self, **kwargs)


class Logger:
    """
    Structured logger for PHOENIX components.

    Provides consistent logging with context and metadata support.
    """

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self._name = name
        self._level = level
        self._logger = logging.getLogger(f"phoenix.{name}")
        self._logger.setLevel(getattr(logging, level.value))

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Internal logging method with context support."""
        extra = {"context": context} if context else {}
        if error:
            extra["error"] = str(error)
            extra["error_type"] = type(error).__name__

        getattr(self._logger, level.value.lower())(message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result of a component execution.

    Attributes:
        success: Whether execution succeeded
        data: Output data
        error: Error message if failed
        duration: Execution duration in seconds
        metadata: Additional metadata
        execution_id: Unique execution identifier
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def success_result(
        cls,
        data: Any,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Create a successful result."""
        return cls(
            success=True,
            data=data,
            duration=duration,
            metadata=metadata or {},
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            duration=duration,
            metadata=metadata or {},
        )


class BaseComponent(ABC):
    """
    Abstract base class for all PHOENIX LangChain components.

    Provides common functionality including:
    - Configuration management
    - Logging
    - Execution tracking
    - Error handling
    """

    def __init__(self, config: Optional[Config] = None):
        self._config = config or Config()
        self._logger = Logger(self.__class__.__name__, self._config.log_level)
        self._execution_count: int = 0
        self._total_duration: float = 0.0

    @property
    def config(self) -> Config:
        """Get component configuration."""
        return self._config

    @property
    def logger(self) -> Logger:
        """Get component logger."""
        return self._logger

    @property
    def execution_count(self) -> int:
        """Get total execution count."""
        return self._execution_count

    @property
    def average_duration(self) -> float:
        """Get average execution duration."""
        if self._execution_count == 0:
            return 0.0
        return self._total_duration / self._execution_count

    def _track_execution(self, duration: float) -> None:
        """Track execution metrics."""
        self._execution_count += 1
        self._total_duration += duration

    @abstractmethod
    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the component with given input.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult with output data or error
        """
        pass

    def batch(self, inputs: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """
        Execute component with multiple inputs.

        Args:
            inputs: List of input data dictionaries

        Returns:
            List of ExecutionResult
        """
        results = []
        for input_data in inputs:
            result = self.invoke(input_data)
            results.append(result)
        return results

    def stream(self, input_data: Dict[str, Any]) -> Any:
        """
        Stream execution results.

        Args:
            input_data: Input data dictionary

        Yields:
            Streaming results
        """
        raise NotImplementedError("Streaming not supported by this component")

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._execution_count = 0
        self._total_duration = 0.0


class ComponentRegistry:
    """
    Registry for managing PHOENIX components.

    Provides component discovery, registration, and lifecycle management.
    """

    def __init__(self):
        self._components: Dict[str, BaseComponent] = {}
        self._factories: Dict[str, Callable[..., BaseComponent]] = {}
        self._logger = Logger("ComponentRegistry")

    def register(self, name: str, component: BaseComponent) -> None:
        """
        Register a component instance.

        Args:
            name: Component name
            component: Component instance
        """
        if name in self._components:
            self._logger.warning(f"Overwriting existing component: {name}")
        self._components[name] = component
        self._logger.info(f"Registered component: {name}")

    def register_factory(
        self, name: str, factory: Callable[..., BaseComponent]
    ) -> None:
        """
        Register a component factory.

        Args:
            name: Component name
            factory: Factory function that creates component
        """
        self._factories[name] = factory
        self._logger.info(f"Registered factory: {name}")

    def get(self, name: str) -> Optional[BaseComponent]:
        """
        Get a registered component.

        Args:
            name: Component name

        Returns:
            Component instance or None
        """
        return self._components.get(name)

    def create(self, name: str, **kwargs: Any) -> Optional[BaseComponent]:
        """
        Create a component using registered factory.

        Args:
            name: Component name
            **kwargs: Factory arguments

        Returns:
            Created component or None
        """
        factory = self._factories.get(name)
        if factory is None:
            self._logger.error(f"No factory registered for: {name}")
            return None

        try:
            component = factory(**kwargs)
            self.register(name, component)
            return component
        except Exception as e:
            self._logger.error(f"Failed to create component {name}: {e}")
            return None

    def list_components(self) -> List[str]:
        """List all registered component names."""
        return list(self._components.keys())

    def list_factories(self) -> List[str]:
        """List all registered factory names."""
        return list(self._factories.keys())

    def remove(self, name: str) -> bool:
        """
        Remove a registered component.

        Args:
            name: Component name

        Returns:
            True if removed, False if not found
        """
        if name in self._components:
            del self._components[name]
            self._logger.info(f"Removed component: {name}")
            return True
        return False

    def clear(self) -> None:
        """Remove all registered components."""
        self._components.clear()
        self._factories.clear()
        self._logger.info("Cleared all components")


# Global component registry
_registry = ComponentRegistry()


def get_registry() -> ComponentRegistry:
    """Get the global component registry."""
    return _registry


def register_component(name: str, component: BaseComponent) -> None:
    """Register a component in the global registry."""
    _registry.register(name, component)


def get_component(name: str) -> Optional[BaseComponent]:
    """Get a component from the global registry."""
    return _registry.get(name)
