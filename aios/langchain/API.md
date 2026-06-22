# PHOENIX AIOS LangChain Integration API Reference

## Core Classes

### BaseComponent

Abstract base class for all components.

```python
class BaseComponent(ABC):
    @property
    def config(self) -> Config: ...

    @property
    def logger(self) -> Logger: ...

    @property
    def execution_count(self) -> int: ...

    @property
    def average_duration(self) -> float: ...

    @abstractmethod
    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult: ...

    def batch(self, inputs: List[Dict[str, Any]]) -> List[ExecutionResult]: ...

    def stream(self, input_data: Dict[str, Any]) -> Any: ...

    def reset_stats(self) -> None: ...
```

### ExecutionResult

Result of a component execution.

```python
@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def success_result(cls, data: Any, duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ExecutionResult: ...

    @classmethod
    def error_result(cls, error: str, duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ExecutionResult: ...
```

### Config

Configuration for components.

```python
@dataclass(frozen=True)
class Config:
    name: str = "phoenix-langchain"
    version: str = "1.0.0"
    log_level: LogLevel = LogLevel.INFO
    max_retries: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_override(self, **kwargs: Any) -> Config: ...
```

## Chains

### Chain

Base chain class.

```python
class Chain(BaseComponent):
    def __init__(self, name: str, config: Optional[Config] = None): ...

    @property
    def name(self) -> str: ...

    @property
    def steps(self) -> List[ChainStep]: ...

    def add_step(self, step: ChainStep) -> Chain: ...

    def remove_step(self, step_name: str) -> bool: ...

    def clear_steps(self) -> None: ...

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult: ...

    def batch(self, inputs: List[Dict[str, Any]]) -> List[ExecutionResult]: ...

    def get_step_names(self) -> List[str]: ...

    def get_step(self, step_name: str) -> Optional[ChainStep]: ...
```

### ChainStep

A single step in a chain.

```python
@dataclass(frozen=True)
class ChainStep:
    name: str
    function: Callable[[Dict[str, Any]], Any]
    description: str = ""
    required: bool = True
    retry_count: int = 0
    timeout: Optional[float] = None

    def execute(self, context: Dict[str, Any]) -> StepResult: ...
```

### StepResult

Result of a chain step execution.

```python
@dataclass(frozen=True)
class StepResult:
    step_name: str
    status: StepStatus
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, step_name: str, data: Any, duration: float = 0.0) -> StepResult: ...

    @classmethod
    def error(cls, step_name: str, error: str, duration: float = 0.0) -> StepResult: ...

    @classmethod
    def skipped(cls, step_name: str) -> StepResult: ...
```

### LCELChain

LCEL-style chain with pipe operator.

```python
class LCELChain(BaseComponent):
    def __init__(self, name: str, config: Optional[Config] = None): ...

    def __or__(self, other: Union[LCELStep, Callable]) -> LCELChain: ...

    def __ror__(self, other: Union[LCELStep, Callable]) -> LCELChain: ...

    def invoke(self, input_data: Any) -> ExecutionResult: ...

    def batch(self, inputs: List[Any]) -> List[ExecutionResult]: ...

    def stream(self, input_data: Any) -> Any: ...
```

### LCELStep

A step in an LCEL chain.

```python
@dataclass(frozen=True)
class LCELStep:
    name: str
    function: Callable[[Any], Any]
    description: str = ""

    def invoke(self, input_data: Any) -> Any: ...
```

### SequentialChain

Executes steps in sequence.

```python
class SequentialChain(Chain):
    def add_step(self, step: ChainStep, position: Optional[int] = None) -> SequentialChain: ...

    def add_transform(self, name: str, transform_fn: Callable[[Any], Any], **kwargs: Any) -> SequentialChain: ...

    def add_filter(self, name: str, filter_fn: Callable[[Any], bool], **kwargs: Any) -> SequentialChain: ...

    def add_aggregator(self, name: str, aggregate_fn: Callable[[List[Any]], Any], **kwargs: Any) -> SequentialChain: ...

    def __add__(self, other: SequentialChain) -> SequentialChain: ...
```

### ParallelChain

Executes steps in parallel.

```python
class ParallelChain(Chain):
    def __init__(self, name: str, config: Optional[Config] = None, max_workers: Optional[int] = None): ...

    def set_aggregator(self, aggregator: Callable[[Dict[str, Any]], Any]) -> ParallelChain: ...

    def add_step(self, step: ChainStep) -> ParallelChain: ...

    def add_branch(self, name: str, branch_fn: Callable[[Dict[str, Any]], Any], **kwargs: Any) -> ParallelChain: ...

    def __add__(self, other: Chain) -> Chain: ...
```

### ConditionalChain

Executes different paths based on conditions.

```python
class ConditionalChain(Chain):
    def add_condition(self, condition: Condition) -> ConditionalChain: ...

    def set_default(self, chain: Chain) -> ConditionalChain: ...

    def invoke(self, input_data: Dict[str, Any]) -> ExecutionResult: ...

    def get_conditions(self) -> List[Condition]: ...

    def remove_condition(self, condition_name: str) -> bool: ...
```

### Condition

Condition for conditional chain branching.

```python
@dataclass(frozen=True)
class Condition:
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    chain: Chain
    priority: int = 0
```

## Memory

### Memory

Abstract base class for memory implementations.

```python
class Memory(BaseComponent, ABC):
    @property
    def memory_type(self) -> MemoryType: ...

    @abstractmethod
    def add_user_message(self, message: str) -> None: ...

    @abstractmethod
    def add_ai_message(self, message: str) -> None: ...

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]: ...

    def get(self, key: str) -> Optional[Any]: ...

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None: ...

    def delete(self, key: str) -> bool: ...

    def clear(self) -> None: ...

    def has(self, key: str) -> bool: ...

    def keys(self) -> List[str]: ...

    def values(self) -> List[Any]: ...

    def items(self) -> List[tuple]: ...

    def get_stats(self) -> MemoryStats: ...

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None: ...

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]: ...
```

### ConversationBufferMemory

Stores all messages in a buffer.

```python
class ConversationBufferMemory(Memory):
    def __init__(self, config: Optional[Config] = None, max_messages: Optional[int] = None): ...

    @property
    def messages(self) -> List[Dict[str, str]]: ...

    def get_last_n_messages(self, n: int) -> List[Dict[str, str]]: ...

    def get_context_string(self, max_messages: Optional[int] = None) -> str: ...
```

### ConversationSummaryMemory

Maintains a running summary.

```python
class ConversationSummaryMemory(Memory):
    def __init__(
        self,
        config: Optional[Config] = None,
        summarizer: Optional[Callable[[List[Dict[str, str]], str], str]] = None,
        max_messages_before_summary: int = 10,
    ): ...

    @property
    def summary(self) -> str: ...

    def get_summary(self) -> str: ...

    def set_summary(self, summary: str) -> None: ...

    def force_summarize(self) -> str: ...
```

### ConversationBufferWindowMemory

Stores only the last K messages.

```python
class ConversationBufferWindowMemory(Memory):
    def __init__(self, config: Optional[Config] = None, window_size: int = 10): ...

    @property
    def window_size(self) -> int: ...

    def set_window_size(self, size: int) -> None: ...
```

### VectorStoreRetrieverMemory

Uses vector similarity for retrieval.

```python
class VectorStoreRetrieverMemory(Memory):
    def __init__(
        self,
        config: Optional[Config] = None,
        embedder: Optional[Callable[[str], List[float]]] = None,
        vector_store: Optional[VectorStore] = None,
        dimension: int = 768,
        top_k: int = 5,
        threshold: float = 0.5,
    ): ...

    @property
    def vector_store(self) -> VectorStore: ...

    def search(self, query: str, top_k: Optional[int] = None, threshold: Optional[float] = None) -> List[Tuple[str, float]]: ...

    def get_relevant_context(self, query: str, max_entries: int = 5) -> str: ...
```

## Tools

### Tool

Abstract base class for tools.

```python
class Tool(BaseComponent, ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    def parameters(self) -> List[ToolParameter]: ...

    def add_parameter(self, name: str, type: Type, description: str = "", required: bool = True, default: Any = None) -> Tool: ...

    @abstractmethod
    def execute(self, tool_input: ToolInput) -> ToolResult: ...

    def get_schema(self) -> Dict[str, Any]: ...
```

### ToolInput

Input for tool execution.

```python
@dataclass(frozen=True)
class ToolInput:
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any: ...

    def with_context(self, **kwargs: Any) -> ToolInput: ...
```

### ToolResult

Result of tool execution.

```python
@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, data: Any, duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ToolResult: ...

    @classmethod
    def error(cls, error: str, duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ToolResult: ...

    @classmethod
    def timeout(cls, duration: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> ToolResult: ...
```

### ToolRegistry

Registry for managing tools.

```python
class ToolRegistry:
    def __init__(self, config: Optional[Config] = None): ...

    @property
    def tools(self) -> Dict[str, Tool]: ...

    def register(self, tool: Tool, categories: Optional[List[str]] = None) -> None: ...

    def unregister(self, name: str) -> bool: ...

    def get(self, name: str) -> Optional[Tool]: ...

    def execute(self, name: str, kwargs: Optional[Dict[str, Any]] = None, args: Optional[tuple] = None, context: Optional[Dict[str, Any]] = None) -> ExecutionResult: ...

    def list_tools(self) -> List[str]: ...

    def list_categories(self) -> List[str]: ...

    def get_tools_by_category(self, category: str) -> List[Tool]: ...

    def search_tools(self, query: str) -> List[Tool]: ...

    def get_schemas(self) -> List[Dict[str, Any]]: ...

    def get_tools_for_llm(self) -> List[Dict[str, Any]]: ...
```

### Built-in Tools

#### SearchTool

```python
class SearchTool(Tool):
    # Parameters:
    # - text (str): Text to search in
    # - pattern (str): Pattern to search for
    # - case_sensitive (bool): Case sensitive search (default: True)
    ...
```

#### CalculatorTool

```python
class CalculatorTool(Tool):
    # Parameters:
    # - expression (str): Mathematical expression to evaluate
    ...
```

#### FileReaderTool

```python
class FileReaderTool(Tool):
    # Parameters:
    # - path (str): File path to read
    # - encoding (str): File encoding (default: "utf-8")
    ...
```

#### FileWriterTool

```python
class FileWriterTool(Tool):
    # Parameters:
    # - path (str): File path to write
    # - content (str): Content to write
    # - encoding (str): File encoding (default: "utf-8")
    # - append (bool): Append to file (default: False)
    ...
```

#### ShellTool

```python
class ShellTool(Tool):
    # Parameters:
    # - command (str): Shell command to execute
    # - timeout (int): Timeout in seconds (default: 30)
    # - cwd (str): Working directory (default: None)
    ...
```

#### HTTPTool

```python
class HTTPTool(Tool):
    # Parameters:
    # - url (str): URL to request
    # - method (str): HTTP method (default: "GET")
    # - headers (dict): Request headers (default: {})
    # - data (str): Request body (default: None)
    # - timeout (int): Timeout in seconds (default: 30)
    ...
```

#### JSONTool

```python
class JSONTool(Tool):
    # Parameters:
    # - action (str): Action: parse, stringify, query
    # - text (str): JSON text
    # - data (Any): Data to stringify
    # - path (str): JSON path for query
    ...
```

#### RegexTool

```python
class RegexTool(Tool):
    # Parameters:
    # - action (str): Action: match, search, findall, sub
    # - text (str): Text to process
    # - pattern (str): Regex pattern
    # - replacement (str): Replacement for sub
    ...
```

## Callbacks

### Callback

Abstract base class for callbacks.

```python
class Callback(ABC):
    def on_chain_start(self, event: CallbackEvent) -> None: ...
    def on_chain_end(self, event: CallbackEvent) -> None: ...
    def on_chain_error(self, event: CallbackEvent) -> None: ...
    def on_step_start(self, event: CallbackEvent) -> None: ...
    def on_step_end(self, event: CallbackEvent) -> None: ...
    def on_step_error(self, event: CallbackEvent) -> None: ...
    def on_tool_start(self, event: CallbackEvent) -> None: ...
    def on_tool_end(self, event: CallbackEvent) -> None: ...
    def on_tool_error(self, event: CallbackEvent) -> None: ...
    def on_llm_start(self, event: CallbackEvent) -> None: ...
    def on_llm_end(self, event: CallbackEvent) -> None: ...
    def on_llm_error(self, event: CallbackEvent) -> None: ...
    def on_llm_token(self, event: CallbackEvent) -> None: ...
    def on_custom_event(self, event: CallbackEvent) -> None: ...
```

### CallbackEvent

Callback event.

```python
@dataclass(frozen=True)
class CallbackEvent:
    event_type: CallbackEventType
    name: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_data(self, data: Any) -> CallbackEvent: ...
    def with_metadata(self, **kwargs: Any) -> CallbackEvent: ...
```

### CallbackManager

Manager for callbacks.

```python
class CallbackManager:
    def __init__(self, config: Optional[Config] = None): ...

    @property
    def callbacks(self) -> List[Callback]: ...

    @property
    def event_history(self) -> List[CallbackEvent]: ...

    def add_callback(self, callback: Callback) -> None: ...

    def remove_callback(self, callback: Callback) -> bool: ...

    def clear_callbacks(self) -> None: ...

    def dispatch(self, event: CallbackEvent) -> None: ...

    def get_events_by_type(self, event_type: CallbackEventType) -> List[CallbackEvent]: ...

    def get_events_by_name(self, name: str) -> List[CallbackEvent]: ...

    def clear_history(self) -> None: ...
```

### StreamingCallback

Streaming callback for LLM responses.

```python
class StreamingCallback(Callback):
    def __init__(
        self,
        config: Optional[Config] = None,
        output: Optional[TextIO] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ): ...

    @property
    def current_text(self) -> str: ...

    @property
    def is_streaming(self) -> bool: ...

    def reset(self) -> None: ...
```

### MetricsCallback

Metrics callback for performance monitoring.

```python
class MetricsCallback(Callback):
    def __init__(self, config: Optional[Config] = None): ...

    @property
    def metrics(self) -> List[MetricEntry]: ...

    def get_metrics(self) -> Dict[str, Any]: ...

    def get_counter(self, name: str) -> int: ...

    def get_duration_stats(self, prefix: str) -> Dict[str, float]: ...

    def reset(self) -> None: ...
```

## Decorators

### @tool

Decorator to create a tool from a function.

```python
@tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
    config: Optional[Config] = None,
)
def my_function(x: int, y: int) -> int:
    return x + y
```

### @toolkit

Decorator to create a toolkit from a class.

```python
@toolkit(
    name: str,
    description: str = "",
    categories: Optional[List[str]] = None,
)
class MyToolkit:
    @staticmethod
    def add(x: int, y: int) -> int:
        return x + y
```

## Factory Functions

### pipe()

Create an LCEL chain from functions.

```python
def pipe(*functions: Callable[[Any], Any]) -> LCELChain: ...
```

### sequential()

Create a sequential chain from functions.

```python
def sequential(name: str, *functions: Callable[[Dict[str, Any]], Any]) -> SequentialChain: ...
```

### parallel()

Create a parallel chain from functions.

```python
def parallel(name: str, *functions: Callable[[Dict[str, Any]], Any], max_workers: Optional[int] = None) -> ParallelChain: ...
```

### conditional()

Create a conditional chain.

```python
def conditional(name: str, conditions: List[Condition], default: Optional[Chain] = None) -> ConditionalChain: ...
```

### switch()

Create a switch-style conditional chain.

```python
def switch(
    name: str,
    key_fn: Callable[[Dict[str, Any]], str],
    branches: Dict[str, Chain],
    default: Optional[Chain] = None,
) -> ConditionalChain: ...
```

### buffer_memory()

Create a conversation buffer memory.

```python
def buffer_memory(max_messages: Optional[int] = None, config: Optional[Config] = None) -> ConversationBufferMemory: ...
```

### summary_memory()

Create a conversation summary memory.

```python
def summary_memory(
    summarizer: Optional[Callable[[List[Dict[str, str]], str], str]] = None,
    max_messages_before_summary: int = 10,
    config: Optional[Config] = None,
) -> ConversationSummaryMemory: ...
```

### window_memory()

Create a conversation buffer window memory.

```python
def window_memory(window_size: int = 10, config: Optional[Config] = None) -> ConversationBufferWindowMemory: ...
```

### vector_memory()

Create a vector store retriever memory.

```python
def vector_memory(
    embedder: Optional[Callable[[str], List[float]]] = None,
    dimension: int = 768,
    top_k: int = 5,
    threshold: float = 0.5,
    config: Optional[Config] = None,
) -> VectorStoreRetrieverMemory: ...
```

### from_function()

Create a tool from a function.

```python
def from_function(
    func: Callable,
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
    config: Optional[Config] = None,
) -> Tool: ...
```

### from_class()

Create tools from a class.

```python
def from_class(
    cls: Type,
    name: Optional[str] = None,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> List[Tool]: ...
```
