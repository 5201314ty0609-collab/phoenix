"""
Verification script for PHOENIX AIOS LangChain Integration.

Verifies that all modules can be imported correctly.
"""

import sys
from typing import List, Tuple


def verify_imports() -> List[Tuple[str, bool, str]]:
    """
    Verify all imports.

    Returns:
        List of (module, success, message) tuples
    """
    results = []

    # Test core imports
    try:
        from .core import BaseComponent, Config, Logger, ExecutionResult, ComponentRegistry
        results.append(("core", True, "Core module imported successfully"))
    except Exception as e:
        results.append(("core", False, f"Core module failed: {e}"))

    # Test chain imports
    try:
        from .chains import (
            Chain, ChainStep, LCELChain, LCELStep,
            SequentialChain, ParallelChain, ConditionalChain, Condition,
        )
        results.append(("chains", True, "Chains module imported successfully"))
    except Exception as e:
        results.append(("chains", False, f"Chains module failed: {e}"))

    # Test memory imports
    try:
        from .memory import (
            Memory, ConversationBufferMemory, ConversationSummaryMemory,
            ConversationBufferWindowMemory, VectorStoreRetrieverMemory,
        )
        results.append(("memory", True, "Memory module imported successfully"))
    except Exception as e:
        results.append(("memory", False, f"Memory module failed: {e}"))

    # Test tools imports
    try:
        from .tools import (
            Tool, ToolRegistry, tool,
            SearchTool, CalculatorTool, JSONTool, RegexTool,
        )
        results.append(("tools", True, "Tools module imported successfully"))
    except Exception as e:
        results.append(("tools", False, f"Tools module failed: {e}"))

    # Test callbacks imports
    try:
        from .callbacks import (
            Callback, CallbackEvent, CallbackManager,
            StreamingCallback, LoggingCallback, MetricsCallback,
        )
        results.append(("callbacks", True, "Callbacks module imported successfully"))
    except Exception as e:
        results.append(("callbacks", False, f"Callbacks module failed: {e}"))

    # Test main package imports
    try:
        from . import (
            Chain, LCELChain, SequentialChain, ParallelChain,
            Memory, ConversationBufferMemory, ConversationSummaryMemory,
            Tool, ToolRegistry, tool,
            CallbackManager, StreamingCallback,
        )
        results.append(("package", True, "Main package imported successfully"))
    except Exception as e:
        results.append(("package", False, f"Main package failed: {e}"))

    return results


def verify_functionality() -> List[Tuple[str, bool, str]]:
    """
    Verify basic functionality.

    Returns:
        List of (test, success, message) tuples
    """
    results = []

    # Test chain creation and execution
    try:
        from .chains import Chain, ChainStep

        chain = Chain("test")
        chain.add_step(ChainStep("double", lambda ctx: ctx["input"] * 2))
        result = chain.invoke({"input": 5})

        if result.success and result.data == 10:
            results.append(("chain_execution", True, "Chain execution works"))
        else:
            results.append(("chain_execution", False, f"Chain execution failed: {result}"))
    except Exception as e:
        results.append(("chain_execution", False, f"Chain execution failed: {e}"))

    # Test LCEL chain
    try:
        from .chains import LCELChain, LCELStep

        chain = (
            LCELChain("test")
            | LCELStep("double", lambda x: x * 2)
            | LCELStep("add_one", lambda x: x + 1)
        )
        result = chain.invoke(5)

        if result.success and result.data == 11:
            results.append(("lcel_chain", True, "LCEL chain works"))
        else:
            results.append(("lcel_chain", False, f"LCEL chain failed: {result}"))
    except Exception as e:
        results.append(("lcel_chain", False, f"LCEL chain failed: {e}"))

    # Test memory
    try:
        from .memory import ConversationBufferMemory

        memory = ConversationBufferMemory()
        memory.add_user_message("Hello")
        memory.add_ai_message("Hi!")
        messages = memory.get_messages()

        if len(messages) == 2:
            results.append(("memory", True, "Memory works"))
        else:
            results.append(("memory", False, f"Memory failed: {messages}"))
    except Exception as e:
        results.append(("memory", False, f"Memory failed: {e}"))

    # Test tools
    try:
        from .tools import ToolRegistry, CalculatorTool

        registry = ToolRegistry()
        registry.register(CalculatorTool())
        result = registry.execute("calculator", kwargs={"expression": "2 + 3"})

        if result.success and result.data == 5:
            results.append(("tools", True, "Tools work"))
        else:
            results.append(("tools", False, f"Tools failed: {result}"))
    except Exception as e:
        results.append(("tools", False, f"Tools failed: {e}"))

    # Test callbacks
    try:
        from .callbacks import CallbackManager, MetricsCallback, CallbackEvent, CallbackEventType

        manager = CallbackManager()
        manager.add_callback(MetricsCallback())

        event = CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="test",
        )
        manager.dispatch(event)

        metrics = manager.callbacks[0].get_metrics()
        if metrics["counters"]["chain_starts"] == 1:
            results.append(("callbacks", True, "Callbacks work"))
        else:
            results.append(("callbacks", False, f"Callbacks failed: {metrics}"))
    except Exception as e:
        results.append(("callbacks", False, f"Callbacks failed: {e}"))

    return results


def main():
    """Run verification."""
    print("PHOENIX AIOS LangChain Integration - Verification")
    print("=" * 50)
    print()

    # Verify imports
    print("Verifying imports...")
    import_results = verify_imports()
    for module, success, message in import_results:
        status = "✓" if success else "✗"
        print(f"  {status} {module}: {message}")

    print()

    # Verify functionality
    print("Verifying functionality...")
    functionality_results = verify_functionality()
    for test, success, message in functionality_results:
        status = "✓" if success else "✗"
        print(f"  {status} {test}: {message}")

    print()

    # Summary
    total_imports = len(import_results)
    successful_imports = sum(1 for _, success, _ in import_results if success)

    total_functionality = len(functionality_results)
    successful_functionality = sum(1 for _, success, _ in functionality_results if success)

    print("Summary")
    print("-" * 50)
    print(f"Imports: {successful_imports}/{total_imports} successful")
    print(f"Functionality: {successful_functionality}/{total_functionality} successful")

    if successful_imports == total_imports and successful_functionality == total_functionality:
        print("\n✓ All verifications passed!")
        return 0
    else:
        print("\n✗ Some verifications failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
