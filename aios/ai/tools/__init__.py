"""
PHOENIX AIOS — Tool/Function Calling Framework

Provides a declarative way to define, register, and execute tools
that OpenAI models can invoke via function calling.

Core concepts:
- Tool: A callable function with a JSON Schema definition
- ToolParameter: A single parameter with type, description, and constraints
- ToolRegistry: Manages tool registration and dispatch
- ToolExecutor: Handles the call-execute-result loop

Usage:
    from aios.ai.tools import Tool, ToolParameter, ToolRegistry

    # Define a tool
    weather_tool = Tool(
        name="get_weather",
        description="Get current weather for a location",
        parameters=[
            ToolParameter(
                name="location",
                type="string",
                description="City name",
                required=True,
            ),
            ToolParameter(
                name="unit",
                type="string",
                description="Temperature unit",
                enum=["celsius", "fahrenheit"],
                default="celsius",
            ),
        ],
        handler=lambda location, unit="celsius": f"{location}: 22°{unit[0].upper()}",
    )

    # Register and use
    registry = ToolRegistry()
    registry.register(weather_tool)
"""

from aios.ai.tools.base import Tool, ToolParameter, ToolRegistry, ToolExecutor

__all__ = ["Tool", "ToolParameter", "ToolRegistry", "ToolExecutor"]
