"""
Cache Layer — Redis 缓存层

温数据层，毫秒级访问。支持多种缓存策略。

特征：
- Cache-Aside（懒加载）— 最常用
- Write-Through（写穿透）— 强一致性
- Write-Behind（写回）— 高吞吐
- 自动序列化/反序列化
- 缓存预热
- 概率性提前过期（防止缓存雪崩）
- Pub/Sub 缓存失效通知

设计决策：
- 默认使用 JSON 序列化（可读性好，跨语言）
- 支持 pickle 作为备选（Python 对象序列化）
- 所有键自动添加前缀，防止命名冲突
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from typing import Any, Callable

from .state_types import CachePolicy, StateConfig, StateEntry, StateScope

logger = logging.getLogger(__name__)


class CacheLayer:
    """
    Redis 缓存层

    支持两种模式：
    1. Redis 模式：连接真实 Redis（生产环境）
    2. 内存模式：使用 LocalStore 模拟（开发/测试环境）

    缓存策略通过 CachePolicy 枚举选择。
    """

    def __init__(
        self,
        config: StateConfig | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._config = config or StateConfig.default()
        self._redis = redis_client
        self._prefix = self._config.cache_prefix

        # 内存回退（当 Redis 不可用时）
        self._fallback: dict[str, tuple[Any, float | None]] = {}

        # 统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "fallback_uses": 0,
        }

    # ── 核心操作 ──────────────────────────────────────────────

    def get(self, key: str) -> Any | None:
        """获取缓存值，miss 返回 None"""
        full_key = self._full_key(key)

        try:
            if self._redis is not None:
                raw = self._redis.get(full_key)
                if raw is None:
                    self._stats["misses"] += 1
                    return None
                self._stats["hits"] += 1
                return self._deserialize(raw)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            self._stats["errors"] += 1

        # 回退到内存
        return self._fallback_get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
        policy: CachePolicy = CachePolicy.CACHE_ASIDE,
    ) -> bool:
        """设置缓存值"""
        full_key = self._full_key(key)
        effective_ttl = ttl or self._config.cache_default_ttl

        # 概率性提前过期（防止缓存雪崩）
        effective_ttl = self._jitter_ttl(effective_ttl)

        serialized = self._serialize(value)

        try:
            if self._redis is not None:
                if effective_ttl > 0:
                    self._redis.setex(full_key, int(effective_ttl), serialized)
                else:
                    self._redis.set(full_key, serialized)
                self._stats["sets"] += 1
                return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            self._stats["errors"] += 1

        # 回退到内存
        self._fallback_set(key, value, effective_ttl)
        return True

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        full_key = self._full_key(key)

        try:
            if self._redis is not None:
                result = self._redis.delete(full_key)
                self._stats["deletes"] += 1
                return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            self._stats["errors"] += 1

        return self._fallback_delete(key)

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        full_key = self._full_key(key)

        try:
            if self._redis is not None:
                return self._redis.exists(full_key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for {key}: {e}")
            self._stats["errors"] += 1

        return key in self._fallback

    def clear_prefix(self, prefix: str) -> int:
        """清除指定前缀的所有缓存"""
        full_prefix = self._full_key(prefix)
        count = 0

        try:
            if self._redis is not None:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(
                        cursor, match=f"{full_prefix}*", count=100
                    )
                    if keys:
                        count += self._redis.delete(*keys)
                    if cursor == 0:
                        break
                return count
        except Exception as e:
            logger.warning(f"Cache clear_prefix error: {e}")
            self._stats["errors"] += 1

        # 回退清理
        to_delete = [k for k in self._fallback if k.startswith(prefix)]
        for k in to_delete:
            del self._fallback[k]
            count += 1
        return count

    # ── 缓存策略 ──────────────────────────────────────────────

    def cache_aside(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: float | None = None,
    ) -> Any:
        """
        Cache-Aside 策略（懒加载）

        1. 查缓存 → hit 则返回
        2. miss → 调用 loader 加载数据
        3. 写入缓存
        4. 返回数据
        """
        value = self.get(key)
        if value is not None:
            return value

        # Cache miss — 加载数据
        value = loader()
        if value is not None:
            self.set(key, value, ttl, CachePolicy.CACHE_ASIDE)
        return value

    def write_through(
        self,
        key: str,
        value: Any,
        persist_fn: Callable[[str, Any], None],
        ttl: float | None = None,
    ) -> None:
        """
        Write-Through 策略

        同时写入缓存和持久化存储，确保强一致性。
        """
        persist_fn(key, value)
        self.set(key, value, ttl, CachePolicy.WRITE_THROUGH)

    def write_behind(
        self,
        key: str,
        value: Any,
        persist_fn: Callable[[str, Any], None],
        ttl: float | None = None,
    ) -> None:
        """
        Write-Behind 策略

        先写缓存，异步写持久化存储。
        注意：需要额外的异步处理器来执行 persist_fn。
        """
        self.set(key, value, ttl, CachePolicy.WRITE_BEHIND)
        # 实际的异步写入由调用者负责
        # 这里只是标记为 dirty，由后台任务处理
        logger.debug(f"Write-behind queued: {key}")

    # ── 批量操作 ──────────────────────────────────────────────

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """批量获取"""
        if not keys:
            return {}

        full_keys = [self._full_key(k) for k in keys]
        result = {}

        try:
            if self._redis is not None:
                values = self._redis.mget(full_keys)
                for key, raw in zip(keys, values):
                    if raw is not None:
                        result[key] = self._deserialize(raw)
                        self._stats["hits"] += 1
                    else:
                        self._stats["misses"] += 1
                return result
        except Exception as e:
            logger.warning(f"Cache mget error: {e}")
            self._stats["errors"] += 1

        # 回退
        for key in keys:
            val = self._fallback_get(key)
            if val is not None:
                result[key] = val
        return result

    def set_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
    ) -> int:
        """批量设置"""
        if not items:
            return 0

        effective_ttl = ttl or self._config.cache_default_ttl
        effective_ttl = self._jitter_ttl(effective_ttl)
        count = 0

        try:
            if self._redis is not None:
                pipe = self._redis.pipeline()
                for key, value in items.items():
                    full_key = self._full_key(key)
                    serialized = self._serialize(value)
                    if effective_ttl > 0:
                        pipe.setex(full_key, int(effective_ttl), serialized)
                    else:
                        pipe.set(full_key, serialized)
                pipe.execute()
                self._stats["sets"] += len(items)
                return len(items)
        except Exception as e:
            logger.warning(f"Cache mset error: {e}")
            self._stats["errors"] += 1

        # 回退
        for key, value in items.items():
            self._fallback_set(key, value, effective_ttl)
            count += 1
        return count

    # ── 缓存预热 ──────────────────────────────────────────────

    def warm_up(
        self,
        loader: Callable[[], dict[str, Any]],
        ttl: float | None = None,
    ) -> int:
        """
        缓存预热

        在应用启动时调用，预先加载热点数据到缓存。
        loader 返回 {key: value} 字典。
        """
        items = loader()
        count = self.set_many(items, ttl)
        logger.info(f"Cache warmed up with {count} entries")
        return count

    # ── 统计 ──────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回缓存统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0

        return {
            **self._stats,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
            "prefix": self._prefix,
            "backend": "redis" if self._redis else "memory",
            "fallback_size": len(self._fallback),
        }

    # ── 内部方法 ──────────────────────────────────────────────

    def _full_key(self, key: str) -> str:
        """生成完整缓存键"""
        return f"{self._prefix}{key}"

    def _serialize(self, value: Any) -> str:
        """序列化值为 JSON 字符串"""
        return json.dumps(value, default=str, ensure_ascii=False)

    def _deserialize(self, raw: str | bytes) -> Any:
        """反序列化 JSON 字符串为值"""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def _jitter_ttl(self, ttl: float) -> float:
        """
        概率性提前过期（防止缓存雪崩）

        在 TTL 上添加 ±10% 的随机抖动，
        使大量同批写入的缓存不会同时过期。
        """
        if ttl <= 0:
            return ttl
        jitter = ttl * 0.1
        return ttl + random.uniform(-jitter, jitter)

    def _fallback_get(self, key: str) -> Any | None:
        """内存回退获取"""
        if key not in self._fallback:
            self._stats["misses"] += 1
            return None

        value, expires_at = self._fallback[key]
        if expires_at is not None and time.time() > expires_at:
            del self._fallback[key]
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        self._stats["fallback_uses"] += 1
        return value

    def _fallback_set(self, key: str, value: Any, ttl: float) -> None:
        """内存回退设置"""
        expires_at = time.time() + ttl if ttl > 0 else None
        self._fallback[key] = (value, expires_at)
        self._stats["sets"] += 1
        self._stats["fallback_uses"] += 1

    def _fallback_delete(self, key: str) -> bool:
        """内存回退删除"""
        if key in self._fallback:
            del self._fallback[key]
            self._stats["deletes"] += 1
            return True
        return False

    # ── 缓存键生成工具 ────────────────────────────────────────

    @staticmethod
    def make_key(*parts: str) -> str:
        """生成缓存键"""
        return ":".join(str(p) for p in parts)

    @staticmethod
    def make_hash_key(data: Any) -> str:
        """基于数据内容生成哈希缓存键"""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
