"""
PHOENIX AIOS — Built-in Tools

Pre-built tools for common operations. These tools demonstrate
the tool framework and provide useful utilities.

Available tools:
- WebSearch: Search the web (placeholder)
- Calculator: Evaluate mathematical expressions
- DateTimeTool: Get current date/time
- JsonFormatter: Format/validate JSON
- TextAnalyzer: Analyze text statistics
"""

from __future__ import annotations

import json
import math
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aios.ai.tools.base import Tool, ToolParameter, ToolFromCallable


# ---------------------------------------------------------------------------
# Calculator Tool
# ---------------------------------------------------------------------------


def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Supports basic arithmetic, powers, roots, and common math functions.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

    Returns:
        Result as a string
    """
    # Safe evaluation with limited builtins
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "pi": math.pi,
        "e": math.e,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    # Sanitize: only allow safe characters
    safe_pattern = re.compile(r'^[0-9+\-*/().,%^ a-zA-Z_]+$')
    if not safe_pattern.match(expression):
        return f"Error: Expression contains disallowed characters"

    try:
        # Replace ^ with ** for exponentiation
        safe_expr = expression.replace("^", "**")
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


CalculatorTool = ToolFromCallable.from_function(
    calculator,
    name="calculator",
    description="Evaluate mathematical expressions. Supports +, -, *, /, ^, sqrt, sin, cos, tan, log, pi, e.",
)


# ---------------------------------------------------------------------------
# DateTime Tool
# ---------------------------------------------------------------------------


def get_datetime(timezone_offset: Optional[str] = None) -> str:
    """
    Get the current date and time.

    Args:
        timezone_offset: UTC offset in hours (e.g., "+8", "-5"). Defaults to UTC.

    Returns:
        Formatted date/time string
    """
    from datetime import timedelta

    if timezone_offset:
        try:
            offset_hours = float(timezone_offset)
            tz = timezone(offset=timedelta(hours=offset_hours))
            now = datetime.now(tz)
            tz_name = f"UTC{timezone_offset}"
        except (ValueError, TypeError):
            now = datetime.now(timezone.utc)
            tz_name = "UTC"
    else:
        now = datetime.now(timezone.utc)
        tz_name = "UTC"

    return json.dumps({
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": tz_name,
        "day_of_week": now.strftime("%A"),
        "unix_timestamp": int(now.timestamp()),
    })


DateTimeTool = ToolFromCallable.from_function(
    get_datetime,
    name="get_datetime",
    description="Get the current date and time. Optionally specify a UTC offset.",
)


# ---------------------------------------------------------------------------
# JSON Formatter Tool
# ---------------------------------------------------------------------------


def format_json(json_string: str, indent: int = 2) -> str:
    """
    Format and validate a JSON string.

    Args:
        json_string: JSON string to format
        indent: Indentation spaces (default: 2)

    Returns:
        Formatted JSON or error message
    """
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


JsonFormatterTool = ToolFromCallable.from_function(
    format_json,
    name="format_json",
    description="Format and validate JSON strings.",
)


# ---------------------------------------------------------------------------
# Text Analyzer Tool
# ---------------------------------------------------------------------------


def analyze_text(text: str) -> str:
    """
    Analyze text and return statistics.

    Args:
        text: Text to analyze

    Returns:
        JSON with text statistics
    """
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]

    word_freq: Dict[str, int] = {}
    for word in words:
        lower = word.lower().strip(".,!?;:'\"")
        if lower:
            word_freq[lower] = word_freq.get(lower, 0) + 1

    # Top 5 words
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

    return json.dumps({
        "characters": len(text),
        "words": len(words),
        "sentences": len(sentences),
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 1),
        "unique_words": len(word_freq),
        "top_words": dict(top_words),
    })


TextAnalyzerTool = ToolFromCallable.from_function(
    analyze_text,
    name="analyze_text",
    description="Analyze text and return statistics (word count, sentence count, top words, etc).",
)


# ---------------------------------------------------------------------------
# Tool Registry Factory
# ---------------------------------------------------------------------------


def create_default_registry() -> ToolRegistry:
    """
    Create a ToolRegistry with all built-in tools.

    Returns:
        ToolRegistry with built-in tools registered
    """
    from aios.ai.tools.base import ToolRegistry

    registry = ToolRegistry()
    registry.register(CalculatorTool)
    registry.register(DateTimeTool)
    registry.register(JsonFormatterTool)
    registry.register(TextAnalyzerTool)
    return registry
