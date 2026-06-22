"""
Built-in tools for PHOENIX AIOS LangChain integration.

Provides common tools for agents.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

from ..core import Config, Logger
from .base import Tool, ToolInput, ToolResult, ToolParameter


class SearchTool(Tool):
    """
    Search tool for searching text.

    Example:
        tool = SearchTool()
        result = tool.execute(ToolInput(kwargs={
            "text": "Hello World",
            "pattern": "World",
        }))
    """

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search for patterns in text"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("text", str, "Text to search in", required=True)
        self.add_parameter("pattern", str, "Pattern to search for", required=True)
        self.add_parameter("case_sensitive", bool, "Case sensitive search", required=False, default=True)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute search."""
        import time
        start = time.time()

        text = tool_input.kwargs["text"]
        pattern = tool_input.kwargs["pattern"]
        case_sensitive = tool_input.kwargs.get("case_sensitive", True)

        try:
            if not case_sensitive:
                matches = re.findall(pattern, text, re.IGNORECASE)
            else:
                matches = re.findall(pattern, text)

            duration = time.time() - start
            return ToolResult.success(
                data={"matches": matches, "count": len(matches)},
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class CalculatorTool(Tool):
    """
    Calculator tool for mathematical operations.

    Example:
        tool = CalculatorTool()
        result = tool.execute(ToolInput(kwargs={
            "expression": "2 + 3 * 4",
        }))
    """

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("expression", str, "Mathematical expression to evaluate", required=True)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute calculation."""
        import time
        start = time.time()

        expression = tool_input.kwargs["expression"]

        try:
            # Safe evaluation
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
                "pi": math.pi,
                "e": math.e,
            }

            # Validate expression
            if any(op in expression for op in ["import", "exec", "eval", "__"]):
                raise ValueError("Unsafe expression")

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            duration = time.time() - start

            return ToolResult.success(data=result, duration=duration)
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class FileReaderTool(Tool):
    """
    File reader tool.

    Example:
        tool = FileReaderTool()
        result = tool.execute(ToolInput(kwargs={
            "path": "/path/to/file.txt",
        }))
    """

    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return "Read file contents"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("path", str, "File path to read", required=True)
        self.add_parameter("encoding", str, "File encoding", required=False, default="utf-8")

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute file read."""
        import time
        start = time.time()

        path = tool_input.kwargs["path"]
        encoding = tool_input.kwargs.get("encoding", "utf-8")

        try:
            # Security check
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

            with open(path, "r", encoding=encoding) as f:
                content = f.read()

            duration = time.time() - start
            return ToolResult.success(
                data={"content": content, "size": len(content)},
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class FileWriterTool(Tool):
    """
    File writer tool.

    Example:
        tool = FileWriterTool()
        result = tool.execute(ToolInput(kwargs={
            "path": "/path/to/file.txt",
            "content": "Hello World",
        }))
    """

    @property
    def name(self) -> str:
        return "file_writer"

    @property
    def description(self) -> str:
        return "Write content to file"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("path", str, "File path to write", required=True)
        self.add_parameter("content", str, "Content to write", required=True)
        self.add_parameter("encoding", str, "File encoding", required=False, default="utf-8")
        self.add_parameter("append", bool, "Append to file", required=False, default=False)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute file write."""
        import time
        start = time.time()

        path = tool_input.kwargs["path"]
        content = tool_input.kwargs["content"]
        encoding = tool_input.kwargs.get("encoding", "utf-8")
        append = tool_input.kwargs.get("append", False)

        try:
            mode = "a" if append else "w"
            with open(path, mode, encoding=encoding) as f:
                f.write(content)

            duration = time.time() - start
            return ToolResult.success(
                data={"path": path, "bytes_written": len(content.encode(encoding))},
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class ShellTool(Tool):
    """
    Shell command execution tool.

    Example:
        tool = ShellTool()
        result = tool.execute(ToolInput(kwargs={
            "command": "ls -la",
        }))
    """

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute shell commands"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("command", str, "Shell command to execute", required=True)
        self.add_parameter("timeout", int, "Timeout in seconds", required=False, default=30)
        self.add_parameter("cwd", str, "Working directory", required=False, default=None)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute shell command."""
        import time
        start = time.time()

        command = tool_input.kwargs["command"]
        timeout = tool_input.kwargs.get("timeout", 30)
        cwd = tool_input.kwargs.get("cwd")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )

            duration = time.time() - start

            if result.returncode == 0:
                return ToolResult.success(
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                    duration=duration,
                )
            else:
                return ToolResult.error(
                    error=f"Command failed with return code {result.returncode}: {result.stderr}",
                    duration=duration,
                )
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return ToolResult.timeout(duration=duration)
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class HTTPTool(Tool):
    """
    HTTP request tool.

    Example:
        tool = HTTPTool()
        result = tool.execute(ToolInput(kwargs={
            "url": "https://api.example.com/data",
            "method": "GET",
        }))
    """

    @property
    def name(self) -> str:
        return "http"

    @property
    def description(self) -> str:
        return "Make HTTP requests"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("url", str, "URL to request", required=True)
        self.add_parameter("method", str, "HTTP method", required=False, default="GET")
        self.add_parameter("headers", dict, "Request headers", required=False, default={})
        self.add_parameter("data", str, "Request body", required=False, default=None)
        self.add_parameter("timeout", int, "Timeout in seconds", required=False, default=30)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute HTTP request."""
        import time
        import urllib.request
        import urllib.error

        start = time.time()

        url = tool_input.kwargs["url"]
        method = tool_input.kwargs.get("method", "GET").upper()
        headers = tool_input.kwargs.get("headers", {})
        data = tool_input.kwargs.get("data")
        timeout = tool_input.kwargs.get("timeout", 30)

        try:
            # Prepare request
            req = urllib.request.Request(url, method=method, headers=headers)
            if data:
                req.data = data.encode("utf-8")

            # Execute request
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                status = response.status

            duration = time.time() - start

            return ToolResult.success(
                data={
                    "status": status,
                    "body": body,
                    "headers": dict(response.headers),
                },
                duration=duration,
            )
        except urllib.error.HTTPError as e:
            duration = time.time() - start
            return ToolResult.error(
                error=f"HTTP {e.code}: {e.reason}",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)


class JSONTool(Tool):
    """
    JSON processing tool.

    Example:
        tool = JSONTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "parse",
            "text": '{"key": "value"}',
        }))
    """

    @property
    def name(self) -> str:
        return "json"

    @property
    def description(self) -> str:
        return "Process JSON data"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("action", str, "Action: parse, stringify, query", required=True)
        self.add_parameter("text", str, "JSON text", required=False)
        self.add_parameter("data", Any, "Data to stringify", required=False)
        self.add_parameter("path", str, "JSON path for query", required=False)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute JSON operation."""
        import time
        start = time.time()

        action = tool_input.kwargs["action"]

        try:
            if action == "parse":
                text = tool_input.kwargs["text"]
                result = json.loads(text)
            elif action == "stringify":
                data = tool_input.kwargs["data"]
                result = json.dumps(data, indent=2)
            elif action == "query":
                text = tool_input.kwargs["text"]
                path = tool_input.kwargs["path"]
                data = json.loads(text)
                result = self._query_json(data, path)
            else:
                raise ValueError(f"Unknown action: {action}")

            duration = time.time() - start
            return ToolResult.success(data=result, duration=duration)
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)

    def _query_json(self, data: Any, path: str) -> Any:
        """Query JSON data using dot notation."""
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current


class RegexTool(Tool):
    """
    Regular expression tool.

    Example:
        tool = RegexTool()
        result = tool.execute(ToolInput(kwargs={
            "action": "match",
            "text": "Hello World",
            "pattern": r"Hello (\w+)",
        }))
    """

    @property
    def name(self) -> str:
        return "regex"

    @property
    def description(self) -> str:
        return "Regular expression operations"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self.add_parameter("action", str, "Action: match, search, findall, sub", required=True)
        self.add_parameter("text", str, "Text to process", required=True)
        self.add_parameter("pattern", str, "Regex pattern", required=True)
        self.add_parameter("replacement", str, "Replacement for sub", required=False)

    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute regex operation."""
        import time
        start = time.time()

        action = tool_input.kwargs["action"]
        text = tool_input.kwargs["text"]
        pattern = tool_input.kwargs["pattern"]

        try:
            if action == "match":
                match = re.match(pattern, text)
                result = {
                    "matched": match is not None,
                    "groups": match.groups() if match else None,
                }
            elif action == "search":
                match = re.search(pattern, text)
                result = {
                    "found": match is not None,
                    "start": match.start() if match else None,
                    "end": match.end() if match else None,
                    "match": match.group() if match else None,
                }
            elif action == "findall":
                matches = re.findall(pattern, text)
                result = {"matches": matches, "count": len(matches)}
            elif action == "sub":
                replacement = tool_input.kwargs.get("replacement", "")
                result = re.sub(pattern, replacement, text)
            else:
                raise ValueError(f"Unknown action: {action}")

            duration = time.time() - start
            return ToolResult.success(data=result, duration=duration)
        except Exception as e:
            duration = time.time() - start
            return ToolResult.error(error=str(e), duration=duration)
