"""
Tool decorators for PHOENIX AIOS LangChain integration.

Provides decorators for creating tools from functions.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional, Type

from ..core import Config
from .base import FunctionTool, Tool, ToolParameter


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
    config: Optional[Config] = None,
) -> Callable:
    """
    Decorator to create a tool from a function.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        categories: Tool categories
        config: Configuration

    Returns:
        Decorated function that returns a Tool

    Example:
        @tool(name="add", description="Add two numbers")
        def add(x: int, y: int) -> int:
            return x + y

        # Use the tool
        result = add(x=1, y=2)

        # Or get the tool object
        tool_obj = add.tool
    """

    def decorator(func: Callable) -> Callable:
        # Extract function metadata
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Tool: {tool_name}"

        # Extract parameters from type hints
        parameters = _extract_parameters(func)

        # Create tool
        tool_obj = FunctionTool(
            name=tool_name,
            description=tool_desc,
            func=func,
            parameters=parameters,
            config=config,
        )

        # Register if categories provided
        if categories:
            from .registry import register_tool
            register_tool(tool_obj, categories)

        # Create wrapper that returns the tool
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if len(args) == 0 and len(kwargs) == 0:
                # Return the tool object
                return tool_obj
            # Execute the tool
            result = tool_obj.invoke({
                "args": args,
                "kwargs": kwargs,
            })
            if result.success:
                return result.data
            raise RuntimeError(result.error)

        # Attach tool to wrapper
        wrapper.tool = tool_obj
        wrapper.__name__ = tool_name
        wrapper.__doc__ = tool_desc

        return wrapper

    return decorator


def toolkit(
    name: str,
    description: str = "",
    categories: Optional[List[str]] = None,
) -> Callable:
    """
    Decorator to create a toolkit from a class.

    A toolkit is a collection of related tools.

    Args:
        name: Toolkit name
        description: Toolkit description
        categories: Tool categories

    Returns:
        Decorated class

    Example:
        @toolkit(name="math", description="Math operations")
        class MathToolkit:
            @staticmethod
            def add(x: int, y: int) -> int:
                return x + y

            @staticmethod
            def subtract(x: int, y: int) -> int:
                return x - y
    """

    def decorator(cls: Type) -> Type:
        # Get all methods
        tools = []
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name)
            if callable(attr):
                # Create tool from method
                tool_name = f"{name}_{attr_name}"
                tool_desc = attr.__doc__ or f"{name}.{attr_name}"
                parameters = _extract_parameters(attr)

                tool_obj = FunctionTool(
                    name=tool_name,
                    description=tool_desc,
                    func=attr,
                    parameters=parameters,
                )
                tools.append(tool_obj)

                # Register tool
                from .registry import register_tool
                register_tool(tool_obj, categories)

        # Attach tools to class
        cls._tools = tools
        cls._toolkit_name = name
        cls._toolkit_description = description

        return cls

    return decorator


def _extract_parameters(func: Callable) -> List[ToolParameter]:
    """
    Extract parameters from function signature.

    Args:
        func: Function to extract parameters from

    Returns:
        List of ToolParameter
    """
    parameters = []

    try:
        sig = inspect.signature(func)
        hints = func.__annotations__ if hasattr(func, "__annotations__") else {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            # Get type from hints
            param_type = hints.get(param_name, str)

            # Check if required
            required = param.default is inspect.Parameter.empty
            default = param.default if not required else None

            # Create parameter
            tool_param = ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter: {param_name}",
                required=required,
                default=default,
            )
            parameters.append(tool_param)
    except Exception:
        # If we can't extract parameters, return empty list
        pass

    return parameters


def from_function(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
    config: Optional[Config] = None,
) -> Tool:
    """
    Create a tool from a function.

    Args:
        func: Function to wrap
        name: Tool name
        description: Tool description
        categories: Tool categories
        config: Configuration

    Returns:
        Tool instance

    Example:
        def my_function(x: int, y: int) -> int:
            return x + y

        tool = from_function(my_function, name="add")
        result = tool.invoke({"kwargs": {"x": 1, "y": 2}})
    """
    tool_name = name or func.__name__
    tool_desc = description or func.__doc__ or f"Tool: {tool_name}"
    parameters = _extract_parameters(func)

    tool_obj = FunctionTool(
        name=tool_name,
        description=tool_desc,
        func=func,
        parameters=parameters,
        config=config,
    )

    if categories:
        from .registry import register_tool
        register_tool(tool_obj, categories)

    return tool_obj


def from_class(
    cls: Type,
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> List[Tool]:
    """
    Create tools from a class.

    Args:
        cls: Class to extract tools from
        name: Toolkit name
        description: Toolkit description
        categories: Tool categories

    Returns:
        List of Tool instances

    Example:
        class MathToolkit:
            @staticmethod
            def add(x: int, y: int) -> int:
                return x + y

        tools = from_class(MathToolkit, name="math")
    """
    toolkit_name = name or cls.__name__
    toolkit_desc = description or cls.__doc__ or f"Toolkit: {toolkit_name}"

    tools = []
    for attr_name in dir(cls):
        if attr_name.startswith("_"):
            continue

        attr = getattr(cls, attr_name)
        if callable(attr):
            tool_name = f"{toolkit_name}_{attr_name}"
            tool_desc = attr.__doc__ or f"{toolkit_name}.{attr_name}"
            parameters = _extract_parameters(attr)

            tool_obj = FunctionTool(
                name=tool_name,
                description=tool_desc,
                func=attr,
                parameters=parameters,
            )
            tools.append(tool_obj)

            if categories:
                from .registry import register_tool
                register_tool(tool_obj, categories)

    return tools
