"""
PHOENIX AIOS — OpenAI Integration Error Types

Hierarchical error classification for the AI integration layer.
Maps OpenAI SDK exceptions to PHOENIX domain errors with context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Base Error
# ---------------------------------------------------------------------------


@dataclass
class AIError(Exception):
    """
    Base error for all AI integration errors.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code
        status_code: HTTP status code (if applicable)
        request_id: OpenAI request ID for debugging
        context: Additional error context
        cause: Original exception (if wrapped)
    """

    message: str
    code: str = "AI_ERROR"
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"[{self.code}]")
        if self.request_id:
            parts.append(f"(request: {self.request_id})")
        return " ".join(parts)

    def __post_init__(self):
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------------------------


@dataclass
class AuthenticationError(AIError):
    """Invalid or missing API key."""

    code: str = "AUTHENTICATION_ERROR"
    status_code: int = 401


@dataclass
class PermissionError(AIError):
    """Insufficient permissions for the requested operation."""

    code: str = "PERMISSION_ERROR"
    status_code: int = 403


# ---------------------------------------------------------------------------
# Rate Limiting & Quotas
# ---------------------------------------------------------------------------


@dataclass
class RateLimitError(AIError):
    """
    Rate limit or quota exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided)
    """

    code: str = "RATE_LIMIT_ERROR"
    status_code: int = 429
    retry_after: Optional[float] = None


# ---------------------------------------------------------------------------
# Network & Connection
# ---------------------------------------------------------------------------


@dataclass
class ConnectionError(AIError):
    """Failed to connect to the OpenAI API."""

    code: str = "CONNECTION_ERROR"


@dataclass
class TimeoutError(AIError):
    """Request timed out."""

    code: str = "TIMEOUT_ERROR"


# ---------------------------------------------------------------------------
# Request Validation
# ---------------------------------------------------------------------------


@dataclass
class ValidationError(AIError):
    """Invalid request parameters."""

    code: str = "VALIDATION_ERROR"
    status_code: int = 400


@dataclass
class NotFoundError(AIError):
    """Requested resource not found (e.g., model does not exist)."""

    code: str = "NOT_FOUND_ERROR"
    status_code: int = 404


@dataclass
class UnprocessableError(AIError):
    """Request was well-formed but semantically invalid."""

    code: str = "UNPROCESSABLE_ERROR"
    status_code: int = 422


# ---------------------------------------------------------------------------
# Server Errors
# ---------------------------------------------------------------------------


@dataclass
class ServerError(AIError):
    """OpenAI server-side error."""

    code: str = "SERVER_ERROR"
    status_code: int = 500


@dataclass
class OverloadedError(AIError):
    """API is overloaded."""

    code: str = "OVERLOADED_ERROR"
    status_code: int = 529


# ---------------------------------------------------------------------------
# Tool Execution Errors
# ---------------------------------------------------------------------------


@dataclass
class ToolExecutionError(AIError):
    """
    Error during tool/function execution.

    Attributes:
        tool_name: Name of the tool that failed
        tool_call_id: ID of the failed tool call
    """

    code: str = "TOOL_EXECUTION_ERROR"
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolNotFoundError(AIError):
    """Requested tool is not registered."""

    code: str = "TOOL_NOT_FOUND"


# ---------------------------------------------------------------------------
# Content & Safety
# ---------------------------------------------------------------------------


@dataclass
class ContentFilterError(AIError):
    """Content was filtered by safety systems."""

    code: str = "CONTENT_FILTER_ERROR"
    status_code: int = 400


# ---------------------------------------------------------------------------
# Error Mapping
# ---------------------------------------------------------------------------


def map_openai_error(error: Exception) -> AIError:
    """
    Map an OpenAI SDK exception to a PHOENIX AIError.

    This function handles all known OpenAI SDK error types and maps them
    to the appropriate PHOENIX error class with context preservation.

    Args:
        error: The original OpenAI SDK exception

    Returns:
        Appropriate AIError subclass instance
    """
    try:
        import openai
    except ImportError:
        return AIError(
            message=str(error),
            code="UNKNOWN_ERROR",
            cause=error,
        )

    request_id = None
    if hasattr(error, "request_id"):
        request_id = error.request_id
    elif hasattr(error, "response") and hasattr(error.response, "headers"):
        request_id = error.response.headers.get("x-request-id")

    context: Dict[str, Any] = {}
    if hasattr(error, "body"):
        context["body"] = error.body

    # Map by exception type
    if isinstance(error, openai.AuthenticationError):
        return AuthenticationError(
            message=f"Authentication failed: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.PermissionDeniedError):
        return PermissionError(
            message=f"Permission denied: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.RateLimitError):
        retry_after = None
        if hasattr(error, "response") and hasattr(error.response, "headers"):
            retry_header = error.response.headers.get("retry-after")
            if retry_header:
                try:
                    retry_after = float(retry_header)
                except (ValueError, TypeError):
                    pass

        return RateLimitError(
            message=f"Rate limit exceeded: {error.message}",
            request_id=request_id,
            retry_after=retry_after,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.APIConnectionError):
        return ConnectionError(
            message=f"Connection failed: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.APITimeoutError):
        return TimeoutError(
            message=f"Request timed out: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.BadRequestError):
        return ValidationError(
            message=f"Bad request: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.NotFoundError):
        return NotFoundError(
            message=f"Not found: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.UnprocessableEntityError):
        return UnprocessableError(
            message=f"Unprocessable: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    if isinstance(error, openai.InternalServerError):
        return ServerError(
            message=f"Server error: {error.message}",
            request_id=request_id,
            context=context,
            cause=error,
        )

    # Generic API status error
    if isinstance(error, openai.APIStatusError):
        return AIError(
            message=f"API error ({error.status_code}): {error.message}",
            code=f"API_ERROR_{error.status_code}",
            status_code=error.status_code,
            request_id=request_id,
            context=context,
            cause=error,
        )

    # Generic API error
    if isinstance(error, openai.APIError):
        return AIError(
            message=f"API error: {error.message}",
            code="API_ERROR",
            request_id=request_id,
            context=context,
            cause=error,
        )

    # Fallback
    return AIError(
        message=str(error),
        code="UNKNOWN_ERROR",
        cause=error,
    )
