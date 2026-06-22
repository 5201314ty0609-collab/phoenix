"""
PHOENIX AIOS State Management System

五层状态架构：
1. Local State (进程内存) — 热数据，微秒级访问
2. Cache Layer (Redis) — 温数据，毫秒级访问
3. Session Store (Redis/DB) — 会话状态，跨请求持久
4. Persistent Store (SQLite/PostgreSQL) — 冷数据，持久化
5. Distributed State (Event Sourcing + CRDT) — 跨节点一致性

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    Application Layer                         │
    │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌─────────────┐ │
    │  │ Session  │ │  Cache   │ │   State    │ │   Event     │ │
    │  │ Manager  │ │  Layer   │ │  Machine   │ │   Store     │ │
    │  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └──────┬──────┘ │
    │       │            │             │               │         │
    │  ┌────┴────────────┴─────────────┴───────────────┴──────┐  │
    │  │              State Coordinator                        │  │
    │  └────┬────────────┬─────────────┬───────────────┬──────┘  │
    │       │            │             │               │         │
    │  ┌────┴────┐ ┌─────┴────┐ ┌──────┴──────┐ ┌─────┴──────┐  │
    │  │ Local   │ │  Cache   │ │ Persistence │ │  CRDT      │  │
    │  │ Store   │ │  Store   │ │   Layer     │ │  Store     │  │
    │  │(memory) │ │ (Redis)  │ │ (SQLite)    │ │(distributed│  │
    │  └─────────┘ └──────────┘ └─────────────┘ └────────────┘  │
    └─────────────────────────────────────────────────────────────┘

核心设计原则：
- 不可变数据结构（StateEntry, Event, Snapshot 等都是 frozen dataclass）
- 线程安全（所有公共方法使用 threading.RLock）
- 自动过期和清理
- 乐观并发控制
- 事件溯源支持
"""

from .state_types import (
    StateScope,
    StateEntry,
    StateConfig,
    CachePolicy,
    SessionConfig,
)
from .local_store import LocalStore
from .cache_layer import CacheLayer
from .session_manager import SessionManager
from .state_machine import StateMachine, StateTransition
from .state_coordinator import StateCoordinator
from .persistence import PersistenceLayer
from .event_store import EventStore, Event, Snapshot, ConcurrencyError
from .crdt import (
    GCounter,
    PNCounter,
    LWWRegister,
    ORSet,
    CRDTStore,
)

__all__ = [
    # 核心类型
    "StateScope",
    "StateEntry",
    "StateConfig",
    "CachePolicy",
    "SessionConfig",
    # 存储层
    "LocalStore",
    "CacheLayer",
    "PersistenceLayer",
    # 会话管理
    "SessionManager",
    # 状态机
    "StateMachine",
    "StateTransition",
    # 事件溯源
    "EventStore",
    "Event",
    "Snapshot",
    "ConcurrencyError",
    # CRDT
    "GCounter",
    "PNCounter",
    "LWWRegister",
    "ORSet",
    "CRDTStore",
    # 协调器
    "StateCoordinator",
]
