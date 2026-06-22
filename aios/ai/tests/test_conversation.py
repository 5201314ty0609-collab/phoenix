"""
PHOENIX AIOS — Tests for Conversation Manager

Tests Conversation and ConversationSummary.
"""

from __future__ import annotations

import json
import unittest

from aios.ai.conversation import Conversation, ConversationSummary, summarize_conversation
from aios.ai.types import ChatMessage, ChatRole, ToolCall


class TestConversation(unittest.TestCase):
    """Test Conversation."""

    def test_creation(self):
        conv = Conversation()
        assert conv.message_count == 0
        assert conv.system_prompt is None

    def test_with_system_prompt(self):
        conv = Conversation(system_prompt="You are helpful.")
        assert conv.system_prompt == "You are helpful."

    def test_add_user_message(self):
        conv = Conversation()
        conv.add_user_message("Hello")
        assert conv.message_count == 1
        assert conv.last_message.role == ChatRole.USER
        assert conv.last_message.content == "Hello"

    def test_add_assistant_message(self):
        conv = Conversation()
        conv.add_assistant_message("Hi there")
        assert conv.message_count == 1
        assert conv.last_message.role == ChatRole.ASSISTANT
        assert conv.last_message.content == "Hi there"

    def test_add_assistant_message_with_tool_calls(self):
        conv = Conversation()
        tc = ToolCall(id="call_1", name="test", arguments="{}")
        conv.add_assistant_message(tool_calls=[tc])
        assert conv.last_message.tool_calls == (tc,)

    def test_add_tool_result(self):
        conv = Conversation()
        conv.add_tool_result("call_1", "test", "result data")
        assert conv.last_message.role == ChatRole.TOOL
        assert conv.last_message.tool_call_id == "call_1"

    def test_user_messages(self):
        conv = Conversation()
        conv.add_user_message("Q1")
        conv.add_assistant_message("A1")
        conv.add_user_message("Q2")
        assert len(conv.user_messages) == 2

    def test_assistant_messages(self):
        conv = Conversation()
        conv.add_user_message("Q1")
        conv.add_assistant_message("A1")
        assert len(conv.assistant_messages) == 1

    def test_last_user_message(self):
        conv = Conversation()
        conv.add_user_message("Q1")
        conv.add_assistant_message("A1")
        conv.add_user_message("Q2")
        assert conv.last_user_message.content == "Q2"

    def test_last_assistant_message(self):
        conv = Conversation()
        conv.add_user_message("Q1")
        conv.add_assistant_message("A1")
        assert conv.last_assistant_message.content == "A1"

    def test_last_message_none(self):
        conv = Conversation()
        assert conv.last_message is None

    def test_get_history_with_system(self):
        conv = Conversation(system_prompt="Be helpful")
        conv.add_user_message("Hello")
        history = conv.get_history(include_system=True)
        assert len(history) == 2
        assert history[0].role == ChatRole.SYSTEM
        assert history[1].role == ChatRole.USER

    def test_get_history_without_system(self):
        conv = Conversation(system_prompt="Be helpful")
        conv.add_user_message("Hello")
        history = conv.get_history(include_system=False)
        assert len(history) == 1
        assert history[0].role == ChatRole.USER

    def test_to_api_messages(self):
        conv = Conversation(system_prompt="Be helpful")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")
        messages = conv.to_api_messages()
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_auto_trim(self):
        conv = Conversation(max_messages=3)
        for i in range(5):
            conv.add_user_message(f"msg {i}")
        assert conv.message_count == 3
        assert conv.last_message.content == "msg 4"

    def test_manual_trim(self):
        conv = Conversation()
        for i in range(10):
            conv.add_user_message(f"msg {i}")
        removed = conv.trim(keep_last=3)
        assert removed == 7
        assert conv.message_count == 3

    def test_clear(self):
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        conv.clear()
        assert conv.message_count == 0

    def test_export_import_dict(self):
        conv = Conversation(system_prompt="Be helpful")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")
        conv.add_tool_result("call_1", "test", "result")

        data = conv.to_dict()
        restored = Conversation.from_dict(data)

        assert restored.system_prompt == "Be helpful"
        assert restored.message_count == 3
        assert restored.messages[0].role == ChatRole.USER
        assert restored.messages[1].role == ChatRole.ASSISTANT
        assert restored.messages[2].role == ChatRole.TOOL

    def test_export_import_json(self):
        conv = Conversation(system_prompt="Be helpful")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")

        json_str = conv.export_json()
        restored = Conversation.import_json(json_str)

        assert restored.system_prompt == "Be helpful"
        assert restored.message_count == 2

    def test_add_response(self):
        from aios.ai.types import ChatChoice, ChatResponse, FinishReason, Usage

        msg = ChatMessage(role=ChatRole.ASSISTANT, content="Hello!")
        choice = ChatChoice(index=0, message=msg, finish_reason=FinishReason.STOP)
        response = ChatResponse(
            id="resp_1",
            model="gpt-4o",
            choices=(choice,),
            usage=Usage(),
        )

        conv = Conversation()
        conv.add_user_message("Hi")
        conv.add_response(response)
        assert conv.message_count == 2
        assert conv.last_assistant_message.content == "Hello!"


class TestConversationSummary(unittest.TestCase):
    """Test ConversationSummary and summarize_conversation."""

    def test_summarize(self):
        conv = Conversation()
        conv.add_user_message("Q1")
        conv.add_assistant_message("A1")
        conv.add_user_message("Q2")
        conv.add_assistant_message("A2")
        conv.add_tool_result("call_1", "test", "result")

        summary = summarize_conversation(conv)
        assert summary.id == conv.id
        assert summary.message_count == 5
        assert summary.user_message_count == 2
        assert summary.assistant_message_count == 2
        assert summary.tool_message_count == 1


if __name__ == "__main__":
    unittest.main()
