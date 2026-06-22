"""
Agent 核心类型定义

不可变数据结构，遵循 PHOENIX 不可变性原则。
所有类型都是 frozen dataclass，修改必须创建新实例。

核心概念：
- Agent: 自主执行实体，拥有配置、状态和执行历史
- Message: Agent 间通信的基本单元
- Tool: Agent 可调用的外部能力
- Plan: 多步骤任务的执行计划
- Action: Agent 执行的单个动作
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Generic, Protocol, TypeVar

T = TypeVar("T")


# ── 枚举定义 ─────────────────────────────────────────────────────────────

class AgentStatus(Enum):
    """Agent 生命周期状态"""

    CREATED = "created"       # 已创建，未启动
    IDLE = "idle"             # 空闲，等待任务
    RUNNING = "running"       # 正在执行任务
    PAUSED = "paused"         # 已暂停
    ERROR = "error"           # 出错状态
    STOPPED = "stopped"       # 已停止
    TERMINATED = "terminated"  # 已终止


class AgentType(Enum):
    """Agent 类型"""

    REACTIVE = "reactive"         # 反应式：直接响应输入
    REACT = "react"               # ReAct：推理 + 行动循环
    PLAN_EXECUTE = "plan_execute"  # 规划执行：先规划后执行
    COORDINATOR = "coordinator"   # 协调者：管理其他 Agent
    SPECIALIST = "specialist"     # 专家：专注特定领域


class MessageRole(Enum):
    """消息角色"""

    SYSTEM = "system"      # 系统提示
    USER = "user"          # 用户输入
    ASSISTANT = "assistant"  # Agent 输出
    TOOL = "tool"          # 工具结果
    AGENT = "agent"        # 其他 Agent 消息


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"       # 等待执行
    PLANNING = "planning"     # 规划中
    EXECUTING = "executing"   # 执行中
    PAUSED = "paused"         # 已暂停
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class ToolStatus(Enum):
    """工具执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ExecutionMode(Enum):
    """执行模式"""

    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行
    CONDITIONAL = "conditional"  # 条件执行


# ── 协议定义 ─────────────────────────────────────────────────────────────

class LLMProvider(Protocol):
    """LLM 提供者协议 — 定义与语言模型交互的接口"""

    def generate(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AgentMessage:
        """生成响应"""
        ...

    def generate_stream(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """流式生成响应"""
        ...


class ToolCallable(Protocol):
    """工具可调用协议"""

    def __call__(self, **kwargs: Any) -> Any:
        """执行工具"""
        ...


# ── 核心类型 ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ToolDefinition:
    """
    工具定义 — 描述 Agent 可调用的外部能力

    每个工具包含名称、描述、参数模式和执行函数。
    工具定义是不可变的，注册后不可修改。
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema 格式
    function: Callable[..., Any] | None = None
    category: str = "general"
    timeout: float = 30.0
    retry_count: int = 0
    required_permissions: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate_parameters(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """验证参数是否符合 schema"""
        errors: list[str] = []
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        # 检查必需参数
        for req in required:
            if req not in params:
                errors.append(f"缺少必需参数: {req}")

        # 检查参数类型
        for key, value in params.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"参数 {key} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"参数 {key} 应为整数类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"参数 {key} 应为数字类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"参数 {key} 应为布尔类型")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"参数 {key} 应为数组类型")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"参数 {key} 应为对象类型")

        return len(errors) == 0, errors


@dataclass(frozen=True)
class ToolResult:
    """
    工具执行结果

    不可变，包含执行状态、输出和元数据。
    """

    tool_name: str
    status: ToolStatus
    output: Any = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == ToolStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.status in (ToolStatus.FAILED, ToolStatus.TIMEOUT)


@dataclass(frozen=True)
class AgentMessage:
    """
    Agent 消息 — 通信的基本单元

    不可变，包含角色、内容和可选的工具调用信息。
    """

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_content(self, new_content: str) -> AgentMessage:
        """返回带有新内容的新实例"""
        return AgentMessage(
            role=self.role,
            content=new_content,
            name=self.name,
            tool_calls=self.tool_calls,
            tool_call_id=self.tool_call_id,
            timestamp=self.timestamp,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass(frozen=True)
class ToolCall:
    """
    工具调用请求

    Agent 决定调用工具时生成的请求。
    """

    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass(frozen=True)
class ActionResult:
    """
    动作执行结果

    单个动作的执行结果，包含状态和输出。
    """

    action_id: str
    tool_call: ToolCall
    result: ToolResult
    step_index: int = 0
    reasoning: str = ""

    @property
    def is_success(self) -> bool:
        return self.result.is_success


@dataclass(frozen=True)
class PlanStep:
    """
    执行计划步骤

    单个步骤的定义，包含描述、所需工具和依赖关系。
    """

    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    description: str = ""
    tool_name: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()  # 依赖的 step_id 列表
    status: TaskStatus = TaskStatus.PENDING
    result: ToolResult | None = None
    retry_count: int = 0
    max_retries: int = 3

    def with_status(self, new_status: TaskStatus) -> PlanStep:
        """返回带有新状态的新实例"""
        return PlanStep(
            step_id=self.step_id,
            description=self.description,
            tool_name=self.tool_name,
            parameters=self.parameters,
            dependencies=self.dependencies,
            status=new_status,
            result=self.result,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
        )

    def with_result(self, new_result: ToolResult) -> PlanStep:
        """返回带有新结果的新实例"""
        return PlanStep(
            step_id=self.step_id,
            description=self.description,
            tool_name=self.tool_name,
            parameters=self.parameters,
            dependencies=self.dependencies,
            status=TaskStatus.COMPLETED if new_result.is_success else TaskStatus.FAILED,
            result=new_result,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
        )


@dataclass(frozen=True)
class ExecutionPlan:
    """
    执行计划

    多步骤任务的完整执行计划。
    """

    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    goal: str = ""
    steps: tuple[PlanStep, ...] = ()
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == TaskStatus.FAILED)

    @property
    def progress(self) -> float:
        """进度百分比 (0.0 - 1.0)"""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    @property
    def is_complete(self) -> bool:
        return all(s.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED) for s in self.steps)

    @property
    def has_failure(self) -> bool:
        return any(s.status == TaskStatus.FAILED for s in self.steps)

    def get_step(self, step_id: str) -> PlanStep | None:
        """根据 ID 获取步骤"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> list[PlanStep]:
        """获取可以执行的步骤（依赖已完成）"""
        completed_ids = {s.step_id for s in self.steps if s.status == TaskStatus.COMPLETED}
        ready: list[PlanStep] = []
        for step in self.steps:
            if step.status != TaskStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in step.dependencies):
                ready.append(step)
        return ready

    def update_step(self, step_id: str, updated_step: PlanStep) -> ExecutionPlan:
        """返回包含更新步骤的新计划"""
        new_steps = tuple(
            updated_step if s.step_id == step_id else s
            for s in self.steps
        )
        return ExecutionPlan(
            plan_id=self.plan_id,
            goal=self.goal,
            steps=new_steps,
            created_at=self.created_at,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class AgentConfig:
    """
    Agent 配置

    定义 Agent 的行为参数和能力。
    """

    agent_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = "PhoenixAgent"
    agent_type: AgentType = AgentType.REACT
    description: str = ""
    system_prompt: str = ""
    model: str = "mimo-v2.5-pro"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_iterations: int = 10
    max_tool_calls: int = 20
    timeout: float = 300.0  # 5 分钟
    tools: tuple[str, ...] = ()  # 可用工具名称列表
    memory_enabled: bool = True
    planning_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_tools(self, *tool_names: str) -> AgentConfig:
        """返回带有新工具列表的新配置"""
        return AgentConfig(
            agent_id=self.agent_id,
            name=self.name,
            agent_type=self.agent_type,
            description=self.description,
            system_prompt=self.system_prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_iterations=self.max_iterations,
            max_tool_calls=self.max_tool_calls,
            timeout=self.timeout,
            tools=tuple(set(self.tools + tool_names)),
            memory_enabled=self.memory_enabled,
            planning_enabled=self.planning_enabled,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class AgentState:
    """
    Agent 运行时状态

    不可变，每次状态变更创建新实例。
    """

    agent_id: str
    status: AgentStatus = AgentStatus.CREATED
    current_task: str | None = None
    iteration_count: int = 0
    tool_call_count: int = 0
    messages: tuple[AgentMessage, ...] = ()
    action_history: tuple[ActionResult, ...] = ()
    current_plan: ExecutionPlan | None = None
    error: str | None = None
    started_at: float | None = None
    last_activity: float = field(default_factory=time.time)

    def with_status(self, new_status: AgentStatus) -> AgentState:
        """返回带有新状态的新实例"""
        return AgentState(
            agent_id=self.agent_id,
            status=new_status,
            current_task=self.current_task,
            iteration_count=self.iteration_count,
            tool_call_count=self.tool_call_count,
            messages=self.messages,
            action_history=self.action_history,
            current_plan=self.current_plan,
            error=self.error,
            started_at=self.started_at,
            last_activity=time.time(),
        )

    def add_message(self, message: AgentMessage) -> AgentState:
        """返回包含新消息的新状态"""
        return AgentState(
            agent_id=self.agent_id,
            status=self.status,
            current_task=self.current_task,
            iteration_count=self.iteration_count,
            tool_call_count=self.tool_call_count,
            messages=self.messages + (message,),
            action_history=self.action_history,
            current_plan=self.current_plan,
            error=self.error,
            started_at=self.started_at,
            last_activity=time.time(),
        )

    def add_action(self, action: ActionResult) -> AgentState:
        """返回包含新动作历史的新状态"""
        return AgentState(
            agent_id=self.agent_id,
            status=self.status,
            current_task=self.current_task,
            iteration_count=self.iteration_count,
            tool_call_count=self.tool_call_count + 1,
            messages=self.messages,
            action_history=self.action_history + (action,),
            current_plan=self.current_plan,
            error=self.error,
            started_at=self.started_at,
            last_activity=time.time(),
        )

    def increment_iteration(self) -> AgentState:
        """返回迭代次数 +1 的新状态"""
        return AgentState(
            agent_id=self.agent_id,
            status=self.status,
            current_task=self.current_task,
            iteration_count=self.iteration_count + 1,
            tool_call_count=self.tool_call_count,
            messages=self.messages,
            action_history=self.action_history,
            current_plan=self.current_plan,
            error=self.error,
            started_at=self.started_at,
            last_activity=time.time(),
        )


@dataclass(frozen=True)
class AgentEvent:
    """
    Agent 事件 — 用于追踪和可观测性

    记录 Agent 生命周期中的关键事件。
    """

    event_type: str
    agent_id: str
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    level: str = "info"  # debug, info, warning, error

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "level": self.level,
            "data": self.data,
        }


# ── 工厂函数 ─────────────────────────────────────────────────────────────

def create_agent_config(
    name: str,
    agent_type: AgentType = AgentType.REACT,
    system_prompt: str = "",
    tools: tuple[str, ...] = (),
    **kwargs: Any,
) -> AgentConfig:
    """创建 Agent 配置的便捷函数"""
    return AgentConfig(
        name=name,
        agent_type=agent_type,
        system_prompt=system_prompt,
        tools=tools,
        **kwargs,
    )


def create_tool_definition(
    name: str,
    description: str,
    parameters: dict[str, Any],
    function: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> ToolDefinition:
    """创建工具定义的便捷函数"""
    return ToolDefinition(
        name=name,
        description=description,
        parameters=parameters,
        function=function,
        **kwargs,
    )


def create_message(
    role: MessageRole,
    content: str,
    name: str | None = None,
    **kwargs: Any,
) -> AgentMessage:
    """创建消息的便捷函数"""
    return AgentMessage(
        role=role,
        content=content,
        name=name,
        **kwargs,
    )
