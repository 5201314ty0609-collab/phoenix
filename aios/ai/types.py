"""
PHOENIX AIOS — OpenAI Integration Types

Immutable data structures for the AI integration layer.
All types follow PHOENIX's immutability principle (frozen=True).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChatRole(Enum):
    """Message roles in a conversation."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class FinishReason(Enum):
    """Reason the model stopped generating."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"  # deprecated


class ResponseFormat(Enum):
    """Output format modes."""

    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


class ToolChoiceMode(Enum):
    """Tool choice strategies."""

    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


# ---------------------------------------------------------------------------
# Core Message Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolCall:
    """
    A tool call requested by the model.

    Attributes:
        id: Unique tool call ID (from the API)
        name: Function name to call
        arguments: JSON string of arguments
        type: Tool type (always "function" for function tools)
    """

    id: str
    name: str
    arguments: str
    type: str = "function"

    @property
    def parsed_arguments(self) -> Dict[str, Any]:
        """Parse arguments JSON string into a dictionary."""
        import json

        try:
            return json.loads(self.arguments)
        except (json.JSONDecodeError, TypeError):
            return {}

    def with_result(self, result: Any) -> ToolResult:
        """Create a ToolResult from this call."""
        import json

        return ToolResult(
            tool_call_id=self.id,
            name=self.name,
            content=json.dumps(result) if not isinstance(result, str) else result,
        )


@dataclass(frozen=True)
class ToolResult:
    """
    Result of a tool execution.

    Attributes:
        tool_call_id: ID of the tool call this responds to
        name: Function name
        content: Result content as string
        role: Always TOOL
    """

    tool_call_id: str
    name: str
    content: str
    role: ChatRole = ChatRole.TOOL


@dataclass(frozen=True)
class Usage:
    """
    Token usage statistics.

    Attributes:
        prompt_tokens: Tokens in the prompt
        completion_tokens: Tokens in the completion
        total_tokens: Total tokens used
        cached_tokens: Tokens served from cache (if available)
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


@dataclass(frozen=True)
class ChatMessage:
    """
    A single message in a conversation.

    Attributes:
        role: Message role (system/user/assistant/tool)
        content: Text content (None if tool_calls present)
        name: Optional sender name
        tool_calls: Tool calls requested by assistant
        tool_call_id: ID of tool call this message responds to (for role=tool)
    """

    role: ChatRole
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: Optional[str] = None

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI API message format."""
        msg: Dict[str, Any] = {"role": self.role.value}

        if self.content is not None:
            msg["content"] = self.content

        if self.name:
            msg["name"] = self.name

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    },
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        return msg

    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """Create a system message."""
        return cls(role=ChatRole.SYSTEM, content=content)

    @classmethod
    def developer(cls, content: str) -> ChatMessage:
        """Create a developer message."""
        return cls(role=ChatRole.DEVELOPER, content=content)

    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> ChatMessage:
        """Create a user message."""
        return cls(role=ChatRole.USER, content=content, name=name)

    @classmethod
    def assistant(
        cls,
        content: Optional[str] = None,
        tool_calls: Optional[Sequence[ToolCall]] = None,
    ) -> ChatMessage:
        """Create an assistant message."""
        return cls(
            role=ChatRole.ASSISTANT,
            content=content,
            tool_calls=tuple(tool_calls) if tool_calls else (),
        )

    @classmethod
    def tool(cls, tool_call_id: str, name: str, content: str) -> ChatMessage:
        """Create a tool result message."""
        return cls(
            role=ChatRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
        )


# ---------------------------------------------------------------------------
# Response Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatChoice:
    """
    A single completion choice.

    Attributes:
        index: Choice index
        message: The generated message
        finish_reason: Why generation stopped
        logprobs: Log probabilities (if requested)
    """

    index: int
    message: ChatMessage
    finish_reason: Optional[FinishReason] = None
    logprobs: Optional[Any] = None


@dataclass(frozen=True)
class ChatResponse:
    """
    Complete chat completion response.

    Attributes:
        id: Unique response ID
        model: Model used
        choices: List of completion choices
        usage: Token usage statistics
        created: Unix timestamp of creation
        system_fingerprint: System fingerprint for reproducibility
    """

    id: str
    model: str
    choices: tuple[ChatChoice, ...]
    usage: Usage = field(default_factory=Usage)
    created: float = field(default_factory=time.time)
    system_fingerprint: Optional[str] = None

    @property
    def first_choice(self) -> Optional[ChatChoice]:
        """Get the first (primary) choice."""
        return self.choices[0] if self.choices else None

    @property
    def content(self) -> Optional[str]:
        """Get the content of the first choice."""
        choice = self.first_choice
        if choice and choice.message:
            return choice.message.content
        return None

    @property
    def tool_calls(self) -> tuple[ToolCall, ...]:
        """Get tool calls from the first choice."""
        choice = self.first_choice
        if choice and choice.message:
            return choice.message.tool_calls
        return ()

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def finish_reason(self) -> Optional[FinishReason]:
        """Get finish reason from the first choice."""
        choice = self.first_choice
        return choice.finish_reason if choice else None


@dataclass(frozen=True)
class ChatStreamChunk:
    """
    A single streaming chunk.

    Attributes:
        id: Chunk ID (same across all chunks in a response)
        model: Model used
        delta: Incremental content
        finish_reason: Set on final chunk
        index: Choice index
        created: Unix timestamp
    """

    id: str
    model: str
    delta: StreamDelta
    finish_reason: Optional[FinishReason] = None
    index: int = 0
    created: float = field(default_factory=time.time)


@dataclass(frozen=True)
class StreamDelta:
    """
    Incremental content in a streaming chunk.

    Attributes:
        role: Role (set on first chunk)
        content: Incremental text content
        tool_calls: Incremental tool call data
    """

    role: Optional[ChatRole] = None
    content: Optional[str] = None
    tool_calls: tuple[ToolCallDelta, ...] = ()


@dataclass(frozen=True)
class ToolCallDelta:
    """
    Incremental tool call data in streaming.

    Attributes:
        index: Tool call index
        id: Tool call ID (set on first chunk of this tool call)
        name: Function name (set on first chunk)
        arguments: Incremental argument string
    """

    index: int
    id: Optional[str] = None
    name: Optional[str] = None
    arguments: str = ""


# ---------------------------------------------------------------------------
# Configuration Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatConfig:
    """
    Configuration for chat completion requests.

    Attributes:
        model: Model ID (e.g., "gpt-4o", "gpt-4o-mini")
        temperature: Sampling temperature (0-2)
        top_p: Nucleus sampling parameter
        max_tokens: Maximum tokens to generate
        frequency_penalty: Frequency penalty (-2 to 2)
        presence_penalty: Presence penalty (-2 to 2)
        seed: Seed for deterministic output
        response_format: Output format constraint
        json_schema: JSON Schema for structured outputs
        user: End-user identifier
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """

    model: str = "gpt-4o"
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    seed: Optional[int] = None
    response_format: Optional[ResponseFormat] = None
    json_schema: Optional[Dict[str, Any]] = None
    user: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3

    def to_api_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for the OpenAI API call."""
        kwargs: Dict[str, Any] = {"model": self.model}

        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        if self.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            kwargs["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            kwargs["seed"] = self.seed
        if self.user:
            kwargs["user"] = self.user

        if self.response_format:
            if self.response_format == ResponseFormat.JSON_SCHEMA and self.json_schema:
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": self.json_schema,
                }
            elif self.response_format == ResponseFormat.JSON_OBJECT:
                kwargs["response_format"] = {"type": "json_object"}

        return kwargs


@dataclass(frozen=True)
class ToolChoiceConfig:
    """
    Configuration for tool choice behavior.

    Attributes:
        mode: Tool choice strategy
        tool_name: Specific tool name (when mode forces a specific tool)
    """

    mode: ToolChoiceMode = ToolChoiceMode.AUTO
    tool_name: Optional[str] = None

    def to_api_value(self) -> Any:
        """Convert to API tool_choice parameter."""
        # Specific tool name takes precedence over mode
        if self.tool_name:
            return {
                "type": "function",
                "function": {"name": self.tool_name},
            }
        if self.mode == ToolChoiceMode.AUTO:
            return "auto"
        if self.mode == ToolChoiceMode.NONE:
            return "none"
        if self.mode == ToolChoiceMode.REQUIRED:
            return "required"
        return "auto"
