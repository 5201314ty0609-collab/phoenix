"""
Streaming callback for PHOENIX AIOS LangChain integration.

Provides streaming support for LLM responses.
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional, TextIO

from ..core import Config, Logger
from .base import Callback, CallbackEvent, CallbackEventType


class StreamingCallback(Callback):
    """
    Streaming callback for LLM responses.

    Streams tokens as they are generated.

    Example:
        callback = StreamingCallback()
        callback.on_llm_start(event)
        callback.on_llm_token(event)  # Called for each token
        callback.on_llm_end(event)
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        output: Optional[TextIO] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ):
        self._config = config or Config()
        self._logger = Logger("StreamingCallback")
        self._output = output or sys.stdout
        self._on_token = on_token
        self._current_text: str = ""
        self._is_streaming: bool = False

    @property
    def current_text(self) -> str:
        """Get current streamed text."""
        return self._current_text

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming

    def on_chain_start(self, event: CallbackEvent) -> None:
        """Called when chain starts."""
        self._logger.debug(f"Chain started: {event.name}")

    def on_chain_end(self, event: CallbackEvent) -> None:
        """Called when chain ends."""
        self._logger.debug(f"Chain ended: {event.name}")

    def on_chain_error(self, event: CallbackEvent) -> None:
        """Called when chain errors."""
        self._logger.error(f"Chain error: {event.name}")

    def on_step_start(self, event: CallbackEvent) -> None:
        """Called when step starts."""
        self._logger.debug(f"Step started: {event.name}")

    def on_step_end(self, event: CallbackEvent) -> None:
        """Called when step ends."""
        self._logger.debug(f"Step ended: {event.name}")

    def on_step_error(self, event: CallbackEvent) -> None:
        """Called when step errors."""
        self._logger.error(f"Step error: {event.name}")

    def on_tool_start(self, event: CallbackEvent) -> None:
        """Called when tool starts."""
        self._logger.debug(f"Tool started: {event.name}")

    def on_tool_end(self, event: CallbackEvent) -> None:
        """Called when tool ends."""
        self._logger.debug(f"Tool ended: {event.name}")

    def on_tool_error(self, event: CallbackEvent) -> None:
        """Called when tool errors."""
        self._logger.error(f"Tool error: {event.name}")

    def on_llm_start(self, event: CallbackEvent) -> None:
        """Called when LLM starts."""
        self._current_text = ""
        self._is_streaming = True
        self._logger.debug(f"LLM started: {event.name}")

    def on_llm_end(self, event: CallbackEvent) -> None:
        """Called when LLM ends."""
        self._is_streaming = False
        self._logger.debug(f"LLM ended: {event.name}")

    def on_llm_error(self, event: CallbackEvent) -> None:
        """Called when LLM errors."""
        self._is_streaming = False
        self._logger.error(f"LLM error: {event.name}")

    def on_llm_token(self, event: CallbackEvent) -> None:
        """Called when LLM generates a token."""
        token = event.data
        if isinstance(token, str):
            self._current_text += token

            # Call custom handler
            if self._on_token:
                self._on_token(token)

            # Write to output
            self._output.write(token)
            self._output.flush()

    def reset(self) -> None:
        """Reset streaming state."""
        self._current_text = ""
        self._is_streaming = False


class StreamingHandler:
    """
    Handler for streaming responses.

    Provides a convenient way to handle streaming output.

    Example:
        handler = StreamingHandler()

        # Use with callback
        callback = StreamingCallback(on_token=handler.handle_token)

        # Get final result
        result = handler.get_result()
    """

    def __init__(self):
        self._tokens: List[str] = []
        self._current_text: str = ""
        self._is_complete: bool = False

    @property
    def tokens(self) -> List[str]:
        """Get all tokens."""
        return self._tokens.copy()

    @property
    def current_text(self) -> str:
        """Get current text."""
        return self._current_text

    @property
    def is_complete(self) -> bool:
        """Check if streaming is complete."""
        return self._is_complete

    def handle_token(self, token: str) -> None:
        """
        Handle a token.

        Args:
            token: Token text
        """
        self._tokens.append(token)
        self._current_text += token

    def complete(self) -> None:
        """Mark streaming as complete."""
        self._is_complete = True

    def get_result(self) -> str:
        """
        Get final result.

        Returns:
            Complete text
        """
        return self._current_text

    def reset(self) -> None:
        """Reset handler state."""
        self._tokens.clear()
        self._current_text = ""
        self._is_complete = False

    def __len__(self) -> int:
        """Get number of tokens."""
        return len(self._tokens)

    def __repr__(self) -> str:
        """String representation."""
        return f"StreamingHandler(tokens={len(self._tokens)}, complete={self._is_complete})"


class BufferedStreamingCallback(Callback):
    """
    Buffered streaming callback.

    Buffers tokens and emits them in chunks.

    Example:
        callback = BufferedStreamingCallback(buffer_size=10)
        # Tokens are buffered and emitted every 10 tokens
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        buffer_size: int = 10,
        on_buffer: Optional[Callable[[str], None]] = None,
    ):
        self._config = config or Config()
        self._logger = Logger("BufferedStreamingCallback")
        self._buffer_size = buffer_size
        self._on_buffer = on_buffer
        self._buffer: List[str] = []
        self._current_text: str = ""
        self._is_streaming: bool = False

    @property
    def current_text(self) -> str:
        """Get current text."""
        return self._current_text

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming

    def on_chain_start(self, event: CallbackEvent) -> None:
        pass

    def on_chain_end(self, event: CallbackEvent) -> None:
        pass

    def on_chain_error(self, event: CallbackEvent) -> None:
        pass

    def on_step_start(self, event: CallbackEvent) -> None:
        pass

    def on_step_end(self, event: CallbackEvent) -> None:
        pass

    def on_step_error(self, event: CallbackEvent) -> None:
        pass

    def on_tool_start(self, event: CallbackEvent) -> None:
        pass

    def on_tool_end(self, event: CallbackEvent) -> None:
        pass

    def on_tool_error(self, event: CallbackEvent) -> None:
        pass

    def on_llm_start(self, event: CallbackEvent) -> None:
        """Called when LLM starts."""
        self._buffer.clear()
        self._current_text = ""
        self._is_streaming = True

    def on_llm_end(self, event: CallbackEvent) -> None:
        """Called when LLM ends."""
        self._is_streaming = False
        self._flush_buffer()

    def on_llm_error(self, event: CallbackEvent) -> None:
        """Called when LLM errors."""
        self._is_streaming = False
        self._flush_buffer()

    def on_llm_token(self, event: CallbackEvent) -> None:
        """Called when LLM generates a token."""
        token = event.data
        if isinstance(token, str):
            self._buffer.append(token)
            self._current_text += token

            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to output."""
        if self._buffer:
            chunk = "".join(self._buffer)
            self._buffer.clear()

            if self._on_buffer:
                self._on_buffer(chunk)

    def reset(self) -> None:
        """Reset state."""
        self._buffer.clear()
        self._current_text = ""
        self._is_streaming = False


class CollectingStreamingCallback(Callback):
    """
    Collecting streaming callback.

    Collects all tokens without outputting them.

    Example:
        callback = CollectingStreamingCallback()
        # ... run chain ...
        result = callback.get_result()
    """

    def __init__(self, config: Optional[Config] = None):
        self._config = config or Config()
        self._logger = Logger("CollectingStreamingCallback")
        self._tokens: List[str] = []
        self._current_text: str = ""
        self._is_streaming: bool = False

    @property
    def tokens(self) -> List[str]:
        """Get all tokens."""
        return self._tokens.copy()

    @property
    def current_text(self) -> str:
        """Get current text."""
        return self._current_text

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming

    def on_chain_start(self, event: CallbackEvent) -> None:
        pass

    def on_chain_end(self, event: CallbackEvent) -> None:
        pass

    def on_chain_error(self, event: CallbackEvent) -> None:
        pass

    def on_step_start(self, event: CallbackEvent) -> None:
        pass

    def on_step_end(self, event: CallbackEvent) -> None:
        pass

    def on_step_error(self, event: CallbackEvent) -> None:
        pass

    def on_tool_start(self, event: CallbackEvent) -> None:
        pass

    def on_tool_end(self, event: CallbackEvent) -> None:
        pass

    def on_tool_error(self, event: CallbackEvent) -> None:
        pass

    def on_llm_start(self, event: CallbackEvent) -> None:
        """Called when LLM starts."""
        self._tokens.clear()
        self._current_text = ""
        self._is_streaming = True

    def on_llm_end(self, event: CallbackEvent) -> None:
        """Called when LLM ends."""
        self._is_streaming = False

    def on_llm_error(self, event: CallbackEvent) -> None:
        """Called when LLM errors."""
        self._is_streaming = False

    def on_llm_token(self, event: CallbackEvent) -> None:
        """Called when LLM generates a token."""
        token = event.data
        if isinstance(token, str):
            self._tokens.append(token)
            self._current_text += token

    def get_result(self) -> str:
        """Get complete result."""
        return self._current_text

    def reset(self) -> None:
        """Reset state."""
        self._tokens.clear()
        self._current_text = ""
        self._is_streaming = False
