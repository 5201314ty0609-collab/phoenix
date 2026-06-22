"""
Local Store — 进程内存状态存储

热数据层，微秒级访问。使用 LRU/LFU/FIFO 淘汰策略。

特征：
- 线程安全（使用 threading.Lock）
- 不可变条目（StateEntry 是 frozen dataclass）
- 自动过期清理
- 内存限制和淘汰
- 统计指标

典型用途：
- 请求级别的临时数据
- 频繁读取的配置
- 计算结果缓存
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable

from .state_types import StateConfig, StateEntry, StateScope, StateStatus


class LocalStore:
    """
    进程内存状态存储

    使用 OrderedDict 实现 LRU，支持三种淘汰策略：
    - LRU (Least Recently Used): 最近最少使用
    - LFU (Least Frequently Used): 最不经常使用
    - FIFO (First In First Out): 先进先出
    """

    def __init__(self, config: StateConfig | None = None) -> None:
        self._config = config or StateConfig.default()
        self._store: dict[str, StateEntry] = OrderedDict()
        self._access_count: dict[str, int] = {}
        self._lock = threading.RLock()

        # 统计
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._total_sets = 0

    # ── 核心操作 ──────────────────────────────────────────────

    def get(self, key: str) -> StateEntry | None:
        """获取状态条目，返回 None 表示不存在或已过期"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                self._remove(key)
                self._misses += 1
                return None

            self._hits += 1
            self._access_count[key] = self._access_count.get(key, 0) + 1

            # LRU: 移到末尾
            if self._config.local_eviction_policy == "lru":
                self._store.move_to_end(key)

            return entry

    def set(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.REQUEST,
        ttl: float | None = None,
        tags: tuple[str, ...] = (),
    ) -> StateEntry:
        """设置状态条目，返回新的不可变条目"""
        with self._lock:
            # 检查容量，必要时淘汰
            if len(self._store) >= self._config.local_max_size and key not in self._store:
                self._evict()

            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            elif scope == StateScope.REQUEST:
                expires_at = time.time() + 60.0  # 请求级别默认 1 分钟

            entry = StateEntry(
                key=key,
                value=value,
                scope=scope,
                expires_at=expires_at,
                tags=tags,
            )

            self._store[key] = entry
            self._access_count[key] = 1
            self._total_sets += 1

            return entry

    def delete(self, key: str) -> bool:
        """删除状态条目，返回是否存在"""
        with self._lock:
            if key in self._store:
                self._remove(key)
                return True
            return False

    def has(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        return self.get(key) is not None

    def update(self, key: str, updater: Callable[[Any], Any]) -> StateEntry | None:
        """
        原子更新：读取当前值，应用 updater 函数，写入新条目。

        updater 接收当前值，返回新值。
        返回更新后的条目，如果键不存在则返回 None。
        """
        with self._lock:
            entry = self.get(key)
            if entry is None:
                return None
            new_entry = entry.with_value(updater(entry.value))
            self._store[key] = new_entry
            return new_entry

    def clear(self) -> int:
        """清空所有条目，返回被清除的数量"""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._access_count.clear()
            return count

    def keys(self) -> list[str]:
        """返回所有有效键（不含已过期）"""
        with self._lock:
            self._cleanup_expired()
            return list(self._store.keys())

    def size(self) -> int:
        """返回当前条目数（不含已过期）"""
        with self._lock:
            self._cleanup_expired()
            return len(self._store)

    # ── 标签查询 ──────────────────────────────────────────────

    def find_by_tag(self, tag: str) -> list[StateEntry]:
        """按标签查找条目"""
        with self._lock:
            self._cleanup_expired()
            return [
                entry for entry in self._store.values()
                if tag in entry.tags
            ]

    def delete_by_tag(self, tag: str) -> int:
        """按标签删除条目，返回删除数量"""
        with self._lock:
            keys_to_delete = [
                key for key, entry in self._store.items()
                if tag in entry.tags
            ]
            for key in keys_to_delete:
                self._remove(key)
            return len(keys_to_delete)

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
        scope: StateScope = StateScope.REQUEST,
        ttl: float | None = None,
    ) -> list[StateEntry]:
        """批量设置"""
        return [
            self.set(key, value, scope, ttl)
            for key, value in items.items()
        ]

    # ── 统计 ──────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回存储统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            return {
                "size": len(self._store),
                "max_size": self._config.local_max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
                "total_sets": self._total_sets,
                "eviction_policy": self._config.local_eviction_policy,
            }

    # ── 内部方法 ──────────────────────────────────────────────

    def _remove(self, key: str) -> None:
        """移除条目（调用者需持有锁）"""
        self._store.pop(key, None)
        self._access_count.pop(key, None)

    def _evict(self) -> None:
        """根据淘汰策略移除一个条目（调用者需持有锁）"""
        if not self._store:
            return

        policy = self._config.local_eviction_policy

        if policy == "lru":
            # OrderedDict 末尾是最近使用的，头部是最久未用的
            victim_key = next(iter(self._store))
        elif policy == "lfu":
            # 选择访问次数最少的
            victim_key = min(
                self._store.keys(),
                key=lambda k: self._access_count.get(k, 0),
            )
        elif policy == "fifo":
            victim_key = next(iter(self._store))
        else:
            victim_key = next(iter(self._store))

        self._remove(victim_key)
        self._evictions += 1

    def _cleanup_expired(self) -> None:
        """清理所有已过期条目（调用者需持有锁）"""
        expired_keys = [
            key for key, entry in self._store.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            self._remove(key)
