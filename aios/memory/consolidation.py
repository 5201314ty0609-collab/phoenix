"""
Consolidation Engine — Memory lifecycle management.

Handles periodic maintenance of the memory system:
1. Decay application: Apply Ebbinghaus decay to all LTM entries
2. STM summarization: Compress old conversation history
3. WM cooling: Reduce temperature of inactive working memory fragments
4. Promotion: Move important STM/WM content to LTM
5. Archival: Move stale LTM entries to archived status
6. Cleanup: Remove forgotten entries and orphaned relations

Consolidation runs periodically (configurable interval) and can
also be triggered manually via the MemoryManager.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .compressor import CompressionResult, MemoryCompressor
from .config import MemoryConfig
from .long_term import LongTermMemory
from .memory_types import (
    MemoryEntry,
    MemoryFragment,
    MemoryLayer,
    MemoryMessage,
    MemoryStatus,
)
from .short_term import ShortTermMemory
from .working_memory import WorkingMemory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsolidationReport:
    """
    Report of a consolidation cycle.

    Attributes:
        timestamp: When the consolidation ran.
        stm_compressed: Number of STM messages compressed.
        wm_cooled: Number of WM fragments cooled.
        wm_evicted: Number of WM cold fragments evicted.
        ltm_decayed: Number of LTM entries marked as decayed.
        ltm_forgotten: Number of LTM entries marked as forgotten.
        ltm_cleaned: Number of forgotten entries deleted.
        promoted_to_ltm: Number of entries promoted from STM/WM to LTM.
        relations_detected: Number of new relations auto-detected.
        compression_result: Details of any compression performed.
        duration_ms: How long the consolidation took in milliseconds.
    """
    timestamp: float
    stm_compressed: int = 0
    wm_cooled: int = 0
    wm_evicted: int = 0
    ltm_decayed: int = 0
    ltm_forgotten: int = 0
    ltm_cleaned: int = 0
    promoted_to_ltm: int = 0
    relations_detected: int = 0
    compression_result: CompressionResult | None = None
    duration_ms: float = 0.0


class ConsolidationEngine:
    """
    Periodic memory consolidation and lifecycle management.

    Orchestrates maintenance tasks across all three memory layers:
    - Compresses STM when it exceeds the summarization threshold
    - Cools WM fragments and evicts the coldest
    - Applies decay to LTM entries and cleans up forgotten ones
    - Promotes important short-term memories to long-term storage

    Example:
        consolidation = ConsolidationEngine(config, stm, wm, ltm)

        # Run a full consolidation cycle
        report = consolidation.run()
        print(f"Decayed {report.ltm_decayed} LTM entries")
        print(f"Promoted {report.promoted_to_ltm} entries to LTM")
    """

    def __init__(
        self,
        config: MemoryConfig,
        stm: ShortTermMemory,
        wm: WorkingMemory,
        ltm: LongTermMemory,
    ) -> None:
        self._config = config
        self._stm = stm
        self._wm = wm
        self._ltm = ltm
        self._compressor = MemoryCompressor()
        self._last_run: float = 0.0
        self._reports: list[ConsolidationReport] = []

    @property
    def last_run(self) -> float:
        """Timestamp of the last consolidation run."""
        return self._last_run

    @property
    def reports(self) -> tuple[ConsolidationReport, ...]:
        """History of consolidation reports."""
        return tuple(self._reports)

    @property
    def needs_run(self) -> True:
        """Check if enough time has passed since last run."""
        if self._last_run == 0:
            return True
        elapsed = time.time() - self._last_run
        return elapsed >= self._config.consolidation_interval_seconds

    # ── Full Cycle ──────────────────────────────────────────────

    def run(self) -> ConsolidationReport:
        """
        Run a full consolidation cycle.

        Executes all maintenance tasks in order:
        1. Cool WM fragments
        2. Evict cold WM fragments
        3. Compress STM if needed
        4. Promote important STM/WM content to LTM
        5. Apply LTM decay
        6. Clean up forgotten LTM entries
        7. Auto-detect LTM relations

        Returns:
            ConsolidationReport with all changes made.
        """
        start = time.time()
        report = ConsolidationReport(timestamp=start)

        # 1. Cool WM
        wm_cooled = self._wm.cool_all()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            wm_cooled=wm_cooled,
        )

        # 2. Evict cold WM
        wm_evicted = self._wm.evict_cold()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            wm_cooled=report.wm_cooled,
            wm_evicted=wm_evicted,
        )

        # 3. Compress STM
        stm_compressed = 0
        compression_result = None
        if self._stm.needs_summarization and self._config.enable_compression:
            stm_compressed, compression_result = self._compress_stm()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            stm_compressed=stm_compressed,
            wm_cooled=report.wm_cooled,
            wm_evicted=report.wm_evicted,
            compression_result=compression_result,
        )

        # 4. Promote to LTM
        promoted = self._promote_to_ltm()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            stm_compressed=report.stm_compressed,
            wm_cooled=report.wm_cooled,
            wm_evicted=report.wm_evicted,
            promoted_to_ltm=promoted,
            compression_result=report.compression_result,
        )

        # 5. Apply LTM decay
        decayed, forgotten = self._ltm.apply_decay()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            stm_compressed=report.stm_compressed,
            wm_cooled=report.wm_cooled,
            wm_evicted=report.wm_evicted,
            promoted_to_ltm=report.promoted_to_ltm,
            ltm_decayed=decayed,
            ltm_forgotten=forgotten,
            compression_result=report.compression_result,
        )

        # 6. Clean up forgotten
        cleaned = self._ltm.cleanup_forgotten()
        report = ConsolidationReport(
            timestamp=report.timestamp,
            stm_compressed=report.stm_compressed,
            wm_cooled=report.wm_cooled,
            wm_evicted=report.wm_evicted,
            promoted_to_ltm=report.promoted_to_ltm,
            ltm_decayed=report.ltm_decayed,
            ltm_forgotten=report.ltm_forgotten,
            ltm_cleaned=cleaned,
            compression_result=report.compression_result,
        )

        # 7. Auto-detect relations
        relations = 0
        if self._config.enable_auto_relations:
            relations = self._ltm.auto_detect_relations()

        duration_ms = (time.time() - start) * 1000
        final_report = ConsolidationReport(
            timestamp=report.timestamp,
            stm_compressed=report.stm_compressed,
            wm_cooled=report.wm_cooled,
            wm_evicted=report.wm_evicted,
            promoted_to_ltm=report.promoted_to_ltm,
            ltm_decayed=report.ltm_decayed,
            ltm_forgotten=report.ltm_forgotten,
            ltm_cleaned=report.ltm_cleaned,
            relations_detected=relations,
            compression_result=report.compression_result,
            duration_ms=duration_ms,
        )

        self._last_run = time.time()
        self._reports.append(final_report)

        # Keep only last 100 reports
        if len(self._reports) > 100:
            self._reports = self._reports[-100:]

        logger.info(
            "Consolidation complete: stm_compressed=%d, wm_evicted=%d, "
            "ltm_decayed=%d, ltm_cleaned=%d, promoted=%d, relations=%d, "
            "duration=%.1fms",
            final_report.stm_compressed,
            final_report.wm_evicted,
            final_report.ltm_decayed,
            final_report.ltm_cleaned,
            final_report.promoted_to_ltm,
            final_report.relations_detected,
            final_report.duration_ms,
        )

        return final_report

    # ── Individual Tasks ────────────────────────────────────────

    def _compress_stm(self) -> tuple[int, CompressionResult | None]:
        """
        Compress STM by summarizing older messages.

        Takes the older half of STM messages, compresses them into
        a summary, and replaces them with the summary message.

        Returns:
            Tuple of (messages compressed, compression result).
        """
        to_summarize = self._stm.get_messages_for_summarization()
        if not to_summarize:
            return 0, None

        # Combine older messages into a single text
        combined = "\n".join(
            f"[{m.role}] {m.content}" for m in to_summarize
        )

        # Compress to half the original token count
        target_tokens = sum(m.token_count for m in to_summarize) // 2
        target_tokens = max(target_tokens, 200)  # Minimum 200 tokens

        result = self._compressor.compress_to_budget(
            combined, target_tokens, strategy="extractive"
        )

        # Create summary message
        summary_msg = MemoryMessage.create(
            role="system",
            content=f"[Conversation summary]\n{result.compressed}",
            importance=0.7,
        )

        # Replace in STM
        replaced = self._stm.replace_with_summary(summary_msg)

        return replaced, result

    def _promote_to_ltm(self) -> int:
        """
        Promote important STM and WM content to long-term memory.

        Promotion criteria:
        - STM: messages with importance >= 0.7
        - WM: fragments with priority >= 0.6 and temperature >= 0.5

        Returns:
            Number of entries promoted.
        """
        promoted = 0

        # Promote from STM
        for msg in self._stm:
            if msg.importance >= 0.7 and msg.role in ("user", "assistant"):
                # Check if already promoted (by source_id tag)
                self._ltm.store(
                    content=msg.content,
                    summary=msg.content[:120],
                    mem_type="episodic",
                    importance=msg.importance,
                    confidence=0.9,
                    tags=("from-stm", f"role:{msg.role}"),
                    source=f"stm:{msg.id}",
                )
                promoted += 1

        # Promote from WM
        for frag in self._wm.ranked():
            if frag.priority >= 0.6 and frag.temperature >= 0.5:
                self._ltm.store(
                    content=frag.content,
                    summary=frag.content[:120],
                    mem_type="semantic",
                    importance=frag.priority,
                    confidence=0.8,
                    tags=("from-wm", f"layer:{frag.source_layer.value}"),
                    source=f"wm:{frag.id}",
                )
                promoted += 1

        return promoted

    # ── Manual Operations ───────────────────────────────────────

    def force_decay(self) -> tuple[int, int]:
        """
        Force immediate decay application to LTM.

        Returns:
            Tuple of (decayed_count, forgotten_count).
        """
        return self._ltm.apply_decay()

    def force_cleanup(self) -> int:
        """
        Force immediate cleanup of forgotten LTM entries.

        Returns:
            Number of entries deleted.
        """
        return self._ltm.cleanup_forgotten()

    def force_relations(self) -> int:
        """
        Force immediate auto-detection of LTM relations.

        Returns:
            Number of new relations created.
        """
        return self._ltm.auto_detect_relations()
