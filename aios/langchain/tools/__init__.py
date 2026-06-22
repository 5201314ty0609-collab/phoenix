"""
Tools module for PHOENIX AIOS LangChain integration.

Provides tool definitions and execution framework.
"""

from .base import Tool, ToolResult, ToolInput
from .registry import ToolRegistry, get_registry
from .decorators import tool, toolkit
from .builtin import (
    SearchTool,
    CalculatorTool,
    FileReaderTool,
    FileWriterTool,
    ShellTool,
    HTTPTool,
    JSONTool,
    RegexTool,
)

__all__ = [
    # Base
    "Tool",
    "ToolResult",
    "ToolInput",

    # Registry
    "ToolRegistry",
    "get_registry",

    # Decorators
    "tool",
    "toolkit",

    # Built-in tools
    "SearchTool",
    "CalculatorTool",
    "FileReaderTool",
    "FileWriterTool",
    "ShellTool",
    "HTTPTool",
    "JSONTool",
    "RegexTool",
]
