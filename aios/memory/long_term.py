"""
Long-Term Memory (LTM) — Persistent knowledge storage.

Based on SQLite + FTS5 for full-text search, with:
- Ebbinghaus decay curve for relevance scoring
- Graph relations between memory entries
- Automatic relation detection via Jaccard similarity
- Vector embedding support (optional)
- Tag-based indexing and querying

LTM persists across sessions and is the primary knowledge store
for the memory system. Entries decay over time unless recalled,
mimicking human forgetting curves.
"""

from __future__ import annotations

import json
import logging
import math
import os
import sqlite3
import threading
import time
from typing import Iterator

from .config import LTMConfig
from .memory_types import (
    DecayCurve,
    MemoryEntry,
    MemoryLayer,
    MemoryRelation,
    MemoryStatus,
    RelationType,
    _estimate_tokens,
    _new_id,
)

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Persistent knowledge store with decay and graph relations.

    Thread-safe SQLite-backed storage with FTS5 full-text search.
    Entries decay following configurable curves and are promoted
    or demoted based on access patterns.

    Example:
        ltm = LongTermMemory()

        # Store a memory
        entry = ltm.store(
            content="User prefers dark mode in all applications",
            importance=0.8,
            tags=("preference", "ui"),
        )

        # Recall it later (resets decay)
        ltm.recall(entry.id)

        # Search
        results = ltm.search("dark mode")
    """

    def __init__(self, config: LTMConfig | None = None) -> None:
        self._config = config or LTMConfig()
        self._lock = threading.RLock()
        self._local = threading.local()

        # Ensure directory exists
        db_path = str(self._config.db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    # ── Database Setup ──────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._config.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        """Create tables if they do not exist."""
        conn = self._get_conn()
        with conn:
            # Main entries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    mem_type TEXT NOT NULL DEFAULT 'semantic',
                    importance REAL NOT NULL DEFAULT 0.5,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    status TEXT NOT NULL DEFAULT 'active',
                    layer TEXT NOT NULL DEFAULT 'ltm',
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    decay_strength REAL NOT NULL DEFAULT 1.0,
                    decay_curve TEXT NOT NULL DEFAULT 'ebinghaus',
                    ttl_days INTEGER NOT NULL DEFAULT 90,
                    tags TEXT NOT NULL DEFAULT '[]',
                    source TEXT NOT NULL DEFAULT '',
                    embedding BLOB
                )
            """)

            # FTS5 index for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_entries_fts USING fts5(
                    content, summary, tags, source,
                    content=memory_entries,
                    content_rowid=rowid
                )
            """)

            # Relations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL DEFAULT 'related_to',
                    weight REAL NOT NULL DEFAULT 1.0,
                    reason TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    UNIQUE(source_id, target_id, relation_type)
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_status
                ON memory_entries(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_type
                ON memory_entries(mem_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_last_accessed
                ON memory_entries(last_accessed)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_source
                ON memory_relations(source_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_target
                ON memory_relations(target_id)
            """)

            # FTS triggers for sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_ai AFTER INSERT ON memory_entries BEGIN
                    INSERT INTO memory_entries_fts(rowid, content, summary, tags, source)
                    VALUES (new.rowid, new.content, new.summary, new.tags, new.source);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_ad AFTER DELETE ON memory_entries BEGIN
                    INSERT INTO memory_entries_fts(memory_entries_fts, rowid, content, summary, tags, source)
                    VALUES ('delete', old.rowid, old.content, old.summary, old.tags, old.source);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_entries_au AFTER UPDATE ON memory_entries BEGIN
                    INSERT INTO memory_entries_fts(memory_entries_fts, rowid, content, summary, tags, source)
                    VALUES ('delete', old.rowid, old.content, old.summary, old.tags, old.source);
                    INSERT INTO memory_entries_fts(rowid, content, summary, tags, source)
                    VALUES (new.rowid, new.content, new.summary, new.tags, new.source);
                END
            """)

    # ── Core Operations ─────────────────────────────────────────

    def store(
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
        Store a new memory entry in LTM.

        Args:
            content: The memory content text.
            summary: Short summary (auto-generated if empty).
            mem_type: Memory type (semantic/episodic/procedural/relational).
            importance: Base importance 0.0-1.0.
            confidence: Extraction confidence 0.0-1.0.
            tags: Classification tags.
            source: Origin identifier.
            decay_curve: Decay function shape.
            ttl_days: Maximum days without recall (config default if None).

        Returns:
            The created MemoryEntry.
        """
        entry = MemoryEntry.create(
            content=content,
            summary=summary,
            mem_type=mem_type,
            importance=importance,
            confidence=confidence,
            tags=tags,
            source=source,
            decay_curve=decay_curve,
            ttl_days=ttl_days or self._config.default_ttl_days,
        )

        with self._lock:
            conn = self._get_conn()
            with conn:
                conn.execute("""
                    INSERT INTO memory_entries
                    (id, content, summary, mem_type, importance, confidence,
                     status, layer, created_at, last_accessed, access_count,
                     decay_strength, decay_curve, ttl_days, tags, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id, entry.content, entry.summary, entry.mem_type,
                    entry.importance, entry.confidence, entry.status.value,
                    entry.layer.value, entry.created_at, entry.last_accessed,
                    entry.access_count, entry.decay_strength,
                    entry.decay_curve.value, entry.ttl_days,
                    json.dumps(list(entry.tags)), entry.source,
                ))

        return entry

    def get(self, entry_id: str) -> MemoryEntry | None:
        """
        Retrieve a memory entry by ID.

        Args:
            entry_id: The entry's unique identifier.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM memory_entries WHERE id = ?", (entry_id,)
        ).fetchone()

        if row is None:
            return None

        return self._row_to_entry(row)

    def recall(self, entry_id: str) -> MemoryEntry | None:
        """
        Recall a memory entry — updates access metadata and boosts decay.

        This is the primary mechanism for keeping memories alive.
        Each recall increases decay_strength, making the memory
        decay more slowly.

        Args:
            entry_id: The entry's unique identifier.

        Returns:
            Updated MemoryEntry if found, None otherwise.
        """
        with self._lock:
            entry = self.get(entry_id)
            if entry is None:
                return None

            updated = entry.accessed()
            conn = self._get_conn()
            with conn:
                conn.execute("""
                    UPDATE memory_entries
                    SET last_accessed = ?, access_count = ?, decay_strength = ?
                    WHERE id = ?
                """, (
                    updated.last_accessed, updated.access_count,
                    updated.decay_strength, updated.id,
                ))

            return updated

    def update(
        self,
        entry_id: str,
        content: str | None = None,
        summary: str | None = None,
        importance: float | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> MemoryEntry | None:
        """
        Update fields of an existing memory entry.

        Only non-None arguments are updated. Returns the updated entry.

        Args:
            entry_id: Target entry ID.
            content: New content (if provided).
            summary: New summary (if provided).
            importance: New importance (if provided).
            tags: New tags (if provided).

        Returns:
            Updated MemoryEntry if found, None otherwise.
        """
        with self._lock:
            entry = self.get(entry_id)
            if entry is None:
                return None

            new_content = content if content is not None else entry.content
            new_summary = summary if summary is not None else entry.summary
            new_importance = importance if importance is not None else entry.importance
            new_tags = tags if tags is not None else entry.tags

            conn = self._get_conn()
            with conn:
                conn.execute("""
                    UPDATE memory_entries
                    SET content = ?, summary = ?, importance = ?, tags = ?,
                        last_accessed = ?
                    WHERE id = ?
                """, (
                    new_content, new_summary, new_importance,
                    json.dumps(list(new_tags)), time.time(), entry_id,
                ))

            return self.get(entry_id)

    def delete(self, entry_id: str) -> bool:
        """
        Delete a memory entry and its relations.

        Args:
            entry_id: Target entry ID.

        Returns:
            True if entry was found and deleted.
        """
        with self._lock:
            conn = self._get_conn()
            with conn:
                cursor = conn.execute(
                    "DELETE FROM memory_entries WHERE id = ?", (entry_id,)
                )
                if cursor.rowcount > 0:
                    conn.execute(
                        "DELETE FROM memory_relations WHERE source_id = ? OR target_id = ?",
                        (entry_id, entry_id),
                    )
                    return True
            return False

    # ── Search ──────────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        mem_type: str | None = None,
        status: MemoryStatus = MemoryStatus.ACTIVE,
    ) -> list[MemoryEntry]:
        """
        Full-text search across memory entries using FTS5 BM25.

        Args:
            query: Search text.
            limit: Maximum results.
            mem_type: Optional type filter.
            status: Status filter (default: ACTIVE only).

        Returns:
            List of matching MemoryEntry sorted by relevance.
        """
        conn = self._get_conn()

        sql = """
            SELECT me.* FROM memory_entries me
            JOIN memory_entries_fts fts ON me.rowid = fts.rowid
            WHERE memory_entries_fts MATCH ?
            AND me.status = ?
        """
        params: list = [query, status.value]

        if mem_type is not None:
            sql += " AND me.mem_type = ?"
            params.append(mem_type)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def search_by_tags(
        self,
        tags: tuple[str, ...],
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        Search entries that have any of the given tags.

        Args:
            tags: Tags to match (OR logic).
            limit: Maximum results.

        Returns:
            Matching entries sorted by importance.
        """
        conn = self._get_conn()
        results: list[MemoryEntry] = []

        for tag in tags:
            rows = conn.execute("""
                SELECT * FROM memory_entries
                WHERE status = 'active' AND tags LIKE ?
                ORDER BY importance DESC
                LIMIT ?
            """, (f'%"{tag}"%', limit)).fetchall()
            for row in rows:
                entry = self._row_to_entry(row)
                if entry.id not in {e.id for e in results}:
                    results.append(entry)

        # Sort by importance descending
        results.sort(key=lambda e: e.importance, reverse=True)
        return results[:limit]

    # ── Relations ───────────────────────────────────────────────

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType = RelationType.RELATED_TO,
        weight: float = 1.0,
        reason: str = "",
    ) -> MemoryRelation | None:
        """
        Add a directed relation between two memory entries.

        Args:
            source_id: Source entry ID.
            target_id: Target entry ID.
            relation_type: Type of relation.
            weight: Relation strength 0.0+.
            reason: Optional explanation.

        Returns:
            The created MemoryRelation, or None if entries don't exist.
        """
        # Verify both entries exist
        if self.get(source_id) is None or self.get(target_id) is None:
            return None

        relation = MemoryRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            reason=reason,
        )

        with self._lock:
            conn = self._get_conn()
            with conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_relations
                    (source_id, target_id, relation_type, weight, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    relation.source_id, relation.target_id,
                    relation.relation_type.value, relation.weight,
                    relation.reason, relation.created_at,
                ))

        return relation

    def get_relations(
        self,
        entry_id: str,
        direction: str = "both",
    ) -> list[MemoryRelation]:
        """
        Get all relations involving an entry.

        Args:
            entry_id: Target entry ID.
            direction: "outgoing", "incoming", or "both".

        Returns:
            List of MemoryRelation.
        """
        conn = self._get_conn()
        relations: list[MemoryRelation] = []

        if direction in ("outgoing", "both"):
            rows = conn.execute(
                "SELECT * FROM memory_relations WHERE source_id = ?",
                (entry_id,),
            ).fetchall()
            for row in rows:
                relations.append(self._row_to_relation(row))

        if direction in ("incoming", "both"):
            rows = conn.execute(
                "SELECT * FROM memory_relations WHERE target_id = ?",
                (entry_id,),
            ).fetchall()
            for row in rows:
                relations.append(self._row_to_relation(row))

        return relations

    def auto_detect_relations(self) -> int:
        """
        Automatically detect and create relations via Jaccard similarity.

        Compares tokenized content of all active entries and creates
        relations where Jaccard similarity exceeds the configured threshold.

        Returns:
            Number of new relations created.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, content, summary FROM memory_entries WHERE status = 'active'"
        ).fetchall()

        if len(rows) < 2:
            return 0

        # Tokenize entries
        token_sets: dict[str, set[str]] = {}
        for row in rows:
            text = f"{row['content']} {row['summary']}"
            tokens = {t.lower() for t in text.split() if len(t) >= 3}
            token_sets[row["id"]] = tokens

        created = 0
        entry_ids = list(token_sets.keys())

        for i in range(len(entry_ids)):
            for j in range(i + 1, len(entry_ids)):
                id_a, id_b = entry_ids[i], entry_ids[j]
                set_a, set_b = token_sets[id_a], token_sets[id_b]

                if not set_a or not set_b:
                    continue

                intersection = len(set_a & set_b)
                union = len(set_a | set_b)
                jaccard = intersection / union if union > 0 else 0.0

                if jaccard >= self._config.auto_relation_threshold:
                    # Classify relation type
                    if jaccard > 0.4:
                        rel_type = RelationType.SUPPORTS
                    else:
                        rel_type = RelationType.RELATED_TO

                    rel = self.add_relation(
                        source_id=id_a,
                        target_id=id_b,
                        relation_type=rel_type,
                        weight=jaccard,
                        reason=f"auto-detected (jaccard={jaccard:.3f})",
                    )
                    if rel is not None:
                        created += 1

        return created

    # ── Decay and Lifecycle ─────────────────────────────────────

    def compute_decay_scores(self) -> list[tuple[str, float]]:
        """
        Compute decay scores for all active entries.

        Returns:
            List of (entry_id, decay_score) tuples sorted by score ascending.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM memory_entries WHERE status = 'active'"
        ).fetchall()

        scores: list[tuple[str, float]] = []
        for row in rows:
            entry = self._row_to_entry(row)
            score = entry.compute_decay_score()
            scores.append((entry.id, score))

        scores.sort(key=lambda x: x[1])
        return scores

    def apply_decay(self) -> tuple[int, int]:
        """
        Apply decay classification to all active entries.

        Entries below decay_threshold are marked DECAYED.
        Entries below forget_threshold are marked FORGOTTEN.

        Returns:
            Tuple of (decayed_count, forgotten_count).
        """
        scores = self.compute_decay_scores()
        decayed = 0
        forgotten = 0

        conn = self._get_conn()
        with conn:
            for entry_id, score in scores:
                if score < self._config.forget_threshold:
                    conn.execute(
                        "UPDATE memory_entries SET status = 'forgotten' WHERE id = ?",
                        (entry_id,),
                    )
                    forgotten += 1
                elif score < self._config.decay_threshold:
                    conn.execute(
                        "UPDATE memory_entries SET status = 'decayed' WHERE id = ?",
                        (entry_id,),
                    )
                    decayed += 1

        return decayed, forgotten

    def cleanup_forgotten(self) -> int:
        """
        Delete all entries marked as FORGOTTEN.

        Returns:
            Number of entries deleted.
        """
        with self._lock:
            conn = self._get_conn()
            with conn:
                # Get IDs first for relation cleanup
                rows = conn.execute(
                    "SELECT id FROM memory_entries WHERE status = 'forgotten'"
                ).fetchall()
                ids = [row["id"] for row in rows]

                if not ids:
                    return 0

                # Delete entries
                placeholders = ",".join("?" * len(ids))
                conn.execute(
                    f"DELETE FROM memory_entries WHERE id IN ({placeholders})", ids
                )

                # Clean up orphaned relations
                conn.execute(
                    f"DELETE FROM memory_relations WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    ids + ids,
                )

                return len(ids)

    # ── Statistics ──────────────────────────────────────────────

    def stats(self) -> dict:
        """
        Get LTM statistics.

        Returns:
            Dict with counts, averages, and health metrics.
        """
        conn = self._get_conn()

        total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE status = 'active'"
        ).fetchone()[0]
        archived = conn.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE status = 'archived'"
        ).fetchone()[0]
        decayed = conn.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE status = 'decayed'"
        ).fetchone()[0]
        forgotten = conn.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE status = 'forgotten'"
        ).fetchone()[0]
        relations = conn.execute("SELECT COUNT(*) FROM memory_relations").fetchone()[0]

        avg_importance_row = conn.execute(
            "SELECT AVG(importance) FROM memory_entries WHERE status = 'active'"
        ).fetchone()
        avg_importance = avg_importance_row[0] or 0.0

        avg_access_row = conn.execute(
            "SELECT AVG(access_count) FROM memory_entries WHERE status = 'active'"
        ).fetchone()
        avg_access = avg_access_row[0] or 0.0

        # Type distribution
        type_rows = conn.execute("""
            SELECT mem_type, COUNT(*) as cnt
            FROM memory_entries WHERE status = 'active'
            GROUP BY mem_type
        """).fetchall()
        type_dist = {row["mem_type"]: row["cnt"] for row in type_rows}

        return {
            "total": total,
            "active": active,
            "archived": archived,
            "decayed": decayed,
            "forgotten": forgotten,
            "relations": relations,
            "avg_importance": round(avg_importance, 3),
            "avg_access_count": round(avg_access, 1),
            "type_distribution": type_dist,
        }

    # ── Iteration ───────────────────────────────────────────────

    def iter_active(self, limit: int = 100) -> Iterator[MemoryEntry]:
        """Iterate over active entries, ordered by importance."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM memory_entries
            WHERE status = 'active'
            ORDER BY importance DESC
            LIMIT ?
        """, (limit,)).fetchall()
        for row in rows:
            yield self._row_to_entry(row)

    # ── Internal ────────────────────────────────────────────────

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """Convert a database row to a MemoryEntry."""
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            summary=row["summary"],
            mem_type=row["mem_type"],
            importance=row["importance"],
            confidence=row["confidence"],
            status=MemoryStatus(row["status"]),
            layer=MemoryLayer(row["layer"]),
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
            access_count=row["access_count"],
            decay_strength=row["decay_strength"],
            decay_curve=DecayCurve(row["decay_curve"]),
            ttl_days=row["ttl_days"],
            tags=tuple(json.loads(row["tags"])),
            source=row["source"],
        )

    def _row_to_relation(self, row: sqlite3.Row) -> MemoryRelation:
        """Convert a database row to a MemoryRelation."""
        return MemoryRelation(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=RelationType(row["relation_type"]),
            weight=row["weight"],
            reason=row["reason"],
            created_at=row["created_at"],
        )
