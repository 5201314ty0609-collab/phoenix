"""
Tests for tools module.
"""

import unittest
from typing import Any, Dict

from ..tools import (
    Tool,
    ToolInput,
    ToolResult,
    ToolRegistry,
    tool,
    SearchTool,
    CalculatorTool,
    JSONTool,
    RegexTool,
)


class TestToolInput(unittest.TestCase):
    """Test ToolInput."""

    def test_create(self):
        """Test creating ToolInput."""
        tool_input = ToolInput(
            args=(1, 2),
            kwargs={"x": 1, "y": 2},
            context={"key": "value"},
        )
        self.assertEqual(tool_input.args, (1, 2))
        self.assertEqual(tool_input.kwargs, {"x": 1, "y": 2})
        self.assertEqual(tool_input.context, {"key": "value"})

    def test_get(self):
        """Test getting value."""
        tool_input = ToolInput(kwargs={"x": 1, "y": 2})
        self.assertEqual(tool_input.get("x"), 1)
        self.assertEqual(tool_input.get("z", 3), 3)


class TestToolResult(unittest.TestCase):
    """Test ToolResult."""

    def test_success(self):
        """Test successful result."""
        result = ToolResult.success(data="result", duration=1.0)
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data, "result")
        self.assertEqual(result.duration, 1.0)

    def test_error(self):
        """Test error result."""
        result = ToolResult.error(error="error message")
        self.assertEqual(result.status.value, "error")
        self.assertEqual(result.error, "error message")

    def test_timeout(self):
        """Test timeout result."""
        result = ToolResult.timeout(duration=30.0)
        self.assertEqual(result.status.value, "timeout")


class TestSearchTool(unittest.TestCase):
    """Test SearchTool."""

    def test_search(self):
        """Test search."""
        tool = SearchTool()
        result = tool.execute(ToolInput(kwargs={
            "text": "Hello World",
            "pattern": "World",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data["count"], 1)
        self.assertEqual(result.data["matches"], ["World"])

    def test_case_insensitive(self):
        """Test case insensitive search."""
        tool = SearchTool()
        result = tool.execute(ToolInput(kwargs={
            "text": "Hello World",
            "pattern": "world",
            "case_sensitive": False,
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data["count"], 1)


class TestCalculatorTool(unittest.TestCase):
    """Test CalculatorTool."""

    def test_calculate(self):
        """Test calculation."""
        tool = CalculatorTool()
        result = tool.execute(ToolInput(kwargs={
            "expression": "2 + 3 * 4",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data, 14)

    def test_math_functions(self):
        """Test math functions."""
        tool = CalculatorTool()
        result = tool.execute(ToolInput(kwargs={
            "expression": "sqrt(16)",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data, 4.0)

    def test_unsafe_expression(self):
        """Test unsafe expression."""
        tool = CalculatorTool()
        result = tool.execute(ToolInput(kwargs={
            "expression": "import os",
        }))
        self.assertEqual(result.status.value, "error")


class TestJSONTool(unittest.TestCase):
    """Test JSONTool."""

    def test_parse(self):
        """Test JSON parse."""
        tool = JSONTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "parse",
            "text": '{"key": "value"}',
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data, {"key": "value"})

    def test_stringify(self):
        """Test JSON stringify."""
        tool = JSONTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "stringify",
            "data": {"key": "value"},
        }))
        self.assertEqual(result.status.value, "success")
        self.assertIn('"key": "value"', result.data)

    def test_query(self):
        """Test JSON query."""
        tool = JSONTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "query",
            "text": '{"user": {"name": "John"}}',
            "path": "user.name",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data, "John")


class TestRegexTool(unittest.TestCase):
    """Test RegexTool."""

    def test_match(self):
        """Test regex match."""
        tool = RegexTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "match",
            "text": "Hello World",
            "pattern": r"Hello (\w+)",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertTrue(result.data["matched"])
        self.assertEqual(result.data["groups"], ("World",))

    def test_findall(self):
        """Test regex findall."""
        tool = RegexTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "findall",
            "text": "Hello World World",
            "pattern": r"World",
        }))
        self.assertEqual(result.status.value, "success")
        self.assertEqual(result.data["count"], 2)


class TestToolRegistry(unittest.TestCase):
    """Test ToolRegistry."""

    def test_register(self):
        """Test registering tool."""
        registry = ToolRegistry()
        tool = SearchTool()
        registry.register(tool)
        self.assertIn("search", registry)

    def test_execute(self):
        """Test executing tool."""
        registry = ToolRegistry()
        tool = SearchTool()
        registry.register(tool)

        result = registry.execute("search", kwargs={
            "text": "Hello World",
            "pattern": "World",
        })
        self.assertTrue(result.success)

    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(CalculatorTool())

        tools = registry.list_tools()
        self.assertIn("search", tools)
        self.assertIn("calculator", tools)

    def test_search_tools(self):
        """Test searching tools."""
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(CalculatorTool())

        results = registry.search_tools("search")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "search")


class TestToolDecorator(unittest.TestCase):
    """Test tool decorator."""

    def test_decorator(self):
        """Test tool decorator."""
        @tool(name="add", description="Add two numbers")
        def add(x: int, y: int) -> int:
            return x + y

        result = add(x=1, y=2)
        self.assertEqual(result, 3)

    def test_tool_object(self):
        """Test getting tool object."""
        @tool(name="add", description="Add two numbers")
        def add(x: int, y: int) -> int:
            return x + y

        tool_obj = add.tool
        self.assertEqual(tool_obj.name, "add")


if __name__ == "__main__":
    unittest.main()
