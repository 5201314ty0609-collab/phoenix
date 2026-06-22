# PHOENIX AIOS LangChain Integration Architecture

## Overview

The PHOENIX AIOS LangChain Integration provides a comprehensive framework for building LLM-powered applications. It follows PHOENIX design principles: immutability, type safety, and composability.

## Core Design Principles

### 1. Immutability

All data structures are frozen dataclasses. Modifications create new instances:

```python
@dataclass(frozen=True)
class ToolInput:
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def with_context(self, **kwargs: Any) -> ToolInput:
        """Create new input with additional context."""
        from dataclasses import replace
        return replace(self, context={**self.context, **kwargs})
```

### 2. Type Safety

Full type annotations throughout:

```python
def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
    """Execute with typed input and output."""
    pass
```

### 3. Composability

Components can be combined using operators:

```python
chain = (
    LCELChain("transform")
    | step1
    | step2
    | step3
)
```

### 4. Error Handling

Comprehensive error handling with typed results:

```python
@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
```

## Module Architecture

### Chains Module

```
chains/
├── base.py          # Chain, ChainStep, StepResult
├── lcel.py          # LCELChain, LCELStep, pipe()
├── sequential.py    # SequentialChain
├── parallel.py      # ParallelChain
└── conditional.py   # ConditionalChain, Condition, RouterChain
```

#### Chain Hierarchy

```
BaseComponent
    └── Chain (abstract)
        ├── LCELChain
        ├── SequentialChain
        ├── ParallelChain
        └── ConditionalChain
```

#### Execution Flow

```
Input → Chain → Step1 → Step2 → ... → StepN → Output
         │
         ├── Sequential: step[i].output → step[i+1].input
         ├── Parallel: same input → all steps → aggregate
         └── Conditional: evaluate → select chain → execute
```

### Memory Module

```
memory/
├── base.py          # Memory, MemoryEntry, MemoryStats
├── buffer.py        # ConversationBufferMemory
├── summary.py       # ConversationSummaryMemory
├── window.py        # ConversationBufferWindowMemory
└── vector.py        # VectorStoreRetrieverMemory, VectorStore
```

#### Memory Hierarchy

```
BaseComponent
    └── Memory (abstract)
        ├── ConversationBufferMemory
        ├── ConversationSummaryMemory
        ├── ConversationBufferWindowMemory
        └── VectorStoreRetrieverMemory
```

#### Memory Strategies

| Strategy | Storage | Use Case |
|----------|---------|----------|
| Buffer | All messages | Short conversations |
| Summary | Running summary | Long conversations |
| Window | Last K messages | Recent context |
| Vector | Embeddings | Semantic search |

### Tools Module

```
tools/
├── base.py          # Tool, ToolInput, ToolResult, FunctionTool
├── registry.py      # ToolRegistry
├── decorators.py    # @tool, @toolkit, from_function, from_class
└── builtin.py       # SearchTool, CalculatorTool, etc.
```

#### Tool Hierarchy

```
BaseComponent
    └── Tool (abstract)
        ├── FunctionTool
        ├── SearchTool
        ├── CalculatorTool
        ├── FileReaderTool
        ├── FileWriterTool
        ├── ShellTool
        ├── HTTPTool
        ├── JSONTool
        └── RegexTool
```

#### Tool Execution Flow

```
Input → ToolRegistry → Tool → ToolInput → Execute → ToolResult → Output
           │
           ├── Validate parameters
           ├── Execute function
           └── Track metrics
```

### Callbacks Module

```
callbacks/
├── base.py          # Callback, CallbackEvent, CallbackManager
├── streaming.py     # StreamingCallback, StreamingHandler
├── logging.py       # LoggingCallback
└── metrics.py       # MetricsCallback
```

#### Callback Hierarchy

```
Callback (abstract)
    ├── NoOpCallback
    ├── LambdaCallback
    ├── StreamingCallback
    ├── BufferedStreamingCallback
    ├── CollectingStreamingCallback
    ├── LoggingCallback
    └── MetricsCallback
```

#### Event Flow

```
Chain/Tool/LLM → CallbackManager → Callback1 → on_chain_start()
                                  → Callback2 → on_chain_start()
                                  → Callback3 → on_chain_start()
```

## Integration Points

### With PHOENIX State Management

The LangChain integration can use PHOENIX state management for persistence:

```python
from aios.state import StateCoordinator

# Use state coordinator for memory persistence
coordinator = StateCoordinator(config)
memory = ConversationBufferMemory()

# Save to state
coordinator.set("memory:session_123", memory.get_messages())

# Load from state
messages = coordinator.get("memory:session_123")
```

### With PHOENIX Event Bus

Callbacks can emit events to the PHOENIX event bus:

```python
from aios.event_bus import EventBus

class EventBusCallback(Callback):
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus

    def on_chain_start(self, event: CallbackEvent):
        self._event_bus.emit("chain.started", {"name": event.name})
```

### With PHOENIX Observability

Metrics can be sent to PHOENIX observability:

```python
from aios.observability import Observability

class ObservabilityCallback(Callback):
    def __init__(self, observability: Observability):
        self._observability = observability

    def on_chain_end(self, event: CallbackEvent):
        self._observability.record_metric(
            "chain_duration",
            event.metadata.get("duration", 0),
        )
```

## Data Flow

### Chain Execution

```
1. User calls chain.invoke(input_data)
2. Chain creates execution context
3. For each step:
   a. Execute step function
   b. Update context with result
   c. Dispatch callbacks
4. Return final result
```

### Memory Operations

```
1. User calls memory.add_user_message(message)
2. Memory creates MemoryEntry
3. Memory stores entry (buffer/vector/etc.)
4. Memory dispatches callbacks
5. Memory updates statistics
```

### Tool Execution

```
1. User calls registry.execute(tool_name, kwargs)
2. Registry finds tool
3. Registry creates ToolInput
4. Tool validates parameters
5. Tool executes function
6. Tool returns ToolResult
7. Registry dispatches callbacks
```

## Performance Considerations

### Chain Execution

- Sequential chains: O(n) where n is number of steps
- Parallel chains: O(1) with thread pool (limited by slowest step)
- Conditional chains: O(1) after condition evaluation

### Memory Usage

- Buffer: O(n) where n is number of messages
- Summary: O(1) after summarization
- Window: O(k) where k is window size
- Vector: O(n * d) where d is vector dimension

### Tool Execution

- Most tools: O(1) per execution
- Search tools: O(n) where n is text length
- HTTP tools: Network latency dependent

## Security Considerations

### Tool Execution

- Shell tool: Command validation required
- File tools: Path validation required
- HTTP tools: URL validation required

### Memory Storage

- Sensitive data should not be stored in memory
- Vector embeddings may leak information
- Summary may expose conversation content

### Callback Access

- Callbacks have access to all execution data
- Streaming callbacks may expose sensitive tokens
- Metrics callbacks collect performance data

## Extension Points

### Custom Chains

```python
class CustomChain(Chain):
    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult:
        # Custom implementation
        pass
```

### Custom Memory

```python
class CustomMemory(Memory):
    def add_user_message(self, message: str) -> None:
        # Custom implementation
        pass

    def add_ai_message(self, message: str) -> None:
        # Custom implementation
        pass

    def get_messages(self) -> List[Dict[str, str]]:
        # Custom implementation
        pass
```

### Custom Tools

```python
class CustomTool(Tool):
    @property
    def name(self) -> str:
        return "custom"

    @property
    def description(self) -> str:
        return "Custom tool"

    def execute(self, tool_input: ToolInput) -> ToolResult:
        # Custom implementation
        pass
```

### Custom Callbacks

```python
class CustomCallback(Callback):
    def on_chain_start(self, event: CallbackEvent) -> None:
        # Custom implementation
        pass

    # ... implement other methods
```

## Testing Strategy

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Verify edge cases

### Integration Tests

- Test component interactions
- Verify data flow
- Test error handling

### Performance Tests

- Measure execution time
- Test memory usage
- Verify scalability

## Future Enhancements

### Planned Features

1. **Async Support**: Async chain execution
2. **Streaming Chains**: Real-time chain output
3. **Persistent Memory**: Database-backed memory
4. **Distributed Tools**: Remote tool execution
5. **Plugin System**: Dynamic tool loading

### Integration Opportunities

1. **LangChain Hub**: Share chains and tools
2. **LangSmith**: Advanced debugging and monitoring
3. **LangServe**: API deployment
4. **Vector Databases**: Pinecone, Weaviate, Chroma
