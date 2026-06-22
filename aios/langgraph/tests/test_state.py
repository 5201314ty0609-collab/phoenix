"""
Tests for state management in the PHOENIX AIOS LangGraph framework.
"""

import unittest
from datetime import datetime

from ..core.state import (
    AgentState,
    StateReducer,
    append_reducer,
    replace_reducer,
    merge_reducer,
    max_reducer,
    min_reducer,
    union_reducer,
    increment_reducer,
    merge_dicts,
    apply_reducer,
    validate_state,
    create_default_reducer,
)


class TestAgentState(unittest.TestCase):
    """Tests for AgentState class."""

    def test_create_default(self):
        """Test creating default state."""
        state = AgentState()
        self.assertEqual(state.messages, [])
        self.assertEqual(state.current_node, "")
        self.assertEqual(state.execution_history, [])
        self.assertIsNone(state.error)
        self.assertIsInstance(state.created_at, datetime)

    def test_to_dict(self):
        """Test converting state to dict."""
        state = AgentState(
            messages=[{"role": "user", "content": "hello"}],
            current_node="test",
        )
        d = state.to_dict()
        self.assertEqual(d["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(d["current_node"], "test")
        self.assertIn("created_at", d)

    def test_from_dict(self):
        """Test creating state from dict."""
        now = datetime.now()
        d = {
            "messages": [{"role": "user", "content": "hello"}],
            "current_node": "test",
            "execution_history": [],
            "error": None,
            "metadata": {"key": "value"},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        state = AgentState.from_dict(d)
        self.assertEqual(state.messages, [{"role": "user", "content": "hello"}])
        self.assertEqual(state.current_node, "test")
        self.assertEqual(state.metadata, {"key": "value"})

    def test_update_immutable(self):
        """Test that update returns new instance."""
        state1 = AgentState(current_node="a")
        state2 = state1.update(current_node="b")

        self.assertEqual(state1.current_node, "a")
        self.assertEqual(state2.current_node, "b")
        self.assertIsNot(state1, state2)

    def test_add_message(self):
        """Test adding message to state."""
        state = AgentState()
        new_state = state.add_message("user", "hello")

        self.assertEqual(len(new_state.messages), 1)
        self.assertEqual(new_state.messages[0]["role"], "user")
        self.assertEqual(new_state.messages[0]["content"], "hello")
        self.assertEqual(len(state.messages), 0)  # Original unchanged

    def test_record_execution(self):
        """Test recording node execution."""
        state = AgentState()
        new_state = state.record_execution("node1", {"result": "ok"})

        self.assertEqual(len(new_state.execution_history), 1)
        self.assertEqual(new_state.execution_history[0]["node"], "node1")
        self.assertEqual(new_state.current_node, "node1")

    def test_set_error(self):
        """Test setting error state."""
        state = AgentState()
        error = ValueError("test error")
        new_state = state.set_error(error)

        self.assertIsNotNone(new_state.error)
        self.assertEqual(new_state.error["type"], "ValueError")
        self.assertEqual(new_state.error["message"], "test error")
        self.assertIsNone(state.error)

    def test_clear_error(self):
        """Test clearing error state."""
        state = AgentState()
        state = state.set_error(ValueError("error"))
        new_state = state.clear_error()

        self.assertIsNone(new_state.error)


class TestStateReducer(unittest.TestCase):
    """Tests for StateReducer class."""

    def test_register_and_get(self):
        """Test registering and getting reducers."""
        reducer = StateReducer()
        reducer.register("messages", append_reducer)

        self.assertEqual(reducer.get("messages"), append_reducer)

    def test_default_reducer(self):
        """Test default reducer behavior."""
        reducer = StateReducer()
        self.assertEqual(reducer.get("unknown"), replace_reducer)

    def test_apply_with_reducer(self):
        """Test applying reducer to merge state."""
        reducer = StateReducer()
        reducer.register("messages", append_reducer)

        current = {"messages": ["a"], "value": 1}
        update = {"messages": ["b"], "value": 2}

        result = reducer.apply(current, update)
        self.assertEqual(result["messages"], ["a", "b"])
        self.assertEqual(result["value"], 2)

    def test_apply_without_reducer(self):
        """Test applying without registered reducer (replace)."""
        reducer = StateReducer()

        current = {"value": 1}
        update = {"value": 2}

        result = reducer.apply(current, update)
        self.assertEqual(result["value"], 2)


class TestReducers(unittest.TestCase):
    """Tests for built-in reducer functions."""

    def test_append_reducer(self):
        """Test append reducer."""
        self.assertEqual(append_reducer([1, 2], [3, 4]), [1, 2, 3, 4])
        self.assertEqual(append_reducer(None, [1, 2]), [1, 2])
        self.assertEqual(append_reducer([1, 2], None), [1, 2])

    def test_replace_reducer(self):
        """Test replace reducer."""
        self.assertEqual(replace_reducer(1, 2), 2)
        self.assertEqual(replace_reducer("old", "new"), "new")

    def test_merge_reducer(self):
        """Test merge reducer."""
        current = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}, "e": 4}
        result = merge_reducer(current, update)
        self.assertEqual(result, {"a": 1, "b": {"c": 2, "d": 3}, "e": 4})

    def test_max_reducer(self):
        """Test max reducer."""
        self.assertEqual(max_reducer(1, 2), 2)
        self.assertEqual(max_reducer(5, 3), 5)
        self.assertEqual(max_reducer(None, 1), 1)

    def test_min_reducer(self):
        """Test min reducer."""
        self.assertEqual(min_reducer(1, 2), 1)
        self.assertEqual(min_reducer(5, 3), 3)
        self.assertEqual(min_reducer(None, 1), 1)

    def test_union_reducer(self):
        """Test union reducer."""
        self.assertEqual(union_reducer({1, 2}, {2, 3}), {1, 2, 3})

    def test_increment_reducer(self):
        """Test increment reducer."""
        self.assertEqual(increment_reducer(1, 2), 3)
        self.assertEqual(increment_reducer(0, 5), 5)
        self.assertEqual(increment_reducer(None, 1), 1)


class TestUtilities(unittest.TestCase):
    """Tests for state utility functions."""

    def test_merge_dicts(self):
        """Test deep merge of dicts."""
        d1 = {"a": 1, "b": {"c": 2}}
        d2 = {"b": {"d": 3}, "e": 4}
        result = merge_dicts(d1, d2)
        self.assertEqual(result, {"a": 1, "b": {"c": 2, "d": 3}, "e": 4})

    def test_apply_reducer(self):
        """Test applying reducers to merge state."""
        current = {"messages": ["a"], "score": 0.5}
        update = {"messages": ["b"], "score": 0.8}
        reducers = {"messages": append_reducer, "score": max_reducer}

        result = apply_reducer(current, update, reducers)
        self.assertEqual(result["messages"], ["a", "b"])
        self.assertEqual(result["score"], 0.8)

    def test_create_default_reducer(self):
        """Test creating default reducer."""
        reducer = create_default_reducer()
        self.assertIn("messages", reducer.keys())
        self.assertIn("history", reducer.keys())


if __name__ == "__main__":
    unittest.main()
