"""
State Coordinator — 状态协调器

统一的状态管理入口，协调 LocalStore、CacheLayer、SessionManager 和 PersistenceLayer。

特征：
- 多层透明访问（热→温→冷自动穿透）
- 配置驱动的缓存策略
- 自动过期清理
- 统一统计
- 事件钩子

架构：
    Application
         │
    StateCoordinator
         │
    ┌────┼────┬────────┬──────────┐
    │    │    │        │          │
  Local Cache Session  Persist  StateMachine
  Store Layer  Manager  Layer
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from .cache_layer import CacheLayer
from .local_store import LocalStore
from .persistence import PersistenceLayer
from .session_manager import SessionManager
from .state_machine import StateMachine, StateTransition
from .state_types import CachePolicy, StateConfig, StateEntry, StateScope

logger = logging.getLogger(__name__)


class StateCoordinator:
    """
    状态协调器

    提供统一的状态管理接口，自动在多层存储间穿透：

    1. get(key) → 先查 LocalStore → 再查 Cache → 最后查 Persistence
    2. set(key, value) → 根据 scope 决定写入哪些层
    3. 自动缓存穿透：底层数据被读取时自动提升到上层

    用法：
        coordinator = StateCoordinator()
        coordinator.set("config:theme", "dark", scope=StateScope.USER, ttl=3600)
        value = coordinator.get("config:theme")  # 自动穿透查找
    """

    def __init__(
        self,
        config: StateConfig | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._config = config or StateConfig.default()
        self._lock = threading.RLock()

        # 初始化各层
        self._local = LocalStore(self._config)
        self._cache = CacheLayer(self._config, redis_client)
        self._persistence = PersistenceLayer(self._config)
        self._session = SessionManager(self._config, self._local)

        # 状态机注册表
        self._machines: dict[str, StateMachine] = {}

        # 钩子
        self._on_get: list[Callable[[str, Any], None]] = []
        self._on_set: list[Callable[[str, Any, StateScope], None]] = []
        self._on_miss: list[Callable[[str], None]] = []

        # 后台清理
        self._cleanup_interval = 300.0  # 5 分钟
        self._last_cleanup = time.time()

    # ── 统一状态操作 ──────────────────────────────────────────

    def get(
        self,
        key: str,
        scope: StateScope | None = None,
        policy: CachePolicy = CachePolicy.CACHE_ASIDE,
    ) -> Any | None:
        """
        获取状态值

        按层级穿透查找：Local → Cache → Persist
        找到的值自动提升到更热的层。
        """
        # 1. 查 Local Store
        entry = self._local.get(key)
        if entry is not None:
            self._trigger_hooks(self._on_get, key, entry.value)
            return entry.value

        # 2. 查 Cache Layer
        value = self._cache.get(key)
        if value is not None:
            # 提升到 Local
            self._local.set(key, value, scope or StateScope.REQUEST)
            self._trigger_hooks(self._on_get, key, value)
            return value

        # 3. 查 Persistence
        entry = self._persistence.get(key)
        if entry is not None:
            # 提升到 Cache 和 Local
            self._cache.set(key, entry.value)
            self._local.set(key, entry.value, entry.scope)
            self._trigger_hooks(self._on_get, key, entry.value)
            return entry.value

        # 全部 miss
        self._trigger_hooks(self._on_miss, key)
        return None

    def set(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.SESSION,
        ttl: float | None = None,
        tags: tuple[str, ...] = (),
        persist: bool = False,
    ) -> StateEntry:
        """
        设置状态值

        根据 scope 决定写入哪些层：
        - REQUEST: 只写 Local
        - SESSION: 写 Local + Cache
        - USER: 写 Local + Cache + Persist
        - GLOBAL: 写 Local + Cache + Persist
        - DISTRIBUTED: 写所有层 + 事件日志
        """
        effective_ttl = ttl or self._config.cache_default_ttl

        # 总是写 Local
        entry = self._local.set(key, value, scope, effective_ttl, tags)

        # SESSION 以上写 Cache
        if scope in (StateScope.SESSION, StateScope.USER, StateScope.GLOBAL, StateScope.DISTRIBUTED):
            self._cache.set(key, value, effective_ttl)

        # USER 以上写 Persist
        if persist or scope in (StateScope.USER, StateScope.GLOBAL, StateScope.DISTRIBUTED):
            self._persistence.set(key, value, scope, effective_ttl, tags)

        self._trigger_hooks(self._on_set, key, value, scope)
        return entry

    def delete(self, key: str) -> bool:
        """删除状态值（从所有层删除）"""
        results = [
            self._local.delete(key),
            self._cache.delete(key),
            self._persistence.delete(key),
        ]
        return any(results)

    def has(self, key: str) -> bool:
        """检查键是否存在（任一层存在即返回 True）"""
        return (
            self._local.has(key)
            or self._cache.exists(key)
            or self._persistence.has(key)
        )

    # ── 缓存策略 ──────────────────────────────────────────────

    def cache_aside(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: float | None = None,
    ) -> Any:
        """
        Cache-Aside 策略

        先查所有层，miss 则调用 loader 并缓存结果。
        """
        value = self.get(key)
        if value is not None:
            return value

        # 调用 loader
        value = loader()
        if value is not None:
            self.set(key, value, StateScope.SESSION, ttl)
        return value

    def write_through(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Write-Through 策略：同时写入所有层"""
        self.set(key, value, StateScope.USER, ttl, persist=True)

    # ── 会话管理 ──────────────────────────────────────────────

    @property
    def session(self) -> SessionManager:
        """会话管理器"""
        return self._session

    def create_session(
        self,
        user_id: str | None = None,
        initial_data: dict[str, Any] | None = None,
    ) -> str:
        """创建会话，返回 session_id"""
        config = self._session.create(user_id=user_id, initial_data=initial_data)
        return config.session_id

    def get_session_data(self, session_id: str, key: str) -> Any | None:
        """获取会话数据"""
        return self._session.get_attribute(session_id, key)

    def set_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """设置会话数据"""
        return self._session.set_attribute(session_id, key, value)

    # ── 状态机 ──────────────────────────────────────────────

    def create_state_machine(
        self,
        name: str,
        initial_state: str,
        transitions: list[StateTransition] | None = None,
    ) -> StateMachine:
        """创建并注册状态机"""
        sm = StateMachine(initial_state, name)
        if transitions:
            sm.add_transitions(transitions)
        self._machines[name] = sm
        return sm

    def get_state_machine(self, name: str) -> StateMachine | None:
        """获取已注册的状态机"""
        return self._machines.get(name)

    # ── 钩子 ──────────────────────────────────────────────────

    def on_get(self, callback: Callable[[str, Any], None]) -> None:
        """注册 get 钩子"""
        self._on_get.append(callback)

    def on_set(self, callback: Callable[[str, Any, StateScope], None]) -> None:
        """注册 set 钩子"""
        self._on_set.append(callback)

    def on_miss(self, callback: Callable[[str], None]) -> None:
        """注册 miss 钩子"""
        self._on_miss.append(callback)

    # ── 批量操作 ──────────────────────────────────────────────

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """批量获取"""
        result = {}
        missing_keys = []

        # 先从 Local 查
        for key in keys:
            entry = self._local.get(key)
            if entry is not None:
                result[key] = entry.value
            else:
                missing_keys.append(key)

        if not missing_keys:
            return result

        # 从 Cache 批量查
        cached = self._cache.get_many(missing_keys)
        still_missing = []
        for key in missing_keys:
            if key in cached:
                result[key] = cached[key]
                # 提升到 Local
                self._local.set(key, cached[key], StateScope.REQUEST)
            else:
                still_missing.append(key)

        # 从 Persist 查
        for key in still_missing:
            entry = self._persistence.get(key)
            if entry is not None:
                result[key] = entry.value
                # 提升
                self._cache.set(key, entry.value)
                self._local.set(key, entry.value, entry.scope)

        return result

    def set_many(
        self,
        items: dict[str, Any],
        scope: StateScope = StateScope.SESSION,
        ttl: float | None = None,
    ) -> int:
        """批量设置"""
        count = 0
        for key, value in items.items():
            self.set(key, value, scope, ttl)
            count += 1
        return count

    # ── 清理和统计 ──────────────────────────────────────────

    def cleanup(self) -> dict[str, int]:
        """执行清理操作"""
        with self._lock:
            local_size = self._local.size()
            persist_cleaned = self._persistence.cleanup_expired()
            self._last_cleanup = time.time()

            return {
                "local_size": local_size,
                "persist_cleaned": persist_cleaned,
            }

    def stats(self) -> dict[str, Any]:
        """返回全局统计信息"""
        return {
            "local": self._local.stats(),
            "cache": self._cache.stats(),
            "persistence": self._persistence.stats(),
            "sessions": self._session.stats(),
            "state_machines": len(self._machines),
            "last_cleanup": self._last_cleanup,
        }

    def clear_all(self) -> dict[str, int]:
        """清空所有层"""
        return {
            "local_cleared": self._local.clear(),
            "cache_cleared": self._cache.clear_prefix(""),
            "persist_cleared": self._persistence.clear(),
        }

    # ── 内部方法 ──────────────────────────────────────────────

    def _trigger_hooks(
        self,
        hooks: list[Callable],
        *args: Any,
    ) -> None:
        """触发钩子（忽略错误）"""
        for hook in hooks:
            try:
                hook(*args)
            except Exception as e:
                logger.warning(f"Hook error: {e}")
