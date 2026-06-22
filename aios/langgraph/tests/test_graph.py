"""
Tests for StateGraph in the PHOENIX AIOS LangGraph framework.
"""

import unittest
from typing import TypedDict, Annotated
import operator

from ..core.graph import StateGraph, CompiledGraph
from ..core.constants import START, END
from ..core.state import AgentState, append_reducer


class TestState(TypedDict):
    """Test state type."""
    messages: Annotated[list[str], operator.add]
    value: int
    result: str


class TestStateGraph(unittest.TestCase):
    """Tests for StateGraph class."""

    def test_create_graph(self):
        """Test creating a graph."""
        graph = StateGraph(TestState)
        self.assertIsNotNone(graph)

    def test_add_node(self):
        """Test adding nodes."""
        graph = StateGraph(TestState)

        def node_fn(state):
            return {}

        graph.add_node("test", node_fn)
        self.assertIn("test", graph._nodes)

    def test_add_duplicate_node(self):
        """Test adding duplicate node raises error."""
        graph = StateGraph(TestState)

        def node_fn(state):
            return {}

        graph.add_node("test", node_fn)
        with self.assertRaises(ValueError):
            graph.add_node("test", node_fn)

    def test_add_reserved_node(self):
        """Test adding reserved node name raises error."""
        graph = StateGraph(TestState)

        def node_fn(state):
            return {}

        with self.assertRaises(ValueError):
            graph.add_node(START, node_fn)
        with self.assertRaises(ValueError):
            graph.add_node(END, node_fn)

    def test_add_edge(self):
        """Test adding edges."""
        graph = StateGraph(TestState)

        def node_a(state):
            return {}

        def node_b(state):
            return {}

        graph.add_node("a", node_a)
        graph.add_node("b", node_b)
        graph.add_edge(START, "a")
        graph.add_edge("a", "b")
        graph.add_edge("b", END)

        self.assertEqual(graph._entry_point, "a")
        self.assertIn("b", graph._exit_nodes)

    def test_add_conditional_edges(self):
        """Test adding conditional edges."""
        graph = StateGraph(TestState)

        def node_a(state):
            return {}

        def node_b(state):
            return {}

        def route(state):
            return "b" if state.get("value", 0) > 0 else END

        graph.add_node("a", node_a)
        graph.add_node("b", node_b)
        graph.add_edge(START, "a")
        graph.add_conditional_edges("a", route, ["b", END])

        self.assertIn("a", graph._conditional_edges)

    def test_compile_simple(self):
        """Test compiling a simple graph."""
        graph = StateGraph(TestState)

        def process(state):
            return {"result": "done"}

        graph.add_node("process", process)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()
        self.assertIsInstance(compiled, CompiledGraph)

    def test_compile_no_entry(self):
        """Test compiling without entry point raises error."""
        graph = StateGraph(TestState)

        def process(state):
            return {}

        graph.add_node("process", process)

        with self.assertRaises(ValueError):
            graph.compile()

    def test_compile_no_exit(self):
        """Test compiling without exit point raises error."""
        graph = StateGraph(TestState)

        def process(state):
            return {}

        graph.add_node("process", process)
        graph.add_edge(START, "process")

        with self.assertRaises(ValueError):
            graph.compile()

    def test_set_entry_point(self):
        """Test setting entry point."""
        graph = StateGraph(TestState)

        def process(state):
            return {}

        graph.add_node("process", process)
        graph.set_entry_point("process")
        self.assertEqual(graph._entry_point, "process")

    def test_set_finish_point(self):
        """Test setting finish point."""
        graph = StateGraph(TestState)

        def process(state):
            return {}

        graph.add_node("process", process)
        graph.set_finish_point("process")
        self.assertIn("process", graph._exit_nodes)


class TestCompiledGraph(unittest.TestCase):
    """Tests for CompiledGraph class."""

    def test_invoke_simple(self):
        """Test invoking a simple graph."""
        graph = StateGraph(TestState)

        def process(state):
            return {"result": "done", "value": state.get("value", 0) + 1}

        graph.add_node("process", process)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()
        result = compiled.invoke({"messages": [], "value": 0, "result": ""})

        self.assertEqual(result["result"], "done")
        self.assertEqual(result["value"], 1)

    def test_invoke_linear(self):
        """Test invoking a linear graph."""
        graph = StateGraph(TestState)

        def step1(state):
            return {"value": 1}

        def step2(state):
            return {"value": state["value"] + 1}

        def step3(state):
            return {"result": f"final={state['value']}"}

        graph.add_node("step1", step1)
        graph.add_node("step2", step2)
        graph.add_node("step3", step3)
        graph.add_edge(START, "step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "step3")
        graph.add_edge("step3", END)

        compiled = graph.compile()
        result = compiled.invoke({"messages": [], "value": 0, "result": ""})

        self.assertEqual(result["value"], 2)
        self.assertEqual(result["result"], "final=2")

    def test_invoke_conditional(self):
        """Test invoking a graph with conditional routing."""
        graph = StateGraph(TestState)

        def decide(state):
            return {"value": state.get("value", 0)}

        def positive(state):
            return {"result": "positive"}

        def negative(state):
            return {"result": "negative"}

        def route(state):
            return "positive" if state["value"] > 0 else "negative"

        graph.add_node("decide", decide)
        graph.add_node("positive", positive)
        graph.add_node("negative", negative)
        graph.add_edge(START, "decide")
        graph.add_conditional_edges("decide", route, ["positive", "negative"])
        graph.add_edge("positive", END)
        graph.add_edge("negative", END)

        compiled = graph.compile()

        # Test positive path
        result = compiled.invoke({"messages": [], "value": 5, "result": ""})
        self.assertEqual(result["result"], "positive")

        # Test negative path
        result = compiled.invoke({"messages": [], "value": -5, "result": ""})
        self.assertEqual(result["result"], "negative")

    def test_invoke_with_reducer(self):
        """Test invoking with state reducer."""
        from ..core.state import StateReducer, append_reducer

        reducer = StateReducer()
        reducer.register("messages", append_reducer)

        graph = StateGraph(TestState, reducer=reducer)

        def add_messages(state):
            return {"messages": ["hello", "world"]}

        graph.add_node("add", add_messages)
        graph.add_edge(START, "add")
        graph.add_edge("add", END)

        compiled = graph.compile()
        result = compiled.invoke({
            "messages": ["existing"],
            "value": 0,
            "result": "",
        })

        self.assertEqual(result["messages"], ["existing", "hello", "world"])

    def test_stream(self):
        """Test streaming graph execution."""
        graph = StateGraph(TestState)

        def step1(state):
            return {"value": 1}

        def step2(state):
            return {"value": state["value"] + 1}

        graph.add_node("step1", step1)
        graph.add_node("step2", step2)
        graph.add_edge(START, "step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", END)

        compiled = graph.compile()
        events = list(compiled.stream({"messages": [], "value": 0, "result": ""}))

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["node"], "step1")
        self.assertEqual(events[1]["node"], "step2")

    def test_get_graph_visualization(self):
        """Test graph visualization."""
        graph = StateGraph(TestState)
        graph.name = "test_graph"

        def process(state):
            return {}

        graph.add_node("process", process)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()
        viz = compiled.get_graph_visualization()

        self.assertIn("test_graph", viz)
        self.assertIn("process", viz)
        self.assertIn("Entry:", viz)

    def test_to_dict(self):
        """Test exporting graph as dict."""
        graph = StateGraph(TestState)
        graph.name = "test_graph"

        def process(state):
            return {}

        graph.add_node("process", process)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()
        d = compiled.to_dict()

        self.assertEqual(d["name"], "test_graph")
        self.assertIn("process", d["nodes"])
        self.assertEqual(d["entry_point"], "process")

    def test_max_iterations(self):
        """Test max iterations limit."""
        from ..core.types import GraphConfig

        config = GraphConfig(max_iterations=5)
        graph = StateGraph(TestState, config=config)

        def loop(state):
            return {"value": state.get("value", 0) + 1}

        def end_node(state):
            return {"result": "done"}

        graph.add_node("loop", loop)
        graph.add_node("end_node", end_node)
        graph.add_edge(START, "loop")
        graph.add_conditional_edges("loop", lambda s: "loop", ["loop", "end_node"])
        graph.add_edge("end_node", END)

        compiled = graph.compile()

        with self.assertRaises(RuntimeError):
            compiled.invoke({"messages": [], "value": 0, "result": ""})


if __name__ == "__main__":
    unittest.main()
