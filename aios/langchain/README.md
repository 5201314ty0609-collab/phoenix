# PHOENIX AIOS LangChain Integration

A comprehensive LangChain integration framework for PHOENIX AIOS, providing chain composition, memory management, tool execution, and callback mechanisms.

## Features

- **Chain Framework**: Composable chain execution with LCEL support
- **Memory System**: Multiple memory strategies (buffer, summary, window, vector)
- **Tool System**: Tool registration, execution, and built-in tools
- **Callback System**: Event monitoring, streaming, and metrics collection
- **Type Safety**: Full type annotations throughout
- **Immutable Design**: All data structures are immutable by default

## Installation

```python
from aios.langchain import Chain, Memory, Tool
```

## Quick Start

### Chains

```python
from aios.langchain import Chain, ChainStep, LCELChain, LCELStep

# Create a simple chain
chain = Chain("my_chain")
chain.add_step(ChainStep("double", lambda ctx: ctx["input"] * 2))
chain.add_step(ChainStep("add_one", lambda ctx: ctx["double"] + 1))

result = chain.invoke({"input": 5})
# result.data = 11

# LCEL-style chain with pipe operator
lcel_chain = (
    LCELChain("transform")
    | LCELStep("double", lambda x: x * 2)
    | LCELStep("add_one", lambda x: x + 1)
)

result = lcel_chain.invoke(5)
# result.data = 11
```

### Memory

```python
from aios.langchain import ConversationBufferMemory, ConversationSummaryMemory

# Buffer memory
memory = ConversationBufferMemory()
memory.add_user_message("Hello")
memory.add_ai_message("Hi there!")

messages = memory.get_messages()
# [
#     {"role": "user", "content": "Hello"},
#     {"role": "ai", "content": "Hi there!"},
# ]

# Summary memory
def summarizer(messages, current_summary):
    new_text = " ".join(m["content"] for m in messages)
    return f"{current_summary}\n{new_text}" if current_summary else new_text

summary_memory = ConversationSummaryMemory(summarizer=summarizer)
summary_memory.add_user_message("Hello")
summary_memory.add_ai_message("Hi!")
summary = summary_memory.get_summary()
```

### Tools

```python
from aios.langchain import ToolRegistry, tool, SearchTool, CalculatorTool

# Use built-in tools
registry = ToolRegistry()
registry.register(SearchTool())
registry.register(CalculatorTool())

# Execute tool
result = registry.execute("calculator", kwargs={"expression": "2 + 3 * 4"})
# result.data = 14

# Create custom tool with decorator
@tool(name="greet", description="Greet someone")
def greet(name: str) -> str:
    return f"Hello, {name}!"

result = greet(name="World")
# result = "Hello, World!"
```

### Callbacks

```python
from aios.langchain import CallbackManager, StreamingCallback, MetricsCallback

# Create callback manager
manager = CallbackManager()
manager.add_callback(StreamingCallback())
manager.add_callback(MetricsCallback())

# Events are dispatched automatically during chain execution
```

## Chain Types

### Chain (Base)

Basic chain with step-by-step execution.

```python
chain = Chain("my_chain")
chain.add_step(ChainStep("step1", lambda ctx: ctx["input"] * 2))
chain.add_step(ChainStep("step2", lambda ctx: ctx["step1"] + 1))
```

### LCELChain

LangChain Expression Language style chain with pipe operator.

```python
chain = (
    LCELChain("transform")
    | (lambda x: x * 2)
    | (lambda x: x + 1)
)
```

### SequentialChain

Executes steps in sequence, passing output to next step.

```python
chain = SequentialChain("transform")
chain.add_transform("double", lambda x: x * 2)
chain.add_transform("add_one", lambda x: x + 1)
```

### ParallelChain

Executes steps in parallel and collects results.

```python
chain = ParallelChain("analysis")
chain.add_step(ChainStep("sentiment", analyze_sentiment))
chain.add_step(ChainStep("keywords", extract_keywords))
chain.add_step(ChainStep("summary", generate_summary))
```

### ConditionalChain

Executes different paths based on conditions.

```python
chain = ConditionalChain("router")
chain.add_condition(Condition(
    name="is_english",
    predicate=lambda ctx: ctx["language"] == "en",
    chain=english_chain,
    priority=10,
))
chain.set_default(default_chain)
```

## Memory Types

### ConversationBufferMemory

Stores all messages in a simple buffer.

```python
memory = ConversationBufferMemory(max_messages=100)
memory.add_user_message("Hello")
memory.add_ai_message("Hi!")
```

### ConversationSummaryMemory

Maintains a running summary of the conversation.

```python
memory = ConversationSummaryMemory(
    summarizer=my_summarizer,
    max_messages_before_summary=10,
)
```

### ConversationBufferWindowMemory

Stores only the last K messages.

```python
memory = ConversationBufferWindowMemory(window_size=10)
```

### VectorStoreRetrieverMemory

Uses vector similarity to retrieve relevant memories.

```python
memory = VectorStoreRetrieverMemory(
    embedder=my_embedder,
    dimension=768,
    top_k=5,
)
```

## Built-in Tools

| Tool | Description |
|------|-------------|
| `SearchTool` | Search for patterns in text |
| `CalculatorTool` | Evaluate mathematical expressions |
| `FileReaderTool` | Read file contents |
| `FileWriterTool` | Write content to file |
| `ShellTool` | Execute shell commands |
| `HTTPTool` | Make HTTP requests |
| `JSONTool` | Process JSON data |
| `RegexTool` | Regular expression operations |

## Callbacks

### CallbackManager

Manages multiple callbacks and dispatches events.

```python
manager = CallbackManager()
manager.add_callback(LoggingCallback())
manager.add_callback(MetricsCallback())
```

### StreamingCallback

Streams tokens as they are generated.

```python
callback = StreamingCallback(on_token=lambda t: print(t, end=""))
```

### MetricsCallback

Collects performance metrics.

```python
callback = MetricsCallback()
# ... run chain ...
metrics = callback.get_metrics()
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   Chains    │   Memory    │    Tools    │    Callbacks     │
├─────────────┼─────────────┼─────────────┼──────────────────┤
│ Chain       │ Buffer      │ Tool        │ Callback         │
│ LCELChain   │ Summary     │ ToolInput   │ CallbackEvent    │
│ Sequential  │ Window      │ ToolResult  │ CallbackManager  │
│ Parallel    │ Vector      │ ToolRegistry│ Streaming        │
│ Conditional │             │ Decorators  │ Logging          │
│             │             │ Built-in    │ Metrics          │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

## Testing

Run tests:

```python
from aios.langchain.tests import run_tests
from aios.langchain.tests.test_chains import TestChain
from aios.langchain.tests.test_memory import TestConversationBufferMemory
from aios.langchain.tests.test_tools import TestSearchTool
from aios.langchain.tests.test_callbacks import TestStreamingCallback

# Run all tests
results = run_tests(TestChain)
results += run_tests(TestConversationBufferMemory)
results += run_tests(TestSearchTool)
results += run_tests(TestStreamingCallback)

for result in results:
    print(result)
```

## Contributing

1. Follow PHOENIX coding standards
2. Add type annotations to all functions
3. Write tests for new functionality
4. Update documentation

## License

MIT License
