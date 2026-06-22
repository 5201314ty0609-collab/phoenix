#!/usr/bin/env python3
"""
PHOENIX Skill: PR Prep — Pull Request 准备工具。

自动生成 PR 描述、变更摘要、检查清单。

Usage:
  pr-prep.py summary                    生成当前分支的变更摘要
  pr-prep.py description [--base main]  生成 PR 描述
  pr-prep.py checklist                  生成 PR 检查清单
  pr-prep.py diff [--base main]         显示格式化的 diff 摘要
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re
import subprocess
import sys


def run_git(args: List[str], cwd: Optional[str] = None) -> Tuple[str, int]:
    """运行 git 命令"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True, cwd=cwd,
    )
    return result.stdout.strip(), result.returncode


def get_current_branch() -> str:
    """获取当前分支名"""
    output, code = run_git(["branch", "--show-current"])
    return output if code == 0 else "unknown"


def get_commits(base: str = "main") -> List[Dict]:
    """获取分支上的 commits"""
    output, code = run_git([
        "log", f"{base}..HEAD", "--pretty=format:%H|%s|%an|%ai", "--no-merges"
    ])
    if code != 0 or not output:
        return []

    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3],
            })
    return commits


def get_diff_stats(base: str = "main") -> Dict:
    """获取 diff 统计"""
    output, code = run_git(["diff", "--stat", f"{base}...HEAD"])
    if code != 0:
        return {"files": 0, "insertions": 0, "deletions": 0, "raw": ""}

    # Parse summary line: "X files changed, Y insertions(+), Z deletions(-)"
    summary_match = re.search(
        r'(\d+) files? changed(?:, (\d+) insertions?)?(?:, (\d+) deletions?)?',
        output
    )

    files = int(summary_match.group(1)) if summary_match else 0
    insertions = int(summary_match.group(2)) if summary_match and summary_match.group(2) else 0
    deletions = int(summary_match.group(3)) if summary_match and summary_match.group(3) else 0

    return {
        "files": files,
        "insertions": insertions,
        "deletions": deletions,
        "raw": output,
    }


def get_changed_files(base: str = "main") -> List[Dict]:
    """获取变更的文件列表"""
    output, code = run_git(["diff", "--name-status", f"{base}...HEAD"])
    if code != 0:
        return []

    files = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) >= 2:
            status = parts[0][0]  # A=added, M=modified, D=deleted, R=renamed
            path = parts[1]
            files.append({"status": status, "path": path})

    return files


def classify_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """分类 commits（conventional commits 格式）"""
    categories = {
        "feat": [],
        "fix": [],
        "refactor": [],
        "docs": [],
        "test": [],
        "chore": [],
        "perf": [],
        "ci": [],
        "other": [],
    }

    for commit in commits:
        subject = commit["subject"]
        matched = False
        for cat in categories:
            if subject.startswith(f"{cat}:") or subject.startswith(f"{cat}("):
                categories[cat].append(commit)
                matched = True
                break
        if not matched:
            categories["other"].append(commit)

    return {k: v for k, v in categories.items() if v}


def generate_summary(base: str = "main") -> str:
    """生成变更摘要"""
    branch = get_current_branch()
    commits = get_commits(base)
    stats = get_diff_stats(base)
    files = get_changed_files(base)

    lines = []
    lines.append(f"Branch: {branch}")
    lines.append(f"Base: {base}")
    lines.append(f"Commits: {len(commits)}")
    lines.append(f"Files changed: {stats['files']}")
    lines.append(f"Lines: +{stats['insertions']} / -{stats['deletions']}")
    lines.append("")

    # Classify commits
    categories = classify_commits(commits)

    lines.append("Changes by type:")
    for cat, cat_commits in categories.items():
        lines.append(f"  {cat}: {len(cat_commits)}")
        for c in cat_commits[:3]:
            lines.append(f"    - {c['subject']}")
        if len(cat_commits) > 3:
            lines.append(f"    ... and {len(cat_commits) - 3} more")

    # File breakdown
    if files:
        lines.append("")
        lines.append("File changes:")
        by_ext: Dict[str, int] = {}
        for f in files:
            ext = Path(f["path"]).suffix or "(no ext)"
            by_ext[ext] = by_ext.get(ext, 0) + 1
        for ext, count in sorted(by_ext.items(), key=lambda x: -x[1]):
            lines.append(f"  {ext}: {count} files")

    return "\n".join(lines)


def generate_description(base: str = "main") -> str:
    """生成 PR 描述"""
    branch = get_current_branch()
    commits = get_commits(base)
    stats = get_diff_stats(base)
    categories = classify_commits(commits)

    lines = []
    lines.append("## Summary")
    lines.append("")

    # Generate summary from commit types
    if "feat" in categories:
        lines.append("New features:")
        for c in categories["feat"]:
            lines.append(f"- {c['subject']}")
        lines.append("")

    if "fix" in categories:
        lines.append("Bug fixes:")
        for c in categories["fix"]:
            lines.append(f"- {c['subject']}")
        lines.append("")

    if "refactor" in categories:
        lines.append("Refactoring:")
        for c in categories["refactor"]:
            lines.append(f"- {c['subject']}")
        lines.append("")

    # Other changes
    other_cats = [k for k in categories if k not in ("feat", "fix", "refactor")]
    if other_cats:
        lines.append("Other changes:")
        for cat in other_cats:
            for c in categories[cat]:
                lines.append(f"- [{cat}] {c['subject']}")
        lines.append("")

    # Stats
    lines.append("## Changes")
    lines.append(f"- {stats['files']} files changed")
    lines.append(f"- +{stats['insertions']} / -{stats['deletions']} lines")
    lines.append(f"- {len(commits)} commits")
    lines.append("")

    # Checklist
    lines.append("## Checklist")
    lines.append("- [ ] Code follows project style guidelines")
    lines.append("- [ ] Self-review completed")
    lines.append("- [ ] Tests added/updated")
    lines.append("- [ ] Documentation updated (if needed)")
    lines.append("- [ ] No breaking changes (or documented)")
    lines.append("- [ ] Security considerations reviewed")
    lines.append("")

    # Testing
    lines.append("## Testing")
    lines.append("Describe the tests you ran:")
    lines.append("- [ ] Unit tests pass")
    lines.append("- [ ] Integration tests pass (if applicable)")
    lines.append("- [ ] Manual testing performed")
    lines.append("")

    return "\n".join(lines)


def generate_checklist() -> str:
    """生成 PR 检查清单"""
    files = get_changed_files()
    stats = get_diff_stats()

    lines = []
    lines.append("PR Checklist")
    lines.append("=" * 40)
    lines.append("")

    # Auto-detect what checks to include
    has_python = any(f["path"].endswith(".py") for f in files)
    has_ts_js = any(f["path"].endswith((".ts", ".tsx", ".js", ".jsx")) for f in files)
    has_tests = any("test" in f["path"].lower() or "spec" in f["path"].lower() for f in files)
    has_docs = any(f["path"].endswith(".md") for f in files)
    has_config = any(f["path"].endswith((".yml", ".yaml", ".toml", ".json")) for f in files)
    has_css = any(f["path"].endswith((".css", ".scss", ".less")) for f in files)

    lines.append("General:")
    lines.append("- [ ] Branch is up to date with target")
    lines.append("- [ ] No merge conflicts")
    lines.append("- [ ] Commit messages follow conventional format")
    lines.append("")

    if has_python:
        lines.append("Python:")
        lines.append("- [ ] `ruff check` / `flake8` passes")
        lines.append("- [ ] `mypy` type check passes")
        lines.append("- [ ] `pytest` passes")
        lines.append("")

    if has_ts_js:
        lines.append("TypeScript/JavaScript:")
        lines.append("- [ ] `eslint` passes")
        lines.append("- [ ] `tsc --noEmit` passes")
        lines.append("- [ ] `jest` / `vitest` passes")
        lines.append("")

    if has_css:
        lines.append("CSS:")
        lines.append("- [ ] `stylelint` passes")
        lines.append("- [ ] No layout shifts")
        lines.append("")

    if has_tests:
        lines.append("Testing:")
        lines.append("- [ ] New tests cover edge cases")
        lines.append("- [ ] Coverage meets minimum (80%)")
        lines.append("")

    if has_docs:
        lines.append("Documentation:")
        lines.append("- [ ] Links are valid")
        lines.append("- [ ] Formatting is correct")
        lines.append("")

    if has_config:
        lines.append("Configuration:")
        lines.append("- [ ] No secrets in config files")
        lines.append("- [ ] Schema validation passes")
        lines.append("")

    # Security check (always)
    lines.append("Security:")
    lines.append("- [ ] No hardcoded secrets")
    lines.append("- [ ] Input validation present")
    lines.append("- [ ] Error messages don't leak info")
    lines.append("")

    lines.append(f"Changed files: {len(files)}")
    lines.append(f"Lines: +{stats['insertions']} / -{stats['deletions']}")

    return "\n".join(lines)


def print_diff_summary(base: str = "main"):
    """打印 diff 摘要"""
    stats = get_diff_stats(base)
    files = get_changed_files(base)

    print("Diff Summary")
    print("=" * 60)
    print(f"Files: {stats['files']}")
    print(f"Lines: +{stats['insertions']} / -{stats['deletions']}")
    print()

    # Group by status
    added = [f for f in files if f["status"] == "A"]
    modified = [f for f in files if f["status"] == "M"]
    deleted = [f for f in files if f["status"] == "D"]

    if added:
        print(f"Added ({len(added)}):")
        for f in added:
            print(f"  + {f['path']}")
        print()

    if modified:
        print(f"Modified ({len(modified)}):")
        for f in modified:
            print(f"  ~ {f['path']}")
        print()

    if deleted:
        print(f"Deleted ({len(deleted)}):")
        for f in deleted:
            print(f"  - {f['path']}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    # Parse --base flag
    base = "main"
    for i, arg in enumerate(sys.argv):
        if arg == "--base" and i + 1 < len(sys.argv):
            base = sys.argv[i + 1]

    if cmd == "summary":
        print(generate_summary(base))

    elif cmd == "description":
        print(generate_description(base))

    elif cmd == "checklist":
        print(generate_checklist())

    elif cmd == "diff":
        print_diff_summary(base)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
