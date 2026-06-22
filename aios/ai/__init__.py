"""
PHOENIX AIOS — OpenAI AI Integration Layer

Complete integration with OpenAI API providing:
- Chat Completions with full parameter support
- Function Calling / Tool Use framework
- Streaming response handling
- Structured Outputs (JSON Schema mode)
- Comprehensive error handling and retry logic

Architecture:
    PhoenixAIClient (main entry point)
    ├── ChatCompletions (chat operations)
    ├── ToolRegistry (function/tool definitions)
    ├── StreamHandler (streaming processing)
    └── ErrorHandler (error classification + retry)

Usage:
    from aios.ai import PhoenixAIClient, Tool, ToolRegistry

    client = PhoenixAIClient(api_key="sk-...")

    # Simple chat
    response = client.chat("Hello, world!")

    # With tools
    registry = ToolRegistry()
    registry.register(my_tool)
    response = client.chat("What's the weather?", tools=registry)

    # Streaming
    for chunk in client.chat_stream("Tell me a story"):
        print(chunk.content, end="")
"""

from __future__ import annotations

from aios.ai.client import PhoenixAIClient
from aios.ai.types import (
    ChatMessage,
    ChatRole,
    ChatResponse,
    ChatStreamChunk,
    ToolCall,
    ToolResult,
    Usage,
)
from aios.ai.tools.base import Tool, ToolParameter, ToolRegistry
from aios.ai.streaming.handler import StreamHandler
from aios.ai.errors import (
    AIError,
    AuthenticationError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
    ValidationError,
    ToolExecutionError,
)

__all__ = [
    # Client
    "PhoenixAIClient",
    # Types
    "ChatMessage",
    "ChatRole",
    "ChatResponse",
    "ChatStreamChunk",
    "ToolCall",
    "ToolResult",
    "Usage",
    # Tools
    "Tool",
    "ToolParameter",
    "ToolRegistry",
    # Streaming
    "StreamHandler",
    # Errors
    "AIError",
    "AuthenticationError",
    "RateLimitError",
    "ConnectionError",
    "TimeoutError",
    "ValidationError",
    "ToolExecutionError",
]

__version__ = "1.0.0"
