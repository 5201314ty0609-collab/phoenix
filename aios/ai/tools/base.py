"""
PHOENIX AIOS — Tool/Function Calling Base

Implements the tool definition, registration, and execution framework
for OpenAI function calling integration.

Key design decisions:
- Tools are immutable after creation
- Handlers are plain callables (functions, lambdas, or objects with __call__)
- ToolRegistry is the single source of truth for available tools
- ToolExecutor handles the full call-execute-result cycle with error handling
"""

from __future__ import annotations

import inspect
import json
import traceback
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)

from aios.ai.errors import ToolExecutionError, ToolNotFoundError
from aios.ai.types import ToolCall, ToolResult


# ---------------------------------------------------------------------------
# Tool Parameter Definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolParameter:
    """
    Definition of a single tool parameter.

    Maps directly to JSON Schema property definitions.

    Attributes:
        name: Parameter name
        type: JSON Schema type (string, number, integer, boolean, object, array)
        description: Human-readable description for the model
        required: Whether this parameter is required
        enum: List of allowed values
        default: Default value if not provided
        items: Schema for array items (when type=array)
        properties: Schema for object properties (when type=object)
        minimum: Minimum value (for number/integer)
        maximum: Maximum value (for number/integer)
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Regex pattern for string validation
    """

    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    enum: Optional[Sequence[Any]] = None
    default: Any = None
    items: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema property definition."""
        schema: Dict[str, Any] = {"type": self.type}

        if self.description:
            schema["description"] = self.description

        if self.enum:
            schema["enum"] = list(self.enum)

        if self.default is not None:
            schema["default"] = self.default

        if self.items:
            schema["items"] = self.items

        if self.properties:
            schema["properties"] = self.properties

        if self.minimum is not None:
            schema["minimum"] = self.minimum

        if self.maximum is not None:
            schema["maximum"] = self.maximum

        if self.min_length is not None:
            schema["minLength"] = self.min_length

        if self.max_length is not None:
            schema["maxLength"] = self.max_length

        if self.pattern:
            schema["pattern"] = self.pattern

        return schema


# ---------------------------------------------------------------------------
# Tool Definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tool:
    """
    A callable tool with its JSON Schema definition.

    Tools are the primary way to extend model capabilities with
    function calling. Each tool has:
    - A name and description (used by the model to decide when to call)
    - Parameters defined as JSON Schema (used by the model to generate arguments)
    - A handler function that executes the tool logic

    Attributes:
        name: Tool name (must be a-z, A-Z, 0-9, underscores, dashes; max 64 chars)
        description: Description of what the tool does
        parameters: List of parameter definitions
        handler: Callable that implements the tool logic
        strict: Whether to use strict mode for structured outputs
    """

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()
    handler: Optional[Callable[..., Any]] = None
    strict: bool = False

    def __post_init__(self) -> None:
        """Validate tool definition."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if len(self.name) > 64:
            raise ValueError(f"Tool name too long ({len(self.name)} > 64)")
        # Validate name characters
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        invalid = set(self.name) - allowed
        if invalid:
            raise ValueError(f"Tool name contains invalid characters: {invalid}")

    @property
    def required_parameters(self) -> tuple[ToolParameter, ...]:
        """Get only required parameters."""
        return tuple(p for p in self.parameters if p.required)

    @property
    def optional_parameters(self) -> tuple[ToolParameter, ...]:
        """Get only optional parameters."""
        return tuple(p for p in self.parameters if not p.required)

    def to_api_definition(self) -> Dict[str, Any]:
        """
        Convert to OpenAI API tool definition format.

        Returns:
            Dict matching the OpenAI tools parameter schema
        """
        # Build properties and required list
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)

        # Build the function parameters schema
        parameters_schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters_schema["required"] = required

        definition: Dict[str, Any] = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema,
            },
        }

        if self.strict:
            definition["function"]["strict"] = True

        return definition

    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with given arguments.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ToolExecutionError: If handler is not set or execution fails
        """
        if self.handler is None:
            raise ToolExecutionError(
                message=f"Tool '{self.name}' has no handler",
                tool_name=self.name,
            )

        try:
            return self.handler(**kwargs)
        except Exception as e:
            raise ToolExecutionError(
                message=f"Tool '{self.name}' execution failed: {e}",
                tool_name=self.name,
                cause=e,
            )


@dataclass(frozen=True)
class ToolFromCallable:
    """
    Create a Tool from a Python function.

    Uses function signature and docstring to auto-generate the tool definition.

    Usage:
        @ToolFromCallable.from_function
        def get_weather(location: str, unit: str = "celsius") -> str:
            '''Get current weather for a location.

            Args:
                location: City name
                unit: Temperature unit (celsius or fahrenheit)
            '''
            return f"Weather in {location}: 22°{unit[0].upper()}"
    """

    @staticmethod
    def from_function(
        func: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        strict: bool = False,
    ) -> Tool:
        """
        Create a Tool from a Python function.

        Extracts parameter info from type hints and docstring.

        Args:
            func: The function to wrap
            name: Override tool name (default: function name)
            description: Override description (default: from docstring)
            strict: Enable strict mode

        Returns:
            Tool instance
        """
        sig = inspect.signature(func)
        params: List[ToolParameter] = []

        # Resolve type hints (handles `from __future__ import annotations`)
        try:
            type_hints = typing.get_type_hints(func)
        except Exception:
            type_hints = {}

        # Parse docstring for parameter descriptions
        docstring_descriptions = _parse_docstring_args(func.__doc__ or "")

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Determine type from annotation (use resolved hints)
            annotation = type_hints.get(param_name, param.annotation)
            param_type = _python_type_to_json_schema(annotation)

            # Determine if required
            required = param.default is inspect.Parameter.empty

            # Get default value
            default = None if required else param.default

            # Get description from docstring
            desc = docstring_descriptions.get(param_name, "")

            # Get enum from type hint if it's a Literal or Enum
            enum_values = _extract_enum_values(annotation)

            params.append(
                ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=desc,
                    required=required,
                    default=default,
                    enum=enum_values,
                )
            )

        # Extract description from docstring
        tool_desc = description or _parse_docstring_description(func.__doc__ or "")

        return Tool(
            name=name or func.__name__,
            description=tool_desc,
            parameters=tuple(params),
            handler=func,
            strict=strict,
        )


def _python_type_to_json_schema(annotation: Any) -> str:
    """Map Python type annotation to JSON Schema type."""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return "string"

    type_map: Dict[Type, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # Direct match
    if annotation in type_map:
        return type_map[annotation]

    # Handle Optional[X] (Union[X, None])
    origin = getattr(annotation, "__origin__", None)
    if origin is Union:
        args = getattr(annotation, "__args__", ())
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_schema(non_none[0])

    # Handle List[X]
    if origin is list:
        return "array"

    # Handle Dict[str, Any]
    if origin is dict:
        return "object"

    return "string"


def _extract_enum_values(annotation: Any) -> Optional[List[Any]]:
    """Extract enum values from Literal or Enum type hints."""
    try:
        from typing import Literal

        origin = getattr(annotation, "__origin__", None)
        if origin is Literal:
            return list(annotation.__args__)
    except ImportError:
        pass

    # Handle Enum classes
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return [e.value for e in annotation]

    return None


def _parse_docstring_description(docstring: str) -> str:
    """Extract the main description from a docstring."""
    lines = docstring.strip().split("\n")
    desc_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith("Args:") or stripped.startswith("Returns:"):
            break
        desc_lines.append(stripped)
    return " ".join(desc_lines)


def _parse_docstring_args(docstring: str) -> Dict[str, str]:
    """Extract parameter descriptions from a docstring Args section."""
    descriptions: Dict[str, str] = {}
    in_args = False

    for line in docstring.strip().split("\n"):
        stripped = line.strip()

        if stripped.startswith("Args:"):
            in_args = True
            continue

        if in_args:
            if not stripped:
                continue
            if stripped.startswith("Returns:") or stripped.startswith("Raises:"):
                break

            # Parse "name: description" or "name (type): description"
            if ":" in stripped:
                name_part, _, desc_part = stripped.partition(":")
                name = name_part.strip().split("(")[0].strip().split()[0]
                descriptions[name] = desc_part.strip()

    return descriptions


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------


class ToolRegistry:
    """
    Registry for managing tools.

    Provides:
    - Tool registration (from Tool objects or plain functions)
    - Tool lookup by name
    - Bulk tool definition export for API calls
    - Tool execution dispatch

    Thread-safe for concurrent access (uses dict which is thread-safe in CPython).
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        tool: Union[Tool, Callable[..., Any]],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tool:
        """
        Register a tool.

        Args:
            tool: Tool instance or callable to register
            name: Override name (only used for callables)
            description: Override description (only used for callables)

        Returns:
            The registered Tool instance
        """
        if callable(tool) and not isinstance(tool, Tool):
            tool = ToolFromCallable.from_function(tool, name=name, description=description)

        if tool.name in self._tools:
            pass  # Allow overwriting

        self._tools[tool.name] = tool
        return tool

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            name: Tool name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    @property
    def names(self) -> Set[str]:
        """Get all registered tool names."""
        return set(self._tools.keys())

    @property
    def count(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def to_api_definitions(self) -> List[Dict[str, Any]]:
        """
        Export all tools as OpenAI API tool definitions.

        Returns:
            List of tool definition dicts for the tools parameter
        """
        return [tool.to_api_definition() for tool in self._tools.values()]

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            ToolResult with execution output

        Raises:
            ToolNotFoundError: If the tool is not registered
            ToolExecutionError: If execution fails
        """
        tool = self._tools.get(tool_call.name)
        if tool is None:
            raise ToolNotFoundError(
                message=f"Tool '{tool_call.name}' is not registered",
            )

        # Parse arguments
        try:
            args = tool_call.parsed_arguments
        except Exception as e:
            raise ToolExecutionError(
                message=f"Failed to parse arguments for tool '{tool_call.name}': {e}",
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                cause=e,
            )

        # Execute
        try:
            result = tool.execute(**args)
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(
                message=f"Tool '{tool_call.name}' execution failed: {e}",
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                cause=e,
            )

        # Convert result to string
        if isinstance(result, str):
            content = result
        else:
            try:
                content = json.dumps(result, ensure_ascii=False)
            except (TypeError, ValueError):
                content = str(result)

        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            content=content,
        )

    def execute_all(self, tool_calls: Sequence[ToolCall]) -> List[ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of ToolResult in the same order
        """
        results: List[ToolResult] = []
        for tc in tool_calls:
            try:
                result = self.execute(tc)
                results.append(result)
            except ToolNotFoundError as e:
                results.append(
                    ToolResult(
                        tool_call_id=tc.id,
                        name=tc.name,
                        content=f"Error: {e}",
                    )
                )
            except ToolExecutionError as e:
                results.append(
                    ToolResult(
                        tool_call_id=tc.id,
                        name=tc.name,
                        content=f"Error: {e}",
                    )
                )
        return results

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __iter__(self):
        return iter(self._tools.values())


# ---------------------------------------------------------------------------
# Tool Executor (handles full call-execute-result loop)
# ---------------------------------------------------------------------------


class ToolExecutor:
    """
    Handles the complete tool calling loop.

    The executor manages:
    1. Sending tool definitions to the model
    2. Processing tool call responses
    3. Executing tools and collecting results
    4. Feeding results back for multi-turn tool conversations
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._registry

    def process_tool_calls(
        self, tool_calls: Sequence[ToolCall]
    ) -> List[ToolResult]:
        """
        Process a list of tool calls from the model.

        Args:
            tool_calls: Tool calls from the model response

        Returns:
            List of tool results to send back to the model
        """
        return self._registry.execute_all(tool_calls)

    def build_tool_messages(
        self, tool_calls: Sequence[ToolCall], results: Sequence[ToolResult]
    ) -> List[Dict[str, Any]]:
        """
        Build tool result messages for the next API call.

        Args:
            tool_calls: Original tool calls from the model
            results: Execution results

        Returns:
            List of message dicts to append to the conversation
        """
        from aios.ai.types import ChatMessage

        messages: List[Dict[str, Any]] = []

        # Add assistant message with tool calls
        assistant_msg = ChatMessage.assistant(tool_calls=tool_calls)
        messages.append(assistant_msg.to_api_dict())

        # Add tool result messages
        for result in results:
            tool_msg = ChatMessage.tool(
                tool_call_id=result.tool_call_id,
                name=result.name,
                content=result.content,
            )
            messages.append(tool_msg.to_api_dict())

        return messages
