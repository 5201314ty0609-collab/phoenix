"""
PHOENIX AIOS Agent Core System

完整的 Agent 框架，包含：
1. Agent 核心类型与接口
2. ReAct 引擎（推理 + 行动循环）
3. Plan-and-Execute 引擎（规划 + 执行）
4. 工具注册系统
5. 多 Agent 协作协调器
6. Agent 生命周期管理

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                      Agent Manager                              │
    │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌─────────────────┐ │
    │  │  ReAct   │ │  Plan    │ │   Tool     │ │   Multi-Agent   │ │
    │  │  Engine  │ │ Executor │ │  Registry  │ │   Coordinator   │ │
    │  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └──────┬──────────┘ │
    │       │            │             │               │             │
    │  ┌────┴────────────┴─────────────┴───────────────┴──────────┐  │
    │  │                   Agent Core Types                        │  │
    │  │  (Agent, Message, Tool, Plan, Task, ActionResult)        │  │
    │  └──────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘

核心设计原则：
- 不可变数据结构（所有核心类型都是 frozen dataclass）
- 线程安全（所有公共方法使用 threading.RLock）
- 事件驱动（Agent 间通过消息通信）
- 可组合性（引擎可独立使用或组合使用）
- 可观测性（内置执行追踪和指标收集）
"""

from .agent_types import (
    # 枚举
    AgentStatus,
    AgentType,
    MessageRole,
    TaskStatus,
    ToolStatus,
    ExecutionMode,
    # 核心类型
    AgentConfig,
    AgentMessage,
    ToolDefinition,
    ToolResult,
    ActionResult,
    PlanStep,
    ExecutionPlan,
    AgentState,
    AgentEvent,
    # 工厂函数
    create_agent_config,
    create_tool_definition,
    create_message,
)

from .tool_registry import (
    ToolRegistry,
    ToolExecutor,
    BuiltinTools,
)

from .react_engine import (
    ReActEngine,
    ReActStep,
    ReActResult,
    ReActConfig,
)

from .plan_engine import (
    PlanEngine,
    PlanResult,
    PlanConfig,
    StepExecutor,
)

from .agent_manager import (
    AgentManager,
    AgentInstance,
)

from .multi_agent import (
    MultiAgentCoordinator,
    AgentTeam,
    DelegationResult,
    CollaborationProtocol,
)

__all__ = [
    # 枚举
    "AgentStatus",
    "AgentType",
    "MessageRole",
    "TaskStatus",
    "ToolStatus",
    "ExecutionMode",
    # 核心类型
    "AgentConfig",
    "AgentMessage",
    "ToolDefinition",
    "ToolResult",
    "ActionResult",
    "PlanStep",
    "ExecutionPlan",
    "AgentState",
    "AgentEvent",
    # 工厂函数
    "create_agent_config",
    "create_tool_definition",
    "create_message",
    # 工具注册
    "ToolRegistry",
    "ToolExecutor",
    "BuiltinTools",
    # ReAct 引擎
    "ReActEngine",
    "ReActStep",
    "ReActResult",
    "ReActConfig",
    # 规划引擎
    "PlanEngine",
    "PlanResult",
    "PlanConfig",
    "StepExecutor",
    # Agent 管理
    "AgentManager",
    "AgentInstance",
    # 多 Agent 协作
    "MultiAgentCoordinator",
    "AgentTeam",
    "DelegationResult",
    "CollaborationProtocol",
]
