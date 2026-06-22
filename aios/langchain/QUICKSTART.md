# PHOENIX AIOS LangChain Integration - Quick Start Guide

## Installation

```python
from aios.langchain import Chain, Memory, Tool
```

## 5-Minute Quick Start

### 1. Create Your First Chain

```python
from aios.langchain import Chain, ChainStep

# Create a chain
chain = Chain("my_chain")
chain.add_step(ChainStep("double", lambda ctx: ctx["input"] * 2))
chain.add_step(ChainStep("add_one", lambda ctx: ctx["double"] + 1))

# Execute
result = chain.invoke({"input": 5})
print(result.data)  # 11
```

### 2. Use LCEL-Style Chains

```python
from aios.langchain import LCELChain, LCELStep

# Create chain with pipe operator
chain = (
    LCELChain("transform")
    | LCELStep("double", lambda x: x * 2)
    | LCELStep("add_one", lambda x: x + 1)
)

# Execute
result = chain.invoke(5)
print(result.data)  # 11
```

### 3. Add Memory

```python
from aios.langchain import ConversationBufferMemory

# Create memory
memory = ConversationBufferMemory()

# Add messages
memory.add_user_message("Hello")
memory.add_ai_message("Hi there!")

# Get messages
messages = memory.get_messages()
print(messages)
# [
#     {"role": "user", "content": "Hello"},
#     {"role": "ai", "content": "Hi there!"},
# ]
```

### 4. Use Tools

```python
from aios.langchain import ToolRegistry, CalculatorTool

# Create registry
registry = ToolRegistry()
registry.register(CalculatorTool())

# Execute tool
result = registry.execute("calculator", kwargs={"expression": "2 + 3 * 4"})
print(result.data)  # 14
```

### 5. Add Callbacks

```python
from aios.langchain import CallbackManager, StreamingCallback

# Create callback manager
manager = CallbackManager()
manager.add_callback(StreamingCallback())

# Events are dispatched automatically during chain execution
```

## Common Patterns

### Pattern 1: Data Processing Pipeline

```python
from aios.langchain import SequentialChain

chain = SequentialChain("pipeline")
chain.add_transform("clean", lambda x: x.strip())
chain.add_transform("uppercase", lambda x: x.upper())
chain.add_transform("add_prefix", lambda x: f"Processed: {x}")

result = chain.invoke({"input": "  hello world  "})
print(result.data)  # "Processed: HELLO WORLD"
```

### Pattern 2: Parallel Analysis

```python
from aios.langchain import ParallelChain, ChainStep

chain = ParallelChain("analysis")
chain.add_step(ChainStep("length", lambda ctx: len(ctx["text"])))
chain.add_step(ChainStep("words", lambda ctx: len(ctx["text"].split())))
chain.add_step(ChainStep("upper", lambda ctx: ctx["text"].upper()))

result = chain.invoke({"text": "hello world"})
print(result.data)
# {"length": 11, "words": 2, "upper": "HELLO WORLD"}
```

### Pattern 3: Conditional Routing

```python
from aios.langchain import ConditionalChain, Condition, SequentialChain

# Create chains for different paths
en_chain = SequentialChain("english")
en_chain.add_step(ChainStep("greet", lambda ctx: "Hello!"))

es_chain = SequentialChain("spanish")
es_chain.add_step(ChainStep("greet", lambda ctx: "Hola!"))

# Create router
chain = ConditionalChain("router")
chain.add_condition(Condition(
    name="is_english",
    predicate=lambda ctx: ctx["lang"] == "en",
    chain=en_chain,
))
chain.add_condition(Condition(
    name="is_spanish",
    predicate=lambda ctx: ctx["lang"] == "es",
    chain=es_chain,
))

result = chain.invoke({"lang": "en"})
print(result.data)  # "Hello!"
```

### Pattern 4: Conversation with Memory

```python
from aios.langchain import ConversationBufferMemory, Chain, ChainStep

# Create memory
memory = ConversationBufferMemory()

# Create chain that uses memory
def chat(ctx):
    history = memory.get_context_string()
    user_input = ctx["input"]

    # Simple echo bot
    response = f"You said: {user_input}"
    memory.add_user_message(user_input)
    memory.add_ai_message(response)

    return response

chain = Chain("chatbot")
chain.add_step(ChainStep("chat", chat))

# Have a conversation
result1 = chain.invoke({"input": "Hello"})
print(result1.data)  # "You said: Hello"

result2 = chain.invoke({"input": "How are you?"})
print(result2.data)  # "You said: How are you?"
```

### Pattern 5: Tool-Augmented Chain

```python
from aios.langchain import Chain, ChainStep, ToolRegistry, CalculatorTool

# Setup tools
registry = ToolRegistry()
registry.register(CalculatorTool())

# Create chain that uses tools
def calculate(ctx):
    result = registry.execute("calculator", kwargs={"expression": ctx["expr"]})
    return result.data if result.success else None

chain = Chain("calculator_chain")
chain.add_step(ChainStep("calculate", calculate))
chain.add_step(ChainStep("format", lambda ctx: f"Result: {ctx['calculate']}"))

result = chain.invoke({"expr": "2 + 3 * 4"})
print(result.data)  # "Result: 14"
```

## Built-in Tools Reference

| Tool | Name | Description |
|------|------|-------------|
| SearchTool | `search` | Search for patterns in text |
| CalculatorTool | `calculator` | Evaluate mathematical expressions |
| FileReaderTool | `file_reader` | Read file contents |
| FileWriterTool | `file_writer` | Write content to file |
| ShellTool | `shell` | Execute shell commands |
| HTTPTool | `http` | Make HTTP requests |
| JSONTool | `json` | Process JSON data |
| RegexTool | `regex` | Regular expression operations |

## Memory Types Reference

| Type | Class | Use Case |
|------|-------|----------|
| Buffer | `ConversationBufferMemory` | Store all messages |
| Summary | `ConversationSummaryMemory` | Maintain running summary |
| Window | `ConversationBufferWindowMemory` | Keep last K messages |
| Vector | `VectorStoreRetrieverMemory` | Semantic search |

## Callback Types Reference

| Type | Class | Purpose |
|------|-------|---------|
| Streaming | `StreamingCallback` | Stream LLM tokens |
| Logging | `LoggingCallback` | Log all events |
| Metrics | `MetricsCallback` | Collect performance metrics |

## Error Handling

```python
from aios.langchain import Chain, ChainStep

# Chain with error handling
chain = Chain("safe_chain")
chain.add_step(ChainStep(
    name="risky_step",
    function=lambda ctx: 1 / 0,  # This will fail
    required=False,  # Don't fail the chain
))

result = chain.invoke({"input": 5})
if not result.success:
    print(f"Error: {result.error}")
```

## Next Steps

1. Read the [Architecture Guide](ARCHITECTURE.md) for detailed design
2. Check [Examples](examples.py) for more usage patterns
3. Run tests: `python -m aios.langchain.tests`
4. Explore built-in tools and memory types
