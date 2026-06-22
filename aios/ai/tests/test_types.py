"""
PHOENIX AIOS — Tests for AI Integration Types

Tests all immutable data structures in the types module.
"""

from __future__ import annotations

import json
import time
import unittest
from dataclasses import FrozenInstanceError

from aios.ai.types import (
    ChatChoice,
    ChatConfig,
    ChatMessage,
    ChatResponse,
    ChatRole,
    ChatStreamChunk,
    FinishReason,
    ResponseFormat,
    StreamDelta,
    ToolCall,
    ToolCallDelta,
    ToolChoiceConfig,
    ToolChoiceMode,
    ToolResult,
    Usage,
)


class TestChatRole(unittest.TestCase):
    """Test ChatRole enum."""

    def test_values(self):
        assert ChatRole.SYSTEM.value == "system"
        assert ChatRole.DEVELOPER.value == "developer"
        assert ChatRole.USER.value == "user"
        assert ChatRole.ASSISTANT.value == "assistant"
        assert ChatRole.TOOL.value == "tool"

    def test_from_value(self):
        assert ChatRole("system") == ChatRole.SYSTEM
        assert ChatRole("user") == ChatRole.USER


class TestFinishReason(unittest.TestCase):
    """Test FinishReason enum."""

    def test_values(self):
        assert FinishReason.STOP.value == "stop"
        assert FinishReason.LENGTH.value == "length"
        assert FinishReason.TOOL_CALLS.value == "tool_calls"
        assert FinishReason.CONTENT_FILTER.value == "content_filter"


class TestToolCall(unittest.TestCase):
    """Test ToolCall immutable data structure."""

    def test_creation(self):
        tc = ToolCall(id="call_1", name="get_weather", arguments='{"city":"Tokyo"}')
        assert tc.id == "call_1"
        assert tc.name == "get_weather"
        assert tc.arguments == '{"city":"Tokyo"}'
        assert tc.type == "function"

    def test_immutability(self):
        tc = ToolCall(id="call_1", name="test", arguments="{}")
        with self.assertRaises(FrozenInstanceError):
            tc.id = "new_id"  # type: ignore

    def test_parsed_arguments(self):
        tc = ToolCall(id="call_1", name="test", arguments='{"a": 1, "b": "hello"}')
        parsed = tc.parsed_arguments
        assert parsed == {"a": 1, "b": "hello"}

    def test_parsed_arguments_invalid_json(self):
        tc = ToolCall(id="call_1", name="test", arguments="not json")
        parsed = tc.parsed_arguments
        assert parsed == {}

    def test_with_result(self):
        tc = ToolCall(id="call_1", name="test", arguments="{}")
        result = tc.with_result("hello")
        assert isinstance(result, ToolResult)
        assert result.tool_call_id == "call_1"
        assert result.name == "test"
        assert result.content == "hello"

    def test_with_result_dict(self):
        tc = ToolCall(id="call_1", name="test", arguments="{}")
        result = tc.with_result({"key": "value"})
        assert json.loads(result.content) == {"key": "value"}


class TestToolResult(unittest.TestCase):
    """Test ToolResult immutable data structure."""

    def test_creation(self):
        tr = ToolResult(tool_call_id="call_1", name="test", content="result")
        assert tr.tool_call_id == "call_1"
        assert tr.name == "test"
        assert tr.content == "result"
        assert tr.role == ChatRole.TOOL

    def test_immutability(self):
        tr = ToolResult(tool_call_id="call_1", name="test", content="result")
        with self.assertRaises(FrozenInstanceError):
            tr.content = "new"  # type: ignore


class TestUsage(unittest.TestCase):
    """Test Usage immutable data structure."""

    def test_defaults(self):
        u = Usage()
        assert u.prompt_tokens == 0
        assert u.completion_tokens == 0
        assert u.total_tokens == 0
        assert u.cached_tokens == 0

    def test_values(self):
        u = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert u.prompt_tokens == 100
        assert u.completion_tokens == 50
        assert u.total_tokens == 150

    def test_immutability(self):
        u = Usage()
        with self.assertRaises(FrozenInstanceError):
            u.prompt_tokens = 100  # type: ignore


class TestChatMessage(unittest.TestCase):
    """Test ChatMessage immutable data structure."""

    def test_system_message(self):
        msg = ChatMessage.system("You are helpful")
        assert msg.role == ChatRole.SYSTEM
        assert msg.content == "You are helpful"

    def test_developer_message(self):
        msg = ChatMessage.developer("Be concise")
        assert msg.role == ChatRole.DEVELOPER
        assert msg.content == "Be concise"

    def test_user_message(self):
        msg = ChatMessage.user("Hello")
        assert msg.role == ChatRole.USER
        assert msg.content == "Hello"
        assert msg.name is None

    def test_user_message_with_name(self):
        msg = ChatMessage.user("Hello", name="Alice")
        assert msg.name == "Alice"

    def test_assistant_message(self):
        msg = ChatMessage.assistant("Hi there")
        assert msg.role == ChatRole.ASSISTANT
        assert msg.content == "Hi there"

    def test_assistant_message_with_tool_calls(self):
        tc = ToolCall(id="call_1", name="test", arguments="{}")
        msg = ChatMessage.assistant(tool_calls=[tc])
        assert msg.role == ChatRole.ASSISTANT
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].id == "call_1"

    def test_tool_message(self):
        msg = ChatMessage.tool("call_1", "test", "result")
        assert msg.role == ChatRole.TOOL
        assert msg.tool_call_id == "call_1"
        assert msg.name == "test"
        assert msg.content == "result"

    def test_to_api_dict_system(self):
        msg = ChatMessage.system("Be helpful")
        d = msg.to_api_dict()
        assert d == {"role": "system", "content": "Be helpful"}

    def test_to_api_dict_user(self):
        msg = ChatMessage.user("Hello", name="Alice")
        d = msg.to_api_dict()
        assert d == {"role": "user", "content": "Hello", "name": "Alice"}

    def test_to_api_dict_assistant_with_tool_calls(self):
        tc = ToolCall(id="call_1", name="get_weather", arguments='{"city":"Tokyo"}')
        msg = ChatMessage.assistant(tool_calls=[tc])
        d = msg.to_api_dict()
        assert d["role"] == "assistant"
        assert "content" not in d  # content is omitted when None
        assert len(d["tool_calls"]) == 1
        assert d["tool_calls"][0]["id"] == "call_1"
        assert d["tool_calls"][0]["function"]["name"] == "get_weather"

    def test_to_api_dict_tool(self):
        msg = ChatMessage.tool("call_1", "test", "result")
        d = msg.to_api_dict()
        assert d == {"role": "tool", "content": "result", "tool_call_id": "call_1", "name": "test"}

    def test_immutability(self):
        msg = ChatMessage.user("Hello")
        with self.assertRaises(FrozenInstanceError):
            msg.content = "Changed"  # type: ignore


class TestChatResponse(unittest.TestCase):
    """Test ChatResponse immutable data structure."""

    def _make_response(self, content="Hello", has_tool_calls=False):
        tc = (ToolCall(id="call_1", name="test", arguments="{}"),) if has_tool_calls else ()
        msg = ChatMessage(role=ChatRole.ASSISTANT, content=content, tool_calls=tc)
        choice = ChatChoice(index=0, message=msg, finish_reason=FinishReason.STOP)
        return ChatResponse(
            id="resp_1",
            model="gpt-4o",
            choices=(choice,),
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    def test_content(self):
        resp = self._make_response("Hello world")
        assert resp.content == "Hello world"

    def test_first_choice(self):
        resp = self._make_response()
        assert resp.first_choice is not None
        assert resp.first_choice.index == 0

    def test_has_tool_calls_false(self):
        resp = self._make_response(has_tool_calls=False)
        assert resp.has_tool_calls is False
        assert resp.tool_calls == ()

    def test_has_tool_calls_true(self):
        resp = self._make_response(has_tool_calls=True)
        assert resp.has_tool_calls is True
        assert len(resp.tool_calls) == 1

    def test_finish_reason(self):
        resp = self._make_response()
        assert resp.finish_reason == FinishReason.STOP

    def test_empty_choices(self):
        resp = ChatResponse(id="resp_1", model="gpt-4o", choices=())
        assert resp.first_choice is None
        assert resp.content is None
        assert resp.has_tool_calls is False


class TestStreamDelta(unittest.TestCase):
    """Test StreamDelta immutable data structure."""

    def test_creation(self):
        delta = StreamDelta(role=ChatRole.ASSISTANT, content="Hello")
        assert delta.role == ChatRole.ASSISTANT
        assert delta.content == "Hello"
        assert delta.tool_calls == ()

    def test_immutability(self):
        delta = StreamDelta(content="Hello")
        with self.assertRaises(FrozenInstanceError):
            delta.content = "Changed"  # type: ignore


class TestChatStreamChunk(unittest.TestCase):
    """Test ChatStreamChunk immutable data structure."""

    def test_creation(self):
        delta = StreamDelta(content="Hello")
        chunk = ChatStreamChunk(id="chunk_1", model="gpt-4o", delta=delta)
        assert chunk.id == "chunk_1"
        assert chunk.model == "gpt-4o"
        assert chunk.delta.content == "Hello"
        assert chunk.finish_reason is None


class TestToolCallDelta(unittest.TestCase):
    """Test ToolCallDelta immutable data structure."""

    def test_creation(self):
        delta = ToolCallDelta(index=0, id="call_1", name="test", arguments='{"a":')
        assert delta.index == 0
        assert delta.id == "call_1"
        assert delta.name == "test"
        assert delta.arguments == '{"a":'

    def test_defaults(self):
        delta = ToolCallDelta(index=0)
        assert delta.id is None
        assert delta.name is None
        assert delta.arguments == ""


class TestChatConfig(unittest.TestCase):
    """Test ChatConfig immutable data structure."""

    def test_defaults(self):
        config = ChatConfig()
        assert config.model == "gpt-4o"
        assert config.temperature is None
        assert config.max_tokens is None

    def test_to_api_kwargs_minimal(self):
        config = ChatConfig(model="gpt-4o-mini")
        kwargs = config.to_api_kwargs()
        assert kwargs == {"model": "gpt-4o-mini"}

    def test_to_api_kwargs_full(self):
        config = ChatConfig(
            model="gpt-4o",
            temperature=0.7,
            top_p=0.9,
            max_tokens=1000,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            seed=42,
        )
        kwargs = config.to_api_kwargs()
        assert kwargs["model"] == "gpt-4o"
        assert kwargs["temperature"] == 0.7
        assert kwargs["top_p"] == 0.9
        assert kwargs["max_tokens"] == 1000
        assert kwargs["frequency_penalty"] == 0.5
        assert kwargs["presence_penalty"] == 0.3
        assert kwargs["seed"] == 42

    def test_to_api_kwargs_json_object(self):
        config = ChatConfig(response_format=ResponseFormat.JSON_OBJECT)
        kwargs = config.to_api_kwargs()
        assert kwargs["response_format"] == {"type": "json_object"}

    def test_to_api_kwargs_json_schema(self):
        schema = {"name": "test", "strict": True, "schema": {"type": "object"}}
        config = ChatConfig(
            response_format=ResponseFormat.JSON_SCHEMA,
            json_schema=schema,
        )
        kwargs = config.to_api_kwargs()
        assert kwargs["response_format"] == {"type": "json_schema", "json_schema": schema}


class TestToolChoiceConfig(unittest.TestCase):
    """Test ToolChoiceConfig immutable data structure."""

    def test_auto(self):
        tc = ToolChoiceConfig()
        assert tc.to_api_value() == "auto"

    def test_none(self):
        tc = ToolChoiceConfig(mode=ToolChoiceMode.NONE)
        assert tc.to_api_value() == "none"

    def test_required(self):
        tc = ToolChoiceConfig(mode=ToolChoiceMode.REQUIRED)
        assert tc.to_api_value() == "required"

    def test_specific_tool(self):
        tc = ToolChoiceConfig(
            mode=ToolChoiceMode.AUTO,  # mode is ignored when tool_name is set
            tool_name="get_weather",
        )
        val = tc.to_api_value()
        assert val["type"] == "function"
        assert val["function"]["name"] == "get_weather"


if __name__ == "__main__":
    unittest.main()
