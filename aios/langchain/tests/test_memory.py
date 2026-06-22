"""
Tests for memory module.
"""

import unittest
from typing import Any, Dict, List

from ..memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory,
    VectorStoreRetrieverMemory,
)


class TestConversationBufferMemory(unittest.TestCase):
    """Test ConversationBufferMemory."""

    def test_add_messages(self):
        """Test adding messages."""
        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        messages = memory.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")
        self.assertEqual(messages[1]["role"], "ai")
        self.assertEqual(messages[1]["content"], "Hi there!")

    def test_max_messages(self):
        """Test max messages limit."""
        memory = ConversationBufferMemory(max_messages=3)
        memory.add_user_message("Message 1")
        memory.add_ai_message("Response 1")
        memory.add_user_message("Message 2")
        memory.add_ai_message("Response 2")
        memory.add_user_message("Message 3")

        messages = memory.get_messages()
        self.assertEqual(len(messages), 3)

    def test_clear(self):
        """Test clearing messages."""
        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi!")
        memory.clear()

        messages = memory.get_messages()
        self.assertEqual(len(messages), 0)

    def test_get_context_string(self):
        """Test getting context string."""
        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        context = memory.get_context_string()
        self.assertIn("Human: Hello", context)
        self.assertIn("AI: Hi there!", context)

    def test_save_context(self):
        """Test saving context."""
        memory = ConversationBufferMemory()
        memory.save_context(
            inputs={"input": "Hello"},
            outputs={"output": "Hi there!"},
        )

        messages = memory.get_messages()
        self.assertEqual(len(messages), 2)


class TestConversationSummaryMemory(unittest.TestCase):
    """Test ConversationSummaryMemory."""

    def test_add_messages(self):
        """Test adding messages."""
        memory = ConversationSummaryMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        messages = memory.get_messages()
        self.assertEqual(len(messages), 2)

    def test_summary(self):
        """Test summary."""
        def summarizer(messages, current_summary):
            return "Test summary"

        memory = ConversationSummaryMemory(
            summarizer=summarizer,
            max_messages_before_summary=2,
        )
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        summary = memory.get_summary()
        self.assertEqual(summary, "Test summary")

    def test_force_summarize(self):
        """Test force summarize."""
        def summarizer(messages, current_summary):
            return "Forced summary"

        memory = ConversationSummaryMemory(summarizer=summarizer)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        summary = memory.force_summarize()
        self.assertEqual(summary, "Forced summary")


class TestConversationBufferWindowMemory(unittest.TestCase):
    """Test ConversationBufferWindowMemory."""

    def test_window_size(self):
        """Test window size."""
        memory = ConversationBufferWindowMemory(window_size=3)
        memory.add_user_message("Message 1")
        memory.add_ai_message("Response 1")
        memory.add_user_message("Message 2")
        memory.add_ai_message("Response 2")
        memory.add_user_message("Message 3")

        messages = memory.get_messages()
        self.assertEqual(len(messages), 3)

    def test_set_window_size(self):
        """Test setting window size."""
        memory = ConversationBufferWindowMemory(window_size=5)
        memory.add_user_message("Message 1")
        memory.add_ai_message("Response 1")
        memory.add_user_message("Message 2")

        memory.set_window_size(2)
        messages = memory.get_messages()
        self.assertEqual(len(messages), 2)


class TestVectorStoreRetrieverMemory(unittest.TestCase):
    """Test VectorStoreRetrieverMemory."""

    def test_add_messages(self):
        """Test adding messages."""
        def embedder(text):
            return [0.1] * 768

        memory = VectorStoreRetrieverMemory(embedder=embedder)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        messages = memory.get_messages()
        self.assertEqual(len(messages), 2)

    def test_search(self):
        """Test searching."""
        def embedder(text):
            return [0.1] * 768

        memory = VectorStoreRetrieverMemory(embedder=embedder)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        results = memory.search("Hello")
        self.assertGreater(len(results), 0)

    def test_no_embedder(self):
        """Test without embedder."""
        memory = VectorStoreRetrieverMemory()
        memory.add_user_message("Hello")

        results = memory.search("Hello")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
