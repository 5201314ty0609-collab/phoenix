"""
Examples for PHOENIX AIOS LangChain Integration.

Demonstrates usage of chains, memory, tools, and callbacks.
"""

from typing import Any, Dict, List

from .chains import (
    Chain,
    ChainStep,
    LCELChain,
    LCELStep,
    SequentialChain,
    ParallelChain,
    ConditionalChain,
    Condition,
)
from .memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory,
    VectorStoreRetrieverMemory,
)
from .tools import (
    ToolRegistry,
    tool,
    SearchTool,
    CalculatorTool,
    JSONTool,
)
from .callbacks import (
    CallbackManager,
    StreamingCallback,
    MetricsCallback,
    LoggingCallback,
)
from .core import ExecutionResult


def example_basic_chain():
    """Example: Basic chain execution."""
    print("=== Basic Chain Example ===")

    # Create a chain
    chain = Chain("math_chain")
    chain.add_step(ChainStep(
        name="double",
        function=lambda ctx: ctx["input"] * 2,
    ))
    chain.add_step(ChainStep(
        name="add_ten",
        function=lambda ctx: ctx["double"] + 10,
    ))

    # Execute chain
    result = chain.invoke({"input": 5})
    print(f"Input: 5")
    print(f"Output: {result.data}")  # 20
    print(f"Duration: {result.duration:.3f}s")
    print()


def example_lcel_chain():
    """Example: LCEL-style chain with pipe operator."""
    print("=== LCEL Chain Example ===")

    # Create chain using pipe operator
    chain = (
        LCELChain("transform")
        | LCELStep("double", lambda x: x * 2)
        | LCELStep("add_prefix", lambda x: f"Result: {x}")
    )

    # Execute chain
    result = chain.invoke(5)
    print(f"Input: 5")
    print(f"Output: {result.data}")  # "Result: 10"
    print()


def example_sequential_chain():
    """Example: Sequential chain with transforms."""
    print("=== Sequential Chain Example ===")

    # Create sequential chain
    chain = SequentialChain("text_transform")
    chain.add_transform("uppercase", lambda x: x.upper())
    chain.add_transform("add_exclamation", lambda x: f"{x}!")
    chain.add_transform("wrap", lambda x: f"[{x}]")

    # Execute chain
    result = chain.invoke({"input": "hello world"})
    print(f"Input: hello world")
    print(f"Output: {result.data}")  # "[HELLO WORLD!]"
    print()


def example_parallel_chain():
    """Example: Parallel chain execution."""
    print("=== Parallel Chain Example ===")

    # Create parallel chain
    chain = ParallelChain("analysis")
    chain.add_step(ChainStep(
        name="word_count",
        function=lambda ctx: len(ctx["text"].split()),
    ))
    chain.add_step(ChainStep(
        name="char_count",
        function=lambda ctx: len(ctx["text"]),
    ))
    chain.add_step(ChainStep(
        name="uppercase",
        function=lambda ctx: ctx["text"].upper(),
    ))

    # Execute chain
    result = chain.invoke({"text": "hello world"})
    print(f"Input: hello world")
    print(f"Output: {result.data}")
    # {"word_count": 2, "char_count": 11, "uppercase": "HELLO WORLD"}
    print()


def example_conditional_chain():
    """Example: Conditional chain routing."""
    print("=== Conditional Chain Example ===")

    # Create chains for different paths
    positive_chain = SequentialChain("positive")
    positive_chain.add_step(ChainStep(
        name="double",
        function=lambda ctx: ctx["input"] * 2,
    ))

    negative_chain = SequentialChain("negative")
    negative_chain.add_step(ChainStep(
        name="negate",
        function=lambda ctx: -ctx["input"],
    ))

    zero_chain = SequentialChain("zero")
    zero_chain.add_step(ChainStep(
        name="zero",
        function=lambda ctx: 0,
    ))

    # Create conditional chain
    chain = ConditionalChain("router")
    chain.add_condition(Condition(
        name="is_positive",
        predicate=lambda ctx: ctx["input"] > 0,
        chain=positive_chain,
        priority=10,
    ))
    chain.add_condition(Condition(
        name="is_negative",
        predicate=lambda ctx: ctx["input"] < 0,
        chain=negative_chain,
        priority=5,
    ))
    chain.set_default(zero_chain)

    # Test different inputs
    for input_val in [5, -3, 0]:
        result = chain.invoke({"input": input_val})
        print(f"Input: {input_val}, Output: {result.data}")
    print()


def example_buffer_memory():
    """Example: Conversation buffer memory."""
    print("=== Buffer Memory Example ===")

    # Create memory
    memory = ConversationBufferMemory(max_messages=5)

    # Add messages
    memory.add_user_message("Hello!")
    memory.add_ai_message("Hi there! How can I help you?")
    memory.add_user_message("What's the weather like?")
    memory.add_ai_message("I don't have access to weather data.")

    # Get messages
    messages = memory.get_messages()
    print(f"Messages: {len(messages)}")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")

    # Get context string
    context = memory.get_context_string()
    print(f"\nContext:\n{context}")
    print()


def example_summary_memory():
    """Example: Conversation summary memory."""
    print("=== Summary Memory Example ===")

    # Define summarizer
    def summarizer(messages: List[Dict[str, str]], current_summary: str) -> str:
        new_text = " ".join(m["content"] for m in messages)
        if current_summary:
            return f"{current_summary}\n{new_text}"
        return new_text

    # Create memory
    memory = ConversationSummaryMemory(
        summarizer=summarizer,
        max_messages_before_summary=3,
    )

    # Add messages
    memory.add_user_message("Hello!")
    memory.add_ai_message("Hi there!")
    memory.add_user_message("How are you?")

    # Summary is triggered automatically
    summary = memory.get_summary()
    print(f"Summary: {summary}")
    print()


def example_window_memory():
    """Example: Conversation window memory."""
    print("=== Window Memory Example ===")

    # Create memory with window size 3
    memory = ConversationBufferWindowMemory(window_size=3)

    # Add messages
    memory.add_user_message("Message 1")
    memory.add_ai_message("Response 1")
    memory.add_user_message("Message 2")
    memory.add_ai_message("Response 2")
    memory.add_user_message("Message 3")

    # Only last 3 messages are kept
    messages = memory.get_messages()
    print(f"Messages in window: {len(messages)}")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")
    print()


def example_vector_memory():
    """Example: Vector store retriever memory."""
    print("=== Vector Memory Example ===")

    # Simple embedder (in practice, use a real embedding model)
    def embedder(text: str) -> List[float]:
        # Simple hash-based embedding for demonstration
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        return [b / 255.0 for b in hash_bytes]

    # Create memory
    memory = VectorStoreRetrieverMemory(
        embedder=embedder,
        dimension=16,
        top_k=3,
    )

    # Add messages
    memory.add_user_message("I love Python programming")
    memory.add_ai_message("Python is a great language!")
    memory.add_user_message("What about JavaScript?")
    memory.add_ai_message("JavaScript is also popular for web development.")

    # Search for relevant memories
    results = memory.search("programming languages")
    print(f"Search results: {len(results)}")
    for text, similarity in results:
        print(f"  {text} (similarity: {similarity:.2f})")
    print()


def example_tool_registry():
    """Example: Tool registry usage."""
    print("=== Tool Registry Example ===")

    # Create registry
    registry = ToolRegistry()

    # Register built-in tools
    registry.register(SearchTool())
    registry.register(CalculatorTool())
    registry.register(JSONTool())

    # List tools
    print(f"Registered tools: {registry.list_tools()}")

    # Execute calculator
    result = registry.execute("calculator", kwargs={"expression": "2 + 3 * 4"})
    print(f"Calculator: 2 + 3 * 4 = {result.data}")

    # Execute JSON parse
    result = registry.execute("json", kwargs={
        "action": "parse",
        "text": '{"name": "John", "age": 30}',
    })
    print(f"JSON parse: {result.data}")

    # Search tools
    results = registry.search_tools("calc")
    print(f"Search 'calc': {[t.name for t in results]}")
    print()


def example_custom_tool():
    """Example: Custom tool with decorator."""
    print("=== Custom Tool Example ===")

    # Create tool with decorator
    @tool(name="greet", description="Greet someone")
    def greet(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    # Use tool directly
    result = greet(name="World")
    print(f"Greet: {result}")

    # Get tool object
    tool_obj = greet.tool
    print(f"Tool name: {tool_obj.name}")
    print(f"Tool description: {tool_obj.description}")

    # Get schema
    schema = tool_obj.get_schema()
    print(f"Schema: {schema}")
    print()


def example_callbacks():
    """Example: Callback usage."""
    print("=== Callbacks Example ===")

    # Create callback manager
    manager = CallbackManager()

    # Add callbacks
    manager.add_callback(LoggingCallback())
    manager.add_callback(MetricsCallback())

    # Simulate events
    from .callbacks import CallbackEvent, CallbackEventType

    manager.dispatch(CallbackEvent(
        event_type=CallbackEventType.CHAIN_START,
        name="test_chain",
    ))

    manager.dispatch(CallbackEvent(
        event_type=CallbackEventType.CHAIN_END,
        name="test_chain",
    ))

    # Get metrics
    metrics_callback = manager.callbacks[1]
    metrics = metrics_callback.get_metrics()
    print(f"Metrics: {metrics}")
    print()


def example_streaming():
    """Example: Streaming callback."""
    print("=== Streaming Example ===")

    tokens = []

    # Create streaming callback
    callback = StreamingCallback(on_token=lambda t: tokens.append(t))

    # Simulate streaming
    from .callbacks import CallbackEvent, CallbackEventType

    callback.on_llm_start(CallbackEvent(
        event_type=CallbackEventType.LLM_START,
        name="test_llm",
    ))

    # Simulate tokens
    for token in ["Hello", " ", "World", "!"]:
        callback.on_llm_token(CallbackEvent(
            event_type=CallbackEventType.LLM_TOKEN,
            name="test_llm",
            data=token,
        ))

    callback.on_llm_end(CallbackEvent(
        event_type=CallbackEventType.LLM_END,
        name="test_llm",
    ))

    print(f"Streamed tokens: {tokens}")
    print(f"Full text: {''.join(tokens)}")
    print()


def example_chain_with_memory():
    """Example: Chain with memory integration."""
    print("=== Chain with Memory Example ===")

    # Create memory
    memory = ConversationBufferMemory()

    # Create chain that uses memory
    def process_with_memory(ctx: Dict[str, Any]) -> str:
        # Get history from memory
        history = memory.get_context_string()

        # Process input with history context
        input_text = ctx["input"]
        if history:
            return f"Processing '{input_text}' with history:\n{history}"
        return f"Processing '{input_text}' (no history)"

    chain = Chain("memory_chain")
    chain.add_step(ChainStep(
        name="process",
        function=process_with_memory,
    ))

    # First interaction
    memory.add_user_message("Hello")
    memory.add_ai_message("Hi there!")
    result1 = chain.invoke({"input": "How are you?"})
    print(f"First: {result1.data}")

    # Second interaction
    memory.add_user_message("I'm fine")
    memory.add_ai_message("Great to hear!")
    result2 = chain.invoke({"input": "What's new?"})
    print(f"\nSecond: {result2.data}")
    print()


def example_chain_with_tools():
    """Example: Chain with tool integration."""
    print("=== Chain with Tools Example ===")

    # Create tool registry
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    # Create chain that uses tools
    def calculate_expression(ctx: Dict[str, Any]) -> Any:
        expression = ctx["expression"]
        result = registry.execute("calculator", kwargs={"expression": expression})
        if result.success:
            return result.data
        raise RuntimeError(result.error)

    chain = Chain("calc_chain")
    chain.add_step(ChainStep(
        name="calculate",
        function=calculate_expression,
    ))
    chain.add_step(ChainStep(
        name="format",
        function=lambda ctx: f"Result: {ctx['calculate']}",
    ))

    # Execute chain
    result = chain.invoke({"expression": "2 + 3 * 4"})
    print(f"Expression: 2 + 3 * 4")
    print(f"Output: {result.data}")
    print()


def run_all_examples():
    """Run all examples."""
    print("PHOENIX AIOS LangChain Integration Examples")
    print("=" * 50)
    print()

    example_basic_chain()
    example_lcel_chain()
    example_sequential_chain()
    example_parallel_chain()
    example_conditional_chain()
    example_buffer_memory()
    example_summary_memory()
    example_window_memory()
    example_vector_memory()
    example_tool_registry()
    example_custom_tool()
    example_callbacks()
    example_streaming()
    example_chain_with_memory()
    example_chain_with_tools()


if __name__ == "__main__":
    run_all_examples()
