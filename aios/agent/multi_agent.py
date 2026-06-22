"""
多 Agent 协作协调器

支持多种协作模式：
1. 委托模式 (Delegation): 主 Agent 将子任务委托给专业 Agent
2. 协作模式 (Collaboration): 多个 Agent 共同完成任务
3. 辩论模式 (Debate): 多个 Agent 提出观点，达成共识
4. 流水线模式 (Pipeline): Agent 按顺序处理任务

Design:
    ┌─────────────────────────────────────────────────────────────┐
    │               Multi-Agent Coordinator                        │
    │                                                              │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
    │  │Delegate  │  │Collaborate│  │  Debate  │  │  Pipeline  │ │
    │  │  Mode    │  │  Mode    │  │  Mode    │  │   Mode     │ │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
    │       │             │             │               │         │
    │  ┌────┴─────────────┴─────────────┴───────────────┴──────┐  │
    │  │                  Agent Team                            │  │
    │  │  (管理多个 Agent 实例和它们的协作关系)                 │  │
    │  └───────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

from .agent_types import (
    AgentConfig,
    AgentEvent,
    AgentMessage,
    AgentStatus,
    AgentType,
    LLMProvider,
    MessageRole,
)
from .agent_manager import AgentManager, AgentInstance
from .react_engine import ReActResult
from .plan_engine import PlanResult


class CollaborationProtocol(Enum):
    """协作协议"""

    DELEGATION = "delegation"       # 委托：主 Agent 分配任务
    COLLABORATION = "collaboration"  # 协作：共同完成任务
    DEBATE = "debate"               # 辩论：多观点讨论
    PIPELINE = "pipeline"           # 流水线：顺序处理
    VOTING = "voting"               # 投票：多数决定


@dataclass(frozen=True)
class DelegationResult:
    """
    委托执行结果

    包含主任务结果和所有子任务结果。
    """

    main_task: str
    main_result: str
    sub_results: tuple[tuple[str, str, str], ...] = ()  # (agent_id, task, result)
    total_agents: int = 0
    total_execution_time: float = 0.0
    status: str = "completed"
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == "completed" and self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "main_task": self.main_task,
            "main_result": self.main_result,
            "sub_results": [
                {"agent_id": aid, "task": task, "result": result}
                for aid, task, result in self.sub_results
            ],
            "total_agents": self.total_agents,
            "total_execution_time": self.total_execution_time,
            "status": self.status,
            "error": self.error,
        }


@dataclass(frozen=True)
class AgentTeam:
    """
    Agent 团队

    定义一组可以协作的 Agent。
    """

    team_id: str = field(default_factory=lambda: f"team_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    agent_ids: tuple[str, ...] = ()
    protocol: CollaborationProtocol = CollaborationProtocol.DELEGATION
    coordinator_id: str | None = None  # 协调者 Agent ID
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_agents(self, *agent_ids: str) -> AgentTeam:
        """返回包含新 Agent 的新团队"""
        return AgentTeam(
            team_id=self.team_id,
            name=self.name,
            description=self.description,
            agent_ids=tuple(set(self.agent_ids + agent_ids)),
            protocol=self.protocol,
            coordinator_id=self.coordinator_id,
            metadata=self.metadata,
        )


class MultiAgentCoordinator:
    """
    多 Agent 协作协调器

    管理 Agent 团队和协作协议。
    """

    def __init__(
        self,
        agent_manager: AgentManager,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._manager = agent_manager
        self._llm = llm_provider or agent_manager.llm_provider
        self._teams: dict[str, AgentTeam] = {}
        self._event_handlers: list[Callable[[AgentEvent], None]] = []
        self._lock = threading.RLock()

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
                pass

    def create_team(
        self,
        name: str,
        agent_ids: tuple[str, ...] = (),
        protocol: CollaborationProtocol = CollaborationProtocol.DELEGATION,
        coordinator_id: str | None = None,
        description: str = "",
    ) -> AgentTeam:
        """创建 Agent 团队"""
        team = AgentTeam(
            name=name,
            description=description,
            agent_ids=agent_ids,
            protocol=protocol,
            coordinator_id=coordinator_id,
        )

        with self._lock:
            self._teams[team.team_id] = team

        self._emit_event(AgentEvent(
            event_type="team_created",
            agent_id=coordinator_id or "system",
            data={"team_id": team.team_id, "name": name},
        ))

        return team

    def get_team(self, team_id: str) -> AgentTeam | None:
        """获取团队"""
        with self._lock:
            return self._teams.get(team_id)

    def list_teams(self) -> list[AgentTeam]:
        """列出所有团队"""
        with self._lock:
            return list(self._teams.values())

    def add_to_team(self, team_id: str, agent_id: str) -> bool:
        """将 Agent 添加到团队"""
        with self._lock:
            team = self._teams.get(team_id)
            if team is None:
                return False

            if agent_id not in team.agent_ids:
                self._teams[team_id] = team.with_agents(agent_id)

        return True

    def delegate_task(
        self,
        team_id: str,
        task: str,
        sub_tasks: list[tuple[str, str]] | None = None,
        on_sub_task_complete: Callable[[str, str, str], None] | None = None,
    ) -> DelegationResult:
        """
        委托任务

        将任务分解为子任务，分配给团队中的 Agent。

        Args:
            team_id: 团队 ID
            task: 主任务描述
            sub_tasks: 子任务列表 [(agent_id, sub_task), ...]，如果为 None 则自动分解
            on_sub_task_complete: 子任务完成回调 (agent_id, task, result)

        Returns:
            DelegationResult: 执行结果
        """
        start_time = time.time()

        with self._lock:
            team = self._teams.get(team_id)
            if team is None:
                return DelegationResult(
                    main_task=task,
                    main_result="",
                    status="failed",
                    error=f"团队不存在: {team_id}",
                )

        self._emit_event(AgentEvent(
            event_type="delegation_start",
            agent_id=team.coordinator_id or "system",
            data={"team_id": team_id, "task": task},
        ))

        # 如果没有指定子任务，自动分解
        if sub_tasks is None:
            sub_tasks = self._auto_decompose(task, team)

        # 执行子任务
        sub_results: list[tuple[str, str, str]] = []

        for agent_id, sub_task in sub_tasks:
            # 检查 Agent 是否在团队中
            if agent_id not in team.agent_ids:
                sub_results.append((agent_id, sub_task, f"错误: Agent {agent_id} 不在团队中"))
                continue

            # 启动 Agent（如果需要）
            agent = self._manager.get_agent(agent_id)
            if agent is None:
                sub_results.append((agent_id, sub_task, f"错误: Agent {agent_id} 不存在"))
                continue

            if agent.status in (AgentStatus.CREATED, AgentStatus.STOPPED):
                self._manager.start_agent(agent_id)

            try:
                # 执行任务
                result = self._manager.execute_task(agent_id, sub_task)

                if isinstance(result, ReActResult):
                    result_text = result.final_answer
                elif isinstance(result, PlanResult):
                    result_text = result.final_result
                else:
                    result_text = str(result)

                sub_results.append((agent_id, sub_task, result_text))

                if on_sub_task_complete:
                    on_sub_task_complete(agent_id, sub_task, result_text)

            except Exception as e:
                sub_results.append((agent_id, sub_task, f"执行失败: {str(e)}"))

        # 汇总结果
        main_result = self._aggregate_results(task, sub_results)

        total_time = time.time() - start_time

        result = DelegationResult(
            main_task=task,
            main_result=main_result,
            sub_results=tuple(sub_results),
            total_agents=len(sub_tasks),
            total_execution_time=total_time,
            status="completed",
        )

        self._emit_event(AgentEvent(
            event_type="delegation_complete",
            agent_id=team.coordinator_id or "system",
            data={"team_id": team_id, "status": "completed"},
        ))

        return result

    def _auto_decompose(self, task: str, team: AgentTeam) -> list[tuple[str, str]]:
        """
        自动分解任务

        使用 LLM 将任务分解为适合各个 Agent 的子任务。
        """
        if not self._llm:
            # 如果没有 LLM，简单地将任务分配给第一个 Agent
            if team.agent_ids:
                return [(team.agent_ids[0], task)]
            return []

        # 获取每个 Agent 的信息
        agent_descriptions = []
        for agent_id in team.agent_ids:
            agent = self._manager.get_agent(agent_id)
            if agent:
                agent_descriptions.append(
                    f"- {agent_id} ({agent.name}): {agent.config.description or agent.config.agent_type.value}"
                )

        agents_text = "\n".join(agent_descriptions) if agent_descriptions else "无可用 Agent"

        prompt = f"""请将以下任务分解为适合各个 Agent 的子任务。

任务：{task}

可用 Agent：
{agents_text}

请按以下 JSON 格式输出：
```json
{{
  "sub_tasks": [
    {{
      "agent_id": "Agent ID",
      "task": "子任务描述"
    }}
  ]
}}
```

规则：
1. 每个子任务应该分配给最合适的 Agent
2. 子任务应该清晰、可独立执行
3. 所有子任务的结果应该能够组合成最终答案
"""

        try:
            from .agent_types import AgentMessage, MessageRole
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=0.7,
                max_tokens=2048,
            )

            # 解析响应
            import json
            content = response.content
            json_start = content.find("```json")
            json_end = content.find("```", json_start + 7)
            if json_start >= 0 and json_end > json_start:
                json_text = content[json_start + 7:json_end].strip()
            else:
                json_text = content

            data = json.loads(json_text)
            sub_tasks_data = data.get("sub_tasks", [])

            return [
                (item["agent_id"], item["task"])
                for item in sub_tasks_data
                if "agent_id" in item and "task" in item
            ]

        except Exception:
            # 解析失败，简单分配
            if team.agent_ids:
                return [(team.agent_ids[0], task)]
            return []

    def _aggregate_results(
        self,
        main_task: str,
        sub_results: list[tuple[str, str, str]],
    ) -> str:
        """
        汇总子任务结果

        使用 LLM 将多个子任务结果组合成最终答案。
        """
        if not self._llm:
            # 如果没有 LLM，简单拼接结果
            results_text = "\n\n".join(
                f"## Agent {agent_id} 的结果\n\n{result}"
                for agent_id, _, result in sub_results
            )
            return f"任务: {main_task}\n\n{results_text}"

        results_text = "\n\n".join(
            f"Agent {agent_id} ({task}):\n{result}"
            for agent_id, task, result in sub_results
        )

        prompt = f"""请根据以下各个 Agent 的执行结果，生成最终的任务完成报告。

原始任务：{main_task}

各 Agent 的执行结果：
{results_text}

请生成一个清晰、完整的最终结果，综合所有 Agent 的贡献。"""

        try:
            from .agent_types import AgentMessage, MessageRole
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.content
        except Exception:
            # LLM 调用失败，简单拼接
            results_text = "\n\n".join(
                f"## Agent {agent_id} 的结果\n\n{result}"
                for agent_id, _, result in sub_results
            )
            return f"任务: {main_task}\n\n{results_text}"

    def debate(
        self,
        team_id: str,
        topic: str,
        max_rounds: int = 3,
        on_round_complete: Callable[[int, list[tuple[str, str]]], None] | None = None,
    ) -> tuple[str, list[tuple[str, str, str]]]:
        """
        辩论模式

        多个 Agent 就一个话题进行讨论，达成共识。

        Args:
            team_id: 团队 ID
            topic: 辩论话题
            max_rounds: 最大讨论轮数
            on_round_complete: 每轮完成回调

        Returns:
            (consensus, [(agent_id, round, opinion)])
        """
        with self._lock:
            team = self._teams.get(team_id)
            if team is None:
                return "团队不存在", []

        opinions: list[tuple[str, str, str]] = []  # (agent_id, round, opinion)

        for round_num in range(max_rounds):
            round_opinions: list[tuple[str, str]] = []

            for agent_id in team.agent_ids:
                agent = self._manager.get_agent(agent_id)
                if agent is None:
                    continue

                # 构建提示
                previous_opinions = "\n".join(
                    f"- {aid}: {op}"
                    for aid, _, op in opinions
                )

                prompt = f"""请就以下话题发表你的观点。

话题：{topic}

{"之前的讨论：" + chr(10) + previous_opinions if previous_opinions else "这是第一轮讨论。"}

请清晰地表达你的观点和理由。"""

                try:
                    result = self._manager.execute_task(agent_id, prompt)
                    if isinstance(result, ReActResult):
                        opinion = result.final_answer
                    elif isinstance(result, PlanResult):
                        opinion = result.final_result
                    else:
                        opinion = str(result)

                    opinions.append((agent_id, f"round_{round_num}", opinion))
                    round_opinions.append((agent_id, opinion))

                except Exception as e:
                    opinions.append((agent_id, f"round_{round_num}", f"表达观点失败: {str(e)}"))

            if on_round_complete:
                on_round_complete(round_num, round_opinions)

        # 生成共识
        consensus = self._generate_consensus(topic, opinions)

        return consensus, opinions

    def _generate_consensus(
        self,
        topic: str,
        opinions: list[tuple[str, str, str]],
    ) -> str:
        """生成共识"""
        if not self._llm:
            return "\n\n".join(
                f"{aid}: {op}" for aid, _, op in opinions
            )

        opinions_text = "\n\n".join(
            f"Agent {aid} ({round_}):\n{op}"
            for aid, round_, op in opinions
        )

        prompt = f"""请根据以下讨论，生成一个综合的共识。

话题：{topic}

各方观点：
{opinions_text}

请生成一个平衡、全面的共识，综合各方的观点和理由。"""

        try:
            from .agent_types import AgentMessage, MessageRole
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.content
        except Exception:
            return f"共识生成失败。以下是各方观点：\n\n{opinions_text}"

    def pipeline(
        self,
        team_id: str,
        task: str,
        on_stage_complete: Callable[[str, str, str], None] | None = None,
    ) -> tuple[str, list[tuple[str, str, str]]]:
        """
        流水线模式

        Agent 按顺序处理任务，每个 Agent 的输出作为下一个 Agent 的输入。

        Args:
            team_id: 团队 ID
            task: 初始任务
            on_stage_complete: 阶段完成回调 (agent_id, input, output)

        Returns:
            (final_result, [(agent_id, input, output)])
        """
        with self._lock:
            team = self._teams.get(team_id)
            if team is None:
                return "团队不存在", []

        stages: list[tuple[str, str, str]] = []  # (agent_id, input, output)
        current_input = task

        for agent_id in team.agent_ids:
            agent = self._manager.get_agent(agent_id)
            if agent is None:
                stages.append((agent_id, current_input, f"错误: Agent {agent_id} 不存在"))
                continue

            try:
                result = self._manager.execute_task(agent_id, current_input)

                if isinstance(result, ReActResult):
                    output = result.final_answer
                elif isinstance(result, PlanResult):
                    output = result.final_result
                else:
                    output = str(result)

                stages.append((agent_id, current_input, output))
                current_input = output  # 输出作为下一个 Agent 的输入

                if on_stage_complete:
                    on_stage_complete(agent_id, current_input, output)

            except Exception as e:
                stages.append((agent_id, current_input, f"执行失败: {str(e)}"))
                break

        final_result = stages[-1][2] if stages else "无结果"

        return final_result, stages
