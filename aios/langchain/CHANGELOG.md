# Changelog

All notable changes to the PHOENIX AIOS LangChain Integration will be documented in this file.

## [1.0.0] - 2026-06-19

### Added

#### Core Module
- `BaseComponent` abstract base class
- `Config` frozen dataclass for configuration
- `Logger` structured logging
- `ExecutionResult` typed execution results
- `ComponentRegistry` for component management

#### Chains Module
- `Chain` base chain class
- `ChainStep` for defining chain steps
- `StepResult` for step execution results
- `LCELChain` with pipe operator support
- `LCELStep` for LCEL chain steps
- `SequentialChain` for sequential execution
- `ParallelChain` for parallel execution
- `ConditionalChain` for conditional routing
- `Condition` for defining conditions
- `RouterChain` for dynamic routing

#### Memory Module
- `Memory` abstract base class
- `MemoryEntry` for memory entries
- `MemoryStats` for memory statistics
- `ConversationBufferMemory` for storing all messages
- `ConversationSummaryMemory` for maintaining running summary
- `ConversationBufferWindowMemory` for keeping last K messages
- `VectorStoreRetrieverMemory` for vector similarity search
- `VectorStore` for vector storage

#### Tools Module
- `Tool` abstract base class
- `ToolInput` for tool input
- `ToolResult` for tool results
- `ToolParameter` for parameter definitions
- `FunctionTool` for wrapping functions
- `ToolRegistry` for tool management
- `@tool` decorator for creating tools
- `@toolkit` decorator for creating toolkits
- Built-in tools:
  - `SearchTool` for text search
  - `CalculatorTool` for math expressions
  - `FileReaderTool` for reading files
  - `FileWriterTool` for writing files
  - `ShellTool` for shell commands
  - `HTTPTool` for HTTP requests
  - `JSONTool` for JSON processing
  - `RegexTool` for regex operations

#### Callbacks Module
- `Callback` abstract base class
- `CallbackEvent` for callback events
- `CallbackEventType` enum for event types
- `CallbackManager` for managing callbacks
- `StreamingCallback` for streaming LLM output
- `StreamingHandler` for handling streaming
- `BufferedStreamingCallback` for buffered streaming
- `CollectingStreamingCallback` for collecting tokens
- `LoggingCallback` for event logging
- `MetricsCallback` for performance metrics
- `NoOpCallback` for no-op operations
- `LambdaCallback` for lambda-based callbacks

#### Tests
- `test_chains.py` - Tests for all chain types
- `test_memory.py` - Tests for all memory types
- `test_tools.py` - Tests for tools and registry
- `test_callbacks.py` - Tests for callbacks

#### Documentation
- `README.md` - Main documentation
- `ARCHITECTURE.md` - Architecture documentation
- `QUICKSTART.md` - Quick start guide
- `API.md` - API reference
- `examples.py` - Usage examples
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `CHANGELOG.md` - This changelog

### Design Decisions

1. **Immutability**: All data structures are frozen dataclasses
2. **Type Safety**: Full type annotations throughout
3. **Composability**: Pipe operator for LCEL chains
4. **Error Handling**: Typed execution results
5. **Modularity**: Separate modules for chains, memory, tools, callbacks
6. **Extensibility**: Abstract base classes for custom implementations

### Dependencies

- Python 3.8+
- No external dependencies (pure Python implementation)

### Known Limitations

1. Vector store is in-memory only
2. No async support yet
3. No persistent memory storage
4. Limited built-in tools

### Future Plans

1. Add async support
2. Add persistent memory storage
3. Add more built-in tools
4. Add vector database integrations
5. Add LangChain Hub integration
