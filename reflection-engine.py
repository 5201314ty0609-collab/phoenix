#!/usr/bin/env python3
"""
PHOENIX Reflection Engine — 任务后自动反思。

每个任务完成后自动评估：
- 做了什么
- 效果如何
- 下次怎么改进

吸收自 MUNDO reflection_engine.py 的任务后反思模式。

Usage:
  reflection-engine.py start <task_name>       开始任务追踪
  reflection-engine.py checkpoint <note>       添加检查点
  reflection-engine.py finish [result]         完成任务并触发反思
  reflection-engine.py list                    列出最近任务
  reflection-engine.py reflect <task_id>       手动触发反思
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json
import sys
import uuid

PHOENIX_HOME = Path.home() / ".claude/phoenix"
REFLECTIONS_FILE = PHOENIX_HOME / "reflections.jsonl"
ACTIVE_TASKS_FILE = PHOENIX_HOME / "active-tasks.json"

# ── 数据类 ───────────────────────────────────────────────────────────────

@dataclass
class Checkpoint:
    """任务检查点"""
    timestamp: str
    note: str
    metrics: Dict = field(default_factory=dict)


@dataclass
class TaskReflection:
    """任务反思记录"""
    task_id: str
    task_name: str
    started_at: str
    finished_at: str = ""
    status: str = "active"  # active/success/partial/failed
    checkpoints: List[Dict] = field(default_factory=list)
    result_summary: str = ""
    lessons: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


# ── 持久化 ───────────────────────────────────────────────────────────────

def load_active_tasks() -> Dict[str, TaskReflection]:
    """加载活跃任务"""
    if not ACTIVE_TASKS_FILE.exists():
        return {}

    tasks = {}
    try:
        data = json.loads(ACTIVE_TASKS_FILE.read_text())
        for task_id, info in data.items():
            tasks[task_id] = TaskReflection(**info)
    except Exception:
        pass

    return tasks


def save_active_tasks(tasks: Dict[str, TaskReflection]):
    """保存活跃任务"""
    data = {task_id: asdict(task) for task_id, task in tasks.items()}
    ACTIVE_TASKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def append_reflection(reflection: TaskReflection):
    """追加反思记录到日志"""
    with open(REFLECTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(reflection), ensure_ascii=False) + "\n")


# ── 核心逻辑 ─────────────────────────────────────────────────────────────

def start_task(task_name: str) -> str:
    """开始新任务"""
    tasks = load_active_tasks()

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    task = TaskReflection(
        task_id=task_id,
        task_name=task_name,
        started_at=now,
        status="active",
    )

    tasks[task_id] = task
    save_active_tasks(tasks)

    print(f"Task started: {task_id}")
    print(f"Name: {task_name}")
    print(f"Time: {now}")

    return task_id


def add_checkpoint(task_id: str, note: str, metrics: Dict = None):
    """添加检查点"""
    tasks = load_active_tasks()

    if task_id not in tasks:
        print(f"Task not found: {task_id}")
        return

    task = tasks[task_id]
    now = datetime.now(timezone.utc).isoformat()

    checkpoint = Checkpoint(
        timestamp=now,
        note=note,
        metrics=metrics or {},
    )

    task.checkpoints.append(asdict(checkpoint))
    save_active_tasks(tasks)

    print(f"Checkpoint added to {task_id}: {note}")


def finish_task(task_id: str, status: str = "success", result_summary: str = "",
                lessons: List[str] = None, next_actions: List[str] = None):
    """完成任务并触发反思"""
    tasks = load_active_tasks()

    if task_id not in tasks:
        print(f"Task not found: {task_id}")
        return

    task = tasks[task_id]
    now = datetime.now(timezone.utc).isoformat()

    task.finished_at = now
    task.status = status
    task.result_summary = result_summary
    task.lessons = lessons or []
    task.next_actions = next_actions or []

    # 计算指标
    try:
        start_time = datetime.fromisoformat(task.started_at)
        end_time = datetime.fromisoformat(now)
        duration_minutes = (end_time - start_time).total_seconds() / 60
        task.metrics["duration_minutes"] = round(duration_minutes, 2)
    except Exception:
        pass

    task.metrics["checkpoint_count"] = len(task.checkpoints)

    # 生成反思
    reflection = generate_reflection(task)

    # 保存到日志
    append_reflection(task)

    # 从活跃任务中移除
    del tasks[task_id]
    save_active_tasks(tasks)

    # 输出反思
    print(f"\n{'=' * 60}")
    print(f"Task Completed: {task.task_name}")
    print(f"{'=' * 60}")
    print(f"Status: {task.status}")
    print(f"Duration: {task.metrics.get('duration_minutes', '?')} minutes")
    print(f"Checkpoints: {task.metrics.get('checkpoint_count', 0)}")
    print()
    print("Reflection:")
    print(reflection)
    print(f"{'=' * 60}")

    return reflection


def generate_reflection(task: TaskReflection) -> str:
    """生成反思文本"""
    lines = []

    # 做了什么
    lines.append("## What was done")
    lines.append(f"- Task: {task.task_name}")
    if task.result_summary:
        lines.append(f"- Result: {task.result_summary}")
    if task.checkpoints:
        lines.append(f"- Progress: {len(task.checkpoints)} checkpoints")
        for cp in task.checkpoints[-3:]:  # 最后 3 个检查点
            lines.append(f"  - {cp['note']}")

    # 效果如何
    lines.append("\n## How it went")
    duration = task.metrics.get("duration_minutes", 0)
    if task.status == "success":
        lines.append(f"- Completed successfully in {duration} minutes")
    elif task.status == "partial":
        lines.append(f"- Partially completed in {duration} minutes")
    else:
        lines.append(f"- Failed after {duration} minutes")

    # 经验教训
    if task.lessons:
        lines.append("\n## Lessons learned")
        for lesson in task.lessons:
            lines.append(f"- {lesson}")

    # 下次改进
    if task.next_actions:
        lines.append("\n## Next actions")
        for action in task.next_actions:
            lines.append(f"- {action}")

    return "\n".join(lines)


def list_tasks(limit: int = 10):
    """列出最近任务"""
    if not REFLECTIONS_FILE.exists():
        print("No reflections recorded yet.")
        return

    lines = REFLECTIONS_FILE.read_text().strip().split("\n")
    tasks = []

    for line in lines:
        if not line.strip():
            continue
        try:
            task = json.loads(line)
            tasks.append(task)
        except Exception:
            pass

    # 按时间倒序
    tasks.sort(key=lambda t: t.get("finished_at", ""), reverse=True)

    print(f"Recent tasks ({min(limit, len(tasks))}/{len(tasks)}):")
    print()

    for task in tasks[:limit]:
        status_icon = {
            "success": "✅",
            "partial": "⚠️",
            "failed": "❌",
        }.get(task["status"], "❓")

        duration = task.get("metrics", {}).get("duration_minutes", "?")
        print(f"{status_icon} [{task['task_id']}] {task['task_name']}")
        print(f"   Status: {task['status']} | Duration: {duration} min")
        if task.get("result_summary"):
            print(f"   Result: {task['result_summary'][:80]}")
        print()


def reflect_on_task(task_id: str):
    """手动触发反思"""
    if not REFLECTIONS_FILE.exists():
        print(f"No reflections found.")
        return

    lines = REFLECTIONS_FILE.read_text().strip().split("\n")

    for line in lines:
        if not line.strip():
            continue
        try:
            task = json.loads(line)
            if task["task_id"] == task_id:
                reflection = generate_reflection(TaskReflection(**task))
                print(reflection)
                return
        except Exception:
            pass

    print(f"Task not found: {task_id}")


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "start":
        if len(sys.argv) < 3:
            print("Usage: reflection-engine.py start <task_name>")
            return
        task_name = " ".join(sys.argv[2:])
        start_task(task_name)

    elif cmd == "checkpoint":
        if len(sys.argv) < 4:
            print("Usage: reflection-engine.py checkpoint <task_id> <note>")
            return
        task_id = sys.argv[2]
        note = " ".join(sys.argv[3:])
        add_checkpoint(task_id, note)

    elif cmd == "finish":
        if len(sys.argv) < 3:
            print("Usage: reflection-engine.py finish <task_id> [status] [result]")
            return
        task_id = sys.argv[2]
        status = sys.argv[3] if len(sys.argv) > 3 else "success"
        result = sys.argv[4] if len(sys.argv) > 4 else ""
        finish_task(task_id, status, result)

    elif cmd == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_tasks(limit)

    elif cmd == "reflect":
        if len(sys.argv) < 3:
            print("Usage: reflection-engine.py reflect <task_id>")
            return
        reflect_on_task(sys.argv[2])

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
