"""
Storage backends for checkpoints in the PHOENIX AIOS LangGraph framework.

Provides multiple storage implementations:
- MemoryStorage: In-memory storage for testing
- FileStorage: File-based persistence
- SQLiteStorage: SQLite database storage
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .manager import Checkpoint, CheckpointStorage

logger = logging.getLogger(__name__)


# ============================================================================
# Memory Storage
# ============================================================================

class MemoryStorage:
    """In-memory checkpoint storage.

    Stores checkpoints in memory. Useful for testing and
    short-lived sessions. Data is lost on process exit.

    Example:
        storage = MemoryStorage()
        checkpoint = Checkpoint(id="1", thread_id="t", node_name="n", state={})
        storage.save(checkpoint)
        loaded = storage.load("1")
    """

    def __init__(self) -> None:
        """Initialize memory storage."""
        self._checkpoints: dict[str, Checkpoint] = {}
        self._thread_index: dict[str, list[str]] = defaultdict(list)
        self._lock = threading.Lock()

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to memory.

        Args:
            checkpoint: Checkpoint to save.
        """
        with self._lock:
            self._checkpoints[checkpoint.id] = checkpoint
            self._thread_index[checkpoint.thread_id].append(checkpoint.id)

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint from memory.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            Checkpoint if found, None otherwise.
        """
        with self._lock:
            return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(
        self,
        thread_id: str | None = None,
        limit: int = 100,
    ) -> list[Checkpoint]:
        """List checkpoints from memory.

        Args:
            thread_id: Optional thread ID filter.
            limit: Maximum checkpoints to return.

        Returns:
            List of checkpoints, newest first.
        """
        with self._lock:
            if thread_id:
                # Get checkpoints for specific thread
                ids = self._thread_index.get(thread_id, [])
                checkpoints = [
                    self._checkpoints[id]
                    for id in ids
                    if id in self._checkpoints
                ]
            else:
                # Get all checkpoints
                checkpoints = list(self._checkpoints.values())

            # Sort by creation time (newest first)
            checkpoints.sort(
                key=lambda c: c.created_at,
                reverse=True,
            )

            return checkpoints[:limit]

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint from memory.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if checkpoint_id not in self._checkpoints:
                return False

            checkpoint = self._checkpoints.pop(checkpoint_id)

            # Remove from thread index
            if checkpoint.thread_id in self._thread_index:
                try:
                    self._thread_index[checkpoint.thread_id].remove(checkpoint_id)
                except ValueError:
                    pass

            return True

    def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Number of checkpoints deleted.
        """
        with self._lock:
            ids = self._thread_index.pop(thread_id, [])
            count = 0

            for id in ids:
                if id in self._checkpoints:
                    del self._checkpoints[id]
                    count += 1

            return count

    def clear(self) -> None:
        """Clear all checkpoints."""
        with self._lock:
            self._checkpoints.clear()
            self._thread_index.clear()


# ============================================================================
# File Storage
# ============================================================================

class FileStorage:
    """File-based checkpoint storage.

    Stores checkpoints as JSON files in a directory structure.
    Each thread gets its own directory.

    Example:
        storage = FileStorage("/tmp/checkpoints")
        checkpoint = Checkpoint(id="1", thread_id="t", node_name="n", state={})
        storage.save(checkpoint)
        loaded = storage.load("1")
    """

    def __init__(self, base_dir: str | Path) -> None:
        """Initialize file storage.

        Args:
            base_dir: Base directory for checkpoint files.
        """
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @property
    def base_dir(self) -> Path:
        """Get base directory."""
        return self._base_dir

    def _get_thread_dir(self, thread_id: str) -> Path:
        """Get directory for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Thread directory path.
        """
        # Sanitize thread_id for filesystem
        safe_id = thread_id.replace("/", "_").replace("\\", "_")
        return self._base_dir / safe_id

    def _get_checkpoint_path(self, checkpoint_id: str, thread_id: str) -> Path:
        """Get file path for a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID.
            thread_id: Thread ID.

        Returns:
            Checkpoint file path.
        """
        thread_dir = self._get_thread_dir(thread_id)
        return thread_dir / f"{checkpoint_id}.json"

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to file.

        Args:
            checkpoint: Checkpoint to save.
        """
        with self._lock:
            thread_dir = self._get_thread_dir(checkpoint.thread_id)
            thread_dir.mkdir(parents=True, exist_ok=True)

            path = self._get_checkpoint_path(
                checkpoint.id,
                checkpoint.thread_id,
            )

            with open(path, "w") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

            logger.debug(f"Saved checkpoint {checkpoint.id} to {path}")

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint from file.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            Checkpoint if found, None otherwise.
        """
        with self._lock:
            # Search for checkpoint file
            for thread_dir in self._base_dir.iterdir():
                if not thread_dir.is_dir():
                    continue

                path = thread_dir / f"{checkpoint_id}.json"
                if path.exists():
                    with open(path) as f:
                        data = json.load(f)
                    return Checkpoint.from_dict(data)

            return None

    def list_checkpoints(
        self,
        thread_id: str | None = None,
        limit: int = 100,
    ) -> list[Checkpoint]:
        """List checkpoints from files.

        Args:
            thread_id: Optional thread ID filter.
            limit: Maximum checkpoints to return.

        Returns:
            List of checkpoints, newest first.
        """
        with self._lock:
            checkpoints = []

            if thread_id:
                # List checkpoints for specific thread
                thread_dir = self._get_thread_dir(thread_id)
                if thread_dir.exists():
                    for path in thread_dir.glob("*.json"):
                        try:
                            with open(path) as f:
                                data = json.load(f)
                            checkpoints.append(Checkpoint.from_dict(data))
                        except Exception as e:
                            logger.warning(f"Failed to load {path}: {e}")
            else:
                # List all checkpoints
                for thread_dir in self._base_dir.iterdir():
                    if not thread_dir.is_dir():
                        continue
                    for path in thread_dir.glob("*.json"):
                        try:
                            with open(path) as f:
                                data = json.load(f)
                            checkpoints.append(Checkpoint.from_dict(data))
                        except Exception as e:
                            logger.warning(f"Failed to load {path}: {e}")

            # Sort by creation time (newest first)
            checkpoints.sort(
                key=lambda c: c.created_at,
                reverse=True,
            )

            return checkpoints[:limit]

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint file.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            for thread_dir in self._base_dir.iterdir():
                if not thread_dir.is_dir():
                    continue

                path = thread_dir / f"{checkpoint_id}.json"
                if path.exists():
                    path.unlink()
                    return True

            return False

    def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoint files for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Number of checkpoints deleted.
        """
        with self._lock:
            thread_dir = self._get_thread_dir(thread_id)
            if not thread_dir.exists():
                return 0

            count = 0
            for path in thread_dir.glob("*.json"):
                path.unlink()
                count += 1

            # Remove empty directory
            try:
                thread_dir.rmdir()
            except OSError:
                pass

            return count

    def clear(self) -> None:
        """Clear all checkpoint files."""
        with self._lock:
            import shutil
            if self._base_dir.exists():
                shutil.rmtree(self._base_dir)
                self._base_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# SQLite Storage
# ============================================================================

class SQLiteStorage:
    """SQLite-based checkpoint storage.

    Stores checkpoints in a SQLite database for robust persistence
    and efficient querying.

    Example:
        storage = SQLiteStorage("checkpoints.db")
        checkpoint = Checkpoint(id="1", thread_id="t", node_name="n", state={})
        storage.save(checkpoint)
        loaded = storage.load("1")
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory.
        """
        self._db_path = str(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection.

        Returns:
            SQLite connection.
        """
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                state TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                parent_id TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_thread_id
            ON checkpoints(thread_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON checkpoints(created_at)
        """)
        conn.commit()

    def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to SQLite.

        Args:
            checkpoint: Checkpoint to save.
        """
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO checkpoints
            (id, thread_id, node_name, state, metadata, created_at, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checkpoint.id,
                checkpoint.thread_id,
                checkpoint.node_name,
                json.dumps(checkpoint.state),
                json.dumps(checkpoint.metadata),
                checkpoint.created_at.isoformat(),
                checkpoint.parent_id,
            ),
        )
        conn.commit()

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint from SQLite.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            Checkpoint if found, None otherwise.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return Checkpoint(
            id=row["id"],
            thread_id=row["thread_id"],
            node_name=row["node_name"],
            state=json.loads(row["state"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            parent_id=row["parent_id"],
        )

    def list_checkpoints(
        self,
        thread_id: str | None = None,
        limit: int = 100,
    ) -> list[Checkpoint]:
        """List checkpoints from SQLite.

        Args:
            thread_id: Optional thread ID filter.
            limit: Maximum checkpoints to return.

        Returns:
            List of checkpoints, newest first.
        """
        conn = self._get_connection()

        if thread_id:
            cursor = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (thread_id, limit),
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM checkpoints
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )

        checkpoints = []
        for row in cursor:
            checkpoints.append(Checkpoint(
                id=row["id"],
                thread_id=row["thread_id"],
                node_name=row["node_name"],
                state=json.loads(row["state"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=datetime.fromisoformat(row["created_at"]),
                parent_id=row["parent_id"],
            ))

        return checkpoints

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint from SQLite.

        Args:
            checkpoint_id: Checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            Number of checkpoints deleted.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM checkpoints WHERE thread_id = ?",
            (thread_id,),
        )
        conn.commit()
        return cursor.rowcount

    def clear(self) -> None:
        """Clear all checkpoints."""
        conn = self._get_connection()
        conn.execute("DELETE FROM checkpoints")
        conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection
