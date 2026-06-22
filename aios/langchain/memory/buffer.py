"""
Conversation buffer memory implementation.

Stores all messages in a simple buffer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core import Config, Logger
from .base import Memory, MemoryType


class ConversationBufferMemory(Memory):
    """
    Conversation buffer memory that stores all messages.

    Stores all user and AI messages in order.

    Example:
        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")
        memory.add_user_message("How are you?")
        memory.add_ai_message("I'm doing well!")

        messages = memory.get_messages()
        # [
        #     {"role": "user", "content": "Hello"},
        #     {"role": "ai", "content": "Hi there!"},
        #     {"role": "user", "content": "How are you?"},
        #     {"role": "ai", "content": "I'm doing well!"},
        # ]
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        max_messages: Optional[int] = None,
    ):
        super().__init__(config)
        self._messages: List[Dict[str, str]] = []
        self._max_messages = max_messages
        self._logger = Logger("ConversationBufferMemory")

    @property
    def memory_type(self) -> MemoryType:
        """Get memory type."""
        return MemoryType.BUFFER

    @property
    def messages(self) -> List[Dict[str, str]]:
        """Get all messages."""
        return self._messages.copy()

    def add_user_message(self, message: str) -> None:
        """
        Add a user message.

        Args:
            message: User message
        """
        self._messages.append({"role": "user", "content": message})
        self._trim_messages()
        self._logger.debug(f"Added user message: {message[:50]}...")

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message.

        Args:
            message: AI message
        """
        self._messages.append({"role": "ai", "content": message})
        self._trim_messages()
        self._logger.debug(f"Added AI message: {message[:50]}...")

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages.

        Returns:
            List of message dicts
        """
        return self._messages.copy()

    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]:
        """
        Get last N messages.

        Args:
            n: Number of messages

        Returns:
            List of last N messages
        """
        return self._messages[-n:].copy()

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._logger.debug("Cleared all messages")

    def _trim_messages(self) -> None:
        """Trim messages to max size."""
        if self._max_messages and len(self._messages) > self._max_messages:
            excess = len(self._messages) - self._max_messages
            self._messages = self._messages[excess:]
            self._logger.debug(f"Trimmed {excess} messages")

    def get_context_string(self, max_messages: Optional[int] = None) -> str:
        """
        Get conversation context as string.

        Args:
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation string
        """
        messages = self._messages
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

        return super().invoke(input_data)

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """
        Save context from interaction.

        Args:
            inputs: Input data
            outputs: Output data
        """
        # Extract messages
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
        """Get number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConversationBufferMemory("
            f"messages={len(self._messages)}, "
            f"max_messages={self._max_messages})"
        )


def buffer_memory(
    max_messages: Optional[int] = None,
    config: Optional[Config] = None,
) -> ConversationBufferMemory:
    """
    Create a conversation buffer memory.

    Args:
        max_messages: Maximum messages to store
        config: Configuration

    Returns:
        ConversationBufferMemory

    Example:
        memory = buffer_memory(max_messages=100)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi!")
    """
    return ConversationBufferMemory(config=config, max_messages=max_messages)
