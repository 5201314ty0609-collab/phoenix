"""
Working Memory (WM) — Active reasoning context window.

Working memory holds the currently relevant information for active
reasoning. It has limited capacity and uses priority-based eviction
with temperature decay.

Key concepts:
- Fragments: Individual pieces of information in WM
- Temperature: Hot/warm/cold tiers that decay over time
- Priority: Importance-weighted ranking for eviction
- Pinned: Some fragments are pinned and never evicted
- Focus: Query-driven activation of relevant memories from STM/LTM

Working memory is the "mental workspace" where the agent holds
information it is actively reasoning about.
"""

from __future__ import annotations

import threading
import time
from typing import Callable

from .config import WMConfig
from .memory_types import (
    MemoryFragment,
    MemoryLayer,
    _estimate_tokens,
)


class WorkingMemory:
    """
    Active reasoning context with priority-based eviction.

    Fragments enter working memory from STM, LTM, or direct creation.
    They cool down over time and are evicted when cold and capacity
    is needed for new fragments.

    Thread-safe: all public methods use a reentrant lock.

    Example:
        wm = WorkingMemory()

        # Add a fragment directly
        frag = wm.add("The user prefers dark mode", priority=0.8)

        # Focus on a topic — promotes relevant fragments
        wm.focus("user preferences")

        # Check what's active
        for f in wm.hot_fragments():
            print(f.content)
    """

    def __init__(self, config: WMConfig | None = None) -> None:
        self._config = config or WMConfig()
        self._fragments: dict[str, MemoryFragment] = {}
        self._lock = threading.RLock()

        # Callbacks
        self._on_evict: list[Callable[[MemoryFragment], None]] = []
        self._on_promote: list[Callable[[MemoryFragment], None]] = []

    # ── Properties ──────────────────────────────────────────────

    @property
    def count(self) -> int:
        """Number of fragments in working memory."""
        return len(self._fragments)

    @property
    def total_tokens(self) -> int:
        """Total token count of all fragments."""
        return sum(f.token_count for f in self._fragments.values())

    @property
    def is_full(self) -> bool:
        """True if WM is at or over capacity."""
        return (
            self.count >= self._config.max_fragments
            or self.total_tokens >= self._config.max_tokens
        )

    @property
    def pinned_count(self) -> int:
        """Number of pinned (non-evictable) fragments."""
        return sum(1 for f in self._fragments.values() if f.pinned)

    @property
    def config(self) -> WMConfig:
        """Current WM configuration."""
        return self._config

    # ── Core Operations ─────────────────────────────────────────

    def add(
        self,
        content: str,
        source_layer: MemoryLayer = MemoryLayer.WM,
        source_id: str = "",
        priority: float | None = None,
        pinned: bool = False,
    ) -> MemoryFragment:
        """
        Add a fragment to working memory.

        If capacity is exceeded, the coldest non-pinned fragment is evicted.

        Args:
            content: Fragment text.
            source_layer: Origin memory layer.
            source_id: ID of original entry (if promoted from STM/LTM).
            priority: Priority 0.0-1.0 (config default if None).
            pinned: If True, never evicted automatically.

        Returns:
            The created MemoryFragment.
        """
        with self._lock:
            if priority is None:
                priority = self._config.default_priority

            frag = MemoryFragment.create(
                content=content,
                source_layer=source_layer,
                source_id=source_id,
                priority=priority,
                pinned=pinned,
            )

            # Evict coldest if at capacity
            self._evict_to_capacity(need_slots=1)

            self._fragments[frag.id] = frag

            for cb in self._on_promote:
                cb(frag)

            return frag

    def get(self, fragment_id: str) -> MemoryFragment | None:
        """Retrieve a fragment by ID and warm it up."""
        with self._lock:
            frag = self._fragments.get(fragment_id)
            if frag is None:
                return None
            # Access warms the fragment
            updated = frag.accessed()
            self._fragments[fragment_id] = updated
            return updated

    def remove(self, fragment_id: str) -> bool:
        """
        Manually remove a fragment from working memory.

        Args:
            fragment_id: Target fragment ID.

        Returns:
            True if fragment was found and removed.
        """
        with self._lock:
            frag = self._fragments.pop(fragment_id, None)
            if frag is not None:
                for cb in self._on_evict:
                    cb(frag)
                return True
            return False

    def update_priority(self, fragment_id: str, priority: float) -> bool:
        """
        Update a fragment's priority.

        Args:
            fragment_id: Target fragment ID.
            priority: New priority 0.0-1.0.

        Returns:
            True if fragment was found.
        """
        with self._lock:
            frag = self._fragments.get(fragment_id)
            if frag is None:
                return False
            # Create new fragment with updated priority
            updated = MemoryFragment(
                id=frag.id,
                content=frag.content,
                source_layer=frag.source_layer,
                source_id=frag.source_id,
                priority=max(0.0, min(1.0, priority)),
                temperature=frag.temperature,
                created_at=frag.created_at,
                last_accessed=frag.last_accessed,
                access_count=frag.access_count,
                token_count=frag.token_count,
                pinned=frag.pinned,
            )
            self._fragments[fragment_id] = updated
            return True

    def pin(self, fragment_id: str) -> bool:
        """Pin a fragment to prevent automatic eviction."""
        with self._lock:
            frag = self._fragments.get(fragment_id)
            if frag is None:
                return False
            self._fragments[fragment_id] = MemoryFragment(
                id=frag.id, content=frag.content,
                source_layer=frag.source_layer, source_id=frag.source_id,
                priority=frag.priority, temperature=frag.temperature,
                created_at=frag.created_at, last_accessed=frag.last_accessed,
                access_count=frag.access_count, token_count=frag.token_count,
                pinned=True,
            )
            return True

    def unpin(self, fragment_id: str) -> bool:
        """Unpin a fragment to allow automatic eviction."""
        with self._lock:
            frag = self._fragments.get(fragment_id)
            if frag is None:
                return False
            self._fragments[fragment_id] = MemoryFragment(
                id=frag.id, content=frag.content,
                source_layer=frag.source_layer, source_id=frag.source_id,
                priority=frag.priority, temperature=frag.temperature,
                created_at=frag.created_at, last_accessed=frag.last_accessed,
                access_count=frag.access_count, token_count=frag.token_count,
                pinned=False,
            )
            return True

    def clear(self) -> int:
        """
        Clear all (non-pinned) fragments from working memory.

        Returns:
            Number of fragments removed.
        """
        with self._lock:
            to_remove = [
                fid for fid, frag in self._fragments.items()
                if not frag.pinned
            ]
            for fid in to_remove:
                frag = self._fragments.pop(fid)
                for cb in self._on_evict:
                    cb(frag)
            return len(to_remove)

    def clear_all(self) -> int:
        """Clear ALL fragments including pinned ones."""
        with self._lock:
            count = len(self._fragments)
            self._fragments.clear()
            return count

    # ── Query ───────────────────────────────────────────────────

    def hot_fragments(self) -> list[MemoryFragment]:
        """Get fragments above the hot temperature threshold."""
        with self._lock:
            return sorted(
                [
                    f for f in self._fragments.values()
                    if f.temperature >= self._config.hot_threshold
                ],
                key=lambda f: f.effective_priority,
                reverse=True,
            )

    def cold_fragments(self) -> list[MemoryFragment]:
        """Get fragments below the cold temperature threshold."""
        with self._lock:
            return sorted(
                [
                    f for f in self._fragments.values()
                    if f.temperature <= self._config.cold_threshold
                ],
                key=lambda f: f.temperature,
            )

    def ranked(self) -> list[MemoryFragment]:
        """Get all fragments ranked by effective priority."""
        with self._lock:
            return sorted(
                self._fragments.values(),
                key=lambda f: f.effective_priority,
                reverse=True,
            )

    def search(self, query: str, limit: int = 10) -> list[MemoryFragment]:
        """
        Search fragments by content substring match.

        Args:
            query: Search text (case-insensitive).
            limit: Maximum results.

        Returns:
            Matching fragments sorted by effective priority.
        """
        query_lower = query.lower()
        with self._lock:
            matches = [
                f for f in self._fragments.values()
                if query_lower in f.content.lower()
            ]
            matches.sort(key=lambda f: f.effective_priority, reverse=True)
            return matches[:limit]

    def focus(self, query: str, max_results: int = 5) -> list[MemoryFragment]:
        """
        Focus working memory on a topic.

        Warms up fragments matching the query and returns the
        most relevant ones. Non-matching fragments cool down.

        Args:
            query: Topic to focus on.
            max_results: Maximum fragments to return.

        Returns:
            Top matching fragments after temperature adjustment.
        """
        query_lower = query.lower()
        with self._lock:
            matched_ids: set[str] = set()

            for frag in self._fragments.values():
                if query_lower in frag.content.lower():
                    # Warm up matching fragment
                    self._fragments[frag.id] = MemoryFragment(
                        id=frag.id, content=frag.content,
                        source_layer=frag.source_layer, source_id=frag.source_id,
                        priority=frag.priority,
                        temperature=min(frag.temperature + 0.3, 1.0),
                        created_at=frag.created_at,
                        last_accessed=time.time(),
                        access_count=frag.access_count + 1,
                        token_count=frag.token_count,
                        pinned=frag.pinned,
                    )
                    matched_ids.add(frag.id)
                else:
                    # Cool down non-matching fragment
                    self._fragments[frag.id] = frag.cool_down(
                        self._config.cool_factor
                    )

            # Return top matches
            matched = [
                self._fragments[fid] for fid in matched_ids
            ]
            matched.sort(key=lambda f: f.effective_priority, reverse=True)
            return matched[:max_results]

    # ── Temperature Management ──────────────────────────────────

    def cool_all(self, factor: float | None = None) -> int:
        """
        Cool down all (non-pinned) fragments.

        Args:
            factor: Temperature multiplier (config default if None).

        Returns:
            Number of fragments cooled.
        """
        if factor is None:
            factor = self._config.cool_factor

        with self._lock:
            cooled = 0
            for fid, frag in self._fragments.items():
                if not frag.pinned:
                    self._fragments[fid] = frag.cool_down(factor)
                    cooled += 1
            return cooled

    def evict_cold(self) -> int:
        """
        Evict all fragments below the cold threshold.

        Returns:
            Number of fragments evicted.
        """
        with self._lock:
            to_evict = [
                fid for fid, frag in self._fragments.items()
                if frag.temperature <= self._config.cold_threshold
                and not frag.pinned
            ]
            for fid in to_evict:
                frag = self._fragments.pop(fid)
                for cb in self._on_evict:
                    cb(frag)
            return len(to_evict)

    # ── Context Export ──────────────────────────────────────────

    def export_context(self, max_tokens: int | None = None) -> str:
        """
        Export working memory contents as a context string.

        Suitable for injection into prompts. Fragments are ordered
        by effective priority and truncated to fit the token budget.

        Args:
            max_tokens: Maximum token budget (config default if None).

        Returns:
            Concatenated fragment content, highest priority first.
        """
        if max_tokens is None:
            max_tokens = self._config.max_tokens

        ranked = self.ranked()
        lines: list[str] = []
        used_tokens = 0

        for frag in ranked:
            if used_tokens + frag.token_count > max_tokens:
                break
            lines.append(frag.content)
            used_tokens += frag.token_count

        return "\n---\n".join(lines)

    # ── Callbacks ───────────────────────────────────────────────

    def on_evict(self, callback: Callable[[MemoryFragment], None]) -> None:
        """Register a callback for fragment eviction events."""
        self._on_evict.append(callback)

    def on_promote(self, callback: Callable[[MemoryFragment], None]) -> None:
        """Register a callback for fragment promotion events."""
        self._on_promote.append(callback)

    # ── Serialization ───────────────────────────────────────────

    def to_list(self) -> list[dict]:
        """Serialize all fragments to a list of dicts."""
        with self._lock:
            return [
                {
                    "id": f.id,
                    "content": f.content,
                    "source_layer": f.source_layer.value,
                    "source_id": f.source_id,
                    "priority": f.priority,
                    "temperature": f.temperature,
                    "created_at": f.created_at,
                    "last_accessed": f.last_accessed,
                    "access_count": f.access_count,
                    "token_count": f.token_count,
                    "pinned": f.pinned,
                }
                for f in self._fragments.values()
            ]

    def from_list(self, data: list[dict]) -> int:
        """
        Load fragments from a list of dicts.

        Returns:
            Number of fragments loaded.
        """
        with self._lock:
            self._fragments.clear()
            for d in data:
                frag = MemoryFragment(
                    id=d["id"],
                    content=d["content"],
                    source_layer=MemoryLayer(d["source_layer"]),
                    source_id=d["source_id"],
                    priority=d["priority"],
                    temperature=d["temperature"],
                    created_at=d["created_at"],
                    last_accessed=d["last_accessed"],
                    access_count=d["access_count"],
                    token_count=d["token_count"],
                    pinned=d.get("pinned", False),
                )
                self._fragments[frag.id] = frag
            return len(self._fragments)

    # ── Internal ────────────────────────────────────────────────

    def _evict_to_capacity(self, need_slots: int = 0) -> None:
        """
        Evict coldest non-pinned fragments to make room.

        Args:
            need_slots: Number of additional slots needed.
        """
        while (
            self.count + need_slots > self._config.max_fragments
            or self.total_tokens >= self._config.max_tokens
        ):
            # Find coldest non-pinned fragment
            coldest_id: str | None = None
            coldest_temp = float("inf")

            for fid, frag in self._fragments.items():
                if frag.pinned:
                    continue
                if frag.temperature < coldest_temp:
                    coldest_temp = frag.temperature
                    coldest_id = fid

            if coldest_id is None:
                break  # All fragments are pinned, can't evict

            frag = self._fragments.pop(coldest_id)
            for cb in self._on_evict:
                cb(frag)
