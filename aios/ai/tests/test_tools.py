"""
PHOENIX AIOS — Tests for Tool/Function Calling Framework

Tests Tool, ToolParameter, ToolRegistry, and ToolExecutor.
"""

from __future__ import annotations

import json
import unittest
from typing import Any, Dict, Optional

from aios.ai.errors import ToolExecutionError, ToolNotFoundError
from aios.ai.tools.base import (
    Tool,
    ToolExecutor,
    ToolFromCallable,
    ToolParameter,
    ToolRegistry,
    _parse_docstring_args,
    _parse_docstring_description,
    _python_type_to_json_schema,
)
from aios.ai.types import ChatRole, ToolCall, ToolResult


class TestToolParameter(unittest.TestCase):
    """Test ToolParameter."""

    def test_string_param(self):
        param = ToolParameter(name="city", type="string", description="City name", required=True)
        schema = param.to_schema()
        assert schema["type"] == "string"
        assert schema["description"] == "City name"

    def test_enum_param(self):
        param = ToolParameter(
            name="unit",
            type="string",
            enum=["celsius", "fahrenheit"],
            default="celsius",
        )
        schema = param.to_schema()
        assert schema["enum"] == ["celsius", "fahrenheit"]
        assert schema["default"] == "celsius"

    def test_number_param_with_bounds(self):
        param = ToolParameter(name="temp", type="number", minimum=-100, maximum=100)
        schema = param.to_schema()
        assert schema["minimum"] == -100
        assert schema["maximum"] == 100

    def test_string_param_with_length(self):
        param = ToolParameter(name="name", type="string", min_length=1, max_length=100)
        schema = param.to_schema()
        assert schema["minLength"] == 1
        assert schema["maxLength"] == 100

    def test_array_param(self):
        param = ToolParameter(
            name="tags",
            type="array",
            items={"type": "string"},
        )
        schema = param.to_schema()
        assert schema["items"] == {"type": "string"}

    def test_immutability(self):
        param = ToolParameter(name="test")
        with self.assertRaises(Exception):
            param.name = "changed"  # type: ignore


class TestTool(unittest.TestCase):
    """Test Tool."""

    def test_creation(self):
        tool = Tool(
            name="get_weather",
            description="Get weather",
            parameters=(
                ToolParameter(name="city", type="string", required=True),
            ),
        )
        assert tool.name == "get_weather"
        assert tool.description == "Get weather"
        assert len(tool.parameters) == 1

    def test_name_validation_empty(self):
        with self.assertRaises(ValueError):
            Tool(name="", description="test")

    def test_name_validation_too_long(self):
        with self.assertRaises(ValueError):
            Tool(name="a" * 65, description="test")

    def test_name_validation_invalid_chars(self):
        with self.assertRaises(ValueError):
            Tool(name="my tool!", description="test")

    def test_name_validation_valid(self):
        tool = Tool(name="my-tool_v2", description="test")
        assert tool.name == "my-tool_v2"

    def test_required_parameters(self):
        tool = Tool(
            name="test",
            description="test",
            parameters=(
                ToolParameter(name="a", required=True),
                ToolParameter(name="b", required=False),
                ToolParameter(name="c", required=True),
            ),
        )
        required = tool.required_parameters
        assert len(required) == 2
        assert required[0].name == "a"
        assert required[1].name == "c"

    def test_optional_parameters(self):
        tool = Tool(
            name="test",
            description="test",
            parameters=(
                ToolParameter(name="a", required=True),
                ToolParameter(name="b", required=False),
            ),
        )
        optional = tool.optional_parameters
        assert len(optional) == 1
        assert optional[0].name == "b"

    def test_to_api_definition(self):
        tool = Tool(
            name="get_weather",
            description="Get current weather",
            parameters=(
                ToolParameter(name="city", type="string", description="City name", required=True),
                ToolParameter(
                    name="unit",
                    type="string",
                    description="Temperature unit",
                    enum=["celsius", "fahrenheit"],
                    default="celsius",
                ),
            ),
        )
        api_def = tool.to_api_definition()

        assert api_def["type"] == "function"
        assert api_def["function"]["name"] == "get_weather"
        assert api_def["function"]["description"] == "Get current weather"

        params = api_def["function"]["parameters"]
        assert params["type"] == "object"
        assert "city" in params["properties"]
        assert "unit" in params["properties"]
        assert "city" in params["required"]
        assert "unit" not in params["required"]

    def test_to_api_definition_strict(self):
        tool = Tool(name="test", description="test", strict=True)
        api_def = tool.to_api_definition()
        assert api_def["function"]["strict"] is True

    def test_execute_with_handler(self):
        def handler(city: str) -> str:
            return f"Weather in {city}"

        tool = Tool(name="test", description="test", handler=handler)
        result = tool.execute(city="Tokyo")
        assert result == "Weather in Tokyo"

    def test_execute_no_handler(self):
        tool = Tool(name="test", description="test")
        with self.assertRaises(ToolExecutionError):
            tool.execute()

    def test_execute_handler_error(self):
        def handler():
            raise ValueError("boom")

        tool = Tool(name="test", description="test", handler=handler)
        with self.assertRaises(ToolExecutionError):
            tool.execute()


class TestToolFromCallable(unittest.TestCase):
    """Test ToolFromCallable factory."""

    def test_simple_function(self):
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        tool = ToolFromCallable.from_function(add)
        assert tool.name == "add"
        assert tool.description == "Add two numbers."
        assert len(tool.parameters) == 2

        # Check parameter types
        a_param = tool.parameters[0]
        assert a_param.name == "a"
        assert a_param.type == "integer"
        assert a_param.required is True

    def test_function_with_defaults(self):
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        tool = ToolFromCallable.from_function(greet)
        assert len(tool.parameters) == 2

        name_param = tool.parameters[0]
        assert name_param.required is True

        greeting_param = tool.parameters[1]
        assert greeting_param.required is False
        assert greeting_param.default == "Hello"

    def test_function_with_docstring_args(self):
        def search(query: str, limit: int) -> list:
            """Search for items.

            Args:
                query: Search query string
                limit: Maximum number of results
            """
            return []

        tool = ToolFromCallable.from_function(search)
        query_param = tool.parameters[0]
        assert query_param.description == "Search query string"

        limit_param = tool.parameters[1]
        assert limit_param.description == "Maximum number of results"

    def test_function_with_overrides(self):
        def f(x: int) -> int:
            return x

        tool = ToolFromCallable.from_function(f, name="custom_name", description="Custom desc")
        assert tool.name == "custom_name"
        assert tool.description == "Custom desc"

    def test_execute_from_function(self):
        def multiply(a: int, b: int) -> int:
            return a * b

        tool = ToolFromCallable.from_function(multiply)
        result = tool.execute(a=3, b=4)
        assert result == 12


class TestDocstringParsing(unittest.TestCase):
    """Test docstring parsing utilities."""

    def test_parse_description(self):
        doc = """Get the weather for a location.

        This function retrieves current weather data.
        """
        desc = _parse_docstring_description(doc)
        assert desc == "Get the weather for a location."

    def test_parse_args(self):
        doc = """Do something.

        Args:
            name: The name to use
            count: Number of times
        """
        args = _parse_docstring_args(doc)
        assert args["name"] == "The name to use"
        assert args["count"] == "Number of times"

    def test_parse_args_empty(self):
        args = _parse_docstring_args("No args section.")
        assert args == {}


class TestTypeMapping(unittest.TestCase):
    """Test Python type to JSON Schema mapping."""

    def test_str(self):
        assert _python_type_to_json_schema(str) == "string"

    def test_int(self):
        assert _python_type_to_json_schema(int) == "integer"

    def test_float(self):
        assert _python_type_to_json_schema(float) == "number"

    def test_bool(self):
        assert _python_type_to_json_schema(bool) == "boolean"

    def test_list(self):
        assert _python_type_to_json_schema(list) == "array"

    def test_dict(self):
        assert _python_type_to_json_schema(dict) == "object"

    def test_missing_annotation(self):
        import inspect
        assert _python_type_to_json_schema(inspect.Parameter.empty) == "string"


class TestToolRegistry(unittest.TestCase):
    """Test ToolRegistry."""

    def setUp(self):
        self.registry = ToolRegistry()

    def test_register_tool(self):
        tool = Tool(name="test", description="test")
        self.registry.register(tool)
        assert self.registry.has("test")
        assert self.registry.count == 1

    def test_register_callable(self):
        def my_func(x: int) -> int:
            """Double a number."""
            return x * 2

        self.registry.register(my_func)
        assert self.registry.has("my_func")

    def test_register_with_name_override(self):
        def f():
            pass

        self.registry.register(f, name="custom")
        assert self.registry.has("custom")

    def test_get_existing(self):
        tool = Tool(name="test", description="test")
        self.registry.register(tool)
        assert self.registry.get("test") is tool

    def test_get_missing(self):
        assert self.registry.get("nonexistent") is None

    def test_unregister(self):
        tool = Tool(name="test", description="test")
        self.registry.register(tool)
        assert self.registry.unregister("test") is True
        assert self.registry.has("test") is False

    def test_unregister_missing(self):
        assert self.registry.unregister("nonexistent") is False

    def test_names(self):
        self.registry.register(Tool(name="a", description=""))
        self.registry.register(Tool(name="b", description=""))
        assert self.registry.names == {"a", "b"}

    def test_to_api_definitions(self):
        self.registry.register(Tool(
            name="test",
            description="A test tool",
            parameters=(ToolParameter(name="x", type="integer", required=True),),
        ))
        defs = self.registry.to_api_definitions()
        assert len(defs) == 1
        assert defs[0]["function"]["name"] == "test"

    def test_execute(self):
        tool = Tool(
            name="add",
            description="Add numbers",
            handler=lambda a, b: a + b,
        )
        self.registry.register(tool)

        tc = ToolCall(id="call_1", name="add", arguments='{"a": 1, "b": 2}')
        result = self.registry.execute(tc)
        assert result.tool_call_id == "call_1"
        assert result.name == "add"
        assert result.content == "3"

    def test_execute_not_found(self):
        tc = ToolCall(id="call_1", name="missing", arguments="{}")
        with self.assertRaises(ToolNotFoundError):
            self.registry.execute(tc)

    def test_execute_all(self):
        self.registry.register(Tool(
            name="add",
            description="",
            handler=lambda a, b: a + b,
        ))
        self.registry.register(Tool(
            name="mul",
            description="",
            handler=lambda a, b: a * b,
        ))

        calls = [
            ToolCall(id="c1", name="add", arguments='{"a": 1, "b": 2}'),
            ToolCall(id="c2", name="mul", arguments='{"a": 3, "b": 4}'),
        ]
        results = self.registry.execute_all(calls)
        assert len(results) == 2
        assert results[0].content == "3"
        assert results[1].content == "12"

    def test_execute_all_with_missing_tool(self):
        calls = [
            ToolCall(id="c1", name="missing", arguments="{}"),
        ]
        results = self.registry.execute_all(calls)
        assert len(results) == 1
        assert "Error" in results[0].content

    def test_clear(self):
        self.registry.register(Tool(name="a", description=""))
        self.registry.register(Tool(name="b", description=""))
        self.registry.clear()
        assert self.registry.count == 0

    def test_len(self):
        assert len(self.registry) == 0
        self.registry.register(Tool(name="a", description=""))
        assert len(self.registry) == 1

    def test_contains(self):
        self.registry.register(Tool(name="a", description=""))
        assert "a" in self.registry
        assert "b" not in self.registry

    def test_iter(self):
        self.registry.register(Tool(name="a", description=""))
        self.registry.register(Tool(name="b", description=""))
        names = {t.name for t in self.registry}
        assert names == {"a", "b"}


class TestToolExecutor(unittest.TestCase):
    """Test ToolExecutor."""

    def test_process_tool_calls(self):
        registry = ToolRegistry()
        registry.register(Tool(
            name="add",
            description="",
            handler=lambda a, b: a + b,
        ))

        executor = ToolExecutor(registry)
        calls = [ToolCall(id="c1", name="add", arguments='{"a": 1, "b": 2}')]
        results = executor.process_tool_calls(calls)
        assert len(results) == 1
        assert results[0].content == "3"

    def test_build_tool_messages(self):
        registry = ToolRegistry()
        executor = ToolExecutor(registry)

        calls = [ToolCall(id="c1", name="test", arguments="{}")]
        results = [ToolResult(tool_call_id="c1", name="test", content="ok")]

        messages = executor.build_tool_messages(calls, results)
        assert len(messages) == 2
        assert messages[0]["role"] == "assistant"
        assert messages[0]["tool_calls"][0]["id"] == "c1"
        assert messages[1]["role"] == "tool"
        assert messages[1]["tool_call_id"] == "c1"
        assert messages[1]["content"] == "ok"


if __name__ == "__main__":
    unittest.main()
