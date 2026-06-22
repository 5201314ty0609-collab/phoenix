"""
PHOENIX AIOS — Tests for Built-in Tools

Tests calculator, datetime, JSON formatter, and text analyzer.
"""

from __future__ import annotations

import json
import unittest

from aios.ai.tools.builtin import (
    CalculatorTool,
    DateTimeTool,
    JsonFormatterTool,
    TextAnalyzerTool,
    analyze_text,
    calculator,
    format_json,
    get_datetime,
    create_default_registry,
)


class TestCalculator(unittest.TestCase):
    """Test calculator tool."""

    def test_basic_addition(self):
        result = calculator("2 + 3")
        assert result == "5"

    def test_multiplication(self):
        result = calculator("4 * 5")
        assert result == "20"

    def test_exponentiation(self):
        result = calculator("2 ^ 10")
        assert result == "1024"

    def test_parentheses(self):
        result = calculator("(2 + 3) * 4")
        assert result == "20"

    def test_float_arithmetic(self):
        result = calculator("3.14 * 2")
        assert float(result) == 6.28

    def test_sqrt(self):
        result = calculator("sqrt(16)")
        assert result == "4.0"

    def test_trig(self):
        import math
        result = calculator("sin(0)")
        assert float(result) == 0.0

    def test_pi(self):
        result = calculator("pi")
        assert float(result) > 3.14

    def test_invalid_expression(self):
        result = calculator("import os")
        assert "Error" in result

    def test_disallowed_chars(self):
        result = calculator("__import__('os')")
        assert "Error" in result


class TestDateTime(unittest.TestCase):
    """Test datetime tool."""

    def test_default_utc(self):
        result = get_datetime()
        data = json.loads(result)
        assert "datetime" in data
        assert "date" in data
        assert "time" in data
        assert data["timezone"] == "UTC"

    def test_with_offset(self):
        result = get_datetime("+8")
        data = json.loads(result)
        assert data["timezone"] == "UTC+8"

    def test_with_negative_offset(self):
        result = get_datetime("-5")
        data = json.loads(result)
        assert data["timezone"] == "UTC-5"

    def test_invalid_offset(self):
        result = get_datetime("invalid")
        data = json.loads(result)
        assert data["timezone"] == "UTC"


class TestJsonFormatter(unittest.TestCase):
    """Test JSON formatter tool."""

    def test_format_valid(self):
        result = format_json('{"a":1,"b":[2,3]}')
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": [2, 3]}

    def test_format_compact(self):
        result = format_json('{"name":"test","value":42}')
        assert "\n" in result  # Should be pretty-printed

    def test_format_invalid(self):
        result = format_json("{not json}")
        assert "Invalid JSON" in result

    def test_format_unicode(self):
        result = format_json('{"msg":"你好世界"}')
        assert "你好世界" in result


class TestTextAnalyzer(unittest.TestCase):
    """Test text analyzer tool."""

    def test_basic_analysis(self):
        result = analyze_text("Hello world. This is a test.")
        data = json.loads(result)
        assert data["words"] == 6
        assert data["sentences"] == 2
        assert data["characters"] > 0

    def test_empty_text(self):
        result = analyze_text("")
        data = json.loads(result)
        assert data["words"] == 0
        assert data["sentences"] == 0

    def test_top_words(self):
        result = analyze_text("the cat sat on the mat")
        data = json.loads(result)
        assert "the" in data["top_words"]
        assert data["top_words"]["the"] == 2

    def test_unique_words(self):
        result = analyze_text("hello world hello")
        data = json.loads(result)
        assert data["unique_words"] == 2  # hello, world


class TestToolDefinitions(unittest.TestCase):
    """Test that built-in tools have valid API definitions."""

    def test_calculator_definition(self):
        api_def = CalculatorTool.to_api_definition()
        assert api_def["function"]["name"] == "calculator"
        assert "expression" in api_def["function"]["parameters"]["properties"]

    def test_datetime_definition(self):
        api_def = DateTimeTool.to_api_definition()
        assert api_def["function"]["name"] == "get_datetime"

    def test_json_formatter_definition(self):
        api_def = JsonFormatterTool.to_api_definition()
        assert api_def["function"]["name"] == "format_json"

    def test_text_analyzer_definition(self):
        api_def = TextAnalyzerTool.to_api_definition()
        assert api_def["function"]["name"] == "analyze_text"


class TestDefaultRegistry(unittest.TestCase):
    """Test create_default_registry."""

    def test_creates_registry(self):
        registry = create_default_registry()
        assert registry.count == 4
        assert registry.has("calculator")
        assert registry.has("get_datetime")
        assert registry.has("format_json")
        assert registry.has("analyze_text")

    def test_tools_executable(self):
        registry = create_default_registry()

        # Calculator
        result = registry.execute(
            __import__("aios.ai.types", fromlist=["ToolCall"]).ToolCall(
                id="c1",
                name="calculator",
                arguments='{"expression": "2 + 3"}',
            )
        )
        assert result.content == "5"


if __name__ == "__main__":
    unittest.main()
