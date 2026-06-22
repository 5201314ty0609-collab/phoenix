"""
Agent 管理器 — Agent 生命周期管理

负责：
1. Agent 实例的创建、启动、暂停、恢复、停止
2. Agent 状态的追踪和持久化
3. Agent 事件的收集和分发
4. Agent 资源的管理

Design:
    ┌─────────────────────────────────────────────────────────────┐
    │                     Agent Manager                            │
    │                                                              │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
    │  │  Create  │  │  Start   │  │  Pause   │  │   Stop     │ │
    │  │  Agent   │  │  Agent   │  │  Agent   │  │   Agent    │ │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
    │       │             │             │               │         │
    │  ┌────┴─────────────┴─────────────┴───────────────┴──────┐  │
    │  │                  Agent Registry                        │  │
    │  │  (agent_id → AgentInstance mapping)                   │  │
    │  └───────────────────────────────────────────────────────┘  │
    │       │                                                     │
    │  ┌────┴──────────────────────────────────────────────────┐  │
    │  │                  Event Bus                             │  │
    │  │  (收集和分发 Agent 事件)                               │  │
    │  └───────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .agent_types import (
    AgentConfig,
    AgentEvent,
    AgentMessage,
    AgentState,
    AgentStatus,
    AgentType,
    ExecutionMode,
    LLMProvider,
    MessageRole,
    TaskStatus,
)
from .react_engine import ReActEngine, ReActConfig, ReActResult
from .plan_engine import PlanEngine, PlanConfig, PlanResult
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class AgentInstance:
    """
    Agent 实例

    包含 Agent 的配置、状态和引擎实例。
    """

    config: AgentConfig
    state: AgentState
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def agent_id(self) -> str:
        return self.config.agent_id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        return self.state.status

    @property
    def is_running(self) -> bool:
        return self.state.status == AgentStatus.RUNNING

    @property
    def is_idle(self) -> bool:
        return self.state.status == AgentStatus.IDLE

    def with_state(self, new_state: AgentState) -> AgentInstance:
        """返回带有新状态的新实例"""
        return AgentInstance(
            config=self.config,
            state=new_state,
            created_at=self.created_at,
            metadata=self.metadata,
        )


class AgentManager:
    """
    Agent 管理器

    管理所有 Agent 实例的生命周期。
    线程安全，支持并发操作。
    """

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self._llm = llm_provider
        self._tools = tool_registry or ToolRegistry()
        self._agents: dict[str, AgentInstance] = {}
        self._react_engines: dict[str, ReActEngine] = {}
        self._plan_engines: dict[str, PlanEngine] = {}
        self._event_handlers: list[Callable[[AgentEvent], None]] = []
        self._lock = threading.RLock()

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tools

    @property
    def llm_provider(self) -> LLMProvider | None:
        return self._llm

    def set_llm_provider(self, provider: LLMProvider) -> None:
        """设置 LLM 提供者"""
        self._llm = provider

    def register_event_handler(self, handler: Callable[[AgentEvent], None]) -> None:
        """注册事件处理器"""
        with self._lock:
            self._event_handlers.append(handler)

    def _emit_event(self, event: AgentEvent) -> None:
        """发送事件"""
        with self._lock:
            handlers = list(self._event_handlers)
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # 事件处理器不应影响主流程

    def create_agent(
        self,
        config: AgentConfig,
        auto_start: bool = False,
    ) -> AgentInstance:
        """
        创建 Agent

        Args:
            config: Agent 配置
            auto_start: 是否自动启动

        Returns:
            AgentInstance: 创建的 Agent 实例
        """
        with self._lock:
            if config.agent_id in self._agents:
                raise ValueError(f"Agent 已存在: {config.agent_id}")

            # 创建初始状态
            state = AgentState(
                agent_id=config.agent_id,
                status=AgentStatus.CREATED,
            )

            instance = AgentInstance(
                config=config,
                state=state,
            )

            self._agents[config.agent_id] = instance

            # 根据 Agent 类型创建引擎
            if config.agent_type in (AgentType.REACT, AgentType.REACTIVE):
                react_config = ReActConfig.from_agent_config(config)
                self._react_engines[config.agent_id] = ReActEngine(
                    llm_provider=self._llm,
                    tool_registry=self._tools,
                    config=react_config,
                )
            elif config.agent_type == AgentType.PLAN_EXECUTE:
                plan_config = PlanConfig.from_agent_config(config)
                self._plan_engines[config.agent_id] = PlanEngine(
                    llm_provider=self._llm,
                    tool_registry=self._tools,
                    config=plan_config,
                )

        self._emit_event(AgentEvent(
            event_type="agent_created",
            agent_id=config.agent_id,
            data={"name": config.name, "type": config.agent_type.value},
        ))

        # 自动启动
        if auto_start:
            self.start_agent(config.agent_id)

        return instance

    def get_agent(self, agent_id: str) -> AgentInstance | None:
        """获取 Agent 实例"""
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentInstance]:
        """列出所有 Agent"""
        with self._lock:
            return list(self._agents.values())

    def list_by_status(self, status: AgentStatus) -> list[AgentInstance]:
        """按状态列出 Agent"""
        with self._lock:
            return [a for a in self._agents.values() if a.status == status]

    def start_agent(self, agent_id: str) -> bool:
        """
        启动 Agent

        将 Agent 状态从 CREATED/STOPPED/PAUSED 转换为 IDLE。
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return False

            if instance.status not in (
                AgentStatus.CREATED,
                AgentStatus.STOPPED,
                AgentStatus.PAUSED,
            ):
                return False

            new_state = instance.state.with_status(AgentStatus.IDLE)
            self._agents[agent_id] = instance.with_state(new_state)

        self._emit_event(AgentEvent(
            event_type="agent_started",
            agent_id=agent_id,
        ))

        return True

    def stop_agent(self, agent_id: str) -> bool:
        """
        停止 Agent

        将 Agent 状态转换为 STOPPED。
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return False

            if instance.status in (AgentStatus.STOPPED, AgentStatus.TERMINATED):
                return False

            new_state = instance.state.with_status(AgentStatus.STOPPED)
            self._agents[agent_id] = instance.with_state(new_state)

        self._emit_event(AgentEvent(
            event_type="agent_stopped",
            agent_id=agent_id,
        ))

        return True

    def pause_agent(self, agent_id: str) -> bool:
        """
        暂停 Agent

        将 Agent 状态从 RUNNING/IDLE 转换为 PAUSED。
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return False

            if instance.status not in (AgentStatus.RUNNING, AgentStatus.IDLE):
                return False

            new_state = instance.state.with_status(AgentStatus.PAUSED)
            self._agents[agent_id] = instance.with_state(new_state)

        self._emit_event(AgentEvent(
            event_type="agent_paused",
            agent_id=agent_id,
        ))

        return True

    def resume_agent(self, agent_id: str) -> bool:
        """
        恢复 Agent

        将 Agent 状态从 PAUSED 转换为 IDLE。
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return False

            if instance.status != AgentStatus.PAUSED:
                return False

            new_state = instance.state.with_status(AgentStatus.IDLE)
            self._agents[agent_id] = instance.with_state(new_state)

        self._emit_event(AgentEvent(
            event_type="agent_resumed",
            agent_id=agent_id,
        ))

        return True

    def terminate_agent(self, agent_id: str) -> bool:
        """
        终止 Agent

        将 Agent 状态转换为 TERMINATED，不可恢复。
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return False

            if instance.status == AgentStatus.TERMINATED:
                return False

            new_state = instance.state.with_status(AgentStatus.TERMINATED)
            self._agents[agent_id] = instance.with_state(new_state)

            # 清理引擎
            self._react_engines.pop(agent_id, None)
            self._plan_engines.pop(agent_id, None)

        self._emit_event(AgentEvent(
            event_type="agent_terminated",
            agent_id=agent_id,
        ))

        return True

    def remove_agent(self, agent_id: str) -> bool:
        """
        移除 Agent

        从管理器中完全移除 Agent。
        """
        with self._lock:
            if agent_id not in self._agents:
                return False

            del self._agents[agent_id]
            self._react_engines.pop(agent_id, None)
            self._plan_engines.pop(agent_id, None)

        self._emit_event(AgentEvent(
            event_type="agent_removed",
            agent_id=agent_id,
        ))

        return True

    def execute_task(
        self,
        agent_id: str,
        task: str,
        **kwargs: Any,
    ) -> ReActResult | PlanResult:
        """
        执行任务

        根据 Agent 类型选择合适的引擎执行任务。

        Args:
            agent_id: Agent ID
            task: 任务描述
            **kwargs: 额外参数

        Returns:
            ReActResult | PlanResult: 执行结果
        """
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                raise ValueError(f"Agent 不存在: {agent_id}")

            if instance.status not in (AgentStatus.IDLE, AgentStatus.RUNNING):
                raise ValueError(f"Agent 状态不允许执行任务: {instance.status.value}")

            # 更新状态为运行中
            running_state = instance.state.with_status(AgentStatus.RUNNING)
            self._agents[agent_id] = instance.with_state(running_state)

        self._emit_event(AgentEvent(
            event_type="task_started",
            agent_id=agent_id,
            data={"task": task},
        ))

        start_time = time.time()

        try:
            # 根据 Agent 类型选择引擎
            if instance.config.agent_type in (AgentType.REACT, AgentType.REACTIVE):
                engine = self._react_engines.get(agent_id)
                if engine is None:
                    raise ValueError(f"ReAct 引擎未初始化: {agent_id}")
                result = engine.run(
                    task=task,
                    agent_config=instance.config,
                    **kwargs,
                )
            elif instance.config.agent_type == AgentType.PLAN_EXECUTE:
                engine = self._plan_engines.get(agent_id)
                if engine is None:
                    raise ValueError(f"Plan 引擎未初始化: {agent_id}")
                result = engine.run(
                    task=task,
                    agent_config=instance.config,
                    **kwargs,
                )
            else:
                raise ValueError(f"不支持的 Agent 类型: {instance.config.agent_type.value}")

            # 更新状态为空闲
            with self._lock:
                current = self._agents.get(agent_id)
                if current:
                    idle_state = current.state.with_status(AgentStatus.IDLE)
                    self._agents[agent_id] = current.with_state(idle_state)

            self._emit_event(AgentEvent(
                event_type="task_completed",
                agent_id=agent_id,
                data={
                    "task": task,
                    "status": result.status,
                    "execution_time": time.time() - start_time,
                },
            ))

            return result

        except Exception as e:
            # 更新状态为错误
            with self._lock:
                current = self._agents.get(agent_id)
                if current:
                    error_state = current.state.with_status(AgentStatus.ERROR)
                    self._agents[agent_id] = current.with_state(error_state)

            self._emit_event(AgentEvent(
                event_type="task_failed",
                agent_id=agent_id,
                data={"task": task, "error": str(e)},
            ))

            raise

    def get_agent_stats(self, agent_id: str) -> dict[str, Any] | None:
        """获取 Agent 统计信息"""
        with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                return None

            state = instance.state
            return {
                "agent_id": agent_id,
                "name": instance.name,
                "type": instance.config.agent_type.value,
                "status": state.status.value,
                "iteration_count": state.iteration_count,
                "tool_call_count": state.tool_call_count,
                "message_count": len(state.messages),
                "action_count": len(state.action_history),
                "created_at": instance.created_at,
                "started_at": state.started_at,
                "last_activity": state.last_activity,
            }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有 Agent 的统计信息"""
        with self._lock:
            stats: dict[str, dict[str, Any]] = {}
            for agent_id in self._agents:
                stats[agent_id] = self.get_agent_stats(agent_id)  # type: ignore
            return stats

    def cleanup_terminated(self) -> int:
        """清理已终止的 Agent"""
        with self._lock:
            terminated = [
                agent_id for agent_id, instance in self._agents.items()
                if instance.status == AgentStatus.TERMINATED
            ]
            for agent_id in terminated:
                del self._agents[agent_id]
                self._react_engines.pop(agent_id, None)
                self._plan_engines.pop(agent_id, None)

        for agent_id in terminated:
            self._emit_event(AgentEvent(
                event_type="agent_cleaned",
                agent_id=agent_id,
            ))

        return len(terminated)
