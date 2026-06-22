"""
Persistence Layer — 持久化层

冷数据层，基于 SQLite 的持久化存储。

特征：
- SQLite + WAL 模式（高性能读写）
- 自动表创建和迁移
- 批量操作（INSERT OR REPLACE）
- 过期数据自动清理
- 标签索引查询
- 统计信息

设计决策：
- 使用 SQLite 而非 PostgreSQL，因为：
  1. 零依赖，内嵌式
  2. 足够 PHOENIX AIOS 的单实例需求
  3. WAL 模式支持并发读写
  4. 未来可平滑迁移到 PostgreSQL
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any

from .state_types import StateConfig, StateEntry, StateScope

logger = logging.getLogger(__name__)


class PersistenceLayer:
    """
    SQLite 持久化层

    状态持久化到 SQLite 数据库，支持：
    - 键值存储
    - TTL 过期
    - 标签索引
    - 批量操作
    - 自动清理
    """

    def __init__(self, config: StateConfig | None = None) -> None:
        self._config = config or StateConfig.default()
        self._db_path = os.path.expanduser(self._config.db_path)
        self._lock = threading.RLock()
        self._local = threading.local()

        # 确保目录存在
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        # 初始化数据库
        self._init_db()

    # ── 核心操作 ──────────────────────────────────────────────

    def get(self, key: str) -> StateEntry | None:
        """获取持久化条目"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    """
                    SELECT key, value, scope, created_at, updated_at,
                           expires_at, version, tags, metadata
                    FROM state_entries
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                    """,
                    (key, time.time()),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_entry(row)
            except Exception as e:
                logger.error(f"Persistence get error for {key}: {e}")
                return None

    def set(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.GLOBAL,
        ttl: float | None = None,
        tags: tuple[str, ...] = (),
    ) -> StateEntry:
        """持久化条目"""
        with self._lock:
            now = time.time()
            expires_at = None
            if ttl is not None:
                expires_at = now + ttl

            entry = StateEntry(
                key=key,
                value=value,
                scope=scope,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                tags=tags,
            )

            conn = self._get_connection()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO state_entries
                    (key, value, scope, created_at, updated_at,
                     expires_at, version, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._entry_to_row(entry),
                )
                conn.commit()

                # 更新标签索引
                self._update_tags(conn, key, tags)

                return entry
            except Exception as e:
                logger.error(f"Persistence set error for {key}: {e}")
                conn.rollback()
                raise

    def delete(self, key: str) -> bool:
        """删除持久化条目"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    "DELETE FROM state_entries WHERE key = ?",
                    (key,),
                )
                conn.execute(
                    "DELETE FROM state_tags WHERE key = ?",
                    (key,),
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Persistence delete error for {key}: {e}")
                conn.rollback()
                return False

    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None

    # ── 批量操作 ──────────────────────────────────────────────

    def get_many(self, keys: list[str]) -> dict[str, StateEntry]:
        """批量获取"""
        result = {}
        for key in keys:
            entry = self.get(key)
            if entry is not None:
                result[key] = entry
        return result

    def set_many(
        self,
        items: dict[str, Any],
        scope: StateScope = StateScope.GLOBAL,
        ttl: float | None = None,
        tags: tuple[str, ...] = (),
    ) -> list[StateEntry]:
        """批量设置"""
        with self._lock:
            now = time.time()
            expires_at = now + ttl if ttl else None
            entries = []

            conn = self._get_connection()
            try:
                for key, value in items.items():
                    entry = StateEntry(
                        key=key,
                        value=value,
                        scope=scope,
                        created_at=now,
                        updated_at=now,
                        expires_at=expires_at,
                        tags=tags,
                    )
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO state_entries
                        (key, value, scope, created_at, updated_at,
                         expires_at, version, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        self._entry_to_row(entry),
                    )
                    entries.append(entry)

                conn.commit()

                # 更新标签索引
                for entry in entries:
                    self._update_tags(conn, entry.key, entry.tags)

                return entries
            except Exception as e:
                logger.error(f"Persistence set_many error: {e}")
                conn.rollback()
                raise

    # ── 标签查询 ──────────────────────────────────────────────

    def find_by_tag(self, tag: str) -> list[StateEntry]:
        """按标签查找条目"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    """
                    SELECT e.key, e.value, e.scope, e.created_at, e.updated_at,
                           e.expires_at, e.version, e.tags, e.metadata
                    FROM state_entries e
                    JOIN state_tags t ON e.key = t.key
                    WHERE t.tag = ? AND (e.expires_at IS NULL OR e.expires_at > ?)
                    """,
                    (tag, time.time()),
                )
                return [self._row_to_entry(row) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"Persistence find_by_tag error: {e}")
                return []

    # ── 清理 ──────────────────────────────────────────────────

    def cleanup_expired(self) -> int:
        """清理所有过期条目"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    """
                    DELETE FROM state_entries
                    WHERE expires_at IS NOT NULL AND expires_at <= ?
                    """,
                    (time.time(),),
                )
                # 清理孤立标签
                conn.execute(
                    """
                    DELETE FROM state_tags
                    WHERE key NOT IN (SELECT key FROM state_entries)
                    """,
                )
                conn.commit()
                count = cursor.rowcount
                if count > 0:
                    logger.info(f"Cleaned up {count} expired entries")
                return count
            except Exception as e:
                logger.error(f"Persistence cleanup error: {e}")
                conn.rollback()
                return 0

    def clear(self) -> int:
        """清空所有条目"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM state_entries")
                count = cursor.fetchone()[0]
                conn.execute("DELETE FROM state_entries")
                conn.execute("DELETE FROM state_tags")
                conn.commit()
                return count
            except Exception as e:
                logger.error(f"Persistence clear error: {e}")
                conn.rollback()
                return 0

    # ── 统计 ──────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回持久化层统计信息"""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM state_entries")
                total = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM state_entries "
                    "WHERE expires_at IS NOT NULL AND expires_at <= ?",
                    (time.time(),),
                )
                expired = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM state_tags")
                tag_count = cursor.fetchone()[0]

                return {
                    "total_entries": total,
                    "expired_pending_cleanup": expired,
                    "tag_count": tag_count,
                    "db_path": self._db_path,
                    "db_size_mb": self._get_db_size_mb(),
                }
            except Exception as e:
                logger.error(f"Persistence stats error: {e}")
                return {"error": str(e)}

    # ── 内部方法 ──────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self._db_path,
                timeout=self._config.busy_timeout / 1000.0,
            )
            if self._config.wal_mode:
                self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        """初始化数据库表"""
        conn = sqlite3.connect(self._db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS state_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL,
                    version INTEGER NOT NULL DEFAULT 1,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS state_tags (
                    key TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (key, tag),
                    FOREIGN KEY (key) REFERENCES state_entries(key) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_entries_expires
                    ON state_entries(expires_at)
                    WHERE expires_at IS NOT NULL;

                CREATE INDEX IF NOT EXISTS idx_entries_scope
                    ON state_entries(scope);

                CREATE INDEX IF NOT EXISTS idx_tags_tag
                    ON state_tags(tag);
            """)
            conn.commit()
        finally:
            conn.close()

    def _entry_to_row(self, entry: StateEntry) -> tuple:
        """将 StateEntry 转换为数据库行"""
        return (
            entry.key,
            json.dumps(entry.value, default=str, ensure_ascii=False),
            entry.scope.value,
            entry.created_at,
            entry.updated_at,
            entry.expires_at,
            entry.version,
            json.dumps(list(entry.tags)),
            json.dumps(dict(entry.metadata)),
        )

    def _row_to_entry(self, row: sqlite3.Row) -> StateEntry:
        """将数据库行转换为 StateEntry"""
        return StateEntry(
            key=row["key"],
            value=json.loads(row["value"]),
            scope=StateScope[row["scope"]],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row["expires_at"],
            version=row["version"],
            tags=tuple(json.loads(row["tags"])),
            metadata=tuple(tuple(x) for x in json.loads(row["metadata"])),
        )

    def _update_tags(
        self,
        conn: sqlite3.Connection,
        key: str,
        tags: tuple[str, ...],
    ) -> None:
        """更新标签索引"""
        conn.execute("DELETE FROM state_tags WHERE key = ?", (key,))
        for tag in tags:
            conn.execute(
                "INSERT OR IGNORE INTO state_tags (key, tag) VALUES (?, ?)",
                (key, tag),
            )

    def _get_db_size_mb(self) -> float:
        """获取数据库文件大小（MB）"""
        try:
            size = os.path.getsize(self._db_path)
            return round(size / (1024 * 1024), 2)
        except OSError:
            return 0.0
