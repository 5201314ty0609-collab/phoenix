"""
State Machine — 状态机引擎

显式状态建模与转换管理。

特征：
- 声明式状态和转换定义
- 守卫条件（Guard Conditions）
- 转换副作用（Side Effects）
- 状态历史记录
- 并发安全
- 事件驱动

典型用途：
- 订单状态管理
- 工作流引擎
- Agent 任务状态
- 用户会话状态
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StateTransition:
    """
    状态转换定义 — 不可变

    定义从一个状态到另一个状态的转换规则。
    """

    from_state: str
    to_state: str
    event: str
    guard: Callable[[dict[str, Any]], bool] | None = None
    action: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    description: str = ""

    def can_execute(self, context: dict[str, Any]) -> bool:
        """检查守卫条件是否允许执行"""
        if self.guard is None:
            return True
        return self.guard(context)

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行转换副作用"""
        if self.action is None:
            return context
        return self.action(context)


@dataclass(frozen=True)
class StateRecord:
    """状态历史记录 — 不可变"""

    state: str
    entered_at: float
    exited_at: float | None = None
    event: str | None = None
    context_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        if self.exited_at is None:
            return time.time() - self.entered_at
        return self.exited_at - self.entered_at


class StateMachine:
    """
    状态机引擎

    支持：
    - 声明式状态转换
    - 守卫条件
    - 转换副作用
    - 状态历史
    - 并发安全

    用法：
        sm = StateMachine(initial_state="idle")
        sm.add_transition(StateTransition(
            from_state="idle",
            to_state="running",
            event="start",
            action=lambda ctx: {**ctx, "started_at": time.time()},
        ))
        sm.send_event("start")
    """

    def __init__(
        self,
        initial_state: str,
        name: str = "unnamed",
    ) -> None:
        self._name = name
        self._current_state = initial_state
        self._context: dict[str, Any] = {}
        self._transitions: dict[str, list[StateTransition]] = {}
        self._history: list[StateRecord] = []
        self._lock = threading.RLock()

        # 回调
        self._on_enter: dict[str, list[Callable[[str, dict[str, Any]], None]]] = {}
        self._on_exit: dict[str, list[Callable[[str, dict[str, Any]], None]]] = {}
        self._on_transition: list[Callable[[str, str, str], None]] = []

        # 记录初始状态
        self._history.append(StateRecord(
            state=initial_state,
            entered_at=time.time(),
        ))

    # ── 状态查询 ──────────────────────────────────────────────

    @property
    def current_state(self) -> str:
        """当前状态"""
        return self._current_state

    @property
    def context(self) -> dict[str, Any]:
        """当前上下文（只读副本）"""
        return dict(self._context)

    @property
    def history(self) -> list[StateRecord]:
        """状态历史（只读副本）"""
        return list(self._history)

    def available_events(self) -> list[str]:
        """获取当前状态下可用的事件"""
        with self._lock:
            transitions = self._transitions.get(self._current_state, [])
            return [t.event for t in transitions if t.can_execute(self._context)]

    def can_send_event(self, event: str) -> bool:
        """检查事件是否可执行"""
        return event in self.available_events()

    # ── 转换定义 ──────────────────────────────────────────────

    def add_transition(self, transition: StateTransition) -> None:
        """添加状态转换规则"""
        with self._lock:
            if transition.from_state not in self._transitions:
                self._transitions[transition.from_state] = []
            self._transitions[transition.from_state].append(transition)

    def add_transitions(self, transitions: list[StateTransition]) -> None:
        """批量添加状态转换规则"""
        for t in transitions:
            self.add_transition(t)

    # ── 事件处理 ──────────────────────────────────────────────

    def send_event(
        self,
        event: str,
        context_updates: dict[str, Any] | None = None,
    ) -> bool:
        """
        发送事件触发状态转换

        Returns:
            True 如果转换成功，False 如果事件不被接受
        """
        with self._lock:
            transitions = self._transitions.get(self._current_state, [])

            for transition in transitions:
                if transition.event != event:
                    continue

                if not transition.can_execute(self._context):
                    logger.debug(
                        f"Guard rejected: {self._current_state} --{event}--> "
                        f"{transition.to_state}"
                    )
                    continue

                # 执行转换
                old_state = self._current_state

                # 更新上下文
                if context_updates:
                    self._context.update(context_updates)

                # 执行副作用
                self._context = transition.execute(self._context)

                # 触发退出回调
                for callback in self._on_exit.get(old_state, []):
                    try:
                        callback(old_state, self._context)
                    except Exception as e:
                        logger.error(f"Exit callback error: {e}")

                # 更新状态
                self._current_state = transition.to_state

                # 记录历史
                if self._history:
                    # 更新上一条记录的退出时间
                    last = self._history[-1]
                    self._history[-1] = StateRecord(
                        state=last.state,
                        entered_at=last.entered_at,
                        exited_at=time.time(),
                        event=last.event,
                        context_snapshot=last.context_snapshot,
                    )

                self._history.append(StateRecord(
                    state=transition.to_state,
                    entered_at=time.time(),
                    event=event,
                    context_snapshot=dict(self._context),
                ))

                # 触发进入回调
                for callback in self._on_enter.get(transition.to_state, []):
                    try:
                        callback(transition.to_state, self._context)
                    except Exception as e:
                        logger.error(f"Enter callback error: {e}")

                # 触发转换回调
                for callback in self._on_transition:
                    try:
                        callback(old_state, transition.to_state, event)
                    except Exception as e:
                        logger.error(f"Transition callback error: {e}")

                logger.debug(
                    f"[{self._name}] {old_state} --{event}--> "
                    f"{transition.to_state}"
                )
                return True

            logger.warning(
                f"[{self._name}] No transition for event '{event}' "
                f"in state '{self._current_state}'"
            )
            return False

    # ── 回调注册 ──────────────────────────────────────────────

    def on_enter(self, state: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        """注册进入状态回调"""
        if state not in self._on_enter:
            self._on_enter[state] = []
        self._on_enter[state].append(callback)

    def on_exit(self, state: str, callback: Callable[[str, dict[str, Any]], None]) -> None:
        """注册退出状态回调"""
        if state not in self._on_exit:
            self._on_exit[state] = []
        self._on_exit[state].append(callback)

    def on_transition(self, callback: Callable[[str, str, str], None]) -> None:
        """注册状态转换回调"""
        self._on_transition.append(callback)

    # ── 上下文操作 ────────────────────────────────────────────

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文值"""
        with self._lock:
            self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return self._context.get(key, default)

    def update_context(self, updates: dict[str, Any]) -> None:
        """批量更新上下文"""
        with self._lock:
            self._context.update(updates)

    # ── 重置 ──────────────────────────────────────────────────

    def reset(self, initial_state: str | None = None) -> None:
        """重置状态机到初始状态"""
        with self._lock:
            target = initial_state or self._history[0].state
            self._current_state = target
            self._context = {}
            self._history = [StateRecord(
                state=target,
                entered_at=time.time(),
            )]

    # ── 可视化 ──────────────────────────────────────────────

    def to_dot(self) -> str:
        """导出为 Graphviz DOT 格式"""
        lines = [f'digraph {self._name} {{']
        lines.append(f'  node [shape=box];')
        lines.append(f'  __start__ [shape=point];')
        lines.append(f'  __start__ -> "{self._history[0].state}";')

        # 标记当前状态
        lines.append(f'  "{self._current_state}" [style=filled, fillcolor=lightgreen];')

        for from_state, transitions in self._transitions.items():
            for t in transitions:
                label = t.event
                if t.description:
                    label += f"\\n{t.description}"
                lines.append(
                    f'  "{from_state}" -> "{t.to_state}" '
                    f'[label="{label}"];'
                )

        lines.append('}')
        return '\n'.join(lines)

    def summary(self) -> dict[str, Any]:
        """状态机摘要"""
        with self._lock:
            return {
                "name": self._name,
                "current_state": self._current_state,
                "context": dict(self._context),
                "total_transitions": len(self._history) - 1,
                "available_events": self.available_events(),
                "states": list(set(r.state for r in self._history)),
            }
