# PHOENIX AIOS LangGraph Framework

A stateful, graph-based agent orchestration system inspired by LangGraph's design patterns.

## Overview

This framework provides:

- **StateGraph**: Directed graph with typed state for agent workflows
- **Conditional Routing**: Dynamic path selection based on state inspection
- **Parallel Execution**: Fan-out/fan-in concurrent node execution
- **Checkpointing**: State persistence, recovery, and time-travel debugging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      StateGraph                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Node A  │───▶│  Node B  │───▶│  Node C  │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │               │               │                    │
│       ▼               ▼               ▼                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    State                              │ │
│  │  messages: []    result: ""    metadata: {}          │ │
│  └──────────────────────────────────────────────────────┘ │
│                          │                                 │
│                          ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Conditional Router                       │ │
│  │  - Rule-based routing                                │ │
│  │  - Priority evaluation                               │ │
│  │  - Strategy selection                                │ │
│  └──────────────────────────────────────────────────────┘ │
│                          │                                 │
│                          ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Parallel Executor                        │ │
│  │  - Fan-out dispatch                                  │ │
│  │  - Concurrent execution                              │ │
│  │  - Result aggregation                                │ │
│  └──────────────────────────────────────────────────────┘ │
│                          │                                 │
│                          ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │             Checkpoint Manager                        │ │
│  │  - State snapshots                                   │ │
│  │  - Thread management                                 │ │
│  │  - Time-travel debugging                             │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Define State

```python
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    current_node: str
    result: str
```

### 2. Build Graph

```python
from aios.langgraph import StateGraph, START, END

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("process", process_fn)
graph.add_node("validate", validate_fn)
graph.add_node("error_handler", error_handler_fn)

# Add edges
graph.add_edge(START, "process")
graph.add_conditional_edges(
    "process",
    lambda state: "validate" if state.get("result") else "error_handler",
    ["validate", "error_handler"],
)
graph.add_edge("validate", END)
graph.add_edge("error_handler", END)
```

### 3. Compile and Execute

```python
compiled = graph.compile()
result = compiled.invoke({
    "messages": [],
    "current_node": "",
    "result": "",
})
```

## Core Components

### StateGraph

The main graph construction API.

```python
graph = StateGraph(state_schema, reducer, config)

# Node management
graph.add_node("name", fn)
graph.set_entry_point("name")
graph.set_finish_point("name")

# Edge management
graph.add_edge(START, "node")
graph.add_edge("node", END)
graph.add_conditional_edges("source", condition_fn, ["target1", "target2"])
graph.add_parallel_edges("source", ["target1", "target2"])

# Compilation
compiled = graph.compile()
```

### Conditional Router

Dynamic routing based on state inspection.

```python
from aios.langgraph.routing import ConditionalRouter

router = ConditionalRouter(default_target=END)

# Add rules
router.add_rule(
    name="has_error",
    condition=lambda s: s.get("error") is not None,
    target="error_handler",
    priority=10,
)

# Route
decision = router.route(state, ["error_handler", "normal"])
```

### Parallel Executor

Fan-out/fan-in concurrent execution.

```python
from aios.langgraph.parallel import Send, parallel_execute

# Create sends
sends = [
    Send("processor_1", {"item": items[0]}),
    Send("processor_2", {"item": items[1]}),
    Send("processor_3", {"item": items[2]}),
]

# Execute in parallel
result = parallel_execute(sends, nodes)
```

### Checkpoint Manager

State persistence and recovery.

```python
from aios.langgraph.checkpoint import CheckpointManager, SQLiteStorage

storage = SQLiteStorage("checkpoints.db")
manager = CheckpointManager(storage)

# Create checkpoint
checkpoint = manager.create_checkpoint(
    thread_id="conv-1",
    node_name="process",
    state={"messages": ["hello"]},
)

# Restore checkpoint
restored = manager.load_checkpoint(checkpoint.id)

# Get history
history = manager.get_checkpoint_history(checkpoint.id)
```

## Routing Strategies

### Priority Router

Routes based on target priorities.

```python
from aios.langgraph.routing import PriorityRouter

router = PriorityRouter({
    "critical": 100,
    "normal": 50,
    "fallback": 0,
})
```

### Round Robin Router

Cycles through targets sequentially.

```python
from aios.langgraph.routing import RoundRobinRouter

router = RoundRobinRouter()
target = router.select(state, ["a", "b", "c"])
```

### Weighted Router

Probabilistic routing based on weights.

```python
from aios.langgraph.routing import WeightedRouter

router = WeightedRouter({
    "fast_path": 0.7,
    "slow_path": 0.2,
    "fallback": 0.1,
})
```

### State-Based Router

Routes based on state evaluation.

```python
from aios.langgraph.routing import StateBasedRouter

router = StateBasedRouter()
router.add_scorer("fast", lambda s: 1.0 if s.get("complexity", 0) < 0.5 else 0.0)
router.add_scorer("thorough", lambda s: 1.0 if s.get("complexity", 0) >= 0.5 else 0.0)
```

## Aggregation Strategies

### Merge

Deep merge all results.

```python
from aios.langgraph.parallel import aggregate_results, AggregateStrategy

merged = aggregate_results(results, AggregateStrategy.MERGE)
```

### Append

Append all results to lists.

```python
appended = aggregate_results(results, AggregateStrategy.APPEND)
```

### First / Last

Use first or last successful result.

```python
first = aggregate_results(results, AggregateStrategy.FIRST)
last = aggregate_results(results, AggregateStrategy.LAST)
```

## Checkpoint Storage

### Memory Storage

In-memory storage for testing.

```python
from aios.langgraph.checkpoint import MemoryStorage

storage = MemoryStorage()
```

### File Storage

File-based persistence.

```python
from aios.langgraph.checkpoint import FileStorage

storage = FileStorage("/path/to/checkpoints")
```

### SQLite Storage

SQLite database storage.

```python
from aios.langgraph.checkpoint import SQLiteStorage

storage = SQLiteStorage("checkpoints.db")
```

## Examples

### Simple Agent Workflow

```python
from typing import TypedDict, Annotated
import operator
from aios.langgraph import StateGraph, START, END

class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    result: str

def think(state):
    # Analyze the problem
    return {"result": "analyzed"}

def act(state):
    # Take action
    return {"result": "done", "messages": [{"role": "assistant", "content": "Done!"}]}

graph = StateGraph(AgentState)
graph.add_node("think", think)
graph.add_node("act", act)
graph.add_edge(START, "think")
graph.add_edge("think", "act")
graph.add_edge("act", END)

compiled = graph.compile()
result = compiled.invoke({"messages": [], "result": ""})
```

### Multi-Agent Collaboration

```python
from aios.langgraph import StateGraph, START, END
from aios.langgraph.parallel import Send

class MultiAgentState(TypedDict):
    task: str
    results: Annotated[list[str], operator.add]

def researcher(state):
    return {"results": [f"Research on: {state['task']}"]}

def writer(state):
    return {"results": [f"Written about: {state['task']}"]}

def editor(state):
    return {"results": [f"Edited: {', '.join(state['results'])}"]}

def dispatch(state):
    return [
        Send("researcher", {"task": state["task"]}),
        Send("writer", {"task": state["task"]}),
    ]

graph = StateGraph(MultiAgentState)
graph.add_node("dispatch", dispatch)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
graph.add_node("editor", editor)

graph.add_edge(START, "dispatch")
graph.add_parallel_edges("dispatch", ["researcher", "writer"])
graph.add_edge("researcher", "editor")
graph.add_edge("writer", "editor")
graph.add_edge("editor", END)

compiled = graph.compile()
result = compiled.invoke({"task": "AI agents", "results": []})
```

### Checkpoint Recovery

```python
from aios.langgraph import StateGraph, START, END
from aios.langgraph.checkpoint import CheckpointManager, SQLiteStorage

# Setup with checkpointing
storage = SQLiteStorage("agent.db")
checkpoint_manager = CheckpointManager(storage)

def process(state):
    # Create checkpoint
    checkpoint_manager.create_checkpoint(
        thread_id=state.get("thread_id", "default"),
        node_name="process",
        state=state,
    )
    return {"result": "processed"}

graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)

compiled = graph.compile()

# Run with thread
result = compiled.invoke({
    "messages": [],
    "result": "",
    "thread_id": "conv-123",
})

# Later: restore from checkpoint
latest = checkpoint_manager.get_latest_checkpoint("conv-123")
if latest:
    restored_state = latest.state
    # Continue from restored state
```

## Testing

Run all tests:

```bash
python -m pytest aios/langgraph/tests/
```

Run specific test suite:

```bash
python -m pytest aios/langgraph/tests/test_graph.py
python -m pytest aios/langgraph/tests/test_router.py
python -m pytest aios/langgraph/tests/test_checkpoint.py
python -m pytest aios/langgraph/tests/test_parallel.py
```

## API Reference

### Core

- `StateGraph(state_schema, reducer, config)` - Graph construction
- `CompiledGraph` - Executable graph
- `AgentState` - Base state class
- `StateReducer` - State merge behavior

### Routing

- `ConditionalRouter(default_target, strategy)` - Conditional routing
- `RoutingDecision` - Routing decision record
- `RoutingRule` - Routing rule definition
- `PriorityRouter` - Priority-based routing
- `RoundRobinRouter` - Round-robin routing
- `WeightedRouter` - Weighted routing
- `StateBasedRouter` - State-based routing

### Parallel

- `Send(node, state, metadata)` - Parallel dispatch
- `ParallelExecutor(config, reducer)` - Parallel execution
- `FanOutResult` - Parallel execution result
- `MapReduceExecutor` - Map-reduce pattern

### Checkpoint

- `CheckpointManager(storage, config)` - Checkpoint management
- `Checkpoint` - Checkpoint data
- `MemoryStorage` - In-memory storage
- `FileStorage` - File-based storage
- `SQLiteStorage` - SQLite storage

## Design Principles

1. **Immutability**: State is never mutated; new state objects are created
2. **Type Safety**: Full type annotations for all public APIs
3. **Composability**: Small, focused components that combine well
4. **Testability**: All components are easily testable
5. **Observability**: Comprehensive logging and statistics

## License

Part of the PHOENIX AIOS framework.
