# PHOENIX AIOS State Management Architecture

## 概述

PHOENIX AIOS 的状态管理系统采用五层架构，从热到冷依次为：

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                              │
├──────────┬──────────┬──────────┬──────────┬──────────────────────┤
│  Local   │  Cache   │ Session  │ Persist  │  Distributed        │
│  Store   │  Layer   │ Manager  │  Layer   │  (Event+CRDT)       │
│ (memory) │ (Redis)  │ (Redis)  │ (SQLite) │  (跨节点)            │
├──────────┼──────────┼──────────┼──────────┼──────────────────────┤
│ 微秒级   │ 毫秒级   │ 毫秒级   │ 毫秒级   │ 秒级                 │
│ 进程内   │ 内存     │ 内存     │ 磁盘     │ 网络                 │
│ 无持久   │ 可选持久 │ 持久     │ 持久     │ 最终一致             │
└──────────┴──────────┴──────────┴──────────┴──────────────────────┘
```

## 核心原则

### 1. 不可变性

所有状态条目（StateEntry、Event、Snapshot 等）都是 `frozen dataclass`。
修改必须创建新实例，而非修改现有对象。

```python
# 错误：修改现有对象
entry.value = new_value

# 正确：创建新实例
new_entry = entry.with_value(new_value)
```

### 2. 线程安全

所有公共方法使用 `threading.RLock` 保护，支持多线程并发访问。

### 3. 自动过期

每个状态条目可设置 TTL，过期后自动清理。支持两种过期策略：
- **绝对过期**：创建时指定 `expires_at`
- **滑动过期**：每次访问刷新（用于会话）

### 4. 分层穿透

`StateCoordinator` 自动在多层间穿透查找：
1. 先查 Local Store（热数据）
2. miss 则查 Cache Layer（温数据）
3. miss 则查 Persistence Layer（冷数据）
4. 找到的数据自动提升到更热的层

## 模块详解

### LocalStore — 进程内存存储

**用途**：热数据，微秒级访问

**淘汰策略**：
- LRU (Least Recently Used) — 默认
- LFU (Least Frequently Used)
- FIFO (First In First Out)

**典型场景**：
- 请求级别的临时数据
- 频繁读取的配置
- 计算结果缓存

```python
store = LocalStore()
store.set("key", "value", scope=StateScope.REQUEST, ttl=60)
entry = store.get("key")  # 微秒级
```

### CacheLayer — Redis 缓存层

**用途**：温数据，毫秒级访问

**缓存策略**：
| 策略 | 描述 | 适用场景 |
|------|------|---------|
| Cache-Aside | 先查缓存，miss 则读 DB | 读多写少 |
| Write-Through | 同时写缓存和 DB | 强一致性 |
| Write-Behind | 先写缓存，异步写 DB | 高吞吐 |
| Read-Through | 缓存透明代理 DB | 简化代码 |

**防雪崩**：TTL 自动添加 ±10% 随机抖动。

```python
cache = CacheLayer(config, redis_client)
value = cache.cache_aside("user:123", loader=lambda: db.get_user(123))
```

### SessionManager — 会话管理器

**用途**：跨请求的用户会话状态

**生命周期**：
```
Created → Active → Idle → Expired → Destroyed
             ↑       │
             └───────┘  (续期)
```

**安全特性**：
- 使用 `secrets.token_urlsafe(32)` 生成会话 ID
- 空闲超时 + 最大生命周期双重过期
- 滑动窗口续期

```python
session_mgr = SessionManager(config)
session = session_mgr.create(user_id="user:123")
session_mgr.set_attribute(session.session_id, "theme", "dark")
```

### StateMachine — 状态机引擎

**用途**：显式状态建模与转换管理

**特性**：
- 声明式状态和转换定义
- 守卫条件（Guard Conditions）
- 转换副作用（Side Effects）
- 状态历史记录
- Graphviz DOT 导出

```python
sm = StateMachine("idle", "order")
sm.add_transition(StateTransition(
    from_state="idle",
    to_state="running",
    event="start",
    guard=lambda ctx: ctx.get("ready", False),
    action=lambda ctx: {**ctx, "started_at": time.time()},
))
sm.send_event("start")  # True if transition succeeded
```

### EventStore — 事件溯源存储

**用途**：分布式状态的基础

**核心思想**：`State = fold(events)`

**特性**：
- 不可变事件日志
- 乐观并发控制（版本号）
- 快照支持（避免全量重放）
- 事件订阅（观察者模式）

```python
store = EventStore()

# 追加事件
store.append("order:123", "OrderCreated", {"total": 100})
store.append("order:123", "OrderPaid", {"method": "card"}, expected_version=1)

# 重建状态
state = store.rebuild_state("order:123", order_reducer)
```

### CRDT — 无冲突复制数据类型

**用途**：跨节点状态同步，无需协调

**支持的类型**：
| 类型 | 操作 | 用途 |
|------|------|------|
| G-Counter | 只增 | PV 统计 |
| PN-Counter | 可增可减 | 库存计数 |
| LWW-Register | 覆盖写 | 配置同步 |
| OR-Set | 添加/删除 | 标签管理 |

**数学性质**：合并操作满足交换律、结合律、幂等律。

```python
crdt = CRDTStore(node_id="node-1")
crdt.increment("page_views")
crdt.set_add("tags", "python")

# 合并远程状态
crdt.merge_state(remote_state)
```

### StateCoordinator — 状态协调器

**用途**：统一的状态管理入口

**职责**：
1. 协调多层存储
2. 自动穿透查找
3. 会话管理
4. 状态机注册
5. 统计和监控

```python
coordinator = StateCoordinator(config)

# 统一接口
coordinator.set("config:theme", "dark", scope=StateScope.USER)
value = coordinator.get("config:theme")  # 自动穿透

# 会话管理
session_id = coordinator.create_session(user_id="user:123")
coordinator.set_session_data(session_id, "theme", "dark")

# 状态机
sm = coordinator.create_state_machine("order", "idle", transitions)
```

## 缓存策略详解

### Cache-Aside（懒加载）

最常用的缓存策略。应用负责管理缓存：

```
读：App → Cache? → Hit: return
                 → Miss: DB → Cache → return
写：App → DB → Invalidate Cache
```

**优点**：简单，缓存只包含应用实际读取的数据
**缺点**：首次请求必然 miss

### Write-Through（写穿透）

同时写缓存和 DB，确保强一致性：

```
写：App → Cache + DB → return
读：App → Cache → return (always hit after write)
```

**优点**：数据一致性好
**缺点**：写延迟较高

### Write-Behind（写回）

先写缓存，异步写 DB：

```
写：App → Cache → return (async: Cache → DB)
读：App → Cache → return
```

**优点**：写延迟最低
**缺点**：缓存故障可能丢失数据

## 事件溯源详解

### 事件不可变性

事件一旦追加，不可修改或删除。状态变更只能通过追加新事件表达。

### 乐观并发控制

```python
# 版本检查
store.append("order:123", "OrderPaid", data, expected_version=1)
# 如果当前版本不是 1，抛出 ConcurrencyError
```

### 快照优化

当事件流很长时，定期创建快照避免全量重放：

```python
# 创建快照
store.save_snapshot(Snapshot("order:123", version=100, state=current_state))

# 重建时从快照开始
state = store.rebuild_state("order:123", reducer)
# 只重放快照之后的事件
```

## CRDT 详解

### 为什么需要 CRDT？

在分布式系统中，多个节点可能同时修改同一数据。传统的加锁方式会影响可用性。
CRDT 通过数学性质保证：无论合并顺序如何，最终结果一致。

### G-Counter

```
Node A: {A: 3, B: 2}  → value = 5
Node B: {A: 2, B: 4}  → value = 6

合并: {A: max(3,2), B: max(2,4)} = {A: 3, B: 4} → value = 7
```

### PN-Counter

```
P-Counter: {A: 5, B: 3} → P = 8
N-Counter: {A: 1, B: 2} → N = 3

value = P - N = 8 - 3 = 5
```

### OR-Set

```
Node A: add("x") → elements = {"x": {tag1}}
Node B: add("x") → elements = {"x": {tag2}}
Node A: remove("x") → tombstones = {"x": {tag1}}

合并后: {"x": {tag1, tag2}} - tombstones {"x": {tag1}} = {"x": {tag2}}
→ "x" 仍然存在（因为 tag2 未被删除）
```

## 使用建议

### 选择缓存策略

| 场景 | 推荐策略 |
|------|---------|
| 用户配置 | Cache-Aside + TTL 1h |
| 实时数据 | No Cache |
| 会话状态 | Session Manager |
| 统计数据 | CRDT Counter |
| 审计日志 | Event Sourcing |
| 分布式锁 | Redis + Redlock |

### TTL 建议

| 数据类型 | TTL |
|---------|-----|
| 静态配置 | 1h |
| 用户资料 | 5min |
| 实时数据 | 不缓存 |
| 会话数据 | 30min 空闲 |
| 统计数据 | 1min |

### 监控指标

关注以下指标：
- Cache hit rate（目标 > 80%）
- Session active count
- Event store size
- CRDT merge frequency
- Local store eviction rate
