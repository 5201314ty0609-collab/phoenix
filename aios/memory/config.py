"""
Memory configuration for PHOENIX AIOS Memory System.

Provides typed configuration for each memory layer with sensible defaults.
All configs are immutable (frozen dataclasses).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────────

PHOENIX_HOME = Path(os.environ.get("PHOENIX_HOME", Path.home() / ".claude" / "phoenix"))
DEFAULT_DB_PATH = PHOENIX_HOME / "aios" / "memory.db"
DEFAULT_LTM_DB_PATH = PHOENIX_HOME / "knowledge-base.db"


@dataclass(frozen=True)
class STMConfig:
    """
    Short-Term Memory configuration.

    Controls conversation history buffer size and eviction behavior.

    Attributes:
        max_messages: Maximum messages to retain before eviction.
        max_tokens: Maximum total token budget for STM.
        summarize_threshold: When STM exceeds this ratio of max_messages,
            trigger summarization of older messages.
        importance_boost_user: Importance multiplier for user messages.
        importance_boost_assistant: Importance multiplier for assistant messages.
        importance_boost_system: Importance multiplier for system messages.
        importance_boost_tool: Importance multiplier for tool interactions.
    """
    max_messages: int = 200
    max_tokens: int = 100_000
    summarize_threshold: float = 0.8
    importance_boost_user: float = 1.0
    importance_boost_assistant: float = 0.8
    importance_boost_system: float = 1.2
    importance_boost_tool: float = 0.6


@dataclass(frozen=True)
class WMConfig:
    """
    Working Memory configuration.

    Controls the active reasoning context window.

    Attributes:
        max_fragments: Maximum fragments in working memory.
        max_tokens: Maximum total token budget for WM.
        hot_threshold: Temperature above which a fragment is "hot".
        cold_threshold: Temperature below which a fragment is evicted.
        cool_factor: Temperature multiplier applied each consolidation cycle.
        default_priority: Default priority for new fragments.
        pin_max: Maximum number of pinned fragments (never evicted).
    """
    max_fragments: int = 50
    max_tokens: int = 50_000
    hot_threshold: float = 0.7
    cold_threshold: float = 0.1
    cool_factor: float = 0.9
    default_priority: float = 0.5
    pin_max: int = 10


@dataclass(frozen=True)
class LTMConfig:
    """
    Long-Term Memory configuration.

    Controls persistent knowledge storage and decay behavior.

    Attributes:
        db_path: Path to the SQLite database file.
        default_ttl_days: Default time-to-live for new memories.
        decay_threshold: Decay score below which entries are marked DECAYED.
        forget_threshold: Decay score below which entries are marked FORGOTTEN.
        importance_weight: Weight of importance in decay score computation.
        frequency_weight: Weight of access frequency in decay score.
        recency_weight: Weight of recency in decay score.
        recall_boost: Decay strength added on each recall.
        max_decay_strength: Maximum decay strength cap.
        auto_relation_threshold: Jaccard similarity threshold for auto-linking.
        max_relations_per_entry: Maximum outgoing relations per entry.
    """
    db_path: Path = field(default_factory=lambda: DEFAULT_LTM_DB_PATH)
    default_ttl_days: int = 90
    decay_threshold: float = 0.15
    forget_threshold: float = 0.05
    importance_weight: float = 0.4
    frequency_weight: float = 0.3
    recency_weight: float = 0.3
    recall_boost: float = 0.3
    max_decay_strength: float = 3.0
    auto_relation_threshold: float = 0.15
    max_relations_per_entry: int = 20


@dataclass(frozen=True)
class MemoryConfig:
    """
    Unified memory system configuration.

    Combines STM, WM, and LTM configs with system-wide settings.

    Attributes:
        stm: Short-term memory configuration.
        wm: Working memory configuration.
        ltm: Long-term memory configuration.
        db_path: Path to the unified memory database.
        enable_compression: Whether to enable automatic compression.
        compression_token_threshold: Token count above which compression triggers.
        consolidation_interval_seconds: Seconds between consolidation cycles.
        enable_auto_relations: Whether to auto-detect relations between entries.
        enable_embedding: Whether to compute embeddings for semantic search.
        log_operations: Whether to log memory operations to JSONL.
    """
    stm: STMConfig = field(default_factory=STMConfig)
    wm: WMConfig = field(default_factory=WMConfig)
    ltm: LTMConfig = field(default_factory=LTMConfig)
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)
    enable_compression: bool = True
    compression_token_threshold: int = 5_000
    consolidation_interval_seconds: float = 300.0
    enable_auto_relations: bool = True
    enable_embedding: bool = False
    log_operations: bool = True

    @classmethod
    def default(cls) -> MemoryConfig:
        """Default configuration suitable for most use cases."""
        return cls()

    @classmethod
    def compact(cls) -> MemoryConfig:
        """
        Compact configuration for resource-constrained environments.
        Smaller buffers, shorter TTLs, aggressive compression.
        """
        return cls(
            stm=STMConfig(max_messages=50, max_tokens=20_000),
            wm=WMConfig(max_fragments=20, max_tokens=10_000),
            ltm=LTMConfig(default_ttl_days=30, decay_threshold=0.2),
            enable_compression=True,
            compression_token_threshold=2_000,
            consolidation_interval_seconds=120.0,
        )

    @classmethod
    def expansive(cls) -> MemoryConfig:
        """
        Expansive configuration for high-resource environments.
        Larger buffers, longer TTLs, full features enabled.
        """
        return cls(
            stm=STMConfig(max_messages=500, max_tokens=300_000),
            wm=WMConfig(max_fragments=100, max_tokens=100_000),
            ltm=LTMConfig(default_ttl_days=365, decay_threshold=0.1),
            enable_compression=True,
            compression_token_threshold=20_000,
            consolidation_interval_seconds=600.0,
            enable_auto_relations=True,
            enable_embedding=True,
        )
