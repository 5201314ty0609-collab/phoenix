"""
PHOENIX AIOS Memory Management System

Three-layer memory architecture for AI agents:

1. Short-Term Memory (STM)
   - Conversation history within a session
   - FIFO eviction with importance weighting
   - Automatic summarization when capacity is reached

2. Long-Term Memory (LTM)
   - Persistent knowledge across sessions
   - SQLite + FTS5 for full-text search
   - Ebbinghaus decay curve for relevance scoring
   - Graph relations between memory nodes

3. Working Memory (WM)
   - Active context window for current reasoning
   - Priority-ranked slots with limited capacity
   - Hot/warm/cold temperature tiers
   - Automatic promotion/demotion based on access patterns

Architecture:
    ┌──────────────────────────────────────────────────────────┐
    │                    Memory Manager                         │
    │  ┌────────────┐  ┌────────────┐  ┌───────────────────┐  │
    │  │  Short-Term │  │  Working   │  │    Long-Term      │  │
    │  │   Memory    │  │  Memory    │  │     Memory        │  │
    │  │  (STM)      │  │  (WM)      │  │     (LTM)         │  │
    │  └──────┬──────┘  └─────┬──────┘  └────────┬──────────┘  │
    │         │               │                   │             │
    │  ┌──────┴───────────────┴───────────────────┴──────────┐  │
    │  │              Retrieval Engine                        │  │
    │  │         (Hybrid FTS5 + Vector + Graph)               │  │
    │  └──────────────────────┬───────────────────────────────┘  │
    │                         │                                  │
    │  ┌──────────────────────┴───────────────────────────────┐  │
    │  │              Consolidation Engine                     │  │
    │  │        (Compression + Archival + Decay)               │  │
    │  └──────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────┘

Usage:
    from aios.memory import MemoryManager

    manager = MemoryManager()

    # Short-term: add conversation messages
    manager.stm.add(role="user", content="Hello")
    manager.stm.add(role="assistant", content="Hi there!")

    # Working memory: activate relevant memories
    manager.wm.focus("greeting context")

    # Long-term: persist important memories
    manager.ltm.store(content="User prefers dark mode", importance=0.8)

    # Unified search across all layers
    results = manager.search("user preferences")

    # Consolidate: compress and archive stale memories
    manager.consolidate()
"""

from __future__ import annotations

from .memory_types import (
    MemoryEntry,
    MemoryMessage,
    MemoryFragment,
    MemoryRelation,
    MemoryStats,
    MemoryLayer,
    MemoryStatus,
    RelationType,
    DecayCurve,
)
from .config import MemoryConfig, STMConfig, WMConfig, LTMConfig
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .working_memory import WorkingMemory
from .retrieval import RetrievalEngine, RetrievalResult
from .consolidation import ConsolidationEngine
from .compressor import MemoryCompressor
from .manager import MemoryManager

__all__ = [
    # Core types
    "MemoryEntry",
    "MemoryMessage",
    "MemoryFragment",
    "MemoryRelation",
    "MemoryStats",
    "MemoryLayer",
    "MemoryStatus",
    "RelationType",
    "DecayCurve",
    # Configuration
    "MemoryConfig",
    "STMConfig",
    "WMConfig",
    "LTMConfig",
    # Memory layers
    "ShortTermMemory",
    "LongTermMemory",
    "WorkingMemory",
    # Engines
    "RetrievalEngine",
    "RetrievalResult",
    "ConsolidationEngine",
    "MemoryCompressor",
    # Manager
    "MemoryManager",
]
