"""
Tool registry for PHOENIX AIOS LangChain integration.

Provides centralized tool management.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Type

from ..core import Config, ExecutionResult, Logger
from .base import Tool, ToolInput, ToolResult


class ToolRegistry:
    """
    Registry for managing tools.

    Provides tool registration, discovery, and execution.

    Example:
        registry = ToolRegistry()
        registry.register(my_tool)
        registry.register(another_tool)

        # Execute tool
        result = registry.execute("my_tool", {"x": 1, "y": 2})

        # List tools
        tools = registry.list_tools()
    """

    def __init__(self, config: Optional[Config] = None):
        self._config = config or Config()
        self._logger = Logger("ToolRegistry")
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}

    @property
    def tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()

    def register(self, tool: Tool, categories: Optional[List[str]] = None) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
            categories: Optional categories for the tool
        """
        if tool.name in self._tools:
            self._logger.warning(f"Overwriting existing tool: {tool.name}")

        self._tools[tool.name] = tool

        # Add to categories
        if categories:
            for category in categories:
                if category not in self._categories:
                    self._categories[category] = []
                if tool.name not in self._categories[category]:
                    self._categories[category].append(tool.name)

        self._logger.info(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]

            # Remove from categories
            for category, tools in self._categories.items():
                if name in tools:
                    tools.remove(name)

            self._logger.info(f"Unregistered tool: {name}")
            return True

        return False

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool or None
        """
        return self._tools.get(name)

    def execute(
        self,
        name: str,
        kwargs: Optional[Dict[str, Any]] = None,
        args: Optional[tuple] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a tool.

        Args:
            name: Tool name
            kwargs: Keyword arguments
            args: Positional arguments
            context: Execution context

        Returns:
            ExecutionResult
        """
        tool = self.get(name)
        if tool is None:
            return ExecutionResult.error_result(
                error=f"Tool not found: {name}"
            )

        tool_input = ToolInput(
            args=args or (),
            kwargs=kwargs or {},
            context=context or {},
        )

        return tool.invoke({
            "args": tool_input.args,
            "kwargs": tool_input.kwargs,
            "context": tool_input.context,
        })

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        Get tools by category.

        Args:
            category: Category name

        Returns:
            List of tools in category
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def search_tools(self, query: str) -> List[Tool]:
        """
        Search tools by name or description.

        Args:
            query: Search query

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                results.append(tool)

        return results

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all tools.

        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get tools formatted for LLM function calling.

        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": tool.get_schema(),
            }
            for tool in self._tools.values()
        ]

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute tool from input data.

        Args:
            input_data: Input data with 'tool' key

        Returns:
            ExecutionResult
        """
        tool_name = input_data.get("tool")
        if not tool_name:
            return ExecutionResult.error_result(
                error="Missing 'tool' key in input"
            )

        return self.execute(
            name=tool_name,
            kwargs=input_data.get("kwargs", {}),
            args=input_data.get("args", ()),
            context=input_data.get("context", {}),
        )

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def __repr__(self) -> str:
        """String representation."""
        return f"ToolRegistry(tools={len(self._tools)})"


# Global tool registry
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


def register_tool(tool: Tool, categories: Optional[List[str]] = None) -> None:
    """Register a tool in the global registry."""
    _registry.register(tool, categories)


def get_tool(name: str) -> Optional[Tool]:
    """Get a tool from the global registry."""
    return _registry.get(name)


def execute_tool(
    name: str,
    kwargs: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    """Execute a tool from the global registry."""
    return _registry.execute(name, kwargs)
