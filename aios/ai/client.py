"""
PHOENIX AIOS — OpenAI Client Wrapper

The main entry point for AI operations. Wraps the OpenAI Python SDK
with PHOENIX-specific features:
- Automatic error mapping to PHOENIX error types
- Configurable retry with exponential backoff
- Tool/function calling integration
- Streaming with structured chunk processing
- Conversation management helpers
- Structured output support

Usage:
    from aios.ai import PhoenixAIClient

    client = PhoenixAIClient(api_key="sk-...")

    # Simple chat
    response = client.chat("Hello!")

    # Chat with system prompt
    response = client.chat(
        "What is 2+2?",
        system="You are a math tutor.",
    )

    # Chat with tools
    response = client.chat(
        "What's the weather in Tokyo?",
        tools=my_tool_registry,
    )

    # Streaming
    for chunk in client.chat_stream("Tell me a joke"):
        print(chunk, end="")

    # Structured output
    response = client.chat_structured(
        "List 3 programming languages",
        schema={"type": "object", "properties": {"languages": {"type": "array", "items": {"type": "string"}}}},
    )
"""

from __future__ import annotations

import json
import time
import uuid
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from aios.ai.errors import AIError, map_openai_error
from aios.ai.streaming.handler import StreamHandler, StreamCollector
from aios.ai.tools.base import ToolRegistry
from aios.ai.types import (
    ChatConfig,
    ChatMessage,
    ChatResponse,
    ChatRole,
    ChatStreamChunk,
    ResponseFormat,
    ToolCall,
    ToolChoiceConfig,
    ToolChoiceMode,
    Usage,
)


# ---------------------------------------------------------------------------
# Phoenix AI Client
# ---------------------------------------------------------------------------


class PhoenixAIClient:
    """
    Main client for AI operations.

    Wraps the OpenAI Python SDK with PHOENIX-specific features.

    Attributes:
        config: Default chat configuration
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[ChatConfig] = None,
        default_system: Optional[str] = None,
    ) -> None:
        """
        Initialize the PHOENIX AI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom API base URL
            config: Default chat configuration
            default_system: Default system prompt for all chats
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        self._config = config or ChatConfig()
        self._default_system = default_system

        # Build client kwargs
        client_kwargs: Dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        # Configure timeout and retries
        client_kwargs["timeout"] = self._config.timeout
        client_kwargs["max_retries"] = self._config.max_retries

        self._client = OpenAI(**client_kwargs)

    @property
    def config(self) -> ChatConfig:
        """Get default configuration."""
        return self._config

    def with_config(self, **kwargs: Any) -> PhoenixAIClient:
        """
        Create a new client with overridden configuration.

        Args:
            **kwargs: ChatConfig field overrides

        Returns:
            New PhoenixAIClient instance
        """
        from dataclasses import replace

        new_config = replace(self._config, **kwargs)
        return PhoenixAIClient(
            config=new_config,
            default_system=self._default_system,
        )

    # ------------------------------------------------------------------
    # Chat Completions
    # ------------------------------------------------------------------

    def chat(
        self,
        message: str,
        *,
        system: Optional[str] = None,
        history: Optional[Sequence[ChatMessage]] = None,
        tools: Optional[ToolRegistry] = None,
        tool_choice: Optional[ToolChoiceConfig] = None,
        config: Optional[ChatConfig] = None,
        max_tool_rounds: int = 5,
        user: Optional[str] = None,
    ) -> ChatResponse:
        """
        Send a chat completion request.

        Supports:
        - System/developer prompts
        - Conversation history
        - Tool/function calling with automatic round-trip
        - Configuration overrides per request

        Args:
            message: User message
            system: System prompt (overrides default_system)
            history: Previous messages in the conversation
            tools: Tool registry for function calling
            tool_choice: Tool choice configuration
            config: Per-request config override
            max_tool_rounds: Maximum tool call round-trips (prevents infinite loops)
            user: End-user identifier

        Returns:
            ChatResponse with the model's reply

        Raises:
            AIError: On API errors (mapped from OpenAI exceptions)
        """
        effective_config = config or self._config

        # Build messages
        messages = self._build_messages(message, system=system, history=history)

        # Build API kwargs
        api_kwargs = effective_config.to_api_kwargs()
        api_kwargs["messages"] = messages

        if user:
            api_kwargs["user"] = user

        # Add tools if provided
        if tools and tools.count > 0:
            api_kwargs["tools"] = tools.to_api_definitions()
            if tool_choice:
                api_kwargs["tool_choice"] = tool_choice.to_api_value()

        # Execute with tool loop
        return self._execute_with_tool_loop(
            api_kwargs=api_kwargs,
            tools=tools,
            tool_choice=tool_choice,
            max_rounds=max_tool_rounds,
            config=effective_config,
        )

    def chat_stream(
        self,
        message: str,
        *,
        system: Optional[str] = None,
        history: Optional[Sequence[ChatMessage]] = None,
        config: Optional[ChatConfig] = None,
        user: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream a chat completion response.

        Args:
            message: User message
            system: System prompt
            history: Previous messages
            config: Per-request config override
            user: End-user identifier

        Yields:
            Content delta strings

        Raises:
            AIError: On API errors
        """
        effective_config = config or self._config

        # Build messages
        messages = self._build_messages(message, system=system, history=history)

        # Build API kwargs
        api_kwargs = effective_config.to_api_kwargs()
        api_kwargs["messages"] = messages
        api_kwargs["stream"] = True
        api_kwargs["stream_options"] = {"include_usage": True}

        if user:
            api_kwargs["user"] = user

        # Execute streaming
        try:
            stream = self._client.chat.completions.create(**api_kwargs)
            handler = StreamHandler()
            yield from handler.iter_content(stream)
        except Exception as e:
            raise map_openai_error(e)

    def chat_stream_chunks(
        self,
        message: str,
        *,
        system: Optional[str] = None,
        history: Optional[Sequence[ChatMessage]] = None,
        config: Optional[ChatConfig] = None,
        on_content: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[ChatResponse], None]] = None,
        user: Optional[str] = None,
    ) -> ChatResponse:
        """
        Stream with full chunk processing and callbacks.

        Args:
            message: User message
            system: System prompt
            history: Previous messages
            config: Per-request config override
            on_content: Callback for each content delta
            on_complete: Callback when streaming completes
            user: End-user identifier

        Returns:
            Complete ChatResponse assembled from chunks
        """
        effective_config = config or self._config

        messages = self._build_messages(message, system=system, history=history)

        api_kwargs = effective_config.to_api_kwargs()
        api_kwargs["messages"] = messages
        api_kwargs["stream"] = True
        api_kwargs["stream_options"] = {"include_usage": True}

        if user:
            api_kwargs["user"] = user

        try:
            stream = self._client.chat.completions.create(**api_kwargs)
            handler = StreamHandler(
                on_content=on_content,
                on_complete=on_complete,
            )
            return handler.process_stream(stream)
        except Exception as e:
            raise map_openai_error(e)

    # ------------------------------------------------------------------
    # Structured Output
    # ------------------------------------------------------------------

    def chat_structured(
        self,
        message: str,
        schema: Dict[str, Any],
        *,
        system: Optional[str] = None,
        history: Optional[Sequence[ChatMessage]] = None,
        config: Optional[ChatConfig] = None,
        user: Optional[str] = None,
    ) -> ChatResponse:
        """
        Chat with structured output (JSON Schema mode).

        Uses OpenAI's structured outputs to guarantee the response
        conforms to the provided JSON Schema.

        Args:
            message: User message
            schema: JSON Schema for the response
            system: System prompt
            history: Previous messages
            config: Per-request config override
            user: End-user identifier

        Returns:
            ChatResponse with JSON-conforming content
        """
        effective_config = config or self._config

        # Build structured output config
        schema_name = schema.get("name", "response")
        from dataclasses import replace

        structured_config = replace(
            effective_config,
            response_format=ResponseFormat.JSON_SCHEMA,
            json_schema={
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        )

        return self.chat(
            message,
            system=system,
            history=history,
            config=structured_config,
            user=user,
        )

    # ------------------------------------------------------------------
    # Conversation Helpers
    # ------------------------------------------------------------------

    def continue_conversation(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Optional[ToolRegistry] = None,
        tool_choice: Optional[ToolChoiceConfig] = None,
        config: Optional[ChatConfig] = None,
        max_tool_rounds: int = 5,
    ) -> ChatResponse:
        """
        Continue an existing conversation.

        Args:
            messages: Full conversation history (including new user message)
            tools: Tool registry
            tool_choice: Tool choice configuration
            config: Per-request config override
            max_tool_rounds: Maximum tool call round-trips

        Returns:
            ChatResponse
        """
        effective_config = config or self._config

        api_kwargs = effective_config.to_api_kwargs()
        api_kwargs["messages"] = [m.to_api_dict() for m in messages]

        if tools and tools.count > 0:
            api_kwargs["tools"] = tools.to_api_definitions()
            if tool_choice:
                api_kwargs["tool_choice"] = tool_choice.to_api_value()

        return self._execute_with_tool_loop(
            api_kwargs=api_kwargs,
            tools=tools,
            tool_choice=tool_choice,
            max_rounds=max_tool_rounds,
            config=effective_config,
        )

    # ------------------------------------------------------------------
    # Raw API Access
    # ------------------------------------------------------------------

    def raw_chat(self, **kwargs: Any) -> Any:
        """
        Direct access to the OpenAI chat completions API.

        Args:
            **kwargs: Raw API parameters

        Returns:
            Raw API response
        """
        try:
            return self._client.chat.completions.create(**kwargs)
        except Exception as e:
            raise map_openai_error(e)

    @property
    def openai_client(self) -> Any:
        """Get the underlying OpenAI client for advanced usage."""
        return self._client

    # ------------------------------------------------------------------
    # Internal Methods
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        message: str,
        *,
        system: Optional[str] = None,
        history: Optional[Sequence[ChatMessage]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build the messages list for an API call.

        Args:
            message: User message
            system: System prompt
            history: Previous messages

        Returns:
            List of message dicts
        """
        messages: List[Dict[str, Any]] = []

        # System prompt
        system_text = system or self._default_system
        if system_text:
            messages.append({"role": "system", "content": system_text})

        # History
        if history:
            for msg in history:
                messages.append(msg.to_api_dict())

        # Current message
        messages.append({"role": "user", "content": message})

        return messages

    def _execute_with_tool_loop(
        self,
        api_kwargs: Dict[str, Any],
        tools: Optional[ToolRegistry],
        tool_choice: Optional[ToolChoiceConfig],
        max_rounds: int,
        config: ChatConfig,
    ) -> ChatResponse:
        """
        Execute a chat completion with automatic tool call handling.

        The loop:
        1. Send request to model
        2. If model returns tool calls, execute them
        3. Append tool results to messages
        4. Repeat until model returns text or max rounds reached

        Args:
            api_kwargs: API call kwargs (modified in-place)
            tools: Tool registry
            tool_choice: Tool choice config
            max_rounds: Maximum round-trips
            config: Chat configuration

        Returns:
            Final ChatResponse
        """
        messages = api_kwargs["messages"]

        for round_num in range(max_rounds):
            # Make API call
            try:
                response_raw = self._client.chat.completions.create(**api_kwargs)
            except Exception as e:
                raise map_openai_error(e)

            # Parse response
            response = self._parse_response(response_raw)

            # Check for tool calls
            if not response.has_tool_calls or tools is None:
                return response

            # Execute tool calls
            tool_calls = response.tool_calls
            tool_results = tools.execute_all(tool_calls)

            # Append assistant message with tool calls
            assistant_msg = ChatMessage.assistant(tool_calls=tool_calls)
            messages.append(assistant_msg.to_api_dict())

            # Append tool results
            for result in tool_results:
                tool_msg = ChatMessage.tool(
                    tool_call_id=result.tool_call_id,
                    name=result.name,
                    content=result.content,
                )
                messages.append(tool_msg.to_api_dict())

        # Max rounds reached — return last response
        return response

    def _parse_response(self, raw: Any) -> ChatResponse:
        """
        Parse a raw OpenAI response into a ChatResponse.

        Args:
            raw: Raw OpenAI ChatCompletion object

        Returns:
            ChatResponse
        """
        # Parse choices
        choices = []
        for raw_choice in raw.choices:
            raw_msg = raw_choice.message

            # Parse tool calls
            tool_calls: List[ToolCall] = []
            if raw_msg.tool_calls:
                for raw_tc in raw_msg.tool_calls:
                    func = raw_tc.function
                    tool_calls.append(
                        ToolCall(
                            id=raw_tc.id,
                            name=func.name,
                            arguments=func.arguments,
                        )
                    )

            # Parse role
            try:
                role = ChatRole(raw_msg.role)
            except ValueError:
                role = ChatRole.ASSISTANT

            message = ChatMessage(
                role=role,
                content=raw_msg.content,
                tool_calls=tuple(tool_calls),
            )

            # Parse finish reason
            finish_reason = None
            if raw_choice.finish_reason:
                try:
                    from aios.ai.types import FinishReason

                    finish_reason = FinishReason(raw_choice.finish_reason)
                except ValueError:
                    pass

            from aios.ai.types import ChatChoice

            choices.append(
                ChatChoice(
                    index=raw_choice.index,
                    message=message,
                    finish_reason=finish_reason,
                )
            )

        # Parse usage
        usage = Usage()
        if raw.usage:
            usage = Usage(
                prompt_tokens=raw.usage.prompt_tokens,
                completion_tokens=raw.usage.completion_tokens,
                total_tokens=raw.usage.total_tokens,
                cached_tokens=getattr(raw.usage, "cached_tokens", 0) or 0,
            )

        return ChatResponse(
            id=raw.id,
            model=raw.model,
            choices=tuple(choices),
            usage=usage,
            created=raw.created,
            system_fingerprint=getattr(raw, "system_fingerprint", None),
        )
