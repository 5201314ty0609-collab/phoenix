"""
PHOENIX AIOS — Tests for Streaming Handler

Tests StreamHandler and StreamCollector with mock chunks.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, List, Optional

from aios.ai.streaming.handler import StreamCollector, StreamHandler, _ToolCallBuilder
from aios.ai.types import (
    ChatRole,
    ChatStreamChunk,
    FinishReason,
    StreamDelta,
    ToolCallDelta,
)


# ---------------------------------------------------------------------------
# Mock Objects
# ---------------------------------------------------------------------------


@dataclass
class MockRawChoice:
    index: int = 0
    delta: Any = None
    finish_reason: Optional[str] = None


@dataclass
class MockRawDelta:
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None


@dataclass
class MockRawToolCall:
    index: int = 0
    id: Optional[str] = None
    function: Any = None


@dataclass
class MockRawFunction:
    name: Optional[str] = None
    arguments: str = ""


@dataclass
class MockRawChunk:
    id: str = "chatcmpl-test"
    model: str = "gpt-4o"
    created: float = 1000.0
    choices: Optional[List[Any]] = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStreamHandlerParseChunk(unittest.TestCase):
    """Test StreamHandler._parse_raw_chunk."""

    def setUp(self):
        self.handler = StreamHandler()

    def test_parse_content_chunk(self):
        raw = MockRawChunk(
            choices=[
                MockRawChoice(
                    delta=MockRawDelta(content="Hello"),
                    finish_reason=None,
                )
            ]
        )
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is not None
        assert chunk.delta.content == "Hello"
        assert chunk.id == "chatcmpl-test"
        assert chunk.model == "gpt-4o"

    def test_parse_role_chunk(self):
        raw = MockRawChunk(
            choices=[
                MockRawChoice(delta=MockRawDelta(role="assistant"))
            ]
        )
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is not None
        assert chunk.delta.role == ChatRole.ASSISTANT

    def test_parse_finish_chunk(self):
        raw = MockRawChunk(
            choices=[
                MockRawChoice(
                    delta=MockRawDelta(),
                    finish_reason="stop",
                )
            ]
        )
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is not None
        assert chunk.finish_reason == FinishReason.STOP

    def test_parse_tool_call_chunk(self):
        raw = MockRawChunk(
            choices=[
                MockRawChoice(
                    delta=MockRawDelta(
                        tool_calls=[
                            MockRawToolCall(
                                index=0,
                                id="call_123",
                                function=MockRawFunction(
                                    name="get_weather",
                                    arguments='{"city":',
                                ),
                            )
                        ]
                    )
                )
            ]
        )
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is not None
        assert len(chunk.delta.tool_calls) == 1
        assert chunk.delta.tool_calls[0].id == "call_123"
        assert chunk.delta.tool_calls[0].name == "get_weather"
        assert chunk.delta.tool_calls[0].arguments == '{"city":'

    def test_parse_no_choices(self):
        raw = MockRawChunk(choices=None)
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is None

    def test_parse_empty_choices(self):
        raw = MockRawChunk(choices=[])
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is None

    def test_parse_no_delta(self):
        raw = MockRawChunk(choices=[MockRawChoice(delta=None)])
        chunk = self.handler._parse_raw_chunk(raw)
        assert chunk is None


class TestStreamHandlerIterStream(unittest.TestCase):
    """Test StreamHandler.iter_stream."""

    def test_iter_content_chunks(self):
        handler = StreamHandler()

        chunks = [
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="Hello "))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="world!"))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(), finish_reason="stop")]),
        ]

        results = list(handler.iter_stream(chunks))
        assert len(results) == 3
        assert results[0].delta.content == "Hello "
        assert results[1].delta.content == "world!"
        assert results[2].finish_reason == FinishReason.STOP

    def test_iter_content_text(self):
        handler = StreamHandler()

        chunks = [
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="Hello "))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="world!"))]),
        ]

        text_parts = list(handler.iter_content(chunks))
        assert text_parts == ["Hello ", "world!"]

    def test_iter_skips_none_chunks(self):
        handler = StreamHandler()

        chunks = [
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="Hello"))]),
            MockRawChunk(choices=None),  # Should be skipped
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content=" world"))]),
        ]

        text_parts = list(handler.iter_content(chunks))
        assert text_parts == ["Hello", " world"]


class TestStreamHandlerCallbacks(unittest.TestCase):
    """Test StreamHandler callbacks."""

    def test_on_content_callback(self):
        received: List[str] = []
        handler = StreamHandler(on_content=lambda t: received.append(t))

        chunks = [
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="Hello "))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="world!"))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(), finish_reason="stop")]),
        ]

        handler.process_stream(chunks)
        assert received == ["Hello ", "world!"]

    def test_on_complete_callback(self):
        completed = []
        handler = StreamHandler(on_complete=lambda r: completed.append(r))

        chunks = [
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="Hi"))]),
            MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(), finish_reason="stop")]),
        ]

        handler.process_stream(chunks)
        assert len(completed) == 1
        assert completed[0].content == "Hi"

    def test_on_error_callback(self):
        errors = []

        def on_error(e):
            errors.append(e)

        handler = StreamHandler(on_error=on_error)

        def bad_stream():
            yield MockRawChunk(choices=[MockRawChoice(delta=MockRawDelta(content="ok"))])
            raise ValueError("stream error")

        with self.assertRaises(ValueError):
            handler.process_stream(bad_stream())

        assert len(errors) == 1
        assert str(errors[0]) == "stream error"


class TestStreamCollector(unittest.TestCase):
    """Test StreamCollector."""

    def test_collect_content(self):
        collector = StreamCollector()

        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(role=ChatRole.ASSISTANT, content="Hello "),
        ))
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(content="world!"),
        ))
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(),
            finish_reason=FinishReason.STOP,
        ))

        response = collector.build_response()
        assert response.content == "Hello world!"
        assert response.id == "c1"
        assert response.model == "gpt-4o"
        assert response.finish_reason == FinishReason.STOP

    def test_collect_tool_calls(self):
        collector = StreamCollector()

        # First chunk: tool call start
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(
                tool_calls=(ToolCallDelta(index=0, id="call_1", name="get_weather"),),
            ),
        ))

        # Argument fragments
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(
                tool_calls=(ToolCallDelta(index=0, arguments='{"city":'),),
            ),
        ))
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(
                tool_calls=(ToolCallDelta(index=0, arguments='"Tokyo"}'),),
            ),
        ))

        # Finish
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(),
            finish_reason=FinishReason.TOOL_CALLS,
        ))

        response = collector.build_response()
        assert response.has_tool_calls
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "call_1"
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == '{"city":"Tokyo"}'

    def test_collect_multiple_tool_calls(self):
        collector = StreamCollector()

        # Tool call 1
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(
                tool_calls=(
                    ToolCallDelta(index=0, id="call_1", name="get_weather", arguments='{"city":"Tokyo"}'),
                ),
            ),
        ))

        # Tool call 2
        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(
                tool_calls=(
                    ToolCallDelta(index=1, id="call_2", name="get_time", arguments="{}"),
                ),
            ),
        ))

        collector.add_chunk(ChatStreamChunk(
            id="c1", model="gpt-4o",
            delta=StreamDelta(),
            finish_reason=FinishReason.TOOL_CALLS,
        ))

        response = collector.build_response()
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[1].name == "get_time"


class TestToolCallBuilder(unittest.TestCase):
    """Test _ToolCallBuilder."""

    def test_build_simple(self):
        builder = _ToolCallBuilder()
        builder.add_delta(ToolCallDelta(index=0, id="call_1", name="test", arguments="{}"))
        tc = builder.build()
        assert tc is not None
        assert tc.id == "call_1"
        assert tc.name == "test"
        assert tc.arguments == "{}"

    def test_build_fragmented(self):
        builder = _ToolCallBuilder()
        builder.add_delta(ToolCallDelta(index=0, id="call_1", name="get_weather"))
        builder.add_delta(ToolCallDelta(index=0, arguments='{"city":'))
        builder.add_delta(ToolCallDelta(index=0, arguments='"Tokyo"}'))
        tc = builder.build()
        assert tc is not None
        assert tc.name == "get_weather"
        assert tc.arguments == '{"city":"Tokyo"}'

    def test_build_no_id(self):
        builder = _ToolCallBuilder()
        builder.add_delta(ToolCallDelta(index=0, name="test"))
        tc = builder.build()
        assert tc is None

    def test_build_no_name(self):
        builder = _ToolCallBuilder()
        builder.add_delta(ToolCallDelta(index=0, id="call_1"))
        tc = builder.build()
        assert tc is None


if __name__ == "__main__":
    unittest.main()
