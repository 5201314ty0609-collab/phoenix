"""
ReAct 引擎 — 推理 + 行动循环

ReAct (Reasoning + Acting) 是一种 Agent 执行模式：
1. Thought: Agent 推理当前状态和下一步行动
2. Action: Agent 选择并执行一个工具
3. Observation: Agent 观察工具执行结果
4. 重复直到任务完成或达到最大迭代次数

Reference:
    - Yao et al., 2022: "ReAct: Synergizing Reasoning and Acting in Language Models"
    - arXiv:2210.03629

Design:
    ┌─────────────────────────────────────────────────────────┐
    │                    ReAct Engine                          │
    │                                                          │
    │  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
    │  │  Thought │───▶│  Action  │───▶│  Observation     │  │
    │  │ (推理)   │    │ (执行)   │    │ (观察结果)        │  │
    │  └──────────┘    └──────────┘    └──────────────────┘  │
    │       ▲                                    │            │
    │       └────────────────────────────────────┘            │
    │                    (循环直到完成)                         │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .agent_types import (
    AgentConfig,
    AgentMessage,
    AgentState,
    AgentStatus,
    AgentEvent,
    LLMProvider,
    MessageRole,
    ToolCall,
    ToolDefinition,
    ToolResult,
    ToolStatus,
    ActionResult,
)
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class ReActConfig:
    """ReAct 引擎配置"""

    max_iterations: int = 10
    max_tool_calls: int = 20
    timeout: float = 300.0
    temperature: float = 0.7
    max_tokens: int = 4096
    stop_on_final_answer: bool = True
    include_thought_in_response: bool = False
    verbose: bool = False

    @classmethod
    def from_agent_config(cls, config: AgentConfig) -> ReActConfig:
        """从 Agent 配置创建"""
        return ReActConfig(
            max_iterations=config.max_iterations,
            max_tool_calls=config.max_tool_calls,
            timeout=config.timeout,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


@dataclass(frozen=True)
class ReActStep:
    """
    ReAct 单步执行记录

    记录一次 Thought → Action → Observation 的完整循环。
    """

    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    iteration: int = 0
    thought: str = ""
    action: ToolCall | None = None
    observation: ToolResult | None = None
    is_final: bool = False
    final_answer: str = ""
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0

    @property
    def has_action(self) -> bool:
        return self.action is not None

    @property
    def is_success(self) -> bool:
        if self.observation is None:
            return not self.has_action  # 无动作时视为成功
        return self.observation.is_success


@dataclass(frozen=True)
class ReActResult:
    """
    ReAct 执行结果

    包含完整的执行历史和最终答案。
    """

    agent_id: str
    task: str
    final_answer: str
    steps: tuple[ReActStep, ...] = ()
    total_iterations: int = 0
    total_tool_calls: int = 0
    total_execution_time: float = 0.0
    status: str = "completed"  # completed, failed, timeout, max_iterations
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "completed" and self.error is None

    @property
    def thoughts(self) -> list[str]:
        """获取所有推理过程"""
        return [step.thought for step in self.steps if step.thought]

    @property
    def actions(self) -> list[ToolCall]:
        """获取所有执行的动作"""
        return [step.action for step in self.steps if step.action is not None]

    @property
    def observations(self) -> list[ToolResult]:
        """获取所有观察结果"""
        return [step.observation for step in self.steps if step.observation is not None]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "final_answer": self.final_answer,
            "total_iterations": self.total_iterations,
            "total_tool_calls": self.total_tool_calls,
            "total_execution_time": self.total_execution_time,
            "status": self.status,
            "error": self.error,
            "steps": [
                {
                    "iteration": step.iteration,
                    "thought": step.thought,
                    "action": step.action.name if step.action else None,
                    "observation": step.observation.output if step.observation else None,
                    "is_final": step.is_final,
                }
                for step in self.steps
            ],
        }


class ReActEngine:
    """
    ReAct 执行引擎

    实现 Thought → Action → Observation 循环。
    与 LLM 交互，决定何时调用工具、何时返回最终答案。
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        config: ReActConfig | None = None,
    ) -> None:
        self._llm = llm_provider
        self._tools = tool_registry
        self._config = config or ReActConfig()
        self._events: list[AgentEvent] = []

    @property
    def config(self) -> ReActConfig:
        return self._config

    @property
    def events(self) -> list[AgentEvent]:
        return list(self._events)

    def _emit_event(self, event_type: str, agent_id: str, data: dict[str, Any] | None = None) -> None:
        """发送事件"""
        event = AgentEvent(
            event_type=event_type,
            agent_id=agent_id,
            data=data or {},
        )
        self._events.append(event)

    def _build_system_prompt(self, agent_config: AgentConfig) -> str:
        """构建系统提示"""
        base_prompt = agent_config.system_prompt or "你是一个有用的 AI 助手。"

        tool_descriptions = []
        for tool_def in self._tools.list_tools():
            tool_descriptions.append(
                f"- {tool_def.name}: {tool_def.description}"
            )

        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "无可用工具"

        return f"""{base_prompt}

你可以使用以下工具：
{tools_text}

请按以下格式思考和行动：

Thought: [你的推理过程]
Action: [工具名称]
Action Input: [工具参数，JSON 格式]

当你得到足够信息后，给出最终答案：

Thought: [总结推理过程]
Final Answer: [最终答案]

重要规则：
1. 每次只能执行一个动作
2. 动作输入必须是有效的 JSON
3. 如果不需要使用工具，直接给出 Final Answer
4. 仔细观察工具返回的结果，根据结果决定下一步
"""

    def _parse_llm_response(self, response: AgentMessage) -> tuple[str, ToolCall | None, bool, str]:
        """
        解析 LLM 响应

        返回: (thought, action, is_final, final_answer)
        """
        content = response.content

        thought = ""
        action = None
        is_final = False
        final_answer = ""

        # 提取 Thought
        if "Thought:" in content:
            thought_start = content.index("Thought:") + len("Thought:")
            thought_end = len(content)
            for marker in ["Action:", "Final Answer:"]:
                if marker in content[thought_start:]:
                    marker_pos = content.index(marker, thought_start)
                    thought_end = min(thought_end, marker_pos)
            thought = content[thought_start:thought_end].strip()

        # 检查是否有 Final Answer
        if "Final Answer:" in content:
            is_final = True
            final_start = content.index("Final Answer:") + len("Final Answer:")
            final_answer = content[final_start:].strip()
            return thought, None, is_final, final_answer

        # 提取 Action
        if "Action:" in content:
            action_start = content.index("Action:") + len("Action:")
            action_end = len(content)
            for marker in ["Action Input:", "Thought:", "Final Answer:"]:
                if marker in content[action_start:]:
                    marker_pos = content.index(marker, action_start)
                    action_end = min(action_end, marker_pos)
            action_name = content[action_start:action_end].strip()

            # 提取 Action Input
            arguments: dict[str, Any] = {}
            if "Action Input:" in content:
                input_start = content.index("Action Input:") + len("Action Input:")
                input_text = content[input_start:].strip()
                # 尝试解析 JSON
                try:
                    import json
                    # 找到 JSON 对象的开始和结束
                    json_start = input_text.find("{")
                    json_end = input_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        arguments = json.loads(input_text[json_start:json_end])
                except (json.JSONDecodeError, ValueError):
                    # 如果无法解析 JSON，将整个文本作为单个参数
                    arguments = {"input": input_text}

            action = ToolCall(
                name=action_name,
                arguments=arguments,
            )

        # 如果没有明确的 Thought/Final Answer 标记，将整个内容视为最终答案
        if not thought and not action and not is_final:
            is_final = True
            final_answer = content

        return thought, action, is_final, final_answer

    def _execute_action(self, action: ToolCall) -> ToolResult:
        """执行工具动作"""
        return self._tools.execute_tool_call(action)

    def run(
        self,
        task: str,
        agent_config: AgentConfig,
        initial_messages: list[AgentMessage] | None = None,
        on_step: Callable[[ReActStep], None] | None = None,
    ) -> ReActResult:
        """
        执行 ReAct 循环

        Args:
            task: 要执行的任务描述
            agent_config: Agent 配置
            initial_messages: 初始消息列表（可选）
            on_step: 每步回调函数（可选）

        Returns:
            ReActResult: 执行结果
        """
        start_time = time.time()
        agent_id = agent_config.agent_id

        self._emit_event("react_start", agent_id, {"task": task})

        # 初始化消息列表
        messages: list[AgentMessage] = []
        if initial_messages:
            messages.extend(initial_messages)

        # 添加系统提示
        system_prompt = self._build_system_prompt(agent_config)
        messages.append(AgentMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt,
        ))

        # 添加用户任务
        messages.append(AgentMessage(
            role=MessageRole.USER,
            content=task,
        ))

        # ReAct 循环
        steps: list[ReActStep] = []
        total_tool_calls = 0
        final_answer = ""
        status = "completed"
        error: str | None = None

        for iteration in range(self._config.max_iterations):
            # 检查超时
            if time.time() - start_time > self._config.timeout:
                status = "timeout"
                error = f"执行超时 ({self._config.timeout}s)"
                break

            # 检查工具调用次数限制
            if total_tool_calls >= self._config.max_tool_calls:
                status = "max_tool_calls"
                error = f"达到最大工具调用次数 ({self._config.max_tool_calls})"
                break

            self._emit_event("react_iteration", agent_id, {"iteration": iteration})

            # 调用 LLM
            try:
                response = self._llm.generate(
                    messages=messages,
                    tools=self._tools.to_json_schema() if self._tools.list_tools() else None,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                )
            except Exception as e:
                status = "llm_error"
                error = f"LLM 调用失败: {type(e).__name__}: {str(e)}"
                break

            # 解析响应
            thought, action, is_final, answer = self._parse_llm_response(response)

            # 创建步骤记录
            step = ReActStep(
                iteration=iteration,
                thought=thought,
                action=action,
                is_final=is_final,
                final_answer=answer,
            )

            if is_final:
                final_answer = answer
                steps.append(step)
                self._emit_event("react_final", agent_id, {"answer": answer})
                if on_step:
                    on_step(step)
                break

            # 执行动作
            if action:
                observation = self._execute_action(action)
                total_tool_calls += 1

                step = ReActStep(
                    iteration=iteration,
                    thought=thought,
                    action=action,
                    observation=observation,
                    is_final=False,
                    execution_time=observation.execution_time,
                )
                steps.append(step)

                self._emit_event("react_action", agent_id, {
                    "action": action.name,
                    "success": observation.is_success,
                })

                if on_step:
                    on_step(step)

                # 将 LLM 响应和工具结果添加到消息历史
                messages.append(response)
                messages.append(AgentMessage(
                    role=MessageRole.TOOL,
                    content=str(observation.output) if observation.is_success else f"错误: {observation.error}",
                    tool_call_id=action.id,
                    name=action.name,
                ))
            else:
                # 没有动作也没有最终答案，视为完成
                final_answer = thought or answer
                steps.append(step)
                if on_step:
                    on_step(step)
                break
        else:
            # 达到最大迭代次数
            status = "max_iterations"
            error = f"达到最大迭代次数 ({self._config.max_iterations})"

        total_time = time.time() - start_time

        result = ReActResult(
            agent_id=agent_id,
            task=task,
            final_answer=final_answer,
            steps=tuple(steps),
            total_iterations=len(steps),
            total_tool_calls=total_tool_calls,
            total_execution_time=total_time,
            status=status,
            error=error,
        )

        self._emit_event("react_complete", agent_id, {
            "status": status,
            "iterations": len(steps),
            "tool_calls": total_tool_calls,
        })

        return result

    def run_streaming(
        self,
        task: str,
        agent_config: AgentConfig,
        on_thought: Callable[[str], None] | None = None,
        on_action: Callable[[ToolCall], None] | None = None,
        on_observation: Callable[[ToolResult], None] | None = None,
        on_final: Callable[[str], None] | None = None,
    ) -> ReActResult:
        """
        流式执行 ReAct 循环

        通过回调函数实时通知执行进度。
        """
        def step_callback(step: ReActStep) -> None:
            if step.thought and on_thought:
                on_thought(step.thought)
            if step.action and on_action:
                on_action(step.action)
            if step.observation and on_observation:
                on_observation(step.observation)
            if step.is_final and on_final:
                on_final(step.final_answer)

        return self.run(
            task=task,
            agent_config=agent_config,
            on_step=step_callback,
        )
