"""
Tests for checkpoint system in the PHOENIX AIOS LangGraph framework.
"""

import tempfile
import unittest
from pathlib import Path

from ..checkpoint.manager import (
    CheckpointManager,
    Checkpoint,
    CheckpointConfig,
)
from ..checkpoint.storage import (
    MemoryStorage,
    FileStorage,
    SQLiteStorage,
)


class TestCheckpoint(unittest.TestCase):
    """Tests for Checkpoint class."""

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        checkpoint = Checkpoint(
            id="test-1",
            thread_id="thread-1",
            node_name="process",
            state={"messages": ["hello"]},
        )
        self.assertEqual(checkpoint.id, "test-1")
        self.assertEqual(checkpoint.thread_id, "thread-1")
        self.assertEqual(checkpoint.state, {"messages": ["hello"]})

    def test_to_dict(self):
        """Test converting checkpoint to dict."""
        checkpoint = Checkpoint(
            id="test-1",
            thread_id="thread-1",
            node_name="process",
            state={"value": 42},
        )
        d = checkpoint.to_dict()
        self.assertEqual(d["id"], "test-1")
        self.assertEqual(d["state"], {"value": 42})
        self.assertIn("created_at", d)

    def test_from_dict(self):
        """Test creating checkpoint from dict."""
        d = {
            "id": "test-1",
            "thread_id": "thread-1",
            "node_name": "process",
            "state": {"value": 42},
            "metadata": {},
            "created_at": "2026-06-23T00:00:00",
            "parent_id": None,
        }
        checkpoint = Checkpoint.from_dict(d)
        self.assertEqual(checkpoint.id, "test-1")
        self.assertEqual(checkpoint.state, {"value": 42})


class TestCheckpointManager(unittest.TestCase):
    """Tests for CheckpointManager class."""

    def test_create_manager(self):
        """Test creating a checkpoint manager."""
        manager = CheckpointManager()
        self.assertIsNotNone(manager)

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        manager = CheckpointManager()
        checkpoint = manager.create_checkpoint(
            thread_id="thread-1",
            node_name="process",
            state={"messages": ["hello"]},
        )
        self.assertIsNotNone(checkpoint.id)
        self.assertEqual(checkpoint.thread_id, "thread-1")

    def test_load_checkpoint(self):
        """Test loading a checkpoint."""
        manager = CheckpointManager()
        checkpoint = manager.create_checkpoint(
            thread_id="thread-1",
            node_name="process",
            state={"value": 42},
        )

        loaded = manager.load_checkpoint(checkpoint.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state, {"value": 42})

    def test_load_nonexistent(self):
        """Test loading nonexistent checkpoint."""
        manager = CheckpointManager()
        loaded = manager.load_checkpoint("nonexistent")
        self.assertIsNone(loaded)

    def test_get_latest_checkpoint(self):
        """Test getting latest checkpoint."""
        manager = CheckpointManager()

        # Create multiple checkpoints
        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={"step": 1},
        )
        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node2",
            state={"step": 2},
        )

        latest = manager.get_latest_checkpoint("thread-1")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.state["step"], 2)

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        manager = CheckpointManager()

        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={},
        )
        manager.create_checkpoint(
            thread_id="thread-2",
            node_name="node2",
            state={},
        )

        # List all
        all_checkpoints = manager.list_checkpoints()
        self.assertEqual(len(all_checkpoints), 2)

        # List by thread
        thread1_checkpoints = manager.list_checkpoints(thread_id="thread-1")
        self.assertEqual(len(thread1_checkpoints), 1)

    def test_get_checkpoint_history(self):
        """Test getting checkpoint history."""
        manager = CheckpointManager()

        # Create parent checkpoint
        parent = manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={"step": 1},
        )

        # Create child checkpoint
        child = manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node2",
            state={"step": 2},
            parent_id=parent.id,
        )

        history = manager.get_checkpoint_history(child.id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].id, child.id)
        self.assertEqual(history[1].id, parent.id)

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        manager = CheckpointManager()
        checkpoint = manager.create_checkpoint(
            thread_id="thread-1",
            node_name="process",
            state={},
        )

        self.assertTrue(manager.delete_checkpoint(checkpoint.id))
        self.assertIsNone(manager.load_checkpoint(checkpoint.id))

    def test_delete_thread(self):
        """Test deleting all checkpoints for a thread."""
        manager = CheckpointManager()

        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={},
        )
        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node2",
            state={},
        )

        count = manager.delete_thread("thread-1")
        self.assertEqual(count, 2)
        self.assertEqual(len(manager.list_checkpoints(thread_id="thread-1")), 0)

    def test_clear(self):
        """Test clearing all checkpoints."""
        manager = CheckpointManager()

        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={},
        )

        manager.clear()
        self.assertEqual(len(manager.list_checkpoints()), 0)

    def test_get_stats(self):
        """Test getting checkpoint statistics."""
        manager = CheckpointManager()

        manager.create_checkpoint(
            thread_id="thread-1",
            node_name="node1",
            state={},
        )

        stats = manager.get_stats()
        self.assertEqual(stats["total_checkpoints"], 1)
        self.assertEqual(stats["active_threads"], 1)

    def test_max_checkpoints(self):
        """Test max checkpoints per thread."""
        config = CheckpointConfig(max_checkpoints=2)
        manager = CheckpointManager(config=config)

        for i in range(5):
            manager.create_checkpoint(
                thread_id="thread-1",
                node_name=f"node{i}",
                state={"step": i},
            )

        checkpoints = manager.list_checkpoints(thread_id="thread-1")
        self.assertEqual(len(checkpoints), 2)


class TestMemoryStorage(unittest.TestCase):
    """Tests for MemoryStorage class."""

    def test_save_and_load(self):
        """Test saving and loading checkpoint."""
        storage = MemoryStorage()
        checkpoint = Checkpoint(
            id="test-1",
            thread_id="thread-1",
            node_name="process",
            state={"value": 42},
        )

        storage.save(checkpoint)
        loaded = storage.load("test-1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state, {"value": 42})

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        storage = MemoryStorage()

        storage.save(Checkpoint(id="1", thread_id="t1", node_name="n", state={}))
        storage.save(Checkpoint(id="2", thread_id="t2", node_name="n", state={}))

        all_checkpoints = storage.list_checkpoints()
        self.assertEqual(len(all_checkpoints), 2)

        t1_checkpoints = storage.list_checkpoints(thread_id="t1")
        self.assertEqual(len(t1_checkpoints), 1)

    def test_delete(self):
        """Test deleting checkpoint."""
        storage = MemoryStorage()
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

        self.assertTrue(storage.delete("1"))
        self.assertIsNone(storage.load("1"))

    def test_delete_thread(self):
        """Test deleting thread."""
        storage = MemoryStorage()
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))
        storage.save(Checkpoint(id="2", thread_id="t", node_name="n", state={}))

        count = storage.delete_thread("t")
        self.assertEqual(count, 2)

    def test_clear(self):
        """Test clearing storage."""
        storage = MemoryStorage()
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

        storage.clear()
        self.assertEqual(len(storage.list_checkpoints()), 0)


class TestFileStorage(unittest.TestCase):
    """Tests for FileStorage class."""

    def test_save_and_load(self):
        """Test saving and loading checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            checkpoint = Checkpoint(
                id="test-1",
                thread_id="thread-1",
                node_name="process",
                state={"value": 42},
            )

            storage.save(checkpoint)
            loaded = storage.load("test-1")

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.state, {"value": 42})

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)

            storage.save(Checkpoint(id="1", thread_id="t1", node_name="n", state={}))
            storage.save(Checkpoint(id="2", thread_id="t2", node_name="n", state={}))

            all_checkpoints = storage.list_checkpoints()
            self.assertEqual(len(all_checkpoints), 2)

    def test_delete(self):
        """Test deleting checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

            self.assertTrue(storage.delete("1"))
            self.assertIsNone(storage.load("1"))

    def test_delete_thread(self):
        """Test deleting thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))
            storage.save(Checkpoint(id="2", thread_id="t", node_name="n", state={}))

            count = storage.delete_thread("t")
            self.assertEqual(count, 2)

    def test_clear(self):
        """Test clearing storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

            storage.clear()
            self.assertEqual(len(storage.list_checkpoints()), 0)


class TestSQLiteStorage(unittest.TestCase):
    """Tests for SQLiteStorage class."""

    def test_save_and_load(self):
        """Test saving and loading checkpoint."""
        storage = SQLiteStorage(":memory:")
        checkpoint = Checkpoint(
            id="test-1",
            thread_id="thread-1",
            node_name="process",
            state={"value": 42},
        )

        storage.save(checkpoint)
        loaded = storage.load("test-1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state, {"value": 42})

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        storage = SQLiteStorage(":memory:")

        storage.save(Checkpoint(id="1", thread_id="t1", node_name="n", state={}))
        storage.save(Checkpoint(id="2", thread_id="t2", node_name="n", state={}))

        all_checkpoints = storage.list_checkpoints()
        self.assertEqual(len(all_checkpoints), 2)

        t1_checkpoints = storage.list_checkpoints(thread_id="t1")
        self.assertEqual(len(t1_checkpoints), 1)

    def test_delete(self):
        """Test deleting checkpoint."""
        storage = SQLiteStorage(":memory:")
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

        self.assertTrue(storage.delete("1"))
        self.assertIsNone(storage.load("1"))

    def test_delete_thread(self):
        """Test deleting thread."""
        storage = SQLiteStorage(":memory:")
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))
        storage.save(Checkpoint(id="2", thread_id="t", node_name="n", state={}))

        count = storage.delete_thread("t")
        self.assertEqual(count, 2)

    def test_clear(self):
        """Test clearing storage."""
        storage = SQLiteStorage(":memory:")
        storage.save(Checkpoint(id="1", thread_id="t", node_name="n", state={}))

        storage.clear()
        self.assertEqual(len(storage.list_checkpoints()), 0)


if __name__ == "__main__":
    unittest.main()
