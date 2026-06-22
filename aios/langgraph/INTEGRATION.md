# PHOENIX AIOS LangGraph Integration Guide

This guide explains how to integrate the LangGraph framework with existing PHOENIX systems.

## Overview

The LangGraph framework provides:

1. **StateGraph** - Directed graph for agent workflows
2. **Conditional Router** - Dynamic routing based on state
3. **Parallel Executor** - Fan-out/fan-in concurrent execution
4. **Checkpoint Manager** - State persistence and recovery

## Integration Points

### 1. With PHOENIX State System

The LangGraph framework integrates with the existing PHOENIX state system:

```python
from aios.state.state_types import StateManager
from aios.langgraph import StateGraph, START, END
from aios.langgraph.checkpoint import CheckpointManager, SQLiteStorage

# Create state manager
state_manager = StateManager()

# Create checkpoint manager
storage = SQLiteStorage("checkpoints.db")
checkpoint_manager = CheckpointManager(storage)

# Build graph with state integration
graph = StateGraph(dict)

def process(state):
    # Use state manager for complex state operations
    state_manager.update("current", state)
    return {"result": "processed"}

graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)

compiled = graph.compile()
```

### 2. With PHOENIX Event Bus

Integrate with the event bus for event-driven workflows:

```python
from aios.event_bus import EventBus
from aios.langgraph import StateGraph, START, END
from aios.langgraph.parallel import Send

event_bus = EventBus()

def event_handler(state):
    # Emit events during graph execution
    event_bus.emit("node_executed", {
        "node": "handler",
        "state": state,
    })
    return {"handled": True}

graph = StateGraph(dict)
graph.add_node("handler", event_handler)
graph.add_edge(START, "handler")
graph.add_edge("handler", END)
```

### 3. With PHOENIX Memory System

Integrate with the memory system for context-aware workflows:

```python
from aios.memory import MemoryManager
from aios.langgraph import StateGraph, START, END

memory_manager = MemoryManager()

def recall_context(state):
    # Recall relevant memories
    query = state.get("query", "")
    memories = memory_manager.search(query)

    return {
        "context": [m.content for m in memories],
        "has_context": len(memories) > 0,
    }

def generate_response(state):
    context = state.get("context", [])
    return {
        "response": f"Based on {len(context)} memories...",
    }

graph = StateGraph(dict)
graph.add_node("recall", recall_context)
graph.add_node("generate", generate_response)
graph.add_edge(START, "recall")
graph.add_edge("recall", "generate")
graph.add_edge("generate", END)
```

### 4. With PHOENIX Agent System

Integrate with existing agent definitions:

```python
from aios.agent import Agent, AgentConfig
from aios.langgraph import StateGraph, START, END
from aios.langgraph.parallel import Send, parallel_execute

# Define agents
researcher = Agent(AgentConfig(name="researcher", role="research"))
writer = Agent(AgentConfig(name="writer", role="writing"))
editor = Agent(AgentConfig(name="editor", role="editing"))

# Create agent nodes
def research_node(state):
    result = researcher.execute(state["task"])
    return {"research": result}

def write_node(state):
    result = writer.execute(state["research"])
    return {"draft": result}

def edit_node(state):
    result = editor.execute(state["draft"])
    return {"final": result}

# Build multi-agent graph
graph = StateGraph(dict)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_node("edit", edit_node)

graph.add_edge(START, "research")
graph.add_edge("research", "write")
graph.add_edge("write", "edit")
graph.add_edge("edit", END)

compiled = graph.compile()
```

## Common Patterns

### Pattern 1: Human-in-the-Loop

```python
from aios.langgraph import StateGraph, START, END
from aios.langgraph.checkpoint import CheckpointManager

checkpoint_manager = CheckpointManager()

def needs_approval(state):
    return state.get("needs_approval", False)

def wait_for_approval(state):
    # Create checkpoint and pause
    checkpoint_manager.create_checkpoint(
        thread_id=state["thread_id"],
        node_name="wait_approval",
        state=state,
    )
    return {"status": "waiting"}

def continue_processing(state):
    return {"status": "approved"}

graph = StateGraph(dict)
graph.add_node("check", lambda s: s)
graph.add_node("wait", wait_for_approval)
graph.add_node("continue", continue_processing)

graph.add_edge(START, "check")
graph.add_conditional_edges(
    "check",
    lambda s: "wait" if needs_approval(s) else "continue",
    ["wait", "continue"],
)
graph.add_edge("wait", END)
graph.add_edge("continue", END)
```

### Pattern 2: Error Recovery

```python
from aios.langgraph import StateGraph, START, END

def process(state):
    try:
        # Risky operation
        result = risky_operation(state)
        return {"result": result, "error": None}
    except Exception as e:
        return {"error": str(e)}

def handle_error(state):
    return {
        "result": "fallback result",
        "error_handled": True,
    }

def check_error(state):
    return state.get("error") is not None

graph = StateGraph(dict)
graph.add_node("process", process)
graph.add_node("error_handler", handle_error)

graph.add_edge(START, "process")
graph.add_conditional_edges(
    "process",
    lambda s: "error_handler" if check_error(s) else END,
    ["error_handler", END],
)
graph.add_edge("error_handler", END)
```

### Pattern 3: Parallel Processing with Aggregation

```python
from aios.langgraph import StateGraph, START, END
from aios.langgraph.parallel import Send
from aios.langgraph.core.state import StateReducer, append_reducer

reducer = StateReducer()
reducer.register("results", append_reducer)

def dispatch(state):
    items = state.get("items", [])
    return [
        Send("processor", {"item": item, "index": i})
        for i, item in enumerate(items)
    ]

def process(state):
    item = state.get("item")
    return {"results": [f"Processed: {item}"]}

def aggregate(state):
    results = state.get("results", [])
    return {"summary": f"Processed {len(results)} items"}

graph = StateGraph(dict, reducer=reducer)
graph.add_node("dispatch", dispatch)
graph.add_node("processor", process)
graph.add_node("aggregate", aggregate)

graph.add_edge(START, "dispatch")
graph.add_parallel_edges("dispatch", ["processor"])
graph.add_edge("processor", "aggregate")
graph.add_edge("aggregate", END)
```

### Pattern 4: Checkpoint Recovery

```python
from aios.langgraph import StateGraph, START, END
from aios.langgraph.checkpoint import CheckpointManager, SQLiteStorage

storage = SQLiteStorage("workflow.db")
checkpoint_manager = CheckpointManager(storage)

def save_checkpoint(state):
    checkpoint_manager.create_checkpoint(
        thread_id=state["thread_id"],
        node_name="checkpoint",
        state=state,
    )
    return {"checkpointed": True}

def process(state):
    return {"step": state.get("step", 0) + 1}

graph = StateGraph(dict)
graph.add_node("save", save_checkpoint)
graph.add_node("process", process)

graph.add_edge(START, "save")
graph.add_edge("save", "process")
graph.add_edge("process", END)

# Resume from checkpoint
def resume(thread_id: str):
    latest = checkpoint_manager.get_latest_checkpoint(thread_id)
    if latest:
        compiled = graph.compile()
        return compiled.invoke(latest.state)
    return None
```

## Testing Integration

### Unit Tests

```python
import unittest
from aios.langgraph import StateGraph, START, END

class TestIntegration(unittest.TestCase):
    def test_basic_workflow(self):
        graph = StateGraph(dict)
        graph.add_node("process", lambda s: {"result": "done"})
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()
        result = compiled.invoke({})

        self.assertEqual(result["result"], "done")

    def test_conditional_routing(self):
        graph = StateGraph(dict)
        graph.add_node("decide", lambda s: s)
        graph.add_node("a", lambda s: {"path": "a"})
        graph.add_node("b", lambda s: {"path": "b"})

        graph.add_edge(START, "decide")
        graph.add_conditional_edges(
            "decide",
            lambda s: "a" if s.get("use_a") else "b",
            ["a", "b"],
        )
        graph.add_edge("a", END)
        graph.add_edge("b", END)

        compiled = graph.compile()

        result = compiled.invoke({"use_a": True})
        self.assertEqual(result["path"], "a")

        result = compiled.invoke({"use_a": False})
        self.assertEqual(result["path"], "b")
```

### Integration Tests

```python
import unittest
from aios.langgraph import StateGraph, START, END
from aios.langgraph.checkpoint import CheckpointManager, SQLiteStorage

class TestCheckpointIntegration(unittest.TestCase):
    def test_checkpoint_recovery(self):
        storage = SQLiteStorage(":memory:")
        manager = CheckpointManager(storage)

        graph = StateGraph(dict)
        graph.add_node(
            "process",
            lambda s: {"step": s.get("step", 0) + 1},
        )
        graph.add_edge(START, "process")
        graph.add_edge("process", END)

        compiled = graph.compile()

        # First run
        result1 = compiled.invoke({"step": 0, "thread_id": "test"})
        manager.create_checkpoint("test", "process", result1)

        # Restore and continue
        checkpoint = manager.get_latest_checkpoint("test")
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint.state["step"], 1)
```

## Performance Considerations

### 1. Checkpoint Frequency

Balance between durability and performance:

```python
from aios.langgraph.checkpoint import CheckpointConfig

# High durability (checkpoint every node)
config = CheckpointConfig(
    auto_checkpoint=True,
    checkpoint_interval=1,
)

# Balanced (checkpoint every 10 nodes)
config = CheckpointConfig(
    auto_checkpoint=True,
    checkpoint_interval=10,
)

# High performance (manual checkpoints only)
config = CheckpointConfig(
    auto_checkpoint=False,
)
```

### 2. Parallel Execution Limits

Control concurrency:

```python
from aios.langgraph.parallel import ParallelConfig

# Conservative
config = ParallelConfig(max_workers=2)

# Balanced
config = ParallelConfig(max_workers=5)

# Aggressive
config = ParallelConfig(max_workers=10)
```

### 3. Storage Selection

Choose appropriate storage:

```python
from aios.langgraph.checkpoint import (
    MemoryStorage,    # Fast, ephemeral
    FileStorage,      # Moderate, persistent
    SQLiteStorage,    # Robust, queryable
)

# For testing
storage = MemoryStorage()

# For simple persistence
storage = FileStorage("/path/to/checkpoints")

# For production
storage = SQLiteStorage("checkpoints.db")
```

## Migration Guide

### From Manual State Management

```python
# Before
state = {"messages": [], "result": ""}
state["messages"].append({"role": "user", "content": "hello"})
result = process(state)
state["result"] = result

# After
from aios.langgraph import StateGraph, START, END
from aios.langgraph.core.state import StateReducer, append_reducer

reducer = StateReducer()
reducer.register("messages", append_reducer)

graph = StateGraph(dict, reducer=reducer)
graph.add_node("process", lambda s: {"result": process(s)})
graph.add_edge(START, "process")
graph.add_edge("process", END)

compiled = graph.compile()
state = compiled.invoke({"messages": [{"role": "user", "content": "hello"}]})
```

### From Sequential Processing

```python
# Before
result1 = step1(input)
result2 = step2(result1)
result3 = step3(result2)

# After
graph = StateGraph(dict)
graph.add_node("step1", lambda s: {"r1": step1(s["input"])})
graph.add_node("step2", lambda s: {"r2": step2(s["r1"])})
graph.add_node("step3", lambda s: {"r3": step3(s["r2"])})

graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", "step3")
graph.add_edge("step3", END)

compiled = graph.compile()
result = compiled.invoke({"input": data})
```

## Best Practices

1. **Keep nodes focused** - Each node should do one thing well
2. **Use reducers for lists** - Prevents data loss in parallel execution
3. **Checkpoint critical state** - Enables recovery from failures
4. **Limit parallelism** - Too many concurrent nodes can overwhelm resources
5. **Validate state** - Ensure state schema matches expectations
6. **Handle errors gracefully** - Use conditional edges for error paths
7. **Test thoroughly** - Unit test nodes, integration test graphs
