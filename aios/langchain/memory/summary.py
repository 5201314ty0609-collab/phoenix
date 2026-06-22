"""
Conversation summary memory implementation.

Maintains a running summary of the conversation.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..core import Config, Logger
from .base import Memory, MemoryType


class ConversationSummaryMemory(Memory):
    """
    Conversation summary memory that maintains a running summary.

    Instead of storing all messages, maintains a summary that gets
    updated as new messages arrive.

    Example:
        def summarizer(messages, current_summary):
            # Your summarization logic here
            return "Updated summary..."

        memory = ConversationSummaryMemory(summarizer=summarizer)
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        summary = memory.get_summary()
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        summarizer: Optional[Callable[[List[Dict[str, str]], str], str]] = None,
        max_messages_before_summary: int = 10,
    ):
        super().__init__(config)
        self._messages: List[Dict[str, str]] = []
        self._summary: str = ""
        self._summarizer = summarizer
        self._max_messages_before_summary = max_messages_before_summary
        self._logger = Logger("ConversationSummaryMemory")

    @property
    def memory_type(self) -> MemoryType:
        """Get memory type."""
        return MemoryType.SUMMARY

    @property
    def summary(self) -> str:
        """Get current summary."""
        return self._summary

    def add_user_message(self, message: str) -> None:
        """
        Add a user message.

        Args:
            message: User message
        """
        self._messages.append({"role": "user", "content": message})
        self._check_summarize()
        self._logger.debug(f"Added user message: {message[:50]}...")

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message.

        Args:
            message: AI message
        """
        self._messages.append({"role": "ai", "content": message})
        self._check_summarize()
        self._logger.debug(f"Added AI message: {message[:50]}...")

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get messages with summary context.

        Returns:
            List of message dicts with summary
        """
        messages = []

        # Add summary as system message if available
        if self._summary:
            messages.append({
                "role": "system",
                "content": f"Conversation summary: {self._summary}",
            })

        # Add recent messages
        messages.extend(self._messages)

        return messages

    def get_summary(self) -> str:
        """
        Get conversation summary.

        Returns:
            Summary string
        """
        return self._summary

    def set_summary(self, summary: str) -> None:
        """
        Set conversation summary.

        Args:
            summary: Summary string
        """
        self._summary = summary
        self._logger.debug(f"Set summary: {summary[:50]}...")

    def clear(self) -> None:
        """Clear messages and summary."""
        self._messages.clear()
        self._summary = ""
        self._logger.debug("Cleared messages and summary")

    def _check_summarize(self) -> None:
        """Check if summarization is needed."""
        if len(self._messages) >= self._max_messages_before_summary:
            self._summarize()

    def _summarize(self) -> None:
        """Summarize messages."""
        if not self._summarizer:
            self._logger.warning("No summarizer provided, skipping summarization")
            return

        try:
            new_summary = self._summarizer(self._messages, self._summary)
            self._summary = new_summary
            self._messages.clear()
            self._logger.info(f"Summarized conversation: {new_summary[:50]}...")
        except Exception as e:
            self._logger.error(f"Summarization failed: {e}")

    def force_summarize(self) -> str:
        """
        Force summarization.

        Returns:
            New summary
        """
        self._summarize()
        return self._summary

    def get_context_string(self) -> str:
        """
        Get context as string.

        Returns:
            Formatted context string
        """
        parts = []

        if self._summary:
            parts.append(f"Summary: {self._summary}")

        if self._messages:
            parts.append("Recent messages:")
            for msg in self._messages:
                role = "Human" if msg["role"] == "user" else "AI"
                parts.append(f"{role}: {msg['content']}")

        return "\n".join(parts)

    def invoke(self, input_data: Dict[str, Any]) -> Any:
        """
        Execute memory operation.

        Args:
            input_data: Input data

        Returns:
            ExecutionResult
        """
        action = input_data.get("action", "get_messages")

        if action == "get_summary":
            from ..core import ExecutionResult
            return ExecutionResult.success_result(data=self.get_summary())

        if action == "set_summary":
            from ..core import ExecutionResult
            self.set_summary(input_data["summary"])
            return ExecutionResult.success_result(data=None)

        if action == "force_summarize":
            from ..core import ExecutionResult
            summary = self.force_summarize()
            return ExecutionResult.success_result(data=summary)

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
            Dict with 'history' and 'summary' keys
        """
        return {
            "history": self.get_context_string(),
            "summary": self._summary,
            "messages": self.get_messages(),
        }

    def __len__(self) -> int:
        """Get number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConversationSummaryMemory("
            f"messages={len(self._messages)}, "
            f"summary_length={len(self._summary)})"
        )


def summary_memory(
    summarizer: Optional[Callable[[List[Dict[str, str]], str], str]] = None,
    max_messages_before_summary: int = 10,
    config: Optional[Config] = None,
) -> ConversationSummaryMemory:
    """
    Create a conversation summary memory.

    Args:
        summarizer: Summarization function
        max_messages_before_summary: Messages before summarization
        config: Configuration

    Returns:
        ConversationSummaryMemory

    Example:
        def my_summarizer(messages, current_summary):
            new_text = " ".join(m["content"] for m in messages)
            return f"{current_summary}\n{new_text}" if current_summary else new_text

        memory = summary_memory(summarizer=my_summarizer)
    """
    return ConversationSummaryMemory(
        config=config,
        summarizer=summarizer,
        max_messages_before_summary=max_messages_before_summary,
    )
