"""
Tests for parallel execution in the PHOENIX AIOS LangGraph framework.
"""

import unittest
import time

from ..parallel.executor import (
    Send,
    FanOutResult,
    ParallelConfig,
    ParallelExecutor,
    parallel_execute,
    MapReduceExecutor,
)
from ..parallel.aggregators import (
    aggregate_results,
    merge_states,
    append_states,
    reduce_results,
    aggregate_messages,
    aggregate_scores,
    aggregate_errors,
    AggregateStrategy,
)
from ..core.state import StateReducer, append_reducer, max_reducer


class TestSend(unittest.TestCase):
    """Tests for Send class."""

    def test_create_send(self):
        """Test creating a Send."""
        send = Send(
            node="processor",
            state={"item": "data"},
        )
        self.assertEqual(send.node, "processor")
        self.assertEqual(send.state, {"item": "data"})

    def test_send_with_metadata(self):
        """Test Send with metadata."""
        send = Send(
            node="processor",
            state={"item": "data"},
            metadata={"priority": "high"},
        )
        self.assertEqual(send.metadata, {"priority": "high"})

    def test_send_repr(self):
        """Test Send string representation."""
        send = Send(node="processor", state={"item": "data"})
        repr_str = repr(send)
        self.assertIn("processor", repr_str)


class TestFanOutResult(unittest.TestCase):
    """Tests for FanOutResult class."""

    def test_create_result(self):
        """Test creating a FanOutResult."""
        result = FanOutResult()
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)

    def test_all_succeeded(self):
        """Test all_succeeded property."""
        result = FanOutResult(
            results=[("n1", {}), ("n2", {})],
            success_count=2,
            failure_count=0,
        )
        self.assertTrue(result.all_succeeded)

    def test_all_failed(self):
        """Test all_failed property."""
        result = FanOutResult(
            errors=[("n1", Exception("fail"))],
            success_count=0,
            failure_count=1,
        )
        self.assertTrue(result.all_failed)

    def test_get_merged_state(self):
        """Test merging results."""
        result = FanOutResult(
            results=[
                ("n1", {"a": 1}),
                ("n2", {"b": 2}),
            ],
        )
        merged = result.get_merged_state()
        self.assertEqual(merged, {"a": 1, "b": 2})

    def test_get_merged_state_with_reducer(self):
        """Test merging results with reducer."""
        reducer = StateReducer()
        reducer.register("messages", append_reducer)

        result = FanOutResult(
            results=[
                ("n1", {"messages": ["a"]}),
                ("n2", {"messages": ["b"]}),
            ],
        )
        merged = result.get_merged_state(reducer)
        self.assertEqual(merged["messages"], ["a", "b"])


class TestParallelExecutor(unittest.TestCase):
    """Tests for ParallelExecutor class."""

    def test_create_executor(self):
        """Test creating executor."""
        executor = ParallelExecutor()
        self.assertIsNotNone(executor)

    def test_execute_simple(self):
        """Test simple parallel execution."""
        def process_a(state):
            return {"result_a": "done"}

        def process_b(state):
            return {"result_b": "done"}

        sends = [
            Send("process_a", {"input": "a"}),
            Send("process_b", {"input": "b"}),
        ]
        nodes = {
            "process_a": process_a,
            "process_b": process_b,
        }

        executor = ParallelExecutor()
        result = executor.execute(sends, nodes)

        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.failure_count, 0)
        self.assertTrue(result.all_succeeded)

    def test_execute_with_error(self):
        """Test parallel execution with error."""
        def process_ok(state):
            return {"result": "ok"}

        def process_fail(state):
            raise ValueError("test error")

        sends = [
            Send("process_ok", {}),
            Send("process_fail", {}),
        ]
        nodes = {
            "process_ok": process_ok,
            "process_fail": process_fail,
        }

        config = ParallelConfig(collect_errors=True)
        executor = ParallelExecutor(config=config)
        result = executor.execute(sends, nodes)

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)
        self.assertEqual(len(result.errors), 1)

    def test_execute_fail_fast(self):
        """Test parallel execution with fail_fast."""
        def process_ok(state):
            time.sleep(0.1)
            return {"result": "ok"}

        def process_fail(state):
            raise ValueError("test error")

        sends = [
            Send("process_ok", {}),
            Send("process_fail", {}),
        ]
        nodes = {
            "process_ok": process_ok,
            "process_fail": process_fail,
        }

        config = ParallelConfig(fail_fast=True)
        executor = ParallelExecutor(config=config)

        with self.assertRaises(RuntimeError):
            executor.execute(sends, nodes)

    def test_execute_empty(self):
        """Test executing with no sends."""
        executor = ParallelExecutor()
        result = executor.execute([], {})

        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.failure_count, 0)

    def test_execute_invalid_node(self):
        """Test executing with invalid node."""
        sends = [Send("nonexistent", {})]
        nodes = {}

        executor = ParallelExecutor()
        with self.assertRaises(ValueError):
            executor.execute(sends, nodes)

    def test_convenience_function(self):
        """Test parallel_execute convenience function."""
        def process_a(state):
            return {"a": 1}

        def process_b(state):
            return {"b": 2}

        sends = [
            Send("process_a", {}),
            Send("process_b", {}),
        ]
        nodes = {
            "process_a": process_a,
            "process_b": process_b,
        }

        result = parallel_execute(sends, nodes)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_execution_count(self):
        """Test execution count tracking."""
        def process(state):
            return {}

        sends = [Send("process", {})]
        nodes = {"process": process}

        executor = ParallelExecutor()
        executor.execute(sends, nodes)
        executor.execute(sends, nodes)

        self.assertEqual(executor.execution_count, 2)


class TestMapReduceExecutor(unittest.TestCase):
    """Tests for MapReduceExecutor class."""

    def test_map_reduce(self):
        """Test map-reduce execution."""
        def process_item(state):
            item = state["item"]
            return {"result": item * 2}

        executor = MapReduceExecutor()
        result = executor.execute(
            items=[1, 2, 3, 4, 5],
            map_fn=process_item,
        )

        self.assertIn("results", result)
        self.assertEqual(sorted(result["results"]), [2, 4, 6, 8, 10])

    def test_map_reduce_with_reduce(self):
        """Test map-reduce with reduce function."""
        def process_item(state):
            return {"result": state["item"]}

        def combine(state):
            return {"total": sum(state["results"])}

        executor = MapReduceExecutor()
        result = executor.execute(
            items=[1, 2, 3, 4, 5],
            map_fn=process_item,
            reduce_fn=combine,
        )

        self.assertEqual(result["total"], 15)


class TestAggregators(unittest.TestCase):
    """Tests for aggregator functions."""

    def test_aggregate_merge(self):
        """Test merge aggregation."""
        results = [
            {"a": 1, "b": {"x": 1}},
            {"b": {"y": 2}, "c": 3},
        ]
        merged = aggregate_results(results, AggregateStrategy.MERGE)
        self.assertEqual(merged, {"a": 1, "b": {"x": 1, "y": 2}, "c": 3})

    def test_aggregate_append(self):
        """Test append aggregation."""
        results = [
            {"messages": ["a"]},
            {"messages": ["b"]},
        ]
        appended = aggregate_results(results, AggregateStrategy.APPEND)
        self.assertEqual(appended["messages"], ["a", "b"])

    def test_aggregate_first(self):
        """Test first aggregation."""
        results = [
            {"value": 1},
            {"value": 2},
        ]
        first = aggregate_results(results, AggregateStrategy.FIRST)
        self.assertEqual(first, {"value": 1})

    def test_aggregate_last(self):
        """Test last aggregation."""
        results = [
            {"value": 1},
            {"value": 2},
        ]
        last = aggregate_results(results, AggregateStrategy.LAST)
        self.assertEqual(last, {"value": 2})

    def test_aggregate_custom(self):
        """Test custom aggregation."""
        results = [
            {"value": 1},
            {"value": 2},
        ]

        def custom_fn(results):
            return {"sum": sum(r["value"] for r in results)}

        custom = aggregate_results(
            results,
            AggregateStrategy.CUSTOM,
            custom_fn=custom_fn,
        )
        self.assertEqual(custom, {"sum": 3})

    def test_merge_states(self):
        """Test merge_states function."""
        states = [
            {"a": 1, "b": {"x": 1}},
            {"b": {"y": 2}, "c": 3},
        ]
        merged = merge_states(states)
        self.assertEqual(merged, {"a": 1, "b": {"x": 1, "y": 2}, "c": 3})

    def test_append_states(self):
        """Test append_states function."""
        states = [
            {"a": 1, "b": [1, 2]},
            {"a": 2, "b": [3, 4]},
        ]
        appended = append_states(states)
        self.assertEqual(appended["a"], [1, 2])
        self.assertEqual(appended["b"], [1, 2, 3, 4])

    def test_reduce_results(self):
        """Test reduce_results function."""
        results = [
            {"score": 0.5, "messages": ["a"]},
            {"score": 0.8, "messages": ["b"]},
        ]
        reducers = {
            "score": max_reducer,
            "messages": append_reducer,
        }
        reduced = reduce_results(results, reducers)
        self.assertEqual(reduced["score"], 0.8)
        self.assertEqual(reduced["messages"], ["a", "b"])

    def test_aggregate_messages(self):
        """Test message aggregation."""
        results = [
            {"messages": [{"role": "user", "content": "a"}]},
            {"messages": [{"role": "assistant", "content": "b"}]},
        ]
        messages = aggregate_messages(results)
        self.assertEqual(len(messages), 2)

    def test_aggregate_scores_max(self):
        """Test score aggregation (max)."""
        results = [
            {"score": 0.5},
            {"score": 0.8},
            {"score": 0.3},
        ]
        max_score = aggregate_scores(results, strategy="max")
        self.assertEqual(max_score, 0.8)

    def test_aggregate_scores_avg(self):
        """Test score aggregation (avg)."""
        results = [
            {"score": 0.5},
            {"score": 0.8},
            {"score": 0.3},
        ]
        avg_score = aggregate_scores(results, strategy="avg")
        self.assertAlmostEqual(avg_score, 0.533, places=2)

    def test_aggregate_errors(self):
        """Test error aggregation."""
        results = [
            {"error": None},
            {"error": {"type": "ValueError", "message": "test"}},
            {"error": None},
        ]
        errors = aggregate_errors(results)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["type"], "ValueError")


if __name__ == "__main__":
    unittest.main()
