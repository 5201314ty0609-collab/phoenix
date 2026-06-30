#!/usr/bin/env python3
"""
鲤鱼 Skill: Health Check — 系统健康检查。

检查系统状态：
- 磁盘空间
- 内存使用
- Python/Node 环境
- 鲤鱼 组件状态
- Git 仓库状态

Usage:
  health-check.py                  全面健康检查
  health-check.py --json           JSON 输出
  health-check.py quick            快速检查（仅关键项）
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import os
import platform
import shutil
import subprocess
import sys


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: str         # ok / warning / error / info
    message: str
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


def run_cmd(cmd: List[str], timeout: int = 10) -> Tuple[str, int]:
    """运行命令"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        return "", -1
    except subprocess.TimeoutExpired:
        return "", -2
    except Exception:
        return "", -3


def check_disk_space() -> CheckResult:
    """检查磁盘空间"""
    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_pct = (usage.used / usage.total) * 100

        if free_gb < 5:
            return CheckResult(
                name="Disk Space",
                status="error",
                message=f"Low disk space: {free_gb:.1f} GB free ({used_pct:.0f}% used)",
                details=f"Total: {total_gb:.1f} GB, Free: {free_gb:.1f} GB",
            )
        elif free_gb < 20:
            return CheckResult(
                name="Disk Space",
                status="warning",
                message=f"Disk space getting low: {free_gb:.1f} GB free ({used_pct:.0f}% used)",
                details=f"Total: {total_gb:.1f} GB, Free: {free_gb:.1f} GB",
            )
        else:
            return CheckResult(
                name="Disk Space",
                status="ok",
                message=f"{free_gb:.1f} GB free ({used_pct:.0f}% used)",
                details=f"Total: {total_gb:.1f} GB",
            )
    except Exception as e:
        return CheckResult(name="Disk Space", status="error", message=str(e))


def check_memory() -> CheckResult:
    """检查内存使用"""
    if platform.system() == "Darwin":
        output, code = run_cmd(["vm_stat"])
        if code == 0:
            # Parse vm_stat output
            lines = output.split("\n")
            free_pages = 0
            for line in lines:
                if "Pages free" in line:
                    try:
                        free_pages = int(line.split(".")[-1].strip().rstrip("."))
                    except ValueError:
                        pass

            # Get page size
            page_size_output, _ = run_cmd(["sysctl", "-n", "hw.pagesize"])
            try:
                page_size = int(page_size_output)
                free_mb = (free_pages * page_size) / (1024 ** 2)
            except ValueError:
                free_mb = 0

            if free_mb < 512:
                return CheckResult(
                    name="Memory",
                    status="warning",
                    message=f"Low available memory: ~{free_mb:.0f} MB",
                )
            else:
                return CheckResult(
                    name="Memory",
                    status="ok",
                    message=f"~{free_mb:.0f} MB available",
                )
    elif platform.system() == "Linux":
        output, code = run_cmd(["free", "-m"])
        if code == 0:
            lines = output.split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                try:
                    available = int(parts[6]) if len(parts) > 6 else int(parts[3])
                    if available < 512:
                        return CheckResult(
                            name="Memory", status="warning",
                            message=f"Low available memory: {available} MB",
                        )
                    else:
                        return CheckResult(
                            name="Memory", status="ok",
                            message=f"{available} MB available",
                        )
                except (ValueError, IndexError):
                    pass

    return CheckResult(name="Memory", status="info", message="Unable to determine")


def check_python() -> CheckResult:
    """检查 Python 环境"""
    output, code = run_cmd([sys.executable, "--version"])
    if code == 0:
        return CheckResult(name="Python", status="ok", message=output)
    return CheckResult(name="Python", status="error", message="Python not found")


def check_node() -> CheckResult:
    """检查 Node.js 环境"""
    output, code = run_cmd(["node", "--version"])
    if code == 0:
        return CheckResult(name="Node.js", status="ok", message=output)
    return CheckResult(name="Node.js", status="info", message="Node.js not installed")


def check_git() -> CheckResult:
    """检查 Git 状态"""
    output, code = run_cmd(["git", "--version"])
    if code != 0:
        return CheckResult(name="Git", status="error", message="Git not found")

    # Check if in a repo
    _, repo_code = run_git(["rev-parse", "--is-inside-work-tree"])
    if repo_code != 0:
        return CheckResult(name="Git", status="ok", message=f"{output} (not in repo)")

    # Check for uncommitted changes
    status_output, _ = run_git(["status", "--porcelain"])
    if status_output:
        file_count = len(status_output.strip().split("\n"))
        return CheckResult(
            name="Git", status="warning",
            message=f"{output}, {file_count} uncommitted changes",
        )

    return CheckResult(name="Git", status="ok", message=f"{output}, clean working tree")


def run_git(args: List[str]) -> Tuple[str, int]:
    """运行 git 命令"""
    return run_cmd(["git"] + args)


def check_liyu_home() -> CheckResult:
    """检查 鲤鱼 目录"""
    liyu_home = Path.home() / ".claude" / "liyu"
    if not liyu_home.exists():
        return CheckResult(name="鲤鱼 Home", status="error", message="Directory not found")

    # Count key files
    py_files = list(liyu_home.glob("*.py"))
    skills_dir = liyu_home / "skills"
    skills = list(skills_dir.glob("*.py")) if skills_dir.exists() else []

    return CheckResult(
        name="鲤鱼 Home",
        status="ok",
        message=f"{len(py_files)} scripts, {len(skills)} skills",
        details=str(liyu_home),
    )


def check_knowledge_base() -> CheckResult:
    """检查知识库状态"""
    db_path = Path.home() / ".claude" / "liyu" / "knowledge-base.db"
    if not db_path.exists():
        return CheckResult(name="Knowledge Base", status="info", message="Not initialized")

    size_mb = db_path.stat().st_size / (1024 ** 2)
    return CheckResult(
        name="Knowledge Base",
        status="ok",
        message=f"{size_mb:.1f} MB",
        details=str(db_path),
    )


def check_observability() -> CheckResult:
    """检查可观测性状态"""
    db_path = Path.home() / ".claude" / "liyu" / "observability.db"
    if not db_path.exists():
        return CheckResult(name="Observability", status="info", message="Not initialized")

    size_mb = db_path.stat().st_size / (1024 ** 2)
    return CheckResult(name="Observability", status="ok", message=f"{size_mb:.1f} MB")


def check_reflections() -> CheckResult:
    """检查反思引擎状态"""
    reflections_file = Path.home() / ".claude" / "liyu" / "reflections.jsonl"
    if not reflections_file.exists():
        return CheckResult(name="Reflections", status="info", message="No reflections yet")

    lines = reflections_file.read_text().strip().split("\n")
    count = len([l for l in lines if l.strip()])
    return CheckResult(name="Reflections", status="ok", message=f"{count} entries")


def check_debug_sessions() -> CheckResult:
    """检查调试会话"""
    sessions_file = Path.home() / ".claude" / "liyu" / "debug-sessions.jsonl"
    if not sessions_file.exists():
        return CheckResult(name="Debug Sessions", status="info", message="No sessions")

    try:
        lines = sessions_file.read_text().strip().split("\n")
        sessions = [json.loads(l) for l in lines if l.strip()]
        active = sum(1 for s in sessions if s.get("status") == "active")
        resolved = sum(1 for s in sessions if s.get("status") == "resolved")
        return CheckResult(
            name="Debug Sessions",
            status="ok",
            message=f"{active} active, {resolved} resolved",
        )
    except Exception:
        return CheckResult(name="Debug Sessions", status="warning", message="Parse error")


def run_all_checks(quick: bool = False) -> List[CheckResult]:
    """运行所有检查"""
    checks = [
        check_disk_space(),
        check_memory(),
        check_python(),
        check_git(),
        check_liyu_home(),
    ]

    if not quick:
        checks.extend([
            check_node(),
            check_knowledge_base(),
            check_observability(),
            check_reflections(),
            check_debug_sessions(),
        ])

    return checks


def print_report(checks: List[CheckResult], as_json: bool = False):
    """打印健康报告"""
    if as_json:
        output = {
            "system": platform.system(),
            "hostname": platform.node(),
            "checks": [c.to_dict() for c in checks],
            "summary": {
                "ok": sum(1 for c in checks if c.status == "ok"),
                "warning": sum(1 for c in checks if c.status == "warning"),
                "error": sum(1 for c in checks if c.status == "error"),
                "info": sum(1 for c in checks if c.status == "info"),
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    status_icons = {"ok": "OK", "warning": "WARN", "error": "ERR", "info": "INFO"}

    print(f"鲤鱼 Health Check — {platform.node()}")
    print("=" * 60)

    for check in checks:
        icon = status_icons.get(check.status, "?")
        print(f"  [{icon:4s}] {check.name}: {check.message}")
        if check.details:
            print(f"         {check.details}")

    print()
    ok = sum(1 for c in checks if c.status == "ok")
    warn = sum(1 for c in checks if c.status == "warning")
    err = sum(1 for c in checks if c.status == "error")
    print(f"Summary: {ok} OK, {warn} warnings, {err} errors")

    if err > 0:
        print("\nSome checks failed. Review the errors above.")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    quick = "quick" in args

    checks = run_all_checks(quick=quick)
    print_report(checks, as_json=as_json)

    if any(c.status == "error" for c in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
