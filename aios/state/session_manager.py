"""
Session Manager — 会话管理器

跨请求的用户会话状态管理。

特征：
- 安全的会话 ID 生成（使用 secrets 模块）
- 空闲超时和最大生命周期双重过期
- 会话属性的不可变读写
- 会话续期（滑动窗口）
- 并发安全
- 会话统计

会话生命周期：
    Created → Active → Idle → Expired → Destroyed
                 ↑       │
                 └───────┘  (续期)
"""

from __future__ import annotations

import logging
import secrets
import threading
import time
from typing import Any

from .local_store import LocalStore
from .state_types import SessionConfig, StateConfig, StateEntry, StateScope

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器

    会话存储在 LocalStore 中，利用其淘汰策略管理会话生命周期。
    支持两种会话存储：
    1. 内存存储（默认，适合单实例）
    2. Redis 存储（可选，适合多实例）
    """

    def __init__(
        self,
        config: StateConfig | None = None,
        store: LocalStore | None = None,
    ) -> None:
        self._config = config or StateConfig.default()
        self._store = store or LocalStore(self._config)
        self._lock = threading.RLock()

        # 会话元数据（独立于会话数据）
        self._sessions: dict[str, SessionConfig] = {}

        # 统计
        self._created_count = 0
        self._destroyed_count = 0
        self._active_peak = 0

    # ── 会话生命周期 ──────────────────────────────────────────

    def create(
        self,
        user_id: str | None = None,
        max_idle: float | None = None,
        max_lifetime: float | None = None,
        initial_data: dict[str, Any] | None = None,
    ) -> SessionConfig:
        """
        创建新会话

        返回 SessionConfig（不可变），包含会话 ID。
        """
        with self._lock:
            session_id = self._generate_session_id()

            session_config = SessionConfig(
                session_id=session_id,
                user_id=user_id,
                max_idle=max_idle or self._config.session_ttl,
                max_lifetime=max_lifetime or self._config.session_ttl * 24,
            )

            self._sessions[session_id] = session_config

            # 存储初始数据
            if initial_data:
                for key, value in initial_data.items():
                    self._store.set(
                        f"session:{session_id}:{key}",
                        value,
                        scope=StateScope.SESSION,
                        ttl=session_config.max_lifetime,
                    )

            self._created_count += 1
            active_count = len(self._sessions)
            if active_count > self._active_peak:
                self._active_peak = active_count

            logger.debug(f"Session created: {session_id} (user={user_id})")
            return session_config

    def get(self, session_id: str) -> SessionConfig | None:
        """
        获取会话配置

        自动检查过期，过期会话会被销毁。
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            if session.is_expired:
                self._destroy_session(session_id)
                return None

            # 续期（滑动窗口）
            updated = session.touch()
            self._sessions[session_id] = updated
            return updated

    def destroy(self, session_id: str) -> bool:
        """销毁会话"""
        with self._lock:
            return self._destroy_session(session_id)

    def is_valid(self, session_id: str) -> bool:
        """检查会话是否有效"""
        return self.get(session_id) is not None

    # ── 会话数据操作 ──────────────────────────────────────────

    def get_attribute(self, session_id: str, key: str) -> Any | None:
        """获取会话属性"""
        if not self.is_valid(session_id):
            return None

        entry = self._store.get(f"session:{session_id}:{key}")
        return entry.value if entry else None

    def set_attribute(
        self,
        session_id: str,
        key: str,
        value: Any,
    ) -> bool:
        """设置会话属性"""
        if not self.is_valid(session_id):
            return False

        session = self._sessions.get(session_id)
        if session is None:
            return False

        self._store.set(
            f"session:{session_id}:{key}",
            value,
            scope=StateScope.SESSION,
            ttl=session.max_lifetime,
        )
        return True

    def delete_attribute(self, session_id: str, key: str) -> bool:
        """删除会话属性"""
        if not self.is_valid(session_id):
            return False

        return self._store.delete(f"session:{session_id}:{key}")

    def get_all_attributes(self, session_id: str) -> dict[str, Any]:
        """获取会话所有属性"""
        if not self.is_valid(session_id):
            return {}

        prefix = f"session:{session_id}:"
        result = {}
        for key in self._store.keys():
            if key.startswith(prefix):
                attr_name = key[len(prefix):]
                entry = self._store.get(key)
                if entry:
                    result[attr_name] = entry.value
        return result

    def clear_attributes(self, session_id: str) -> int:
        """清空会话所有属性"""
        if not self.is_valid(session_id):
            return 0

        prefix = f"session:{session_id}:"
        count = 0
        for key in list(self._store.keys()):
            if key.startswith(prefix):
                self._store.delete(key)
                count += 1
        return count

    # ── 会话查询 ──────────────────────────────────────────────

    def find_by_user(self, user_id: str) -> list[SessionConfig]:
        """查找用户的所有会话"""
        with self._lock:
            self._cleanup_expired()
            return [
                session for session in self._sessions.values()
                if session.user_id == user_id
            ]

    def active_sessions(self) -> list[SessionConfig]:
        """获取所有活跃会话"""
        with self._lock:
            self._cleanup_expired()
            return list(self._sessions.values())

    def session_count(self) -> int:
        """获取活跃会话数"""
        with self._lock:
            self._cleanup_expired()
            return len(self._sessions)

    # ── 续期 ──────────────────────────────────────────────────

    def touch(self, session_id: str) -> bool:
        """续期会话（刷新空闲计时器）"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.is_expired:
                return False

            self._sessions[session_id] = session.touch()
            return True

    # ── 统计 ──────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回会话统计信息"""
        with self._lock:
            self._cleanup_expired()
            return {
                "active_sessions": len(self._sessions),
                "total_created": self._created_count,
                "total_destroyed": self._destroyed_count,
                "peak_active": self._active_peak,
                "store_stats": self._store.stats(),
            }

    # ── 内部方法 ──────────────────────────────────────────────

    def _generate_session_id(self) -> str:
        """生成安全的会话 ID"""
        return secrets.token_urlsafe(32)

    def _destroy_session(self, session_id: str) -> bool:
        """销毁会话（调用者需持有锁）"""
        if session_id not in self._sessions:
            return False

        # 清除所有会话数据
        prefix = f"session:{session_id}:"
        for key in list(self._store.keys()):
            if key.startswith(prefix):
                self._store.delete(key)

        del self._sessions[session_id]
        self._destroyed_count += 1
        logger.debug(f"Session destroyed: {session_id}")
        return True

    def _cleanup_expired(self) -> None:
        """清理所有过期会话（调用者需持有锁）"""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired
        ]
        for sid in expired:
            self._destroy_session(sid)
