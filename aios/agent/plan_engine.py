"""
Plan-and-Execute 引擎 — 规划 + 执行模式

Plan-and-Execute 是一种 Agent 执行模式：
1. Planner: 分析任务，生成多步骤执行计划
2. Executor: 按顺序执行每个步骤
3. Replanner: 根据执行结果调整计划（可选）

与 ReAct 相比，Plan-and-Execute 更适合复杂多步骤任务：
- ReAct: 每步独立决策，适合简单任务
- Plan-and-Execute: 全局规划，适合复杂任务

Design:
    ┌─────────────────────────────────────────────────────────────┐
    │                  Plan-and-Execute Engine                     │
    │                                                              │
    │  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │
    │  │ Planner  │───▶│ Executor │───▶│    Replanner         │  │
    │  │ (规划)   │    │ (执行)   │    │ (调整计划，可选)      │  │
    │  └──────────┘    └──────────┘    └──────────────────────┘  │
    │       │                │                    │               │
    │       ▼                ▼                    ▼               │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │              Execution Plan                           │  │
    │  │  (Step 1 → Step 2 → Step 3 → ... → Final Result)    │  │
    │  └──────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .agent_types import (
    AgentConfig,
    AgentMessage,
    AgentEvent,
    ExecutionPlan,
    LLMProvider,
    MessageRole,
    PlanStep,
    TaskStatus,
    ToolCall,
    ToolResult,
    ToolStatus,
)
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class PlanConfig:
    """Plan-and-Execute 配置"""

    max_plan_steps: int = 20
    max_replans: int = 3
    max_step_retries: int = 3
    timeout: float = 600.0  # 10 分钟
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_replanning: bool = True
    parallel_execution: bool = False
    verbose: bool = False

    @classmethod
    def from_agent_config(cls, config: AgentConfig) -> PlanConfig:
        """从 Agent 配置创建"""
        return PlanConfig(
            max_plan_steps=config.max_iterations * 2,
            timeout=config.timeout,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


@dataclass(frozen=True)
class PlanResult:
    """
    Plan-and-Execute 执行结果

    包含完整的执行计划和每个步骤的结果。
    """

    agent_id: str
    task: str
    plan: ExecutionPlan
    final_result: str
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    replan_count: int = 0
    total_execution_time: float = 0.0
    status: str = "completed"  # completed, failed, timeout, max_replans
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "completed" and self.error is None

    @property
    def progress(self) -> float:
        """进度百分比 (0.0 - 1.0)"""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "final_result": self.final_result,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "replan_count": self.replan_count,
            "total_execution_time": self.total_execution_time,
            "status": self.status,
            "error": self.error,
            "plan": {
                "plan_id": self.plan.plan_id,
                "goal": self.plan.goal,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "description": step.description,
                        "tool_name": step.tool_name,
                        "status": step.status.value,
                    }
                    for step in self.plan.steps
                ],
            },
        }


StepExecutor = Callable[[PlanStep], ToolResult]


class PlanEngine:
    """
    Plan-and-Execute 执行引擎

    实现任务分解、计划生成、步骤执行和计划调整。
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        config: PlanConfig | None = None,
    ) -> None:
        self._llm = llm_provider
        self._tools = tool_registry
        self._config = config or PlanConfig()
        self._events: list[AgentEvent] = []

    @property
    def config(self) -> PlanConfig:
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

    def _build_planner_prompt(self, task: str) -> str:
        """构建规划器提示"""
        tool_descriptions = []
        for tool_def in self._tools.list_tools():
            tool_descriptions.append(
                f"- {tool_def.name}: {tool_def.description}"
            )

        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "无可用工具"

        return f"""你是一个任务规划专家。你的职责是分析任务并生成详细的执行计划。

可用工具：
{tools_text}

请为以下任务生成执行计划：

任务：{task}

请按以下 JSON 格式输出计划：

```json
{{
  "goal": "任务目标的简短描述",
  "steps": [
    {{
      "description": "步骤描述",
      "tool_name": "使用的工具名称（可选）",
      "parameters": {{}},
      "dependencies": []
    }}
  ]
}}
```

规则：
1. 每个步骤应该是原子的、可独立执行的
2. 使用 dependencies 字段指定步骤间的依赖关系（填写依赖步骤的索引）
3. 如果某个步骤不需要使用工具，tool_name 设为 null
4. 步骤数量不超过 {self._config.max_plan_steps} 个
5. 确保计划完整，能够解决整个任务
"""

    def _build_replanner_prompt(
        self,
        task: str,
        current_plan: ExecutionPlan,
        completed_results: list[tuple[PlanStep, ToolResult]],
        failed_step: PlanStep | None = None,
    ) -> str:
        """构建重新规划器提示"""
        completed_info = []
        for step, result in completed_results:
            status = "成功" if result.is_success else "失败"
            completed_info.append(
                f"- 步骤 {step.step_id}: {step.description} [{status}]"
                f"\n  结果: {result.output if result.is_success else result.error}"
            )

        completed_text = "\n".join(completed_info) if completed_info else "无"

        failed_info = ""
        if failed_step:
            failed_info = f"""
失败步骤：
- 步骤 ID: {failed_step.step_id}
- 描述: {failed_step.description}
- 工具: {failed_step.tool_name}
"""

        return f"""你是一个任务规划专家。需要根据执行情况调整计划。

原始任务：{task}

当前计划进度：{current_plan.completed_steps}/{current_plan.total_steps} 步骤已完成

已完成步骤的结果：
{completed_text}
{failed_info}
剩余步骤：
{chr(10).join(f'- {s.step_id}: {s.description}' for s in current_plan.steps if s.status == TaskStatus.PENDING)}

请根据当前情况，生成调整后的执行计划。输出格式与规划时相同。

如果任务已经完成，请输出：
```json
{{
  "goal": "任务已完成",
  "steps": [],
  "final_result": "最终结果描述"
}}
```

如果任务无法继续，请输出：
```json
{{
  "goal": "任务失败",
  "steps": [],
  "error": "失败原因"
}}
```
"""

    def _parse_plan_response(self, response: str) -> tuple[str, list[PlanStep], str | None]:
        """
        解析计划响应

        返回: (goal, steps, error)
        """
        try:
            # 提取 JSON 块
            json_start = response.find("```json")
            json_end = response.find("```", json_start + 7)
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start + 7:json_end].strip()
            else:
                # 尝试直接解析整个响应
                json_text = response

            data = json.loads(json_text)

            goal = data.get("goal", "")
            error = data.get("error")
            final_result = data.get("final_result")

            if error:
                return goal, [], error

            if final_result is not None:
                return goal, [], None  # 任务已完成

            steps_data = data.get("steps", [])
            steps: list[PlanStep] = []

            for i, step_data in enumerate(steps_data):
                dependencies = tuple(
                    f"step_{d:04d}" if isinstance(d, int) else d
                    for d in step_data.get("dependencies", [])
                )

                step = PlanStep(
                    step_id=f"step_{i:04d}",
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name"),
                    parameters=step_data.get("parameters", {}),
                    dependencies=dependencies,
                )
                steps.append(step)

            return goal, steps, None

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return "", [], f"解析计划失败: {type(e).__name__}: {str(e)}"

    def _create_plan(self, task: str, agent_id: str) -> tuple[ExecutionPlan, str | None]:
        """
        生成执行计划

        返回: (plan, error)
        """
        self._emit_event("plan_start", agent_id, {"task": task})

        prompt = self._build_planner_prompt(task)

        try:
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
        except Exception as e:
            error = f"规划失败: {type(e).__name__}: {str(e)}"
            self._emit_event("plan_error", agent_id, {"error": error})
            return ExecutionPlan(goal=task), error

        goal, steps, error = self._parse_plan_response(response.content)

        if error:
            self._emit_event("plan_error", agent_id, {"error": error})
            return ExecutionPlan(goal=task), error

        plan = ExecutionPlan(
            goal=goal or task,
            steps=tuple(steps),
        )

        self._emit_event("plan_created", agent_id, {
            "plan_id": plan.plan_id,
            "total_steps": plan.total_steps,
        })

        return plan, None

    def _replan(
        self,
        task: str,
        current_plan: ExecutionPlan,
        completed_results: list[tuple[PlanStep, ToolResult]],
        failed_step: PlanStep | None,
        agent_id: str,
    ) -> tuple[ExecutionPlan, str | None]:
        """
        重新规划

        返回: (new_plan, error)
        """
        self._emit_event("replan_start", agent_id, {
            "plan_id": current_plan.plan_id,
            "completed": current_plan.completed_steps,
        })

        prompt = self._build_replanner_prompt(
            task, current_plan, completed_results, failed_step
        )

        try:
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
        except Exception as e:
            error = f"重新规划失败: {type(e).__name__}: {str(e)}"
            self._emit_event("replan_error", agent_id, {"error": error})
            return current_plan, error

        goal, steps, error = self._parse_plan_response(response.content)

        if error:
            self._emit_event("replan_error", agent_id, {"error": error})
            return current_plan, error

        # 合并已完成的步骤和新计划
        completed_steps = [
            step for step in current_plan.steps
            if step.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
        ]

        new_plan = ExecutionPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            goal=goal or task,
            steps=tuple(completed_steps + steps),
        )

        self._emit_event("replan_complete", agent_id, {
            "new_plan_id": new_plan.plan_id,
            "new_total_steps": new_plan.total_steps,
        })

        return new_plan, None

    def _execute_step(
        self,
        step: PlanStep,
        context: dict[str, Any],
        agent_id: str,
    ) -> ToolResult:
        """
        执行单个步骤

        Args:
            step: 要执行的步骤
            context: 执行上下文（包含之前步骤的结果）
            agent_id: Agent ID

        Returns:
            ToolResult: 执行结果
        """
        self._emit_event("step_start", agent_id, {
            "step_id": step.step_id,
            "description": step.description,
        })

        # 如果步骤指定了工具，直接执行
        if step.tool_name:
            # 合并步骤参数和上下文
            parameters = {**step.parameters}
            for key, value in parameters.items():
                if isinstance(value, str) and value.startswith("$"):
                    # 替换上下文变量
                    ref_key = value[1:]
                    if ref_key in context:
                        parameters[key] = context[ref_key]

            result = self._tools.execute(step.tool_name, parameters)

            self._emit_event("step_complete", agent_id, {
                "step_id": step.step_id,
                "success": result.is_success,
            })

            return result

        # 如果没有指定工具，使用 LLM 生成结果
        try:
            context_text = "\n".join(
                f"- {k}: {v}" for k, v in context.items()
            )

            prompt = f"""请根据以下上下文完成任务：

任务：{step.description}

上下文信息：
{context_text}

请直接给出结果，不要使用任何工具。"""

            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )

            self._emit_event("step_complete", agent_id, {
                "step_id": step.step_id,
                "success": True,
            })

            return ToolResult(
                tool_name="llm_reasoning",
                status=ToolStatus.SUCCESS,
                output=response.content,
            )

        except Exception as e:
            self._emit_event("step_error", agent_id, {
                "step_id": step.step_id,
                "error": str(e),
            })

            return ToolResult(
                tool_name="llm_reasoning",
                status=ToolStatus.FAILED,
                error=f"LLM 推理失败: {type(e).__name__}: {str(e)}",
            )

    def _generate_final_result(
        self,
        task: str,
        plan: ExecutionPlan,
        results: list[tuple[PlanStep, ToolResult]],
        agent_id: str,
    ) -> str:
        """生成最终结果"""
        self._emit_event("final_result_start", agent_id)

        results_text = []
        for step, result in results:
            status = "成功" if result.is_success else "失败"
            output = result.output if result.is_success else result.error
            results_text.append(f"步骤 {step.step_id} [{status}]: {output}")

        results_summary = "\n".join(results_text)

        prompt = f"""请根据以下执行结果，生成最终的任务完成报告。

原始任务：{task}

执行计划目标：{plan.goal}

执行结果：
{results_summary}

请生成一个清晰、完整的最终结果。"""

        try:
            response = self._llm.generate(
                messages=[AgentMessage(
                    role=MessageRole.USER,
                    content=prompt,
                )],
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )

            self._emit_event("final_result_complete", agent_id)

            return response.content

        except Exception as e:
            self._emit_event("final_result_error", agent_id, {"error": str(e)})
            return f"生成最终结果失败: {str(e)}\n\n执行摘要:\n{results_summary}"

    def run(
        self,
        task: str,
        agent_config: AgentConfig,
        on_step_complete: Callable[[PlanStep, ToolResult], None] | None = None,
        on_plan_update: Callable[[ExecutionPlan], None] | None = None,
    ) -> PlanResult:
        """
        执行 Plan-and-Execute 循环

        Args:
            task: 要执行的任务描述
            agent_config: Agent 配置
            on_step_complete: 步骤完成回调
            on_plan_update: 计划更新回调

        Returns:
            PlanResult: 执行结果
        """
        start_time = time.time()
        agent_id = agent_config.agent_id

        self._emit_event("plan_execute_start", agent_id, {"task": task})

        # 生成初始计划
        plan, error = self._create_plan(task, agent_id)
        if error:
            return PlanResult(
                agent_id=agent_id,
                task=task,
                plan=plan,
                final_result="",
                status="failed",
                error=error,
                total_execution_time=time.time() - start_time,
            )

        if on_plan_update:
            on_plan_update(plan)

        # 执行计划
        completed_results: list[tuple[PlanStep, ToolResult]] = []
        context: dict[str, Any] = {}
        replan_count = 0

        while not plan.is_complete:
            # 检查超时
            if time.time() - start_time > self._config.timeout:
                return PlanResult(
                    agent_id=agent_id,
                    task=task,
                    plan=plan,
                    final_result="",
                    total_steps=plan.total_steps,
                    completed_steps=plan.completed_steps,
                    failed_steps=plan.failed_steps,
                    replan_count=replan_count,
                    status="timeout",
                    error=f"执行超时 ({self._config.timeout}s)",
                    total_execution_time=time.time() - start_time,
                )

            # 获取可执行的步骤
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                # 没有可执行的步骤，可能有循环依赖或全部完成
                if plan.has_failure and self._config.enable_replanning:
                    # 尝试重新规划
                    if replan_count >= self._config.max_replans:
                        return PlanResult(
                            agent_id=agent_id,
                            task=task,
                            plan=plan,
                            final_result="",
                            total_steps=plan.total_steps,
                            completed_steps=plan.completed_steps,
                            failed_steps=plan.failed_steps,
                            replan_count=replan_count,
                            status="max_replans",
                            error=f"达到最大重新规划次数 ({self._config.max_replans})",
                            total_execution_time=time.time() - start_time,
                        )

                    failed_step = next(
                        (s for s in plan.steps if s.status == TaskStatus.FAILED),
                        None,
                    )
                    plan, error = self._replan(
                        task, plan, completed_results, failed_step, agent_id
                    )
                    replan_count += 1

                    if on_plan_update:
                        on_plan_update(plan)

                    continue
                else:
                    break

            # 执行步骤
            for step in ready_steps:
                # 检查超时
                if time.time() - start_time > self._config.timeout:
                    break

                # 更新步骤状态为执行中
                plan = plan.update_step(
                    step.step_id,
                    step.with_status(TaskStatus.EXECUTING)
                )

                # 执行步骤
                result = self._execute_step(step, context, agent_id)

                # 更新步骤状态和结果
                updated_step = step.with_result(result)
                plan = plan.update_step(step.step_id, updated_step)

                # 记录结果
                completed_results.append((step, result))

                # 更新上下文
                if result.is_success:
                    context[step.step_id] = result.output
                    # 也用描述作为键，方便引用
                    context[f"step_{len(completed_results)}"] = result.output

                if on_step_complete:
                    on_step_complete(step, result)

                if on_plan_update:
                    on_plan_update(plan)

                # 如果步骤失败且不允许重新规划，停止执行
                if result.is_failure and not self._config.enable_replanning:
                    break

        # 生成最终结果
        final_result = self._generate_final_result(
            task, plan, completed_results, agent_id
        )

        total_time = time.time() - start_time

        # 确定最终状态
        if plan.is_complete and not plan.has_failure:
            status = "completed"
        elif plan.has_failure:
            status = "failed"
        else:
            status = "incomplete"

        result = PlanResult(
            agent_id=agent_id,
            task=task,
            plan=plan,
            final_result=final_result,
            total_steps=plan.total_steps,
            completed_steps=plan.completed_steps,
            failed_steps=plan.failed_steps,
            replan_count=replan_count,
            total_execution_time=total_time,
            status=status,
        )

        self._emit_event("plan_execute_complete", agent_id, {
            "status": status,
            "total_steps": plan.total_steps,
            "completed": plan.completed_steps,
            "failed": plan.failed_steps,
        })

        return result
