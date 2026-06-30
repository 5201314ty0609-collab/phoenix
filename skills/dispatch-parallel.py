#!/usr/bin/env python3
"""
鲤鱼 Skill: Dispatch Parallel — 并行任务分派。

当面对 2+ 独立任务时，自动分派并行 Agent。

Usage:
  dispatch-parallel.py analyze <task>     分析任务是否可并行
  dispatch-parallel.py plan <task1> <task2> ...  规划并行执行
  dispatch-parallel.py execute <plan_file>       执行并行计划
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json
import sys


@dataclass
class Task:
    """任务定义"""
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_minutes: int = 5
    can_parallel: bool = True


@dataclass
class ParallelPlan:
    """并行执行计划"""
    tasks: List[Task]
    groups: List[List[str]]  # 分组，每组内的任务可并行
    total_estimated_minutes: int = 0


def analyze_task(task_description: str) -> Dict:
    """分析任务是否可并行"""
    analysis = {
        "task": task_description,
        "can_parallel": False,
        "reason": "",
        "suggested_splits": [],
    }

    # 检查是否包含多个独立子任务
    indicators = [
        "同时", "并行", "一起", "分别", "各自",
        "and", "also", "as well as", "in addition",
        "multiple", "several", "various",
    ]

    task_lower = task_description.lower()
    has_multiple = any(ind in task_lower for ind in indicators)

    if has_multiple:
        analysis["can_parallel"] = True
        analysis["reason"] = "Task contains multiple independent sub-tasks"

        # 尝试拆分
        splits = []
        for sep in ["，", "。", "和", "以及", "同时", "然后", "and", "also", ","]:
            if sep in task_description:
                parts = [p.strip() for p in task_description.split(sep) if p.strip()]
                if len(parts) >= 2:
                    splits = parts
                    break

        if splits:
            analysis["suggested_splits"] = splits

    return analysis


def create_plan(tasks: List[str]) -> ParallelPlan:
    """创建并行执行计划"""
    task_objects = []

    for i, task_desc in enumerate(tasks):
        task = Task(
            name=f"task-{i + 1}",
            description=task_desc,
            estimated_minutes=5,
            can_parallel=True,
        )
        task_objects.append(task)

    # 简单分组：所有任务都可并行
    groups = [[task.name for task in task_objects]]

    plan = ParallelPlan(
        tasks=task_objects,
        groups=groups,
        total_estimated_minutes=5,  # 并行执行，取最长的
    )

    return plan


def save_plan(plan: ParallelPlan, output_path: Path):
    """保存执行计划"""
    plan_data = {
        "tasks": [
            {
                "name": task.name,
                "description": task.description,
                "dependencies": task.dependencies,
                "estimated_minutes": task.estimated_minutes,
                "can_parallel": task.can_parallel,
            }
            for task in plan.tasks
        ],
        "groups": plan.groups,
        "total_estimated_minutes": plan.total_estimated_minutes,
    }

    output_path.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2))
    print(f"Plan saved to: {output_path}")


def load_plan(plan_path: Path) -> ParallelPlan:
    """加载执行计划"""
    data = json.loads(plan_path.read_text())

    tasks = [
        Task(
            name=t["name"],
            description=t["description"],
            dependencies=t.get("dependencies", []),
            estimated_minutes=t.get("estimated_minutes", 5),
            can_parallel=t.get("can_parallel", True),
        )
        for t in data["tasks"]
    ]

    return ParallelPlan(
        tasks=tasks,
        groups=data["groups"],
        total_estimated_minutes=data.get("total_estimated_minutes", 0),
    )


def print_plan(plan: ParallelPlan):
    """打印执行计划"""
    print("Parallel Execution Plan")
    print("=" * 60)
    print(f"Tasks: {len(plan.tasks)}")
    print(f"Groups: {len(plan.groups)}")
    print(f"Estimated time: {plan.total_estimated_minutes} minutes")
    print()

    for i, group in enumerate(plan.groups):
        print(f"Group {i + 1} (parallel):")
        for task_name in group:
            task = next((t for t in plan.tasks if t.name == task_name), None)
            if task:
                print(f"  - {task.name}: {task.description}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "analyze":
        if len(sys.argv) < 3:
            print("Usage: dispatch-parallel.py analyze <task>")
            return
        task = " ".join(sys.argv[2:])
        analysis = analyze_task(task)

        print("Task Analysis")
        print("=" * 60)
        print(f"Task: {analysis['task']}")
        print(f"Can parallel: {analysis['can_parallel']}")
        if analysis["reason"]:
            print(f"Reason: {analysis['reason']}")
        if analysis["suggested_splits"]:
            print("Suggested splits:")
            for split in analysis["suggested_splits"]:
                print(f"  - {split}")

    elif cmd == "plan":
        if len(sys.argv) < 4:
            print("Usage: dispatch-parallel.py plan <task1> <task2> ...")
            print("Need at least 2 tasks")
            return
        tasks = sys.argv[2:]
        plan = create_plan(tasks)
        print_plan(plan)

    elif cmd == "execute":
        if len(sys.argv) < 3:
            print("Usage: dispatch-parallel.py execute <plan_file>")
            return
        plan_path = Path(sys.argv[2])
        if not plan_path.exists():
            print(f"Plan file not found: {plan_path}")
            return

        plan = load_plan(plan_path)
        print_plan(plan)

        print("To execute this plan, use:")
        print(f"  Run each group in parallel")
        print(f"  Wait for all tasks in a group to complete before starting the next")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
