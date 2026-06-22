"""
PHOENIX AIOS — Tests for Error Types

Tests error hierarchy and map_openai_error.
"""

from __future__ import annotations

import unittest

from aios.ai.errors import (
    AIError,
    AuthenticationError,
    ConnectionError,
    ContentFilterError,
    NotFoundError,
    OverloadedError,
    PermissionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ToolExecutionError,
    ToolNotFoundError,
    UnprocessableError,
    ValidationError,
    map_openai_error,
)


class TestAIError(unittest.TestCase):
    """Test base AIError."""

    def test_creation(self):
        err = AIError(message="Something went wrong")
        assert err.message == "Something went wrong"
        assert err.code == "AI_ERROR"
        assert err.status_code is None

    def test_str(self):
        err = AIError(message="fail", code="TEST_ERROR")
        assert "fail" in str(err)
        assert "TEST_ERROR" in str(err)

    def test_str_with_request_id(self):
        err = AIError(message="fail", request_id="req_123")
        assert "req_123" in str(err)

    def test_is_exception(self):
        err = AIError(message="fail")
        assert isinstance(err, Exception)


class TestSubErrors(unittest.TestCase):
    """Test all error subclasses."""

    def test_authentication_error(self):
        err = AuthenticationError(message="bad key")
        assert err.code == "AUTHENTICATION_ERROR"
        assert err.status_code == 401

    def test_permission_error(self):
        err = PermissionError(message="no access")
        assert err.code == "PERMISSION_ERROR"
        assert err.status_code == 403

    def test_rate_limit_error(self):
        err = RateLimitError(message="slow down", retry_after=30.0)
        assert err.code == "RATE_LIMIT_ERROR"
        assert err.status_code == 429
        assert err.retry_after == 30.0

    def test_connection_error(self):
        err = ConnectionError(message="no connection")
        assert err.code == "CONNECTION_ERROR"

    def test_timeout_error(self):
        err = TimeoutError(message="timed out")
        assert err.code == "TIMEOUT_ERROR"

    def test_validation_error(self):
        err = ValidationError(message="bad params")
        assert err.code == "VALIDATION_ERROR"
        assert err.status_code == 400

    def test_not_found_error(self):
        err = NotFoundError(message="not found")
        assert err.code == "NOT_FOUND_ERROR"
        assert err.status_code == 404

    def test_unprocessable_error(self):
        err = UnprocessableError(message="unprocessable")
        assert err.code == "UNPROCESSABLE_ERROR"
        assert err.status_code == 422

    def test_server_error(self):
        err = ServerError(message="server boom")
        assert err.code == "SERVER_ERROR"
        assert err.status_code == 500

    def test_overloaded_error(self):
        err = OverloadedError(message="too busy")
        assert err.code == "OVERLOADED_ERROR"
        assert err.status_code == 529

    def test_tool_execution_error(self):
        err = ToolExecutionError(
            message="tool failed",
            tool_name="get_weather",
            tool_call_id="call_1",
        )
        assert err.code == "TOOL_EXECUTION_ERROR"
        assert err.tool_name == "get_weather"
        assert err.tool_call_id == "call_1"

    def test_tool_not_found_error(self):
        err = ToolNotFoundError(message="no such tool")
        assert err.code == "TOOL_NOT_FOUND"

    def test_content_filter_error(self):
        err = ContentFilterError(message="filtered")
        assert err.code == "CONTENT_FILTER_ERROR"


class TestMapOpenAIError(unittest.TestCase):
    """Test map_openai_error function."""

    def test_map_generic_exception(self):
        """Non-OpenAI exceptions should be wrapped as AIError."""
        err = map_openai_error(ValueError("bad value"))
        assert isinstance(err, AIError)
        assert err.code == "UNKNOWN_ERROR"
        assert "bad value" in err.message

    def test_cause_preserved(self):
        original = ValueError("original")
        err = map_openai_error(original)
        assert err.cause is original


if __name__ == "__main__":
    unittest.main()
