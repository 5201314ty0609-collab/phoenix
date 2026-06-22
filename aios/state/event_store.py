"""
Event Store — 事件溯源存储

分布式状态的基础：所有状态变更记录为不可变事件。

特征：
- 不可变事件日志
- 事件重放重建状态
- 快照支持（避免全量重放）
- 乐观并发控制（版本号）
- 事件订阅（观察者模式）

Event Sourcing 核心思想：
    State = fold(events)
    当前状态 = 所有事件的折叠结果

典型用途：
- 审计追踪
- 时间旅行调试
- 跨节点状态同步
- CQRS 写模型
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Event:
    """
    领域事件 — 不可变

    每个事件记录一次状态变更。
    """

    stream_id: str       # 聚合/实体 ID
    event_type: str      # 事件类型（如 OrderCreated, UserUpdated）
    data: dict[str, Any] # 事件数据
    version: int         # 流内版本号（乐观并发）
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""   # 事件唯一 ID（自动生成）

    def __post_init__(self) -> None:
        if not self.event_id:
            object.__setattr__(
                self, "event_id",
                f"{self.stream_id}:{self.version}:{int(self.timestamp * 1000)}",
            )


@dataclass(frozen=True)
class Snapshot:
    """
    状态快照 — 不可变

    用于避免从头重放所有事件。
    """

    stream_id: str
    version: int
    state: dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class EventStore:
    """
    事件溯源存储

    基于 SQLite 的事件日志，支持：
    - 追加事件（乐观并发）
    - 读取事件流
    - 创建/加载快照
    - 事件订阅
    """

    def __init__(self, db_path: str = "~/.claude/phoenix/aios/events.db") -> None:
        self._db_path = os.path.expanduser(db_path)
        self._lock = threading.RLock()
        self._local = threading.local()

        # 事件订阅者
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._global_subscribers: list[Callable[[Event], None]] = []

        # 初始化数据库
        self._init_db()

    # ── 事件追加 ──────────────────────────────────────────────

    def append(
        self,
        stream_id: str,
        event_type: str,
        data: dict[str, Any],
        expected_version: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        """
        追加事件到流

        Args:
            stream_id: 聚合/实体 ID
            event_type: 事件类型
            data: 事件数据
            expected_version: 期望的当前版本（乐观并发控制）
                             None 表示不检查版本
            metadata: 事件元数据

        Returns:
            创建的 Event 对象

        Raises:
            ConcurrencyError: 版本冲突时抛出
        """
        with self._lock:
            conn = self._get_connection()

            # 获取当前版本
            current_version = self._get_current_version(conn, stream_id)

            # 乐观并发检查
            if expected_version is not None and current_version != expected_version:
                raise ConcurrencyError(
                    f"Expected version {expected_version}, "
                    f"but current is {current_version} "
                    f"for stream '{stream_id}'"
                )

            new_version = current_version + 1
            event = Event(
                stream_id=stream_id,
                event_type=event_type,
                data=data,
                version=new_version,
                metadata=metadata or {},
            )

            try:
                conn.execute(
                    """
                    INSERT INTO events
                    (event_id, stream_id, event_type, data, version,
                     timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.stream_id,
                        event.event_type,
                        json.dumps(event.data, default=str, ensure_ascii=False),
                        event.version,
                        event.timestamp,
                        json.dumps(event.metadata, default=str),
                    ),
                )
                conn.commit()

                # 通知订阅者
                self._notify_subscribers(event)

                logger.debug(
                    f"Event appended: {stream_id}:{event_type}:v{new_version}"
                )
                return event

            except Exception as e:
                conn.rollback()
                logger.error(f"Event append error: {e}")
                raise

    # ── 事件读取 ──────────────────────────────────────────────

    def load_stream(
        self,
        stream_id: str,
        from_version: int = 0,
        to_version: int | None = None,
    ) -> list[Event]:
        """读取事件流"""
        with self._lock:
            conn = self._get_connection()

            if to_version is not None:
                cursor = conn.execute(
                    """
                    SELECT event_id, stream_id, event_type, data,
                           version, timestamp, metadata
                    FROM events
                    WHERE stream_id = ? AND version > ? AND version <= ?
                    ORDER BY version ASC
                    """,
                    (stream_id, from_version, to_version),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT event_id, stream_id, event_type, data,
                           version, timestamp, metadata
                    FROM events
                    WHERE stream_id = ? AND version > ?
                    ORDER BY version ASC
                    """,
                    (stream_id, from_version),
                )

            return [self._row_to_event(row) for row in cursor.fetchall()]

    def load_all(
        self,
        from_timestamp: float | None = None,
        limit: int = 1000,
    ) -> list[Event]:
        """读取所有事件（用于全局查询）"""
        with self._lock:
            conn = self._get_connection()

            if from_timestamp:
                cursor = conn.execute(
                    """
                    SELECT event_id, stream_id, event_type, data,
                           version, timestamp, metadata
                    FROM events
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                    (from_timestamp, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT event_id, stream_id, event_type, data,
                           version, timestamp, metadata
                    FROM events
                    ORDER BY timestamp ASC
                    LIMIT ?
                    """,
                    (limit,),
                )

            return [self._row_to_event(row) for row in cursor.fetchall()]

    # ── 快照 ──────────────────────────────────────────────────

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """保存状态快照"""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO snapshots
                    (stream_id, version, state, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        snapshot.stream_id,
                        snapshot.version,
                        json.dumps(snapshot.state, default=str, ensure_ascii=False),
                        snapshot.timestamp,
                    ),
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Snapshot save error: {e}")
                raise

    def load_snapshot(self, stream_id: str) -> Snapshot | None:
        """加载最新快照"""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                SELECT stream_id, version, state, timestamp
                FROM snapshots
                WHERE stream_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (stream_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return Snapshot(
                stream_id=row[0],
                version=row[1],
                state=json.loads(row[2]),
                timestamp=row[3],
            )

    # ── 重建状态 ──────────────────────────────────────────────

    def rebuild_state(
        self,
        stream_id: str,
        reducer: Callable[[dict[str, Any], Event], dict[str, Any]],
        initial_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        通过重放事件重建状态

        Args:
            stream_id: 流 ID
            reducer: 状态归约函数 (state, event) -> new_state
            initial_state: 初始状态

        Returns:
            重建后的状态
        """
        # 尝试从快照开始
        snapshot = self.load_snapshot(stream_id)
        if snapshot:
            state = snapshot.state
            from_version = snapshot.version
        else:
            state = initial_state or {}
            from_version = 0

        # 重放快照之后的事件
        events = self.load_stream(stream_id, from_version)
        for event in events:
            state = reducer(state, event)

        return state

    # ── 订阅 ──────────────────────────────────────────────────

    def subscribe(
        self,
        callback: Callable[[Event], None],
        event_type: str | None = None,
    ) -> None:
        """
        订阅事件

        Args:
            callback: 事件回调
            event_type: 指定事件类型订阅，None 表示订阅所有
        """
        if event_type:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
        else:
            self._global_subscribers.append(callback)

    # ── 统计 ──────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回事件存储统计"""
        with self._lock:
            conn = self._get_connection()

            cursor = conn.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT stream_id) FROM events")
            total_streams = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM snapshots")
            total_snapshots = cursor.fetchone()[0]

            return {
                "total_events": total_events,
                "total_streams": total_streams,
                "total_snapshots": total_snapshots,
                "db_path": self._db_path,
                "subscribers": {
                    "global": len(self._global_subscribers),
                    "by_type": {
                        k: len(v) for k, v in self._subscribers.items()
                    },
                },
            }

    # ── 内部方法 ──────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地连接"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, timeout=5.0)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self._db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS snapshots (
                    stream_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    PRIMARY KEY (stream_id, version)
                );

                CREATE INDEX IF NOT EXISTS idx_events_stream
                    ON events(stream_id, version);

                CREATE INDEX IF NOT EXISTS idx_events_type
                    ON events(event_type);

                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                    ON events(timestamp);
            """)
            conn.commit()
        finally:
            conn.close()

    def _get_current_version(self, conn: sqlite3.Connection, stream_id: str) -> int:
        """获取流的当前最大版本"""
        cursor = conn.execute(
            "SELECT MAX(version) FROM events WHERE stream_id = ?",
            (stream_id,),
        )
        row = cursor.fetchone()
        return row[0] or 0

    def _row_to_event(self, row: tuple) -> Event:
        """将数据库行转为 Event"""
        return Event(
            event_id=row[0],
            stream_id=row[1],
            event_type=row[2],
            data=json.loads(row[3]),
            version=row[4],
            timestamp=row[5],
            metadata=json.loads(row[6]),
        )

    def _notify_subscribers(self, event: Event) -> None:
        """通知订阅者"""
        # 全局订阅者
        for callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Global subscriber error: {e}")

        # 类型订阅者
        type_subscribers = self._subscribers.get(event.event_type, [])
        for callback in type_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Type subscriber error for {event.event_type}: {e}")


class ConcurrencyError(Exception):
    """乐观并发冲突"""
    pass
