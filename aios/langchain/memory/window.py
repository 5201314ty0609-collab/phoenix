"""
Conversation buffer window memory implementation.

Stores only the last K messages.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional

from ..core import Config, Logger
from .base import Memory, MemoryType


class ConversationBufferWindowMemory(Memory):
    """
    Conversation buffer window memory that stores last K messages.

    Maintains a sliding window of the most recent messages.

    Example:
        memory = ConversationBufferWindowMemory(window_size=5)
        memory.add_user_message("Message 1")
        memory.add_ai_message("Response 1")
        # ... more messages ...

        # Only last 5 messages are kept
        messages = memory.get_messages()
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        window_size: int = 10,
    ):
        super().__init__(config)
        self._window_size = window_size
        self._messages: deque = deque(maxlen=window_size)
        self._logger = Logger("ConversationBufferWindowMemory")

    @property
    def memory_type(self) -> MemoryType:
        """Get memory type."""
        return MemoryType.WINDOW

    @property
    def window_size(self) -> int:
        """Get window size."""
        return self._window_size

    @property
    def messages(self) -> List[Dict[str, str]]:
        """Get all messages in window."""
        return list(self._messages)

    def add_user_message(self, message: str) -> None:
        """
        Add a user message.

        Args:
            message: User message
        """
        self._messages.append({"role": "user", "content": message})
        self._logger.debug(f"Added user message: {message[:50]}...")

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message.

        Args:
            message: AI message
        """
        self._messages.append({"role": "ai", "content": message})
        self._logger.debug(f"Added AI message: {message[:50]}...")

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get messages in window.

        Returns:
            List of message dicts
        """
        return list(self._messages)

    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """
        Get last N messages.

        Args:
            n: Number of messages

        Returns:
            List of last N messages
        """
        return list(self._messages)[-n:]

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._logger.debug("Cleared all messages")

    def set_window_size(self, size: int) -> None:
        """
        Set window size.

        Args:
            size: New window size
        """
        self._window_size = size
        self._messages = deque(self._messages, maxlen=size)
        self._logger.debug(f"Set window size: {size}")

    def get_context_string(self, max_messages: Optional[int] = None) -> str:
        """
        Get conversation context as string.

        Args:
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation string
        """
        messages = list(self._messages)
        if max_messages:
            messages = messages[-max_messages:]

        lines = []
        for msg in messages:
            role = "Human" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)

    def invoke(self, input_data: Dict[str, Any]) -> Any:
        """
        Execute memory operation.

        Args:
            input_data: Input data

        Returns:
            ExecutionResult
        """
        action = input_data.get("action", "get_messages")

        if action == "get_context":
            max_messages = input_data.get("max_messages")
            context = self.get_context_string(max_messages)
            from ..core import ExecutionResult
            return ExecutionResult.success_result(data=context)

        if action == "set_window_size":
            from ..core import ExecutionResult
            self.set_window_size(input_data["size"])
            return ExecutionResult.success_result(data=None)

        return super().invoke(input_data)

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """
        Save context from interaction.

        Args:
            inputs: Input data
            outputs: Output data
        """
        user_message = inputs.get("input", "")
        ai_message = outputs.get("output", "")

        if user_message:
            self.add_user_message(user_message)
        if ai_message:
            self.add_ai_message(ai_message)

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables.

        Args:
            inputs: Input data

        Returns:
            Dict with 'history' key
        """
        return {
            "history": self.get_context_string(),
            "messages": self.get_messages(),
        }

    def __len__(self) -> int:
        """Get number of messages in window."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConversationBufferWindowMemory("
            f"messages={len(self._messages)}, "
            f"window_size={self._window_size})"
        )


def window_memory(
    window_size: int = 10,
    config: Optional[Config] = None,
) -> ConversationBufferWindowMemory:
    """
    Create a conversation buffer window memory.

    Args:
        window_size: Number of messages to keep
        config: Configuration

    Returns:
        ConversationBufferWindowMemory

    Example:
        memory = window_memory(window_size=5)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi!")
    """
    return ConversationBufferWindowMemory(
        config=config,
        window_size=window_size,
    )
