#!/usr/bin/env python3
"""
鲤鱼 Skill: Skill Pipeline — 技能组合与链式执行。

将多个技能串联执行，前一个的输出影响后一个的输入。

Usage:
  skill-pipeline.py run <skill1> <skill2> ... [--target <path>]  链式执行
  skill-pipeline.py define <name> <skill1> <skill2> ...          定义管道
  skill-pipeline.py list                                         列出已定义的管道
  skill-pipeline.py run-pipeline <name> [--target <path>]        执行已定义的管道
  skill-pipeline.py history                                      查看执行历史
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json
import subprocess
import sys
import uuid


鲤鱼_HOME = Path.home() / ".claude" / "liyu"
SKILLS_DIR = 鲤鱼_HOME / "skills"
PIPELINES_FILE = 鲤鱼_HOME / "pipelines.json"
PIPELINE_HISTORY_FILE = 鲤鱼_HOME / "pipeline-history.jsonl"


# ── Data Model ──────────────────────────────────────────────────────────────

@dataclass
class PipelineStep:
    """管道步骤"""
    skill: str
    args: List[str] = field(default_factory=list)
    optional: bool = False       # 失败时是否继续
    condition: str = ""          # 执行条件（如 "previous_passed"）

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "args": self.args,
            "optional": self.optional,
            "condition": self.condition,
        }


@dataclass
class Pipeline:
    """管道定义"""
    name: str
    description: str
    steps: List[PipelineStep]
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
        }


@dataclass
class StepResult:
    """步骤执行结果"""
    skill: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    passed: bool

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:500],  # Truncate for storage
            "stderr": self.stderr[:500],
            "duration_ms": self.duration_ms,
            "passed": self.passed,
        }


@dataclass
class PipelineResult:
    """管道执行结果"""
    pipeline_name: str
    run_id: str
    started_at: str
    finished_at: str
    total_duration_ms: int
    steps: List[StepResult]
    passed: bool
    target: str = ""

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_duration_ms": self.total_duration_ms,
            "steps": [s.to_dict() for s in self.steps],
            "passed": self.passed,
            "target": self.target,
        }


# ── Pipeline Manager ────────────────────────────────────────────────────────

class PipelineManager:
    """管道管理器"""

    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self._load_pipelines()

    def _load_pipelines(self):
        """加载已定义的管道"""
        if not PIPELINES_FILE.exists():
            return
        try:
            data = json.loads(PIPELINES_FILE.read_text())
            for name, p in data.items():
                steps = [PipelineStep(**s) for s in p.get("steps", [])]
                self.pipelines[name] = Pipeline(
                    name=name,
                    description=p.get("description", ""),
                    steps=steps,
                    created_at=p.get("created_at", ""),
                )
        except Exception:
            pass

    def _save_pipelines(self):
        """保存管道定义"""
        data = {name: p.to_dict() for name, p in self.pipelines.items()}
        PIPELINES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def define(self, name: str, description: str, steps: List[PipelineStep]):
        """定义新管道"""
        now = datetime.now(timezone.utc).isoformat()
        self.pipelines[name] = Pipeline(
            name=name,
            description=description,
            steps=steps,
            created_at=now,
        )
        self._save_pipelines()

    def get(self, name: str) -> Optional[Pipeline]:
        """获取管道"""
        return self.pipelines.get(name)

    def list_all(self) -> List[Pipeline]:
        """列出所有管道"""
        return sorted(self.pipelines.values(), key=lambda p: p.name)

    def run(self, pipeline: Pipeline, target: str = "") -> PipelineResult:
        """执行管道"""
        run_id = f"pipe-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc)
        import time
        start_ms = int(time.time() * 1000)

        step_results: List[StepResult] = []
        all_passed = True

        for i, step in enumerate(pipeline.steps):
            # Check condition
            if step.condition == "previous_passed" and step_results:
                if not step_results[-1].passed:
                    step_results.append(StepResult(
                        skill=step.skill, exit_code=-1, stdout="", stderr="Skipped: previous step failed",
                        duration_ms=0, passed=False,
                    ))
                    continue

            # Build command
            cmd = [sys.executable, str(SKILLS_DIR / f"{step.skill}.py")]
            if target:
                cmd.append(target)
            cmd.extend(step.args)

            # Execute
            import time as time_mod
            step_start = int(time_mod.time() * 1000)

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120,
                )
                step_end = int(time_mod.time() * 1000)

                step_result = StepResult(
                    skill=step.skill,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration_ms=step_end - step_start,
                    passed=result.returncode == 0,
                )
            except subprocess.TimeoutExpired:
                step_result = StepResult(
                    skill=step.skill, exit_code=-1, stdout="",
                    stderr="Timeout (120s)", duration_ms=120000, passed=False,
                )
            except Exception as e:
                step_result = StepResult(
                    skill=step.skill, exit_code=-1, stdout="",
                    stderr=str(e), duration_ms=0, passed=False,
                )

            step_results.append(step_result)

            if not step_result.passed:
                all_passed = False
                if not step.optional:
                    break

        finished_at = datetime.now(timezone.utc)
        end_ms = int(time_mod.time() * 1000)

        pipeline_result = PipelineResult(
            pipeline_name=pipeline.name,
            run_id=run_id,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            total_duration_ms=end_ms - start_ms,
            steps=step_results,
            passed=all_passed,
            target=target,
        )

        # Save to history
        self._save_history(pipeline_result)

        return pipeline_result

    def _save_history(self, result: PipelineResult):
        """保存执行历史"""
        with open(PIPELINE_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def load_history(self, limit: int = 20) -> List[Dict]:
        """加载执行历史"""
        if not PIPELINE_HISTORY_FILE.exists():
            return []

        lines = PIPELINE_HISTORY_FILE.read_text().strip().split("\n")
        history = []
        for line in lines:
            if line.strip():
                try:
                    history.append(json.loads(line))
                except Exception:
                    pass

        return history[-limit:]


# ── Predefined Pipelines ────────────────────────────────────────────────────

PREDEFINED_PIPELINES = {
    "code-quality": Pipeline(
        name="code-quality",
        description="Full code quality check: tidy -> verify -> complexity",
        steps=[
            PipelineStep(skill="code-tidy"),
            PipelineStep(skill="verify-completion", condition="previous_passed"),
            PipelineStep(skill="complexity-analyzer", condition="previous_passed"),
        ],
    ),
    "security-review": Pipeline(
        name="security-review",
        description="Security review: audit -> verify -> complexity check",
        steps=[
            PipelineStep(skill="security-audit"),
            PipelineStep(skill="verify-completion"),
            PipelineStep(skill="complexity-analyzer", optional=True),
        ],
    ),
    "pre-commit": Pipeline(
        name="pre-commit",
        description="Pre-commit checks: tidy -> security -> verify",
        steps=[
            PipelineStep(skill="code-tidy"),
            PipelineStep(skill="security-audit", condition="previous_passed"),
            PipelineStep(skill="verify-completion", condition="previous_passed"),
        ],
    ),
    "full-review": Pipeline(
        name="full-review",
        description="Complete review: tidy -> security -> verify -> complexity -> doc check",
        steps=[
            PipelineStep(skill="code-tidy"),
            PipelineStep(skill="security-audit"),
            PipelineStep(skill="verify-completion"),
            PipelineStep(skill="complexity-analyzer", optional=True),
            PipelineStep(skill="doc-gen", args=["docstrings", "--check"], optional=True),
        ],
    ),
}


def ensure_predefined(manager: PipelineManager):
    """确保预定义管道存在"""
    for name, pipeline in PREDEFINED_PIPELINES.items():
        if name not in manager.pipelines:
            manager.pipelines[name] = pipeline
    manager._save_pipelines()


# ── Output ──────────────────────────────────────────────────────────────────

def print_result(result: PipelineResult):
    """打印执行结果"""
    status = "PASSED" if result.passed else "FAILED"

    print(f"Pipeline: {result.pipeline_name} [{status}]")
    print(f"Run ID: {result.run_id}")
    if result.target:
        print(f"Target: {result.target}")
    print(f"Duration: {result.total_duration_ms}ms")
    print()

    for i, step in enumerate(result.steps):
        step_status = "OK" if step.passed else "FAIL"
        print(f"  Step {i + 1}: {step.skill} [{step_status}] ({step.duration_ms}ms)")
        if not step.passed and step.stderr:
            # Show first few lines of stderr
            for line in step.stderr.strip().split("\n")[:3]:
                print(f"    | {line}")
        if step.passed and step.stdout:
            # Show summary line
            summary = step.stdout.strip().split("\n")
            if summary:
                print(f"    {summary[-1][:80]}")
    print()


def print_history(history: List[Dict]):
    """打印执行历史"""
    if not history:
        print("No pipeline history.")
        return

    print("Pipeline History")
    print("=" * 60)

    for entry in reversed(history):
        status = "PASS" if entry.get("passed") else "FAIL"
        name = entry.get("pipeline_name", "?")
        run_id = entry.get("run_id", "?")[:12]
        duration = entry.get("total_duration_ms", 0)
        target = entry.get("target", "")
        steps = entry.get("steps", [])
        step_summary = " -> ".join(
            f"{s['skill']}{'*' if not s.get('passed') else ''}"
            for s in steps
        )

        print(f"  [{status}] {name} ({run_id}) {duration}ms")
        if target:
            print(f"    Target: {target}")
        print(f"    Steps: {step_summary}")
        print()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    manager = PipelineManager()
    ensure_predefined(manager)

    if cmd == "run":
        if len(sys.argv) < 3:
            print("Usage: skill-pipeline.py run <skill1> <skill2> ... [--target <path>]")
            return

        # Parse args
        args = sys.argv[2:]
        target = ""
        for i, arg in enumerate(args):
            if arg == "--target" and i + 1 < len(args):
                target = args[i + 1]

        skills = [a for a in args if not a.startswith("--")]
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args):
                skills = [a for a in skills if a != args[idx + 1]]

        # Create ad-hoc pipeline
        steps = [PipelineStep(skill=s) for s in skills]
        pipeline = Pipeline(name="ad-hoc", description="Ad-hoc pipeline", steps=steps)

        result = manager.run(pipeline, target=target)
        print_result(result)

    elif cmd == "define":
        if len(sys.argv) < 4:
            print("Usage: skill-pipeline.py define <name> <skill1> <skill2> ...")
            return

        name = sys.argv[2]
        skills = sys.argv[3:]
        steps = [PipelineStep(skill=s) for s in skills]
        manager.define(name, f"Custom pipeline: {' -> '.join(skills)}", steps)
        print(f"Pipeline '{name}' defined with {len(steps)} steps")

    elif cmd == "list":
        pipelines = manager.list_all()
        if not pipelines:
            print("No pipelines defined.")
            return

        print("Pipelines")
        print("=" * 60)
        for p in pipelines:
            steps_str = " -> ".join(s.skill for s in p.steps)
            print(f"  {p.name}")
            print(f"    {p.description}")
            print(f"    Steps: {steps_str}")
            print()

    elif cmd == "run-pipeline":
        if len(sys.argv) < 3:
            print("Usage: skill-pipeline.py run-pipeline <name> [--target <path>]")
            return

        name = sys.argv[2]
        target = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--target" and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]

        pipeline = manager.get(name)
        if not pipeline:
            print(f"Pipeline not found: {name}")
            print("Available:", ", ".join(manager.pipelines.keys()))
            sys.exit(1)

        result = manager.run(pipeline, target=target)
        print_result(result)

        if not result.passed:
            sys.exit(1)

    elif cmd == "history":
        history = manager.load_history()
        print_history(history)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
