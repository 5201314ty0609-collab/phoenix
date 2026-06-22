"""
Base memory module for PHOENIX AIOS LangChain integration.

Provides abstract base class for memory implementations.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from ..core import BaseComponent, Config, ExecutionResult, Logger

T = TypeVar("T")


class MemoryType(Enum):
    """Types of memory."""
    BUFFER = "buffer"
    SUMMARY = "summary"
    WINDOW = "window"
    VECTOR = "vector"
    ENTITY = "entity"
    KNOWLEDGE_GRAPH = "knowledge_graph"


@dataclass(frozen=True)
class MemoryEntry:
    """
    A single memory entry.

    Attributes:
        key: Entry key
        value: Entry value
        timestamp: Creation timestamp
        metadata: Additional metadata
        ttl: Time to live in seconds (None = no expiry)
    """
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ttl: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def with_value(self, value: Any) -> MemoryEntry:
        """Create new entry with updated value."""
        from dataclasses import replace
        return replace(self, value=value, timestamp=time.time())

    def with_metadata(self, **kwargs: Any) -> MemoryEntry:
        """Create new entry with additional metadata."""
        from dataclasses import replace
        new_metadata = {**self.metadata, **kwargs}
        return replace(self, metadata=new_metadata)


@dataclass(frozen=True)
class MemoryStats:
    """
    Memory statistics.

    Attributes:
        total_entries: Total number of entries
        active_entries: Non-expired entries
        expired_entries: Expired entries
        memory_type: Type of memory
        size_bytes: Approximate size in bytes
        hit_count: Number of successful retrievals
        miss_count: Number of failed retrievals
    """
    total_entries: int = 0
    active_entries: int = 0
    expired_entries: int = 0
    memory_type: MemoryType = MemoryType.BUFFER
    size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total


class Memory(BaseComponent, ABC):
    """
    Abstract base class for memory implementations.

    Provides common functionality for storing and retrieving conversation context.

    Example:
        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi there!")

        messages = memory.get_messages()
    """

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self._logger = Logger(f"Memory.{self.__class__.__name__}")
        self._entries: Dict[str, MemoryEntry] = {}
        self._hit_count: int = 0
        self._miss_count: int = 0

    @property
    def memory_type(self) -> MemoryType:
        """Get memory type."""
        return MemoryType.BUFFER

    @abstractmethod
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to memory.

        Args:
            message: User message
        """
        pass

    @abstractmethod
    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message to memory.

        Args:
            message: AI message
        """
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages in memory.

        Returns:
            List of message dicts with 'role' and 'content'
        """
        pass

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from memory.

        Args:
            key: Entry key

        Returns:
            Entry value or None
        """
        entry = self._entries.get(key)

        if entry is None:
            self._miss_count += 1
            return None

        if entry.is_expired:
            self._entries.pop(key)
            self._miss_count += 1
            return None

        self._hit_count += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in memory.

        Args:
            key: Entry key
            value: Entry value
            ttl: Time to live in seconds
        """
        entry = MemoryEntry(key=key, value=value, ttl=ttl)
        self._entries[key] = entry
        self._logger.debug(f"Set entry: {key}")

    def delete(self, key: str) -> bool:
        """
        Delete an entry from memory.

        Args:
            key: Entry key

        Returns:
            True if deleted, False if not found
        """
        if key in self._entries:
            del self._entries[key]
            self._logger.debug(f"Deleted entry: {key}")
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from memory."""
        self._entries.clear()
        self._logger.debug("Cleared all entries")

    def has(self, key: str) -> bool:
        """
        Check if key exists in memory.

        Args:
            key: Entry key

        Returns:
            True if key exists and not expired
        """
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.is_expired:
            self._entries.pop(key)
            return False
        return True

    def keys(self) -> List[str]:
        """Get all keys in memory."""
        self._cleanup_expired()
        return list(self._entries.keys())

    def values(self) -> List[Any]:
        """Get all values in memory."""
        self._cleanup_expired()
        return [entry.value for entry in self._entries.values()]

    def items(self) -> List[tuple]:
        """Get all key-value pairs in memory."""
        self._cleanup_expired()
        return [(k, v.value) for k, v in self._entries.items()]

    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        self._cleanup_expired()
        total = len(self._entries)
        return MemoryStats(
            total_entries=total,
            active_entries=total,
            expired_entries=0,
            memory_type=self.memory_type,
            size_bytes=self._estimate_size(),
            hit_count=self._hit_count,
            miss_count=self._miss_count,
        )

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._entries.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._entries[key]
            self._logger.debug(f"Removed expired entry: {key}")

    def _estimate_size(self) -> int:
        """Estimate memory size in bytes."""
        import sys
        total = 0
        for entry in self._entries.values():
            total += sys.getsizeof(entry.key)
            total += sys.getsizeof(entry.value)
            total += sys.getsizeof(entry.metadata)
        return total

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute memory operation.

        Args:
            input_data: Input data with 'action' and optional parameters

        Returns:
            ExecutionResult
        """
        action = input_data.get("action", "get_messages")

        try:
            if action == "add_user":
                self.add_user_message(input_data["message"])
                return ExecutionResult.success_result(data=None)
            elif action == "add_ai":
                self.add_ai_message(input_data["message"])
                return ExecutionResult.success_result(data=None)
            elif action == "get_messages":
                messages = self.get_messages()
                return ExecutionResult.success_result(data=messages)
            elif action == "get":
                value = self.get(input_data["key"])
                return ExecutionResult.success_result(data=value)
            elif action == "set":
                self.set(
                    input_data["key"],
                    input_data["value"],
                    input_data.get("ttl"),
                )
                return ExecutionResult.success_result(data=None)
            elif action == "clear":
                self.clear()
                return ExecutionResult.success_result(data=None)
            elif action == "stats":
                stats = self.get_stats()
                return ExecutionResult.success_result(data=stats)
            else:
                return ExecutionResult.error_result(
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            return ExecutionResult.error_result(error=str(e))

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """
        Save context from interaction.

        Args:
            inputs: Input data
            outputs: Output data
        """
        # Extract user message
        user_message = inputs.get("input", "")
        if user_message:
            self.add_user_message(user_message)

        # Extract AI message
        ai_message = outputs.get("output", "")
        if ai_message:
            self.add_ai_message(ai_message)

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables for chain input.

        Args:
            inputs: Input data

        Returns:
            Dict of memory variables
        """
        messages = self.get_messages()
        return {"history": messages}
