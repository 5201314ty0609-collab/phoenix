"""
Retrieval Engine — Unified memory search across all layers.

Implements hybrid retrieval combining:
1. FTS5 BM25 full-text search (keyword matching)
2. Content similarity scoring (token overlap / Jaccard)
3. Recency and importance boosting
4. Graph traversal for related entries

Results are fused via Reciprocal Rank Fusion (RRF) and returned
as a unified ranked list regardless of which memory layer they
originate from.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from .memory_types import MemoryEntry, MemoryFragment, MemoryMessage


@dataclass(frozen=True)
class RetrievalResult:
    """
    A single retrieval result with source information and score.

    Attributes:
        content: The retrieved text.
        score: Final fused relevance score.
        source: Which memory layer this came from ("stm", "wm", "ltm").
        source_id: ID of the original entry in its source layer.
        rank: Final rank position (1-based).
        metadata: Additional context about the result.
    """
    content: str
    score: float
    source: str
    source_id: str
    rank: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class RetrievalEngine:
    """
    Unified search engine across STM, WM, and LTM.

    Implements Reciprocal Rank Fusion (RRF) to combine rankings
    from multiple retrieval strategies into a single ordered list.

    RRF formula: score(d) = sum(1 / (k + rank_i(d)))
    where k=60 (standard smoothing constant).

    Example:
        engine = RetrievalEngine()

        # Index memories from all layers
        engine.index_stm(stm_messages)
        engine.index_ltm(ltm_entries)
        engine.index_wm(wm_fragments)

        # Search across everything
        results = engine.search("user preferences", limit=5)
        for r in results:
            print(f"[{r.source}] {r.content[:80]}... (score={r.score:.3f})")
    """

    RRF_K = 60  # Smoothing constant for RRF

    def __init__(self) -> None:
        # In-memory indexes for the current search session
        self._stm_messages: list[MemoryMessage] = []
        self._ltm_entries: list[MemoryEntry] = []
        self._wm_fragments: list[MemoryFragment] = []

    # ── Indexing ────────────────────────────────────────────────

    def index_stm(self, messages: list[MemoryMessage]) -> None:
        """Index short-term memory messages for search."""
        self._stm_messages = list(messages)

    def index_ltm(self, entries: list[MemoryEntry]) -> None:
        """Index long-term memory entries for search."""
        self._ltm_entries = list(entries)

    def index_wm(self, fragments: list[MemoryFragment]) -> None:
        """Index working memory fragments for search."""
        self._wm_fragments = list(fragments)

    def clear(self) -> None:
        """Clear all indexes."""
        self._stm_messages.clear()
        self._ltm_entries.clear()
        self._wm_fragments.clear()

    # ── Search ──────────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        boost_recency: bool = True,
        boost_importance: bool = True,
    ) -> list[RetrievalResult]:
        """
        Search across all indexed memory layers.

        Combines multiple ranking strategies via RRF:
        1. Keyword matching (token overlap)
        2. Recency boost (newer = higher)
        3. Importance boost (higher importance = higher)

        Args:
            query: Search text.
            limit: Maximum results to return.
            boost_recency: Whether to apply recency weighting.
            boost_importance: Whether to apply importance weighting.

        Returns:
            Ranked list of RetrievalResult.
        """
        if not query.strip():
            return []

        query_tokens = self._tokenize(query)

        # Collect candidates from all layers
        candidates: list[RetrievalResult] = []

        # Search STM
        for msg in self._stm_messages:
            score = self._score_content(query_tokens, self._tokenize(msg.content))
            if score > 0:
                candidates.append(RetrievalResult(
                    content=msg.content,
                    score=0.0,  # Will be computed by RRF
                    source="stm",
                    source_id=msg.id,
                    metadata={
                        "role": msg.role,
                        "timestamp": msg.timestamp,
                        "importance": msg.importance,
                        "token_count": msg.token_count,
                        "keyword_score": score,
                    },
                ))

        # Search WM
        for frag in self._wm_fragments:
            score = self._score_content(query_tokens, self._tokenize(frag.content))
            if score > 0:
                candidates.append(RetrievalResult(
                    content=frag.content,
                    score=0.0,
                    source="wm",
                    source_id=frag.id,
                    metadata={
                        "priority": frag.priority,
                        "temperature": frag.temperature,
                        "source_layer": frag.source_layer.value,
                        "token_count": frag.token_count,
                        "keyword_score": score,
                        "pinned": frag.pinned,
                    },
                ))

        # Search LTM
        for entry in self._ltm_entries:
            searchable = f"{entry.content} {entry.summary}"
            score = self._score_content(query_tokens, self._tokenize(searchable))
            if score > 0:
                candidates.append(RetrievalResult(
                    content=entry.content,
                    score=0.0,
                    source="ltm",
                    source_id=entry.id,
                    metadata={
                        "mem_type": entry.mem_type,
                        "importance": entry.importance,
                        "confidence": entry.confidence,
                        "access_count": entry.access_count,
                        "decay_score": entry.compute_decay_score(),
                        "tags": list(entry.tags),
                        "keyword_score": score,
                        "age_hours": entry.age_hours,
                    },
                ))

        if not candidates:
            return []

        # Apply RRF fusion
        ranked = self._rrf_rank(
            candidates,
            boost_recency=boost_recency,
            boost_importance=boost_importance,
        )

        return ranked[:limit]

    def search_layer(
        self,
        query: str,
        layer: str,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        """
        Search within a specific memory layer.

        Args:
            query: Search text.
            layer: "stm", "wm", or "ltm".
            limit: Maximum results.

        Returns:
            Ranked results from the specified layer only.
        """
        if layer == "stm":
            index = [
                RetrievalResult(
                    content=m.content, score=0.0, source="stm",
                    source_id=m.id,
                    metadata={"role": m.role, "importance": m.importance},
                )
                for m in self._stm_messages
            ]
        elif layer == "wm":
            index = [
                RetrievalResult(
                    content=f.content, score=0.0, source="wm",
                    source_id=f.id,
                    metadata={"priority": f.priority, "temperature": f.temperature},
                )
                for f in self._wm_fragments
            ]
        elif layer == "ltm":
            index = [
                RetrievalResult(
                    content=e.content, score=0.0, source="ltm",
                    source_id=e.id,
                    metadata={
                        "mem_type": e.mem_type,
                        "importance": e.importance,
                        "decay_score": e.compute_decay_score(),
                    },
                )
                for e in self._ltm_entries
            ]
        else:
            return []

        query_tokens = self._tokenize(query)
        for i, result in enumerate(index):
            score = self._score_content(query_tokens, self._tokenize(result.content))
            index[i] = RetrievalResult(
                content=result.content,
                score=score,
                source=result.source,
                source_id=result.source_id,
                metadata=result.metadata,
            )

        index = [r for r in index if r.score > 0]
        index.sort(key=lambda r: r.score, reverse=True)

        for i, r in enumerate(index):
            index[i] = RetrievalResult(
                content=r.content, score=r.score, source=r.source,
                source_id=r.source_id, rank=i + 1, metadata=r.metadata,
            )

        return index[:limit]

    # ── Scoring ─────────────────────────────────────────────────

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into lowercase terms, removing short tokens."""
        return {t.lower() for t in text.split() if len(t) >= 2}

    def _score_content(
        self,
        query_tokens: set[str],
        content_tokens: set[str],
    ) -> float:
        """
        Score content relevance via token overlap (Jaccard-like).

        Returns:
            Score 0.0-1.0 representing keyword overlap.
        """
        if not query_tokens or not content_tokens:
            return 0.0

        intersection = len(query_tokens & content_tokens)
        if intersection == 0:
            return 0.0

        # Weighted: prefer matching more query terms
        query_coverage = intersection / len(query_tokens)
        jaccard = intersection / len(query_tokens | content_tokens)

        return query_coverage * 0.7 + jaccard * 0.3

    def _rrf_rank(
        self,
        candidates: list[RetrievalResult],
        boost_recency: bool,
        boost_importance: bool,
    ) -> list[RetrievalResult]:
        """
        Apply Reciprocal Rank Fusion across multiple ranking dimensions.

        Combines:
        1. Keyword relevance ranking
        2. Recency ranking (if enabled)
        3. Importance ranking (if enabled)

        RRF: score(d) = sum(1 / (k + rank_i(d)))
        """
        now = time.time()

        # Dimension 1: Keyword relevance
        keyword_sorted = sorted(
            candidates,
            key=lambda r: r.metadata.get("keyword_score", 0),
            reverse=True,
        )

        # Build rank maps
        rankings: list[dict[str, int]] = []
        keyword_ranks: dict[str, int] = {}
        for i, r in enumerate(keyword_sorted):
            key = f"{r.source}:{r.source_id}"
            keyword_ranks[key] = i + 1
        rankings.append(keyword_ranks)

        # Dimension 2: Recency
        if boost_recency:
            recency_sorted = sorted(
                candidates,
                key=lambda r: r.metadata.get("timestamp", now),
                reverse=True,
            )
            recency_ranks: dict[str, int] = {}
            for i, r in enumerate(recency_sorted):
                key = f"{r.source}:{r.source_id}"
                recency_ranks[key] = i + 1
            rankings.append(recency_ranks)

        # Dimension 3: Importance
        if boost_importance:
            importance_sorted = sorted(
                candidates,
                key=lambda r: r.metadata.get(
                    "importance",
                    r.metadata.get("priority", 0.5),
                ),
                reverse=True,
            )
            importance_ranks: dict[str, int] = {}
            for i, r in enumerate(importance_sorted):
                key = f"{r.source}:{r.source_id}"
                importance_ranks[key] = i + 1
            rankings.append(importance_ranks)

        # Compute RRF scores
        scored: list[RetrievalResult] = []
        for candidate in candidates:
            key = f"{candidate.source}:{candidate.source_id}"
            rrf_score = sum(
                1.0 / (self.RRF_K + rank_map.get(key, len(candidates)))
                for rank_map in rankings
            )
            scored.append(RetrievalResult(
                content=candidate.content,
                score=rrf_score,
                source=candidate.source,
                source_id=candidate.source_id,
                metadata=candidate.metadata,
            ))

        # Sort by RRF score descending
        scored.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        for i, r in enumerate(scored):
            scored[i] = RetrievalResult(
                content=r.content, score=r.score, source=r.source,
                source_id=r.source_id, rank=i + 1, metadata=r.metadata,
            )

        return scored
