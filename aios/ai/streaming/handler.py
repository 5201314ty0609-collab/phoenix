"""
PHOENIX AIOS — Streaming Response Handler

Implements processing of OpenAI SSE streaming responses.

Key responsibilities:
1. Parse raw SSE chunks into ChatStreamChunk objects
2. Accumulate content deltas into a complete response
3. Assemble tool call fragments from multiple chunks
4. Provide callback-based and iterator-based consumption
5. Handle errors gracefully during streaming

Architecture:
    OpenAI SSE Stream
         │
         ▼
    StreamHandler.parse_chunk()  → ChatStreamChunk
         │
         ├── on_content(delta)   → incremental text callback
         ├── on_tool_call(delta) → incremental tool call callback
         └── on_complete()       → assembled ChatResponse callback
         │
         ▼
    StreamCollector (accumulates full response)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
)

from aios.ai.types import (
    ChatChoice,
    ChatMessage,
    ChatResponse,
    ChatRole,
    ChatStreamChunk,
    FinishReason,
    StreamDelta,
    ToolCall,
    ToolCallDelta,
    Usage,
)


# ---------------------------------------------------------------------------
# Stream Handler
# ---------------------------------------------------------------------------


class StreamHandler:
    """
    Processes OpenAI streaming responses.

    Provides both callback-based and iterator-based interfaces
    for consuming streaming data.

    Callbacks:
        on_content: Called with each content delta (text chunk)
        on_tool_call: Called with each tool call delta
        on_complete: Called when streaming finishes with full response
        on_error: Called on streaming errors

    Usage (callback):
        handler = StreamHandler(
            on_content=lambda text: print(text, end=""),
            on_complete=lambda resp: print(f"\\nDone! {resp.usage.total_tokens} tokens"),
        )
        handler.process_stream(api_stream)

    Usage (iterator):
        handler = StreamHandler()
        for chunk in handler.iter_stream(api_stream):
            print(chunk.delta.content, end="")
    """

    def __init__(
        self,
        on_content: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[ToolCallDelta], None]] = None,
        on_complete: Optional[Callable[[ChatResponse], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        self._on_content = on_content
        self._on_tool_call = on_tool_call
        self._on_complete = on_complete
        self._on_error = on_error

    def process_stream(self, stream: Any) -> ChatResponse:
        """
        Process an entire streaming response.

        Args:
            stream: OpenAI streaming response object

        Returns:
            Complete ChatResponse assembled from chunks
        """
        collector = StreamCollector()

        try:
            for raw_chunk in stream:
                chunk = self._parse_raw_chunk(raw_chunk)
                if chunk is None:
                    continue

                collector.add_chunk(chunk)

                # Fire content callback
                if chunk.delta.content and self._on_content:
                    self._on_content(chunk.delta.content)

                # Fire tool call callbacks
                for tc_delta in chunk.delta.tool_calls:
                    if self._on_tool_call:
                        self._on_tool_call(tc_delta)

        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

        response = collector.build_response()

        if self._on_complete:
            self._on_complete(response)

        return response

    def iter_stream(self, stream: Any) -> Iterator[ChatStreamChunk]:
        """
        Iterate over streaming chunks.

        Args:
            stream: OpenAI streaming response object

        Yields:
            ChatStreamChunk for each SSE event
        """
        try:
            for raw_chunk in stream:
                chunk = self._parse_raw_chunk(raw_chunk)
                if chunk is not None:
                    yield chunk
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise

    def iter_content(self, stream: Any) -> Iterator[str]:
        """
        Iterate over content deltas only.

        Args:
            stream: OpenAI streaming response object

        Yields:
            Text content strings
        """
        for chunk in self.iter_stream(stream):
            if chunk.delta.content:
                yield chunk.delta.content

    def _parse_raw_chunk(self, raw_chunk: Any) -> Optional[ChatStreamChunk]:
        """
        Parse a raw OpenAI chunk into a ChatStreamChunk.

        Args:
            raw_chunk: Raw chunk from the OpenAI SDK

        Returns:
            ChatStreamChunk or None if chunk should be skipped
        """
        try:
            # Extract basic fields
            chunk_id = getattr(raw_chunk, "id", "") or ""
            model = getattr(raw_chunk, "model", "") or ""
            created = getattr(raw_chunk, "created", None) or time.time()

            choices = getattr(raw_chunk, "choices", None)
            if not choices:
                # Might be a usage-only chunk at the end
                return None

            choice = choices[0]
            delta_raw = getattr(choice, "delta", None)
            if delta_raw is None:
                return None

            # Parse delta
            role = None
            role_raw = getattr(delta_raw, "role", None)
            if role_raw:
                try:
                    role = ChatRole(role_raw)
                except ValueError:
                    pass

            content = getattr(delta_raw, "content", None)

            # Parse tool call deltas
            tool_call_deltas: List[ToolCallDelta] = []
            raw_tool_calls = getattr(delta_raw, "tool_calls", None)
            if raw_tool_calls:
                for raw_tc in raw_tool_calls:
                    func = getattr(raw_tc, "function", None)
                    tool_call_deltas.append(
                        ToolCallDelta(
                            index=getattr(raw_tc, "index", 0),
                            id=getattr(raw_tc, "id", None),
                            name=getattr(func, "name", None) if func else None,
                            arguments=getattr(func, "arguments", "") if func else "",
                        )
                    )

            # Parse finish reason
            finish_reason = None
            raw_finish = getattr(choice, "finish_reason", None)
            if raw_finish:
                try:
                    finish_reason = FinishReason(raw_finish)
                except ValueError:
                    pass

            return ChatStreamChunk(
                id=chunk_id,
                model=model,
                delta=StreamDelta(
                    role=role,
                    content=content,
                    tool_calls=tuple(tool_call_deltas),
                ),
                finish_reason=finish_reason,
                index=getattr(choice, "index", 0),
                created=created,
            )

        except Exception:
            # Skip unparseable chunks
            return None


# ---------------------------------------------------------------------------
# Stream Collector (Accumulates Full Response)
# ---------------------------------------------------------------------------


class StreamCollector:
    """
    Accumulates streaming chunks into a complete ChatResponse.

    Handles:
    - Content text concatenation
    - Tool call fragment assembly (by index)
    - Usage tracking (if stream_options includes usage)
    """

    def __init__(self) -> None:
        self._id: str = ""
        self._model: str = ""
        self._created: float = time.time()
        self._content_parts: List[str] = []
        self._tool_call_fragments: Dict[int, _ToolCallBuilder] = {}
        self._finish_reason: Optional[FinishReason] = None
        self._usage: Optional[Usage] = None

    def add_chunk(self, chunk: ChatStreamChunk) -> None:
        """
        Add a streaming chunk to the accumulator.

        Args:
            chunk: Parsed streaming chunk
        """
        if not self._id:
            self._id = chunk.id
        if not self._model:
            self._model = chunk.model
        if chunk.created:
            self._created = chunk.created

        # Accumulate content
        if chunk.delta.content:
            self._content_parts.append(chunk.delta.content)

        # Accumulate tool calls
        for tc_delta in chunk.delta.tool_calls:
            if tc_delta.index not in self._tool_call_fragments:
                self._tool_call_fragments[tc_delta.index] = _ToolCallBuilder()
            builder = self._tool_call_fragments[tc_delta.index]
            builder.add_delta(tc_delta)

        # Track finish reason
        if chunk.finish_reason:
            self._finish_reason = chunk.finish_reason

    def build_response(self) -> ChatResponse:
        """
        Build the complete ChatResponse from accumulated chunks.

        Returns:
            ChatResponse with assembled content and tool calls
        """
        # Assemble content
        content = "".join(self._content_parts) if self._content_parts else None

        # Assemble tool calls
        tool_calls: List[ToolCall] = []
        for index in sorted(self._tool_call_fragments.keys()):
            builder = self._tool_call_fragments[index]
            tc = builder.build()
            if tc:
                tool_calls.append(tc)

        # Build message
        message = ChatMessage(
            role=ChatRole.ASSISTANT,
            content=content,
            tool_calls=tuple(tool_calls) if tool_calls else (),
        )

        # Build choice
        choice = ChatChoice(
            index=0,
            message=message,
            finish_reason=self._finish_reason,
        )

        return ChatResponse(
            id=self._id,
            model=self._model,
            choices=(choice,),
            usage=self._usage or Usage(),
            created=self._created,
        )


@dataclass
class _ToolCallBuilder:
    """Accumulates tool call fragments from streaming chunks."""

    _id: Optional[str] = None
    _name_parts: List[str] = field(default_factory=list)
    _argument_parts: List[str] = field(default_factory=list)

    def add_delta(self, delta: ToolCallDelta) -> None:
        """Add a tool call delta fragment."""
        if delta.id:
            self._id = delta.id
        if delta.name:
            self._name_parts.append(delta.name)
        if delta.arguments:
            self._argument_parts.append(delta.arguments)

    def build(self) -> Optional[ToolCall]:
        """Build the complete ToolCall."""
        if not self._id:
            return None

        name = "".join(self._name_parts)
        arguments = "".join(self._argument_parts)

        if not name:
            return None

        return ToolCall(
            id=self._id,
            name=name,
            arguments=arguments,
        )
