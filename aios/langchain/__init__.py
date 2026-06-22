"""
PHOENIX AIOS LangChain Integration Framework

A comprehensive LangChain integration for PHOENIX AIOS, providing:
- Chain definition and execution framework
- Memory management with multiple strategies
- Tool registration and execution
- Callback and streaming support
- Integration with PHOENIX state management

Usage:
    from aios.langchain import Chain, Memory, Tool

    # Create a chain
    chain = Chain("my_chain")
    chain.add_step(prompt_step)
    chain.add_step(llm_step)

    # Execute
    result = chain.invoke({"input": "Hello"})
"""

__version__ = "1.0.0"
__author__ = "PHOENIX Team"

from .chains import Chain, LCELChain, SequentialChain, ParallelChain
from .memory import Memory, ConversationBufferMemory, ConversationSummaryMemory
from .tools import Tool, ToolRegistry, tool
from .callbacks import CallbackManager, StreamingCallback
from .core import BaseComponent, Config, Logger

__all__ = [
    # Chains
    "Chain",
    "LCELChain",
    "SequentialChain",
    "ParallelChain",

    # Memory
    "Memory",
    "ConversationBufferMemory",
    "ConversationSummaryMemory",

    # Tools
    "Tool",
    "ToolRegistry",
    "tool",

    # Callbacks
    "CallbackManager",
    "StreamingCallback",

    # Core
    "BaseComponent",
    "Config",
    "Logger",
]
