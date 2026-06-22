"""
Base tool module for PHOENIX AIOS LangChain integration.

Provides abstract base class for tools.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from ..core import BaseComponent, Config, ExecutionResult, Logger


class ToolStatus(Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ToolInput:
    """
    Input for tool execution.

    Args:
        args: Positional arguments
        kwargs: Keyword arguments
        context: Execution context
    """
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from kwargs."""
        return self.kwargs.get(key, default)

    def with_context(self, **kwargs: Any) -> ToolInput:
        """Create new input with additional context."""
        from dataclasses import replace
        new_context = {**self.context, **kwargs}
        return replace(self, context=new_context)


@dataclass(frozen=True)
class ToolResult:
    """
    Result of tool execution.

    Attributes:
        status: Execution status
        data: Output data
        error: Error message if failed
        duration: Execution duration in seconds
        metadata: Additional metadata
    """
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        data: Any,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Create a successful result."""
        return cls(
            status=ToolStatus.SUCCESS,
            data=data,
            duration=duration,
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        error: str,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Create an error result."""
        return cls(
            status=ToolStatus.ERROR,
            error=error,
            duration=duration,
            metadata=metadata or {},
        )

    @classmethod
    def timeout(
        cls,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Create a timeout result."""
        return cls(
            status=ToolStatus.TIMEOUT,
            error="Tool execution timed out",
            duration=duration,
            metadata=metadata or {},
        )


@dataclass(frozen=True)
class ToolParameter:
    """
    Tool parameter definition.

    Attributes:
        name: Parameter name
        type: Parameter type
        description: Parameter description
        required: Whether parameter is required
        default: Default value
    """
    name: str
    type: Type
    description: str = ""
    required: bool = True
    default: Any = None


class Tool(BaseComponent, ABC):
    """
    Abstract base class for tools.

    Tools are functions that can be called by agents to perform actions.

    Example:
        class MyTool(Tool):
            @property
            def name(self) -> str:
                return "my_tool"

            @property
            def description(self) -> str:
                return "Does something useful"

            def execute(self, tool_input: ToolInput) -> ToolResult:
                # Tool logic here
                return ToolResult.success(data="result")
    """

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self._logger = Logger(f"Tool.{self.name}")
        self._parameters: List[ToolParameter] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Get tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get tool description."""
        pass

    @property
    def parameters(self) -> List[ToolParameter]:
        """Get tool parameters."""
        return self._parameters.copy()

    def add_parameter(
        self,
        name: str,
        type: Type,
        description: str = "",
        required: bool = True,
        default: Any = None,
    ) -> Tool:
        """
        Add a parameter definition.

        Args:
            name: Parameter name
            type: Parameter type
            description: Parameter description
            required: Whether parameter is required
            default: Default value

        Returns:
            Self for method chaining
        """
        param = ToolParameter(
            name=name,
            type=type,
            description=description,
            required=required,
            default=default,
        )
        self._parameters.append(param)
        return self

    @abstractmethod
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """
        Execute the tool.

        Args:
            tool_input: Tool input

        Returns:
            ToolResult with output or error
        """
        pass

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute tool with dictionary input.

        Args:
            input_data: Input data dictionary

        Returns:
            ExecutionResult
        """
        start_time = time.time()

        # Extract arguments
        args = input_data.get("args", ())
        kwargs = input_data.get("kwargs", {})
        context = input_data.get("context", {})

        tool_input = ToolInput(
            args=args,
            kwargs=kwargs,
            context=context,
        )

        # Validate parameters
        validation_error = self._validate_parameters(tool_input)
        if validation_error:
            duration = time.time() - start_time
            self._track_execution(duration)
            return ExecutionResult.error_result(
                error=validation_error,
                duration=duration,
            )

        # Execute tool
        try:
            result = self.execute(tool_input)
            duration = time.time() - start_time
            self._track_execution(duration)

            if result.status == ToolStatus.SUCCESS:
                return ExecutionResult.success_result(
                    data=result.data,
                    duration=duration,
                    metadata=result.metadata,
                )
            else:
                return ExecutionResult.error_result(
                    error=result.error or "Tool execution failed",
                    duration=duration,
                    metadata=result.metadata,
                )
        except Exception as e:
            duration = time.time() - start_time
            self._track_execution(duration)
            return ExecutionResult.error_result(
                error=str(e),
                duration=duration,
            )

    def _validate_parameters(self, tool_input: ToolInput) -> Optional[str]:
        """Validate tool parameters."""
        for param in self._parameters:
            if param.required and param.name not in tool_input.kwargs:
                if param.default is None:
                    return f"Missing required parameter: {param.name}"

            if param.name in tool_input.kwargs:
                value = tool_input.kwargs[param.name]
                if not isinstance(value, param.type):
                    try:
                        # Try to convert
                        tool_input.kwargs[param.name] = param.type(value)
                    except (ValueError, TypeError):
                        return (
                            f"Parameter '{param.name}' must be {param.type.__name__}, "
                            f"got {type(value).__name__}"
                        )

        return None

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.

        Returns:
            Tool schema dictionary
        """
        properties = {}
        required = []

        for param in self._parameters:
            properties[param.name] = {
                "type": param.type.__name__,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"Tool(name='{self.name}')"

    def __call__(self, **kwargs: Any) -> Any:
        """Call tool directly."""
        result = self.invoke({"kwargs": kwargs})
        if result.success:
            return result.data
        raise RuntimeError(result.error)


class FunctionTool(Tool):
    """
    Tool wrapper for functions.

    Wraps a function as a tool.

    Example:
        def my_function(x: int, y: int) -> int:
            return x + y

        tool = FunctionTool(
            name="add",
            description="Add two numbers",
            func=my_function,
        )
        result = tool(x=1, y=2)  # 3
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[List[ToolParameter]] = None,
        config: Optional[Config] = None,
    ):
        super().__init__(config)
        self._name = name
        self._description = description
        self._func = func
        if parameters:
            self._parameters = parameters

    @property
    def name(self) -> str:
        """Get tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Get tool description."""
        return self._description

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """
        Execute the function.

        Args:
            tool_input: Tool input

        Returns:
            ToolResult
        """
        start_time = time.time()

        try:
            result = self._func(*tool_input.args, **tool_input.kwargs)
            duration = time.time() - start_time
            return ToolResult.success(data=result, duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            return ToolResult.error(error=str(e), duration=duration)
