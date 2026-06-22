"""
Tests for callbacks module.
"""

import unittest
from typing import Any, Dict, List

from ..callbacks import (
    Callback,
    CallbackEvent,
    CallbackEventType,
    CallbackManager,
    StreamingCallback,
    StreamingHandler,
    LoggingCallback,
    MetricsCallback,
)


class TestCallbackEvent(unittest.TestCase):
    """Test CallbackEvent."""

    def test_create(self):
        """Test creating event."""
        event = CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
            data={"key": "value"},
        )
        self.assertEqual(event.event_type, CallbackEventType.CHAIN_START)
        self.assertEqual(event.name, "test_chain")
        self.assertEqual(event.data, {"key": "value"})

    def test_with_data(self):
        """Test with_data."""
        event = CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
        )
        new_event = event.with_data({"new": "data"})
        self.assertEqual(new_event.data, {"new": "data"})

    def test_with_metadata(self):
        """Test with_metadata."""
        event = CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
        )
        new_event = event.with_metadata(key="value")
        self.assertEqual(new_event.metadata, {"key": "value"})


class TestCallbackManager(unittest.TestCase):
    """Test CallbackManager."""

    def test_add_callback(self):
        """Test adding callback."""
        manager = CallbackManager()
        callback = LoggingCallback()
        manager.add_callback(callback)
        self.assertEqual(len(manager), 1)

    def test_remove_callback(self):
        """Test removing callback."""
        manager = CallbackManager()
        callback = LoggingCallback()
        manager.add_callback(callback)
        manager.remove_callback(callback)
        self.assertEqual(len(manager), 0)

    def test_dispatch(self):
        """Test dispatching event."""
        events = []

        class TestCallback(Callback):
            def on_chain_start(self, event):
                events.append(event)

            def on_chain_end(self, event):
                pass

            def on_chain_error(self, event):
                pass

            def on_step_start(self, event):
                pass

            def on_step_end(self, event):
                pass

            def on_step_error(self, event):
                pass

            def on_tool_start(self, event):
                pass

            def on_tool_end(self, event):
                pass

            def on_tool_error(self, event):
                pass

            def on_llm_start(self, event):
                pass

            def on_llm_end(self, event):
                pass

            def on_llm_error(self, event):
                pass

            def on_llm_token(self, event):
                pass

        manager = CallbackManager()
        manager.add_callback(TestCallback())

        event = CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
        )
        manager.dispatch(event)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, "test_chain")


class TestStreamingCallback(unittest.TestCase):
    """Test StreamingCallback."""

    def test_streaming(self):
        """Test streaming."""
        tokens = []

        callback = StreamingCallback(on_token=lambda t: tokens.append(t))

        callback.on_llm_start(CallbackEvent(
            event_type=CallbackEventType.LLM_START,
            name="test_llm",
        ))

        callback.on_llm_token(CallbackEvent(
            event_type=CallbackEventType.LLM_TOKEN,
            name="test_llm",
            data="Hello",
        ))
        callback.on_llm_token(CallbackEvent(
            event_type=CallbackEventType.LLM_TOKEN,
            name="test_llm",
            data=" World",
        ))

        callback.on_llm_end(CallbackEvent(
            event_type=CallbackEventType.LLM_END,
            name="test_llm",
        ))

        self.assertEqual(tokens, ["Hello", " World"])
        self.assertEqual(callback.current_text, "Hello World")
        self.assertFalse(callback.is_streaming)


class TestStreamingHandler(unittest.TestCase):
    """Test StreamingHandler."""

    def test_handler(self):
        """Test handler."""
        handler = StreamingHandler()
        handler.handle_token("Hello")
        handler.handle_token(" World")
        handler.complete()

        self.assertEqual(handler.get_result(), "Hello World")
        self.assertTrue(handler.is_complete)
        self.assertEqual(len(handler), 2)


class TestMetricsCallback(unittest.TestCase):
    """Test MetricsCallback."""

    def test_metrics(self):
        """Test metrics collection."""
        callback = MetricsCallback()

        # Simulate chain execution
        callback.on_chain_start(CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
        ))
        callback.on_chain_end(CallbackEvent(
            event_type=CallbackEventType.CHAIN_END,
            name="test_chain",
        ))

        metrics = callback.get_metrics()
        self.assertEqual(metrics["counters"]["chain_starts"], 1)
        self.assertEqual(metrics["counters"]["chain_completions"], 1)

    def test_duration_stats(self):
        """Test duration stats."""
        callback = MetricsCallback()

        # Simulate chain execution
        callback.on_chain_start(CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test_chain",
        ))
        callback.on_chain_end(CallbackEvent(
            event_type=CallbackEventType.CHAIN_END,
            name="test_chain",
        ))

        stats = callback.get_duration_stats("chain")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["total"], 0)


if __name__ == "__main__":
    unittest.main()
