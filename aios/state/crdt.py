"""
CRDT — Conflict-free Replicated Data Types

分布式无冲突复制数据类型，用于跨节点状态同步。

支持的 CRDT 类型：
1. G-Counter (Grow-only Counter) — 只增计数器
2. PN-Counter (Positive-Negative Counter) — 可增可减计数器
3. LWW-Register (Last-Writer-Wins Register) — 最后写入者获胜寄存器
4. OR-Set (Observed-Remove Set) — 可观察删除集
5. LWW-Element-Set — 最后写入者获胜元素集

CRDT 核心思想：
    所有副本可以独立更新，然后自动合并，无需协调。
    合并操作必须满足交换律、结合律、幂等律。

用途：
- 分布式计数器（如 PV/UV 统计）
- 分布式配置同步
- 离线优先应用
- 多节点状态最终一致
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class GCounter:
    """
    Grow-only Counter — 只增计数器

    每个节点维护自己的计数，合并时取各节点的最大值。
    只支持递增操作。

    数学性质：
        value = Σ counts[node] for all nodes
    """

    node_id: str
    counts: dict[str, int] = field(default_factory=dict)

    def increment(self, amount: int = 1) -> None:
        """递增本地计数"""
        if amount < 0:
            raise ValueError("GCounter only supports non-negative increments")
        current = self.counts.get(self.node_id, 0)
        self.counts[self.node_id] = current + amount

    @property
    def value(self) -> int:
        """获取总计数"""
        return sum(self.counts.values())

    def merge(self, other: GCounter) -> GCounter:
        """合并另一个 G-Counter"""
        merged_counts = dict(self.counts)
        for node, count in other.counts.items():
            merged_counts[node] = max(merged_counts.get(node, 0), count)
        return GCounter(node_id=self.node_id, counts=merged_counts)

    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "counts": dict(self.counts)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GCounter:
        return cls(node_id=data["node_id"], counts=data["counts"])


@dataclass
class PNCounter:
    """
    Positive-Negative Counter — 可增可减计数器

    用两个 G-Counter 实现：一个记录增量，一个记录减量。
    value = P - N
    """

    node_id: str
    p_counts: dict[str, int] = field(default_factory=dict)
    n_counts: dict[str, int] = field(default_factory=dict)

    def increment(self, amount: int = 1) -> None:
        """递增"""
        if amount < 0:
            raise ValueError("Use decrement for negative amounts")
        current = self.p_counts.get(self.node_id, 0)
        self.p_counts[self.node_id] = current + amount

    def decrement(self, amount: int = 1) -> None:
        """递减"""
        if amount < 0:
            raise ValueError("Use increment for positive amounts")
        current = self.n_counts.get(self.node_id, 0)
        self.n_counts[self.node_id] = current + amount

    @property
    def value(self) -> int:
        """获取当前值"""
        p = sum(self.p_counts.values())
        n = sum(self.n_counts.values())
        return p - n

    def merge(self, other: PNCounter) -> PNCounter:
        """合并另一个 PN-Counter"""
        merged_p = dict(self.p_counts)
        for node, count in other.p_counts.items():
            merged_p[node] = max(merged_p.get(node, 0), count)

        merged_n = dict(self.n_counts)
        for node, count in other.n_counts.items():
            merged_n[node] = max(merged_n.get(node, 0), count)

        return PNCounter(
            node_id=self.node_id,
            p_counts=merged_p,
            n_counts=merged_n,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "p_counts": dict(self.p_counts),
            "n_counts": dict(self.n_counts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PNCounter:
        return cls(
            node_id=data["node_id"],
            p_counts=data["p_counts"],
            n_counts=data["n_counts"],
        )


@dataclass
class LWWRegister(Generic[T]):
    """
    Last-Writer-Wins Register — 最后写入者获胜寄存器

    使用时间戳决定哪个写入生效。
    时间戳相同时，按 node_id 字典序决定。
    """

    node_id: str
    value: T | None = None
    timestamp: float = 0.0
    writer_node: str = ""

    def set(self, value: T) -> None:
        """设置值"""
        self.value = value
        self.timestamp = time.time()
        self.writer_node = self.node_id

    def merge(self, other: LWWRegister[T]) -> LWWRegister[T]:
        """合并另一个 LWW-Register"""
        if other.timestamp > self.timestamp:
            return LWWRegister(
                node_id=self.node_id,
                value=other.value,
                timestamp=other.timestamp,
                writer_node=other.writer_node,
            )
        elif other.timestamp == self.timestamp:
            # 时间戳相同，按 node_id 字典序
            if other.writer_node > self.writer_node:
                return LWWRegister(
                    node_id=self.node_id,
                    value=other.value,
                    timestamp=other.timestamp,
                    writer_node=other.writer_node,
                )
        return LWWRegister(
            node_id=self.node_id,
            value=self.value,
            timestamp=self.timestamp,
            writer_node=self.writer_node,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "value": self.value,
            "timestamp": self.timestamp,
            "writer_node": self.writer_node,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LWWRegister:
        return cls(**data)


@dataclass
class ORSet:
    """
    Observed-Remove Set — 可观察删除集

    支持添加和删除操作，解决 G-Set 只能添加的限制。
    使用标签（tag）区分同一个元素的不同添加。

    add(e): 添加元素，生成唯一标签
    remove(e): 删除元素的所有已观察标签
    """

    node_id: str
    elements: dict[str, set[str]] = field(default_factory=dict)
    tombstones: dict[str, set[str]] = field(default_factory=dict)
    _counter: int = 0

    def add(self, element: str) -> None:
        """添加元素"""
        self._counter += 1
        tag = f"{self.node_id}:{self._counter}"

        if element not in self.elements:
            self.elements[element] = set()
        self.elements[element].add(tag)

    def remove(self, element: str) -> bool:
        """删除元素（只删除已观察到的标签）"""
        if element not in self.elements:
            return False

        # 将当前标签移到墓碑
        if element not in self.tombstones:
            self.tombstones[element] = set()
        self.tombstones[element].update(self.elements[element])

        # 移除元素
        del self.elements[element]
        return True

    def contains(self, element: str) -> bool:
        """检查元素是否存在"""
        if element not in self.elements:
            return False

        # 检查是否有未被墓碑覆盖的标签
        tags = self.elements[element]
        dead_tags = self.tombstones.get(element, set())
        return bool(tags - dead_tags)

    @property
    def value(self) -> set[str]:
        """获取当前集合值"""
        return {e for e in self.elements if self.contains(e)}

    def merge(self, other: ORSet) -> ORSet:
        """合并另一个 OR-Set"""
        merged_elements: dict[str, set[str]] = {}
        merged_tombstones: dict[str, set[str]] = {}

        # 合并元素
        all_keys = set(self.elements.keys()) | set(other.elements.keys())
        for key in all_keys:
            tags = set()
            if key in self.elements:
                tags.update(self.elements[key])
            if key in other.elements:
                tags.update(other.elements[key])
            if tags:
                merged_elements[key] = tags

        # 合并墓碑
        all_tomb_keys = set(self.tombstones.keys()) | set(other.tombstones.keys())
        for key in all_tomb_keys:
            dead = set()
            if key in self.tombstones:
                dead.update(self.tombstones[key])
            if key in other.tombstones:
                dead.update(other.tombstones[key])
            if dead:
                merged_tombstones[key] = dead

        return ORSet(
            node_id=self.node_id,
            elements=merged_elements,
            tombstones=merged_tombstones,
            _counter=max(self._counter, other._counter),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "elements": {k: list(v) for k, v in self.elements.items()},
            "tombstones": {k: list(v) for k, v in self.tombstones.items()},
            "counter": self._counter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ORSet:
        return cls(
            node_id=data["node_id"],
            elements={k: set(v) for k, v in data["elements"].items()},
            tombstones={k: set(v) for k, v in data["tombstones"].items()},
            _counter=data["counter"],
        )


class CRDTStore:
    """
    CRDT 存储管理器

    管理多个 CRDT 实例，提供统一的合并和同步接口。
    """

    def __init__(self, node_id: str) -> None:
        self._node_id = node_id
        self._counters: dict[str, PNCounter] = {}
        self._registers: dict[str, LWWRegister] = {}
        self._sets: dict[str, ORSet] = {}
        self._lock = threading.RLock()

    # ── 计数器 ────────────────────────────────────────────────

    def get_counter(self, name: str) -> PNCounter:
        """获取或创建计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = PNCounter(node_id=self._node_id)
            return self._counters[name]

    def increment(self, name: str, amount: int = 1) -> int:
        """递增计数器"""
        counter = self.get_counter(name)
        counter.increment(amount)
        return counter.value

    def decrement(self, name: str, amount: int = 1) -> int:
        """递减计数器"""
        counter = self.get_counter(name)
        counter.decrement(amount)
        return counter.value

    # ── 寄存器 ────────────────────────────────────────────────

    def get_register(self, name: str) -> LWWRegister:
        """获取或创建寄存器"""
        with self._lock:
            if name not in self._registers:
                self._registers[name] = LWWRegister(node_id=self._node_id)
            return self._registers[name]

    def set_register(self, name: str, value: Any) -> None:
        """设置寄存器值"""
        register = self.get_register(name)
        register.set(value)

    # ── 集合 ──────────────────────────────────────────────────

    def get_set(self, name: str) -> ORSet:
        """获取或创建集合"""
        with self._lock:
            if name not in self._sets:
                self._sets[name] = ORSet(node_id=self._node_id)
            return self._sets[name]

    def set_add(self, name: str, element: str) -> None:
        """向集合添加元素"""
        s = self.get_set(name)
        s.add(element)

    def set_remove(self, name: str, element: str) -> bool:
        """从集合删除元素"""
        s = self.get_set(name)
        return s.remove(element)

    # ── 合并 ──────────────────────────────────────────────────

    def merge_state(self, remote_state: dict[str, Any]) -> None:
        """
        合并远程状态

        remote_state 格式：
        {
            "counters": {name: PNCounter.to_dict()},
            "registers": {name: LWWRegister.to_dict()},
            "sets": {name: ORSet.to_dict()},
        }
        """
        with self._lock:
            # 合并计数器
            for name, data in remote_state.get("counters", {}).items():
                remote = PNCounter.from_dict(data)
                local = self.get_counter(name)
                self._counters[name] = local.merge(remote)

            # 合并寄存器
            for name, data in remote_state.get("registers", {}).items():
                remote = LWWRegister.from_dict(data)
                local = self.get_register(name)
                self._registers[name] = local.merge(remote)

            # 合并集合
            for name, data in remote_state.get("sets", {}).items():
                remote = ORSet.from_dict(data)
                local = self.get_set(name)
                self._sets[name] = local.merge(remote)

    def export_state(self) -> dict[str, Any]:
        """导出当前状态（用于同步）"""
        with self._lock:
            return {
                "counters": {
                    name: counter.to_dict()
                    for name, counter in self._counters.items()
                },
                "registers": {
                    name: register.to_dict()
                    for name, register in self._registers.items()
                },
                "sets": {
                    name: s.to_dict()
                    for name, s in self._sets.items()
                },
            }

    def stats(self) -> dict[str, Any]:
        """返回统计信息"""
        return {
            "node_id": self._node_id,
            "counters": len(self._counters),
            "registers": len(self._registers),
            "sets": len(self._sets),
        }
