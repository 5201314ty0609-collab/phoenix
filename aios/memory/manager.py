"""
Memory Manager — Unified interface for the PHOENIX AIOS Memory System.

Provides a single entry point for all memory operations:
- Short-term memory (conversation history)
- Working memory (active reasoning context)
- Long-term memory (persistent knowledge)
- Unified search across all layers
- Automatic consolidation
- Session lifecycle management

The MemoryManager coordinates between all three memory layers
and the retrieval/consolidation engines.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

from .compressor import CompressionResult, MemoryCompressor
from .config import MemoryConfig
from .consolidation import ConsolidationEngine, ConsolidationReport
from .long_term import LongTermMemory
from .memory_types import (
    DecayCurve,
    MemoryEntry,
    MemoryFragment,
    MemoryLayer,
    MemoryMessage,
    MemoryRelation,
    MemoryStats,
    MemoryStatus,
    RelationType,
)
from .retrieval import RetrievalEngine, RetrievalResult
from .short_term import ShortTermMemory
from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Unified memory manager for PHOENIX AIOS.

    Coordinates STM, WM, and LTM with automatic consolidation,
    hybrid retrieval, and session lifecycle management.

    Thread-safe: all public methods use a reentrant lock.

    Example:
        # Create with default config
        mm = MemoryManager()

        # Session start: prime with relevant memories
        mm.session_start(session_id="sess-001")

        # Add conversation messages
        mm.add_message(role="user", content="How do I configure dark mode?")
        mm.add_message(role="assistant", content="You can set it in Settings > Appearance.")

        # Focus working memory on a topic
        mm.focus("dark mode configuration")

        # Search across all memory layers
        results = mm.search("user preferences")

        # Store an important insight
        mm.remember(
            content="User prefers dark mode across all apps",
            importance=0.9,
            tags=("preference", "ui"),
        )

        # Session end: consolidate and persist
        mm.session_end()
    """

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._config = config or MemoryConfig.default()
        self._lock = threading.RLock()
        self._session_id: str = ""

        # Initialize memory layers
        self._stm = ShortTermMemory(self._config.stm)
        self._wm = WorkingMemory(self._config.wm)
        self._ltm = LongTermMemory(self._config.ltm)

        # Initialize engines
        self._retrieval = RetrievalEngine()
        self._consolidation = ConsolidationEngine(
            self._config, self._stm, self._wm, self._ltm
        )
        self._compressor = MemoryCompressor()

        # Operation log
        self._log_path = Path(os.path.expanduser(
            str(self._config.db_path)
        )).parent / "memory-operations.jsonl"

    # ── Properties ──────────────────────────────────────────────

    @property
    def stm(self) -> ShortTermMemory:
        """Short-term memory layer."""
        return self._stm

    @property
    def wm(self) -> WorkingMemory:
        """Working memory layer."""
        return self._wm

    @property
    def ltm(self) -> LongTermMemory:
        """Long-term memory layer."""
        return self._ltm

    @property
    def config(self) -> MemoryConfig:
        """Current configuration."""
        return self._config

    @property
    def session_id(self) -> str:
        """Current session ID."""
        return self._session_id

    # ── Session Lifecycle ───────────────────────────────────────

    def session_start(
        self,
        session_id: str,
        prime_query: str = "",
        max_prime_results: int = 5,
    ) -> list[RetrievalResult]:
        """
        Start a new memory session.

        Optionally primes working memory with relevant LTM entries
        based on a query or recent context.

        Args:
            session_id: Unique session identifier.
            prime_query: Optional query to prime WM with relevant memories.
            max_prime_results: Maximum memories to prime.

        Returns:
            List of primed memories (if query provided).
        """
        with self._lock:
            self._session_id = session_id
            self._stm.clear()
            self._wm.clear_all()

            self._log_operation("session_start", {"session_id": session_id})

            primed: list[RetrievalResult] = []

            if prime_query:
                # Search LTM for relevant entries
                ltm_results = self._ltm.search(prime_query, limit=max_prime_results)
                for entry in ltm_results:
                    # Promote to working memory
                    self._wm.add(
                        content=entry.content,
                        source_layer=MemoryLayer.LTM,
                        source_id=entry.id,
                        priority=entry.importance,
                    )
                    primed.append(RetrievalResult(
                        content=entry.content,
                        score=entry.compute_decay_score(),
                        source="ltm",
                        source_id=entry.id,
                        metadata={
                            "mem_type": entry.mem_type,
                            "importance": entry.importance,
                            "tags": list(entry.tags),
                        },
                    ))

                    # Recall to boost decay
                    self._ltm.recall(entry.id)

            self._log_operation("session_primed", {
                "query": prime_query,
                "primed_count": len(primed),
            })

            return primed

    def session_end(self) -> ConsolidationReport:
        """
        End the current session and run consolidation.

        Promotes important content to LTM, runs decay, and cleans up.

        Returns:
            ConsolidationReport with session-end changes.
        """
        with self._lock:
            # Run consolidation
            report = self._consolidation.run()

            self._log_operation("session_end", {
                "session_id": self._session_id,
                "stm_count": self._stm.count,
                "wm_count": self._wm.count,
                "promoted": report.promoted_to_ltm,
                "ltm_cleaned": report.ltm_cleaned,
            })

            return report

    # ── Message Operations ──────────────────────────────────────

    def add_message(
        self,
        role: str,
        content: str,
        importance: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryMessage:
        """
        Add a message to short-term memory.

        Args:
            role: Speaker role (user/assistant/system/tool).
            content: Message text.
            importance: Optional explicit importance.
            metadata: Optional metadata.

        Returns:
            The created MemoryMessage.
        """
        with self._lock:
            msg = self._stm.add(
                role=role,
                content=content,
                importance=importance,
                metadata=metadata,
            )

            self._log_operation("add_message", {
                "role": role,
                "tokens": msg.token_count,
                "importance": msg.importance,
            })

            # Check if consolidation is needed
            if self._stm.needs_summarization:
                self._consolidation.run()

            return msg

    def get_recent_messages(self, n: int = 10) -> list[MemoryMessage]:
        """Get the N most recent messages from STM."""
        return self._stm.recent(n)

    # ── Working Memory Operations ───────────────────────────────

    def focus(self, query: str, max_results: int = 5) -> list[MemoryFragment]:
        """
        Focus working memory on a topic.

        Warms matching fragments and cools non-matching ones.
        Also searches LTM and STM for relevant content to add.

        Args:
            query: Topic to focus on.
            max_results: Maximum fragments to return.

        Returns:
            Top matching fragments.
        """
        with self._lock:
            # Focus existing WM content
            results = self._wm.focus(query, max_results)

            # Also search LTM for additional context
            ltm_entries = self._ltm.search(query, limit=max_results)
            for entry in ltm_entries:
                # Check if already in WM
                if not any(f.source_id == entry.id for f in self._wm.ranked()):
                    self._wm.add(
                        content=entry.content,
                        source_layer=MemoryLayer.LTM,
                        source_id=entry.id,
                        priority=entry.importance,
                    )
                    self._ltm.recall(entry.id)

            self._log_operation("focus", {
                "query": query,
                "wm_count": self._wm.count,
                "ltm_matches": len(ltm_entries),
            })

            return results

    def add_to_wm(
        self,
        content: str,
        priority: float = 0.5,
        pinned: bool = False,
    ) -> MemoryFragment:
        """
        Add a fragment directly to working memory.

        Args:
            content: Fragment text.
            priority: Priority 0.0-1.0.
            pinned: If True, never evicted.

        Returns:
            The created MemoryFragment.
        """
        return self._wm.add(
            content=content,
            source_layer=MemoryLayer.WM,
            priority=priority,
            pinned=pinned,
        )

    # ── Long-Term Memory Operations ─────────────────────────────

    def remember(
        self,
        content: str,
        summary: str = "",
        mem_type: str = "semantic",
        importance: float = 0.5,
        confidence: float = 0.8,
        tags: tuple[str, ...] = (),
        source: str = "",
        decay_curve: DecayCurve = DecayCurve.EBINGHAUS,
        ttl_days: int | None = None,
    ) -> MemoryEntry:
        """
        Store a memory in long-term storage.

        This is the primary way to persist important information
        that should survive across sessions.

        Args:
            content: Memory content text.
            summary: Short summary.
            mem_type: Type (semantic/episodic/procedural/relational).
            importance: Base importance 0.0-1.0.
            confidence: Extraction confidence 0.0-1.0.
            tags: Classification tags.
            source: Origin identifier.
            decay_curve: Decay function shape.
            ttl_days: Maximum days without recall.

        Returns:
            The stored MemoryEntry.
        """
        with self._lock:
            entry = self._ltm.store(
                content=content,
                summary=summary,
                mem_type=mem_type,
                importance=importance,
                confidence=confidence,
                tags=tags,
                source=source or f"session:{self._session_id}",
                decay_curve=decay_curve,
                ttl_days=ttl_days,
            )

            self._log_operation("remember", {
                "entry_id": entry.id,
                "mem_type": mem_type,
                "importance": importance,
                "tags": list(tags),
            })

            return entry

    def recall(self, entry_id: str) -> MemoryEntry | None:
        """
        Recall a long-term memory (resets decay).

        Args:
            entry_id: Target entry ID.

        Returns:
            Updated MemoryEntry if found.
        """
        entry = self._ltm.recall(entry_id)
        if entry:
            self._log_operation("recall", {"entry_id": entry_id})
        return entry

    def forget(self, entry_id: str) -> bool:
        """
        Explicitly forget (delete) a long-term memory.

        Args:
            entry_id: Target entry ID.

        Returns:
            True if entry was found and deleted.
        """
        result = self._ltm.delete(entry_id)
        if result:
            self._log_operation("forget", {"entry_id": entry_id})
        return result

    def link(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType = RelationType.RELATED_TO,
        weight: float = 1.0,
        reason: str = "",
    ) -> MemoryRelation | None:
        """
        Create a relation between two LTM entries.

        Args:
            source_id: Source entry ID.
            target_id: Target entry ID.
            relation_type: Type of relation.
            weight: Relation strength.
            reason: Optional explanation.

        Returns:
            The created MemoryRelation, or None if entries don't exist.
        """
        return self._ltm.add_relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            reason=reason,
        )

    # ── Unified Search ──────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        layers: tuple[str, ...] = ("stm", "wm", "ltm"),
    ) -> list[RetrievalResult]:
        """
        Search across all memory layers with RRF fusion.

        Args:
            query: Search text.
            limit: Maximum results.
            layers: Which layers to search ("stm", "wm", "ltm").

        Returns:
            Ranked results fused across all requested layers.
        """
        with self._lock:
            # Index current state
            if "stm" in layers:
                self._retrieval.index_stm(list(self._stm))
            if "wm" in layers:
                self._retrieval.index_wm(self._wm.ranked())
            if "ltm" in layers:
                ltm_entries = list(self._ltm.iter_active(limit=200))
                self._retrieval.index_ltm(ltm_entries)

            results = self._retrieval.search(query, limit=limit)

            self._log_operation("search", {
                "query": query,
                "layers": list(layers),
                "results": len(results),
            })

            return results

    def search_ltm(
        self,
        query: str,
        limit: int = 10,
        mem_type: str | None = None,
    ) -> list[MemoryEntry]:
        """
        Search long-term memory specifically (FTS5).

        Args:
            query: Search text.
            limit: Maximum results.
            mem_type: Optional type filter.

        Returns:
            Matching LTM entries.
        """
        return self._ltm.search(query, limit=limit, mem_type=mem_type)

    def search_by_tags(
        self,
        tags: tuple[str, ...],
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search LTM entries by tags."""
        return self._ltm.search_by_tags(tags, limit=limit)

    # ── Consolidation ───────────────────────────────────────────

    def consolidate(self) -> ConsolidationReport:
        """
        Run a manual consolidation cycle.

        Returns:
            ConsolidationReport with all changes made.
        """
        with self._lock:
            report = self._consolidation.run()
            self._log_operation("consolidate", {
                "stm_compressed": report.stm_compressed,
                "wm_evicted": report.wm_evicted,
                "ltm_decayed": report.ltm_decayed,
                "ltm_cleaned": report.ltm_cleaned,
                "promoted": report.promoted_to_ltm,
                "duration_ms": report.duration_ms,
            })
            return report

    # ── Statistics ──────────────────────────────────────────────

    def stats(self) -> MemoryStats:
        """
        Get aggregated statistics across all memory layers.

        Returns:
            MemoryStats with system-wide metrics.
        """
        ltm_stats = self._ltm.stats()

        # Average decay score
        decay_scores = self._ltm.compute_decay_scores()
        avg_decay = (
            sum(s for _, s in decay_scores) / len(decay_scores)
            if decay_scores else 0.0
        )

        # Oldest entry age
        oldest_age = 0.0
        if decay_scores:
            # The lowest decay score is likely the oldest
            for entry_id, _ in decay_scores:
                entry = self._ltm.get(entry_id)
                if entry:
                    oldest_age = max(oldest_age, entry.age_hours / 24.0)
                    break

        # Most accessed
        most_accessed = 0
        for entry in self._ltm.iter_active(limit=1):
            most_accessed = entry.access_count

        return MemoryStats(
            stm_count=self._stm.count,
            stm_tokens=self._stm.total_tokens,
            wm_count=self._wm.count,
            wm_tokens=self._wm.total_tokens,
            ltm_count=ltm_stats["total"],
            ltm_active=ltm_stats["active"],
            ltm_archived=ltm_stats["archived"],
            ltm_decayed=ltm_stats["decayed"],
            total_relations=ltm_stats["relations"],
            avg_decay_score=round(avg_decay, 3),
            oldest_entry_age_days=round(oldest_age, 1),
            most_accessed_count=most_accessed,
            compression_ratio=0.0,  # Computed during consolidation
        )

    def ltm_stats(self) -> dict:
        """Get detailed LTM statistics."""
        return self._ltm.stats()

    # ── Context Export ──────────────────────────────────────────

    def export_context(self, max_tokens: int = 8000) -> str:
        """
        Export a unified context string from all memory layers.

        Combines WM contents with recent STM messages, suitable
        for injection into an LLM prompt.

        Args:
            max_tokens: Maximum token budget for the context.

        Returns:
            Formatted context string.
        """
        parts: list[str] = []
        used_tokens = 0

        # Working memory (highest priority)
        wm_context = self._wm.export_context(max_tokens=max_tokens // 2)
        if wm_context:
            parts.append(f"[Active Context]\n{wm_context}")
            used_tokens += len(wm_context) // 4  # Rough estimate

        # Recent STM messages
        remaining = max_tokens - used_tokens
        if remaining > 0:
            recent = self._stm.recent(20)
            stm_lines: list[str] = []
            for msg in recent:
                line = f"[{msg.role}] {msg.content}"
                line_tokens = len(line) // 4
                if used_tokens + line_tokens > max_tokens:
                    break
                stm_lines.append(line)
                used_tokens += line_tokens

            if stm_lines:
                parts.append(f"[Recent Conversation]\n" + "\n".join(stm_lines))

        return "\n\n".join(parts)

    # ── Serialization ───────────────────────────────────────────

    def save_state(self, path: str | Path | None = None) -> Path:
        """
        Save current memory state to a JSON file.

        Args:
            path: File path (default: memory-state.json in DB directory).

        Returns:
            Path to the saved file.
        """
        if path is None:
            path = Path(os.path.expanduser(
                str(self._config.db_path)
            )).parent / "memory-state.json"
        else:
            path = Path(path)

        state = {
            "session_id": self._session_id,
            "timestamp": time.time(),
            "stm": self._stm.to_list(),
            "wm": self._wm.to_list(),
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False))

        return path

    def load_state(self, path: str | Path) -> bool:
        """
        Load memory state from a JSON file.

        Only restores STM and WM state. LTM is loaded from the database.

        Args:
            path: File path to load from.

        Returns:
            True if state was loaded successfully.
        """
        path = Path(path)
        if not path.exists():
            return False

        try:
            state = json.loads(path.read_text())
            self._session_id = state.get("session_id", "")
            self._stm.from_list(state.get("stm", []))
            self._wm.from_list(state.get("wm", []))
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load memory state: %s", e)
            return False

    # ── Internal ────────────────────────────────────────────────

    def _log_operation(self, op: str, data: dict[str, Any]) -> None:
        """Log a memory operation to JSONL."""
        if not self._config.log_operations:
            return

        try:
            entry = {
                "timestamp": time.time(),
                "session_id": self._session_id,
                "operation": op,
                **data,
            }
            log_path = self._log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # Non-critical, don't break memory operations
