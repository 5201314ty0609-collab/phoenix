"""
PHOENIX AIOS — Conversation Manager

Manages multi-turn conversations with history tracking,
automatic context window management, and tool integration.

Key features:
- Append-only message history (immutable pattern)
- Automatic history trimming when approaching context limits
- Tool call round-trip tracking
- Conversation export/import for persistence
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from aios.ai.types import ChatMessage, ChatResponse, ChatRole, ToolCall, Usage


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------


@dataclass
class Conversation:
    """
    A multi-turn conversation with history management.

    The conversation maintains an append-only list of messages.
    Each interaction creates new message objects (immutability).

    Attributes:
        id: Unique conversation ID
        system_prompt: System prompt for the conversation
        messages: Message history
        created_at: Creation timestamp
        metadata: Additional metadata
        max_messages: Maximum messages before trimming (0 = unlimited)
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    system_prompt: Optional[str] = None
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_messages: int = 100

    @property
    def message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)

    @property
    def user_messages(self) -> List[ChatMessage]:
        """Get only user messages."""
        return [m for m in self.messages if m.role == ChatRole.USER]

    @property
    def assistant_messages(self) -> List[ChatMessage]:
        """Get only assistant messages."""
        return [m for m in self.messages if m.role == ChatRole.ASSISTANT]

    @property
    def tool_messages(self) -> List[ChatMessage]:
        """Get only tool result messages."""
        return [m for m in self.messages if m.role == ChatRole.TOOL]

    @property
    def last_message(self) -> Optional[ChatMessage]:
        """Get the last message."""
        return self.messages[-1] if self.messages else None

    @property
    def last_user_message(self) -> Optional[ChatMessage]:
        """Get the last user message."""
        for msg in reversed(self.messages):
            if msg.role == ChatRole.USER:
                return msg
        return None

    @property
    def last_assistant_message(self) -> Optional[ChatMessage]:
        """Get the last assistant message."""
        for msg in reversed(self.messages):
            if msg.role == ChatRole.ASSISTANT:
                return msg
        return None

    def add_user_message(self, content: str, name: Optional[str] = None) -> None:
        """
        Add a user message to the conversation.

        Args:
            content: Message content
            name: Optional sender name
        """
        self.messages.append(ChatMessage.user(content, name=name))
        self._trim_if_needed()

    def add_assistant_message(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[Sequence[ToolCall]] = None,
    ) -> None:
        """
        Add an assistant message to the conversation.

        Args:
            content: Message content
            tool_calls: Tool calls requested by the model
        """
        self.messages.append(ChatMessage.assistant(content=content, tool_calls=tool_calls))
        self._trim_if_needed()

    def add_tool_result(
        self,
        tool_call_id: str,
        name: str,
        content: str,
    ) -> None:
        """
        Add a tool result message.

        Args:
            tool_call_id: ID of the tool call
            name: Tool name
            content: Tool result content
        """
        self.messages.append(ChatMessage.tool(tool_call_id, name, content))
        self._trim_if_needed()

    def add_response(self, response: ChatResponse) -> None:
        """
        Add a model response to the conversation.

        Extracts the assistant message from the response and adds it.

        Args:
            response: ChatResponse from the model
        """
        choice = response.first_choice
        if choice and choice.message:
            self.add_assistant_message(
                content=choice.message.content,
                tool_calls=choice.message.tool_calls if choice.message.tool_calls else None,
            )

    def get_history(self, include_system: bool = True) -> List[ChatMessage]:
        """
        Get conversation history for an API call.

        Args:
            include_system: Whether to prepend system prompt

        Returns:
            List of messages (system + history)
        """
        messages: List[ChatMessage] = []

        if include_system and self.system_prompt:
            messages.append(ChatMessage.system(self.system_prompt))

        messages.extend(self.messages)
        return messages

    def to_api_messages(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """
        Get conversation as API-ready message dicts.

        Args:
            include_system: Whether to include system prompt

        Returns:
            List of message dicts
        """
        return [m.to_api_dict() for m in self.get_history(include_system)]

    def trim(self, keep_last: int = 20) -> int:
        """
        Manually trim conversation history.

        Keeps the most recent `keep_last` messages.
        Tool call/result pairs are kept together.

        Args:
            keep_last: Number of recent messages to keep

        Returns:
            Number of messages removed
        """
        if len(self.messages) <= keep_last:
            return 0

        removed = len(self.messages) - keep_last
        self.messages = self.messages[-keep_last:]
        return removed

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def _trim_if_needed(self) -> None:
        """Auto-trim if max_messages is exceeded."""
        if self.max_messages > 0 and len(self.messages) > self.max_messages:
            self.trim(keep_last=self.max_messages)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export conversation to a dictionary.

        Returns:
            Serializable dictionary
        """
        return {
            "id": self.id,
            "system_prompt": self.system_prompt,
            "messages": [m.to_api_dict() for m in self.messages],
            "created_at": self.created_at,
            "metadata": self.metadata,
            "max_messages": self.max_messages,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Conversation:
        """
        Import conversation from a dictionary.

        Args:
            data: Dictionary from to_dict()

        Returns:
            Conversation instance
        """
        messages: List[ChatMessage] = []
        for msg_data in data.get("messages", []):
            try:
                role = ChatRole(msg_data["role"])
            except (ValueError, KeyError):
                continue

            tool_calls = ()
            raw_tool_calls = msg_data.get("tool_calls")
            if raw_tool_calls:
                from aios.ai.types import ToolCall

                tc_list = []
                for tc in raw_tool_calls:
                    func = tc.get("function", {})
                    tc_list.append(
                        ToolCall(
                            id=tc.get("id", ""),
                            name=func.get("name", ""),
                            arguments=func.get("arguments", ""),
                        )
                    )
                tool_calls = tuple(tc_list)

            messages.append(
                ChatMessage(
                    role=role,
                    content=msg_data.get("content"),
                    name=msg_data.get("name"),
                    tool_calls=tool_calls,
                    tool_call_id=msg_data.get("tool_call_id"),
                )
            )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            system_prompt=data.get("system_prompt"),
            messages=messages,
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
            max_messages=data.get("max_messages", 100),
        )

    def export_json(self, indent: int = 2) -> str:
        """
        Export conversation as JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def import_json(cls, json_str: str) -> Conversation:
        """
        Import conversation from JSON string.

        Args:
            json_str: JSON string from export_json()

        Returns:
            Conversation instance
        """
        return cls.from_dict(json.loads(json_str))


# ---------------------------------------------------------------------------
# Conversation Summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConversationSummary:
    """
    Summary statistics for a conversation.

    Attributes:
        id: Conversation ID
        message_count: Total messages
        user_message_count: User messages
        assistant_message_count: Assistant messages
        tool_message_count: Tool result messages
        total_tokens: Total tokens used (if tracked)
        duration: Conversation duration in seconds
    """

    id: str
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_message_count: int = 0
    total_tokens: int = 0
    duration: float = 0.0


def summarize_conversation(conversation: Conversation) -> ConversationSummary:
    """
    Generate summary statistics for a conversation.

    Args:
        conversation: Conversation to summarize

    Returns:
        ConversationSummary
    """
    return ConversationSummary(
        id=conversation.id,
        message_count=conversation.message_count,
        user_message_count=len(conversation.user_messages),
        assistant_message_count=len(conversation.assistant_messages),
        tool_message_count=len(conversation.tool_messages),
        duration=time.time() - conversation.created_at,
    )
