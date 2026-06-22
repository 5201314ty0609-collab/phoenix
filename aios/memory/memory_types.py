"""
Core memory data structures for PHOENIX AIOS Memory System.

All types are immutable (frozen=True) following PHOENIX immutability principle.
Modifications create new instances via with_* methods.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ── Enums ──────────────────────────────────────────────────────────────────


class MemoryLayer(Enum):
    """Which memory layer owns this entry."""
    STM = "stm"           # Short-term memory
    WM = "wm"             # Working memory
    LTM = "ltm"           # Long-term memory


class MemoryStatus(Enum):
    """Lifecycle status of a memory entry."""
    ACTIVE = "active"       # Normal, retrievable
    COMPRESSED = "compressed"  # Summarized, original archived
    ARCHIVED = "archived"   # Moved to cold storage
    DECAYED = "decayed"     # Below decay threshold, pending cleanup
    FORGOTTEN = "forgotten" # Marked for deletion


class RelationType(Enum):
    """Types of relations between memory entries."""
    RELATED_TO = "related_to"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    PART_OF = "part_of"


class DecayCurve(Enum):
    """Decay function shapes for memory relevance."""
    EBINGHAUS = "ebinghaus"    # R = e^(-t/S), classic forgetting curve
    LINEAR = "linear"          # R = max(0, 1 - t/max_age)
    STEP = "step"              # R = 1 if t < threshold, else 0
    LOGISTIC = "logistic"      # S-curve decay


# ── Data Classes ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MemoryMessage:
    """
    A single message in conversation history (short-term memory unit).

    Represents one turn in a dialogue: user message, assistant response,
    system instruction, or tool interaction.

    Attributes:
        id: Unique message identifier.
        role: Speaker role (user/assistant/system/tool).
        content: Raw message text.
        token_count: Estimated token count for budget management.
        timestamp: Unix timestamp of message creation.
        importance: Computed importance score 0.0-1.0.
        metadata: Arbitrary key-value metadata (immutable tuple of pairs).
    """
    id: str
    role: str
    content: str
    token_count: int
    timestamp: float
    importance: float = 0.5
    metadata: tuple[tuple[str, Any], ...] = ()

    @staticmethod
    def create(
        role: str,
        content: str,
        token_count: int | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryMessage:
        """Create a new MemoryMessage with auto-generated ID and timestamp."""
        estimated_tokens = token_count or _estimate_tokens(content)
        meta_tuple = tuple(sorted((metadata or {}).items()))
        return MemoryMessage(
            id=_new_id(),
            role=role,
            content=content,
            token_count=estimated_tokens,
            timestamp=time.time(),
            importance=importance,
            metadata=meta_tuple,
        )

    def with_importance(self, new_importance: float) -> MemoryMessage:
        """Return a new message with updated importance."""
        return MemoryMessage(
            id=self.id,
            role=self.role,
            content=self.content,
            token_count=self.token_count,
            timestamp=self.timestamp,
            importance=max(0.0, min(1.0, new_importance)),
            metadata=self.metadata,
        )

    @property
    def meta_dict(self) -> dict[str, Any]:
        """Convert immutable metadata tuple back to dict."""
        return dict(self.metadata)


@dataclass(frozen=True)
class MemoryEntry:
    """
    A persistent memory entry in long-term storage.

    Represents a unit of knowledge, experience, or procedure that persists
    across sessions. Subject to Ebbinghaus decay unless recalled.

    Attributes:
        id: Unique entry identifier.
        content: The memory content (text).
        summary: Short summary for quick display and injection.
        mem_type: Memory type (semantic/episodic/procedural/relational).
        importance: Base importance score 0.0-1.0.
        confidence: Extraction/source confidence 0.0-1.0.
        status: Current lifecycle status.
        layer: Which memory layer owns this entry.
        created_at: Unix timestamp of creation.
        last_accessed: Unix timestamp of last access.
        access_count: Number of times this memory has been recalled.
        decay_strength: Current decay strength (higher = slower decay).
        decay_curve: Shape of the decay function.
        ttl_days: Maximum days to live without recall.
        tags: Classification tags.
        source: Origin identifier (session-id, filename, etc.).
        embedding: Optional vector embedding for semantic search.
    """
    id: str
    content: str
    summary: str
    mem_type: str
    importance: float
    confidence: float
    status: MemoryStatus
    layer: MemoryLayer
    created_at: float
    last_accessed: float
    access_count: int
    decay_strength: float
    decay_curve: DecayCurve
    ttl_days: int
    tags: tuple[str, ...]
    source: str
    embedding: tuple[float, ...] | None = None

    @staticmethod
    def create(
        content: str,
        summary: str = "",
        mem_type: str = "semantic",
        importance: float = 0.5,
        confidence: float = 0.8,
        tags: tuple[str, ...] = (),
        source: str = "",
        decay_curve: DecayCurve = DecayCurve.EBINGHAUS,
        ttl_days: int = 90,
    ) -> MemoryEntry:
        """Create a new MemoryEntry with auto-generated fields."""
        now = time.time()
        return MemoryEntry(
            id=_new_id(),
            content=content,
            summary=summary or content[:120],
            mem_type=mem_type,
            importance=max(0.0, min(1.0, importance)),
            confidence=max(0.0, min(1.0, confidence)),
            status=MemoryStatus.ACTIVE,
            layer=MemoryLayer.LTM,
            created_at=now,
            last_accessed=now,
            access_count=0,
            decay_strength=1.0,
            decay_curve=decay_curve,
            ttl_days=ttl_days,
            tags=tags,
            source=source,
        )

    @property
    def age_hours(self) -> float:
        """Hours since creation."""
        return (time.time() - self.created_at) / 3600.0

    @property
    def idle_hours(self) -> float:
        """Hours since last access."""
        return (time.time() - self.last_accessed) / 3600.0

    def compute_decay_score(self) -> float:
        """
        Compute current relevance score based on decay curve.

        Combines:
        - Recency: exponential decay based on idle time
        - Frequency: log-scale access count boost
        - Importance: base importance weight

        Returns:
            Float 0.0-1.0 representing current relevance.
        """
        import math

        # Recency component
        if self.decay_curve == DecayCurve.EBINGHAUS:
            recency = math.exp(-self.idle_hours / (self.decay_strength * 24.0))
        elif self.decay_curve == DecayCurve.LINEAR:
            max_hours = self.ttl_days * 24.0
            recency = max(0.0, 1.0 - self.idle_hours / max_hours)
        elif self.decay_curve == DecayCurve.STEP:
            threshold_hours = self.ttl_days * 24.0 * 0.5
            recency = 1.0 if self.idle_hours < threshold_hours else 0.0
        else:  # LOGISTIC
            midpoint = self.ttl_days * 12.0  # Half-life at ttl_days/2
            steepness = 0.1
            recency = 1.0 / (1.0 + math.exp(steepness * (self.idle_hours - midpoint)))

        # Frequency component (log scale, capped)
        frequency = 1.0 + min(math.log1p(self.access_count) * 0.1, 0.5)

        # Combined score
        score = recency * frequency * self.importance
        return max(0.0, min(1.0, score))

    def accessed(self) -> MemoryEntry:
        """Return new entry with updated access metadata (recall boost)."""
        return MemoryEntry(
            id=self.id,
            content=self.content,
            summary=self.summary,
            mem_type=self.mem_type,
            importance=self.importance,
            confidence=self.confidence,
            status=self.status,
            layer=self.layer,
            created_at=self.created_at,
            last_accessed=time.time(),
            access_count=self.access_count + 1,
            decay_strength=min(self.decay_strength + 0.3, 3.0),
            decay_curve=self.decay_curve,
            ttl_days=self.ttl_days,
            tags=self.tags,
            source=self.source,
            embedding=self.embedding,
        )

    def with_status(self, new_status: MemoryStatus) -> MemoryEntry:
        """Return new entry with updated status."""
        return MemoryEntry(
            id=self.id,
            content=self.content,
            summary=self.summary,
            mem_type=self.mem_type,
            importance=self.importance,
            confidence=self.confidence,
            status=new_status,
            layer=self.layer,
            created_at=self.created_at,
            last_accessed=self.last_accessed,
            access_count=self.access_count,
            decay_strength=self.decay_strength,
            decay_curve=self.decay_curve,
            ttl_days=self.ttl_days,
            tags=self.tags,
            source=self.source,
            embedding=self.embedding,
        )


@dataclass(frozen=True)
class MemoryFragment:
    """
    A chunk of content in working memory.

    Working memory holds a limited number of fragments ranked by priority.
    Fragments can be promoted from STM/LTM or created directly for the
    current reasoning context.

    Attributes:
        id: Unique fragment identifier.
        content: The fragment text.
        source_layer: Which memory layer this was promoted from.
        source_id: ID of the original memory entry (if promoted).
        priority: Priority score 0.0-1.0 (higher = more important).
        temperature: Hot/warm/cold tier for access management.
        created_at: Unix timestamp.
        last_accessed: Unix timestamp.
        access_count: Number of accesses since promotion.
        token_count: Estimated token count.
        pinned: If True, never evicted automatically.
    """
    id: str
    content: str
    source_layer: MemoryLayer
    source_id: str
    priority: float
    temperature: float
    created_at: float
    last_accessed: float
    access_count: int
    token_count: int
    pinned: bool = False

    @staticmethod
    def create(
        content: str,
        source_layer: MemoryLayer = MemoryLayer.WM,
        source_id: str = "",
        priority: float = 0.5,
        pinned: bool = False,
    ) -> MemoryFragment:
        """Create a new working memory fragment."""
        now = time.time()
        return MemoryFragment(
            id=_new_id(),
            content=content,
            source_layer=source_layer,
            source_id=source_id or _new_id(),
            priority=max(0.0, min(1.0, priority)),
            temperature=1.0,
            created_at=now,
            last_accessed=now,
            access_count=0,
            token_count=_estimate_tokens(content),
            pinned=pinned,
        )

    def accessed(self) -> MemoryFragment:
        """Return new fragment with updated access and temperature boost."""
        return MemoryFragment(
            id=self.id,
            content=self.content,
            source_layer=self.source_layer,
            source_id=self.source_id,
            priority=self.priority,
            temperature=min(self.temperature + 0.2, 1.0),
            created_at=self.created_at,
            last_accessed=time.time(),
            access_count=self.access_count + 1,
            token_count=self.token_count,
            pinned=self.pinned,
        )

    def cool_down(self, factor: float = 0.9) -> MemoryFragment:
        """Return new fragment with reduced temperature."""
        return MemoryFragment(
            id=self.id,
            content=self.content,
            source_layer=self.source_layer,
            source_id=self.source_id,
            priority=self.priority,
            temperature=max(0.0, self.temperature * factor),
            created_at=self.created_at,
            last_accessed=self.last_accessed,
            access_count=self.access_count,
            token_count=self.token_count,
            pinned=self.pinned,
        )

    @property
    def effective_priority(self) -> float:
        """Priority adjusted by temperature and recency."""
        age_factor = max(0.1, 1.0 - (time.time() - self.last_accessed) / 3600.0)
        return self.priority * self.temperature * age_factor


@dataclass(frozen=True)
class MemoryRelation:
    """
    A directed relation between two memory entries.

    Forms the edges in the memory graph for traversal and discovery.
    """
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    reason: str = ""
    created_at: float = field(default_factory=time.time)

    def with_weight(self, new_weight: float) -> MemoryRelation:
        """Return new relation with updated weight."""
        return MemoryRelation(
            source_id=self.source_id,
            target_id=self.target_id,
            relation_type=self.relation_type,
            weight=max(0.0, new_weight),
            reason=self.reason,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class MemoryStats:
    """Aggregated statistics across all memory layers."""
    stm_count: int
    stm_tokens: int
    wm_count: int
    wm_tokens: int
    ltm_count: int
    ltm_active: int
    ltm_archived: int
    ltm_decayed: int
    total_relations: int
    avg_decay_score: float
    oldest_entry_age_days: float
    most_accessed_count: int
    compression_ratio: float  # compressed / original token ratio


# ── Helpers ────────────────────────────────────────────────────────────────


def _new_id() -> str:
    """Generate a unique ID for memory entries."""
    return uuid.uuid4().hex[:16]


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses a simple heuristic: ~4 characters per token for English,
    ~2 characters per token for CJK. Falls back to len/4.
    """
    if not text:
        return 0
    cjk_chars = sum(1 for c in text if '一' <= c <= '鿿')
    non_cjk = len(text) - cjk_chars
    return (cjk_chars * 2 + non_cjk) // 4 + 1
