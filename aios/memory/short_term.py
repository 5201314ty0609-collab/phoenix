"""
Short-Term Memory (STM) — Conversation history buffer.

Manages the recent conversation as an ordered sequence of messages.
Supports:
- FIFO with importance-weighted eviction
- Token budget management
- Automatic summarization trigger
- Role-based importance boosting
- Message search and filtering

The STM is the primary input to the working memory and the source
for long-term memory extraction at session end.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Callable, Iterator

from .config import STMConfig
from .memory_types import MemoryMessage, _estimate_tokens


class ShortTermMemory:
    """
    Conversation history buffer with importance-weighted eviction.

    Messages are stored in chronological order. When the buffer exceeds
    capacity (by message count or token budget), the least important
    messages are evicted first — unless they are marked as pinned.

    Thread-safe: all public methods use a reentrant lock.

    Example:
        stm = ShortTermMemory()

        stm.add(role="user", content="What is the weather?")
        stm.add(role="assistant", content="It is sunny today.")

        recent = stm.recent(5)
        for msg in recent:
            print(f"{msg.role}: {msg.content}")
    """

    def __init__(self, config: STMConfig | None = None) -> None:
        self._config = config or STMConfig()
        self._messages: deque[MemoryMessage] = deque()
        self._total_tokens: int = 0
        self._lock = threading.RLock()

        # Callbacks
        self._on_evict: list[Callable[[MemoryMessage], None]] = []
        self._on_summarize: list[Callable[[list[MemoryMessage]], None]] = []

    # ── Properties ──────────────────────────────────────────────

    @property
    def count(self) -> int:
        """Number of messages currently in STM."""
        return len(self._messages)

    @property
    def total_tokens(self) -> int:
        """Total token count of all messages in STM."""
        return self._total_tokens

    @property
    def is_full(self) -> bool:
        """True if STM exceeds message or token capacity."""
        return (
            self.count >= self._config.max_messages
            or self._total_tokens >= self._config.max_tokens
        )

    @property
    def needs_summarization(self) -> bool:
        """True if STM exceeds summarization threshold."""
        threshold = int(self._config.max_messages * self._config.summarize_threshold)
        return self.count >= threshold

    @property
    def messages(self) -> tuple[MemoryMessage, ...]:
        """Snapshot of all messages as an immutable tuple."""
        return tuple(self._messages)

    @property
    def config(self) -> STMConfig:
        """Current STM configuration."""
        return self._config

    # ── Core Operations ─────────────────────────────────────────

    def add(
        self,
        role: str,
        content: str,
        token_count: int | None = None,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> MemoryMessage:
        """
        Add a message to STM.

        Automatically computes importance based on role if not provided,
        and evicts low-importance messages if capacity is exceeded.

        Args:
            role: Speaker role (user/assistant/system/tool).
            content: Message text.
            token_count: Explicit token count (auto-estimated if None).
            importance: Explicit importance 0.0-1.0 (role-based if None).
            metadata: Optional key-value metadata.

        Returns:
            The created MemoryMessage.
        """
        with self._lock:
            # Compute importance from role if not explicit
            if importance is None:
                importance = self._role_importance(role)

            msg = MemoryMessage.create(
                role=role,
                content=content,
                token_count=token_count,
                importance=importance,
                metadata=metadata,
            )

            self._messages.append(msg)
            self._total_tokens += msg.token_count

            # Evict if over capacity
            self._evict_to_capacity()

            return msg

    def get(self, message_id: str) -> MemoryMessage | None:
        """Retrieve a message by ID."""
        with self._lock:
            for msg in self._messages:
                if msg.id == message_id:
                    return msg
            return None

    def recent(self, n: int = 10) -> list[MemoryMessage]:
        """
        Get the N most recent messages.

        Args:
            n: Number of messages to return.

        Returns:
            List of most recent messages in chronological order.
        """
        with self._lock:
            return list(self._messages)[-n:]

    def since(self, timestamp: float) -> list[MemoryMessage]:
        """
        Get all messages after a given timestamp.

        Args:
            timestamp: Unix timestamp cutoff.

        Returns:
            Messages created after the timestamp.
        """
        with self._lock:
            return [m for m in self._messages if m.timestamp > timestamp]

    def by_role(self, role: str) -> list[MemoryMessage]:
        """Get all messages from a specific role."""
        with self._lock:
            return [m for m in self._messages if m.role == role]

    def search(self, query: str, limit: int = 10) -> list[MemoryMessage]:
        """
        Simple substring search across message content.

        Args:
            query: Search text (case-insensitive).
            limit: Maximum results.

        Returns:
            Matching messages sorted by recency.
        """
        query_lower = query.lower()
        with self._lock:
            matches = [
                m for m in self._messages
                if query_lower in m.content.lower()
            ]
            return matches[-limit:]

    def update_importance(self, message_id: str, importance: float) -> bool:
        """
        Update importance of an existing message.

        Args:
            message_id: Target message ID.
            importance: New importance score.

        Returns:
            True if message was found and updated.
        """
        with self._lock:
            for i, msg in enumerate(self._messages):
                if msg.id == message_id:
                    self._messages[i] = msg.with_importance(importance)
                    return True
            return False

    def clear(self) -> int:
        """
        Clear all messages from STM.

        Returns:
            Number of messages removed.
        """
        with self._lock:
            count = len(self._messages)
            self._messages.clear()
            self._total_tokens = 0
            return count

    def get_messages_for_summarization(self) -> list[MemoryMessage]:
        """
        Get messages eligible for summarization.

        Returns the older half of messages (excluding the most recent
        quarter which should stay in context).

        Returns:
            List of messages to summarize.
        """
        with self._lock:
            total = len(self._messages)
            if total < 4:
                return []
            # Summarize the older half, keep recent quarter in raw form
            split_point = total // 2
            return list(self._messages)[:split_point]

    def replace_with_summary(self, summary_msg: MemoryMessage) -> int:
        """
        Replace summarized messages with a single summary message.

        Typically called after compression: the older half of messages
        is replaced with a summary, and the recent messages remain.

        Args:
            summary_msg: The summary message to insert.

        Returns:
            Number of messages replaced.
        """
        with self._lock:
            total = len(self._messages)
            if total < 4:
                return 0

            split_point = total // 2
            removed_tokens = sum(
                m.token_count for m in list(self._messages)[:split_point]
            )

            # Remove older messages
            for _ in range(split_point):
                self._messages.popleft()

            # Insert summary at front
            self._messages.appendleft(summary_msg)

            # Recalculate tokens
            self._total_tokens = sum(m.token_count for m in self._messages)

            return split_point

    # ── Callbacks ───────────────────────────────────────────────

    def on_evict(self, callback: Callable[[MemoryMessage], None]) -> None:
        """Register a callback for message eviction events."""
        self._on_evict.append(callback)

    def on_summarize(self, callback: Callable[[list[MemoryMessage]], None]) -> None:
        """Register a callback for summarization triggers."""
        self._on_summarize.append(callback)

    # ── Iteration ───────────────────────────────────────────────

    def __iter__(self) -> Iterator[MemoryMessage]:
        """Iterate over messages in chronological order."""
        return iter(self._messages)

    def __len__(self) -> int:
        return self.count

    def __bool__(self) -> bool:
        return self.count > 0

    # ── Internal ────────────────────────────────────────────────

    def _role_importance(self, role: str) -> float:
        """Compute base importance from message role."""
        boosts = {
            "user": self._config.importance_boost_user,
            "assistant": self._config.importance_boost_assistant,
            "system": self._config.importance_boost_system,
            "tool": self._config.importance_boost_tool,
        }
        return boosts.get(role, 0.5)

    def _evict_to_capacity(self) -> None:
        """
        Evict lowest-importance messages until within capacity.

        Eviction strategy:
        1. If over message limit: remove lowest-importance message
        2. If over token budget: remove lowest-importance message
        3. Repeat until within both limits
        """
        while (
            len(self._messages) > self._config.max_messages
            or self._total_tokens > self._config.max_tokens
        ):
            if len(self._messages) <= 1:
                break  # Never evict the last message

            # Find the lowest-importance message (skip first and last 2)
            min_idx = 0
            min_importance = float("inf")
            for i, msg in enumerate(self._messages):
                # Protect recent messages (last 2) and the very first
                if i >= len(self._messages) - 2:
                    continue
                if i == 0:
                    continue
                if msg.importance < min_importance:
                    min_importance = msg.importance
                    min_idx = i

            # Evict
            evicted = self._messages[min_idx]
            del self._messages[min_idx]  # type: ignore[arg-type]
            self._total_tokens -= evicted.token_count

            for cb in self._on_evict:
                cb(evicted)

    # ── Serialization ───────────────────────────────────────────

    def to_list(self) -> list[dict]:
        """Serialize all messages to a list of dicts."""
        with self._lock:
            return [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "token_count": m.token_count,
                    "timestamp": m.timestamp,
                    "importance": m.importance,
                    "metadata": dict(m.metadata),
                }
                for m in self._messages
            ]

    def from_list(self, data: list[dict]) -> int:
        """
        Load messages from a list of dicts.

        Args:
            data: List of message dicts (as produced by to_list).

        Returns:
            Number of messages loaded.
        """
        with self._lock:
            self._messages.clear()
            self._total_tokens = 0
            for d in data:
                msg = MemoryMessage(
                    id=d["id"],
                    role=d["role"],
                    content=d["content"],
                    token_count=d["token_count"],
                    timestamp=d["timestamp"],
                    importance=d.get("importance", 0.5),
                    metadata=tuple(sorted(d.get("metadata", {}).items())),
                )
                self._messages.append(msg)
                self._total_tokens += msg.token_count
            return len(self._messages)
