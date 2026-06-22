"""
Checkpoint manager for the PHOENIX AIOS LangGraph framework.

Provides state persistence, recovery, and time-travel debugging
capabilities for graph executions.
"""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ============================================================================
# Checkpoint Data
# ============================================================================

@dataclass(frozen=True)
class Checkpoint:
    """A saved graph state checkpoint.

    Attributes:
        id: Unique checkpoint identifier.
        thread_id: Thread/conversation identifier.
        node_name: Name of node that created this checkpoint.
        state: Saved state dictionary.
        metadata: Checkpoint metadata.
        created_at: Creation timestamp.
        parent_id: Parent checkpoint ID (for branching).
    """

    id: str
    thread_id: str
    node_name: str
    state: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    parent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary.

        Returns:
            Checkpoint as dict.
        """
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "node_name": self.node_name,
            "state": self.state,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Create checkpoint from dictionary.

        Args:
            data: Checkpoint dictionary.

        Returns:
            Checkpoint instance.
        """
        return cls(
            id=data["id"],
            thread_id=data["thread_id"],
            node_name=data["node_name"],
            state=data["state"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            parent_id=data.get("parent_id"),
        )


# ============================================================================
# Checkpoint Configuration
# ============================================================================

@dataclass
class CheckpointConfig:
    """Configuration for checkpoint behavior.

    Attributes:
        enabled: Whether checkpointing is enabled.
        auto_checkpoint: Automatically create checkpoints.
        checkpoint_interval: Nodes between auto-checkpoints.
        max_checkpoints: Maximum checkpoints per thread.
        compress_state: Compress state data.
        include_metadata: Include metadata in checkpoints.
    """

    enabled: bool = True
    auto_checkpoint: bool = True
    checkpoint_interval: int = 10
    max_checkpoints: int = 100
    compress_state: bool = False
    include_metadata: bool = True


# ============================================================================
# Storage Protocol
# ============================================================================

@runtime_checkable
class CheckpointStorage(Protocol):
    """Protocol for checkpoint storage backends.

    Implementations provide persistence for checkpoints
    using different storage mechanisms.
    """

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint.

        Args:
            checkpoint: Checkpoint to save.
        """
        ...

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            Checkpoint if found, None otherwise.
        """
        ...

    def list_checkpoints(
        self,
        thread_id: str | None = None,
        limit: int = 100,
    ) -> list[Checkpoint]:
        """List checkpoints.

        Args:
            thread_id: Optional thread ID filter.
            limit: Maximum number of checkpoints to return.

        Returns:
            List of checkpoints.
        """
        ...

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        ...

    def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Number of checkpoints deleted.
        """
        ...

    def clear(self) -> None:
        """Clear all checkpoints."""
        ...


# ============================================================================
# Checkpoint Manager
# ============================================================================

class CheckpointManager:
    """Manages graph state checkpoints.

    Provides checkpoint creation, retrieval, and management
    for graph executions. Supports time-travel debugging
    and state recovery.

    Features:
        - Automatic checkpointing at intervals
        - Manual checkpoint creation
        - Thread-based checkpoint organization
        - Time-travel debugging (restore to any checkpoint)
        - Checkpoint branching for parallel paths

    Example:
        storage = MemoryStorage()
        manager = CheckpointManager(storage)

        # Create checkpoint
        checkpoint = manager.create_checkpoint(
            thread_id="conv-1",
            node_name="process",
            state={"messages": ["hello"]},
        )

        # Restore checkpoint
        restored = manager.load_checkpoint(checkpoint.id)

        # List thread checkpoints
        checkpoints = manager.list_checkpoints(thread_id="conv-1")
    """

    def __init__(
        self,
        storage: CheckpointStorage | None = None,
        config: CheckpointConfig | None = None,
    ) -> None:
        """Initialize checkpoint manager.

        Args:
            storage: Storage backend (defaults to MemoryStorage).
            config: Checkpoint configuration.
        """
        from .storage import MemoryStorage

        self._storage = storage or MemoryStorage()
        self._config = config or CheckpointConfig()

        # Statistics
        self._checkpoint_count = 0
        self._restore_count = 0

    @property
    def config(self) -> CheckpointConfig:
        """Get checkpoint configuration."""
        return self._config

    @property
    def checkpoint_count(self) -> int:
        """Get total checkpoints created."""
        return self._checkpoint_count

    @property
    def restore_count(self) -> int:
        """Get total restores performed."""
        return self._restore_count

    def create_checkpoint(
        self,
        thread_id: str,
        node_name: str,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        parent_id: str | None = None,
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            thread_id: Thread/conversation identifier.
            node_name: Name of node creating checkpoint.
            state: State to save.
            metadata: Optional checkpoint metadata.
            parent_id: Optional parent checkpoint ID.

        Returns:
            Created checkpoint.
        """
        if not self._config.enabled:
            # Return a no-op checkpoint
            return Checkpoint(
                id="disabled",
                thread_id=thread_id,
                node_name=node_name,
                state=state,
            )

        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            node_name=node_name,
            state=state.copy(),
            metadata=metadata or {},
            parent_id=parent_id,
        )

        self._storage.save(checkpoint)
        self._checkpoint_count += 1

        # Enforce max checkpoints per thread
        self._enforce_max_checkpoints(thread_id)

        logger.debug(f"Created checkpoint {checkpoint.id} for thread {thread_id}")
        return checkpoint

    def load_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            Checkpoint if found, None otherwise.
        """
        checkpoint = self._storage.load(checkpoint_id)
        if checkpoint:
            self._restore_count += 1
        return checkpoint

    def get_latest_checkpoint(
        self,
        thread_id: str,
    ) -> Checkpoint | None:
        """Get the latest checkpoint for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Latest checkpoint if any, None otherwise.
        """
        checkpoints = self._storage.list_checkpoints(
            thread_id=thread_id,
            limit=1,
        )
        return checkpoints[0] if checkpoints else None

    def list_checkpoints(
        self,
        thread_id: str | None = None,
        limit: int = 100,
    ) -> list[Checkpoint]:
        """List checkpoints.

        Args:
            thread_id: Optional thread ID filter.
            limit: Maximum checkpoints to return.

        Returns:
            List of checkpoints.
        """
        return self._storage.list_checkpoints(thread_id, limit)

    def get_checkpoint_history(
        self,
        checkpoint_id: str,
    ) -> list[Checkpoint]:
        """Get checkpoint history (parent chain).

        Traverses parent links to build history.

        Args:
            checkpoint_id: Starting checkpoint ID.

        Returns:
            List of checkpoints from newest to oldest.
        """
        history = []
        current_id = checkpoint_id

        while current_id:
            checkpoint = self._storage.load(current_id)
            if not checkpoint:
                break
            history.append(checkpoint)
            current_id = checkpoint.parent_id

        return history

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        return self._storage.delete(checkpoint_id)

    def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Number of checkpoints deleted.
        """
        return self._storage.delete_thread(thread_id)

    def clear(self) -> None:
        """Clear all checkpoints."""
        self._storage.clear()
        self._checkpoint_count = 0
        self._restore_count = 0

    def get_stats(self) -> dict[str, Any]:
        """Get checkpoint statistics.

        Returns:
            Dictionary with statistics.
        """
        all_checkpoints = self._storage.list_checkpoints(limit=10000)
        thread_ids = set(c.thread_id for c in all_checkpoints)

        return {
            "total_checkpoints": self._checkpoint_count,
            "total_restores": self._restore_count,
            "active_threads": len(thread_ids),
            "storage_type": type(self._storage).__name__,
        }

    def _enforce_max_checkpoints(self, thread_id: str) -> None:
        """Enforce maximum checkpoints per thread.

        Args:
            thread_id: Thread ID to enforce limit for.
        """
        checkpoints = self._storage.list_checkpoints(
            thread_id=thread_id,
            limit=self._config.max_checkpoints + 10,
        )

        if len(checkpoints) > self._config.max_checkpoints:
            # Delete oldest checkpoints
            to_delete = checkpoints[self._config.max_checkpoints:]
            for checkpoint in to_delete:
                self._storage.delete(checkpoint.id)


# ============================================================================
# Checkpoint Decorator
# ============================================================================

def checkpoint_after(
    manager: CheckpointManager,
    thread_id: str,
    node_name: str,
):
    """Decorator to automatically checkpoint after node execution.

    Args:
        manager: Checkpoint manager instance.
        thread_id: Thread ID for checkpoint.
        node_name: Node name for checkpoint.

    Returns:
        Decorator function.
    """
    def decorator(fn):
        def wrapper(state: dict[str, Any]) -> dict[str, Any]:
            # Execute node
            result = fn(state)

            # Create checkpoint
            manager.create_checkpoint(
                thread_id=thread_id,
                node_name=node_name,
                state={**state, **result},
            )

            return result

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator
