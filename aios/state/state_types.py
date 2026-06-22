"""
状态管理核心类型定义

不可变数据结构，遵循 PHOENIX 不可变性原则。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class StateScope(Enum):
    """状态作用域 — 决定状态的生命周期和可见性"""

    REQUEST = auto()   # 单次请求，请求结束即销毁
    SESSION = auto()   # 会话级别，跨请求持久
    USER = auto()      # 用户级别，跨会话持久
    GLOBAL = auto()    # 全局级别，跨用户共享
    DISTRIBUTED = auto()  # 分布式，跨节点同步


class CachePolicy(Enum):
    """缓存策略"""

    NO_CACHE = "no_cache"           # 不缓存，每次从源头读取
    CACHE_ASIDE = "cache_aside"     # 懒加载：先查缓存，miss 则读 DB 并写缓存
    WRITE_THROUGH = "write_through" # 写穿透：同时写缓存和 DB
    WRITE_BEHIND = "write_behind"   # 写回：先写缓存，异步写 DB
    READ_THROUGH = "read_through"   # 读穿透：缓存透明代理 DB 读取
    TTL_EXPIRY = "ttl_expiry"       # TTL 过期：基于时间自动失效


class StateStatus(Enum):
    """状态条目状态"""

    ACTIVE = "active"
    EXPIRED = "expired"
    DIRTY = "dirty"       # 已修改但未持久化
    LOCKED = "locked"     # 被锁定，不允许修改
    EVICTED = "evicted"   # 已被驱逐


@dataclass(frozen=True)
class StateEntry(Generic[T]):
    """
    状态条目 — 不可变

    每个状态条目包含值、元数据和生命周期信息。
    frozen=True 确保不可变性——修改必须创建新实例。
    """

    key: str
    value: T
    scope: StateScope
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    version: int = 1
    tags: tuple[str, ...] = ()
    metadata: tuple[tuple[str, Any], ...] = ()

    @property
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float | None:
        """剩余 TTL（秒），None 表示永不过期"""
        if self.expires_at is None:
            return None
        return max(0.0, self.expires_at - time.time())

    def with_value(self, new_value: T) -> StateEntry[T]:
        """返回带有新值的新实例（不可变更新）"""
        return StateEntry(
            key=self.key,
            value=new_value,
            scope=self.scope,
            created_at=self.created_at,
            updated_at=time.time(),
            expires_at=self.expires_at,
            version=self.version + 1,
            tags=self.tags,
            metadata=self.metadata,
        )

    def with_ttl(self, ttl_seconds: float) -> StateEntry[T]:
        """返回带有新 TTL 的新实例"""
        return StateEntry(
            key=self.key,
            value=self.value,
            scope=self.scope,
            created_at=self.created_at,
            updated_at=self.updated_at,
            expires_at=time.time() + ttl_seconds,
            version=self.version,
            tags=self.tags,
            metadata=self.metadata,
        )

    def with_tags(self, *new_tags: str) -> StateEntry[T]:
        """返回带有新标签的新实例"""
        merged = tuple(set(self.tags + new_tags))
        return StateEntry(
            key=self.key,
            value=self.value,
            scope=self.scope,
            created_at=self.created_at,
            updated_at=self.updated_at,
            expires_at=self.expires_at,
            version=self.version,
            tags=merged,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class StateConfig:
    """全局状态配置"""

    # Local Store 配置
    local_max_size: int = 10000
    local_eviction_policy: str = "lru"  # lru, lfu, fifo

    # Cache 配置
    cache_default_ttl: float = 300.0  # 5 分钟
    cache_max_memory: str = "256mb"
    cache_eviction: str = "allkeys-lru"
    cache_prefix: str = "phoenix:"

    # Session 配置
    session_ttl: float = 3600.0  # 1 小时
    session_cookie_name: str = "phoenix_sid"
    session_max_active: int = 1000

    # Persistence 配置
    db_path: str = "~/.claude/phoenix/aios/state.db"
    wal_mode: bool = True
    busy_timeout: int = 5000

    # Distributed 配置
    event_log_max_size: int = 100000
    crdt_sync_interval: float = 5.0

    @classmethod
    def default(cls) -> StateConfig:
        return cls()

    @classmethod
    def development(cls) -> StateConfig:
        """开发环境配置 — 更短的 TTL，更小的缓存"""
        return cls(
            local_max_size=1000,
            cache_default_ttl=60.0,
            session_ttl=1800.0,
            cache_max_memory="64mb",
        )

    @classmethod
    def production(cls) -> StateConfig:
        """生产环境配置 — 更大的缓存，更长的 TTL"""
        return cls(
            local_max_size=50000,
            cache_default_ttl=600.0,
            session_ttl=7200.0,
            cache_max_memory="1gb",
        )


@dataclass(frozen=True)
class SessionConfig:
    """会话配置"""

    session_id: str
    user_id: str | None = None
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    max_idle: float = 1800.0  # 30 分钟空闲超时
    max_lifetime: float = 86400.0  # 24 小时最大生命周期
    attributes: tuple[tuple[str, Any], ...] = ()

    @property
    def is_expired(self) -> bool:
        now = time.time()
        idle_expired = (now - self.last_accessed) > self.max_idle
        lifetime_expired = (now - self.created_at) > self.max_lifetime
        return idle_expired or lifetime_expired

    def touch(self) -> SessionConfig:
        """返回更新 last_accessed 的新实例"""
        return SessionConfig(
            session_id=self.session_id,
            user_id=self.user_id,
            created_at=self.created_at,
            last_accessed=time.time(),
            max_idle=self.max_idle,
            max_lifetime=self.max_lifetime,
            attributes=self.attributes,
        )
