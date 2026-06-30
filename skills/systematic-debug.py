#!/usr/bin/env python3
"""
鲤鱼 Skill: Systematic Debug — 4 阶段根因调试。

系统化调试流程：
1. 重现问题
2. 缩小范围
3. 提出假设
4. 验证修复

Usage:
  systematic-debug.py start <problem>      开始调试会话
  systematic-debug.py note <observation>   记录观察
  systematic-debug.py hypothesis <theory>  提出假设
  systematic-debug.py verify <test>        验证假设
  systematic-debug.py resolve <solution>   解决问题
  systematic-debug.py list                 列出调试会话
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json
import sys
import uuid

鲤鱼_HOME = Path.home() / ".claude/liyu"
DEBUG_SESSIONS_FILE = 鲤鱼_HOME / "debug-sessions.jsonl"


def load_sessions() -> List[Dict]:
    """加载调试会话"""
    if not DEBUG_SESSIONS_FILE.exists():
        return []

    sessions = []
    for line in DEBUG_SESSIONS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                sessions.append(json.loads(line))
            except Exception:
                pass
    return sessions


def save_session(session: Dict):
    """保存调试会话"""
    with open(DEBUG_SESSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(session, ensure_ascii=False) + "\n")


def start_session(problem: str) -> str:
    """开始调试会话"""
    session_id = f"debug-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    session = {
        "session_id": session_id,
        "problem": problem,
        "started_at": now,
        "status": "active",
        "phase": "reproduce",
        "observations": [],
        "hypotheses": [],
        "verifications": [],
        "solution": None,
    }

    save_session(session)

    print(f"Debug session started: {session_id}")
    print(f"Problem: {problem}")
    print()
    print("Phase 1: REPRODUCE")
    print("  Goal: Understand and reproduce the problem")
    print("  Actions:")
    print("    - Run the failing command")
    print("    - Capture error messages")
    print("    - Identify conditions that trigger the issue")

    return session_id


def add_observation(session_id: str, observation: str):
    """记录观察"""
    sessions = load_sessions()

    for session in sessions:
        if session["session_id"] == session_id:
            now = datetime.now(timezone.utc).isoformat()
            session["observations"].append({
                "timestamp": now,
                "note": observation,
            })

            # 更新阶段
            if len(session["observations"]) >= 2 and session["phase"] == "reproduce":
                session["phase"] = "isolate"
                print(f"\nPhase 2: ISOLATE")
                print(f"  Goal: Narrow down the root cause")
                print(f"  Observations so far: {len(session['observations'])}")

            # 重新保存所有会话
            _rewrite_sessions(sessions)

            print(f"Observation recorded: {observation}")
            return

    print(f"Session not found: {session_id}")


def add_hypothesis(session_id: str, hypothesis: str):
    """提出假设"""
    sessions = load_sessions()

    for session in sessions:
        if session["session_id"] == session_id:
            now = datetime.now(timezone.utc).isoformat()
            session["hypotheses"].append({
                "timestamp": now,
                "theory": hypothesis,
                "verified": None,
            })

            if session["phase"] == "isolate":
                session["phase"] = "hypothesize"
                print(f"\nPhase 3: HYPOTHESIZE")
                print(f"  Goal: Form testable theories")
                print(f"  Hypotheses: {len(session['hypotheses'])}")

            _rewrite_sessions(sessions)

            print(f"Hypothesis recorded: {hypothesis}")
            return

    print(f"Session not found: {session_id}")


def verify_hypothesis(session_id: str, test: str, result: str = ""):
    """验证假设"""
    sessions = load_sessions()

    for session in sessions:
        if session["session_id"] == session_id:
            now = datetime.now(timezone.utc).isoformat()
            session["verifications"].append({
                "timestamp": now,
                "test": test,
                "result": result,
            })

            if session["phase"] == "hypothesize":
                session["phase"] = "verify"
                print(f"\nPhase 4: VERIFY")
                print(f"  Goal: Confirm the root cause")
                print(f"  Verifications: {len(session['verifications'])}")

            _rewrite_sessions(sessions)

            print(f"Verification recorded: {test}")
            if result:
                print(f"Result: {result}")
            return

    print(f"Session not found: {session_id}")


def resolve(session_id: str, solution: str):
    """解决问题"""
    sessions = load_sessions()

    for session in sessions:
        if session["session_id"] == session_id:
            now = datetime.now(timezone.utc).isoformat()
            session["solution"] = {
                "timestamp": now,
                "description": solution,
            }
            session["status"] = "resolved"
            session["finished_at"] = now

            _rewrite_sessions(sessions)

            print(f"\n{'=' * 60}")
            print(f"Problem RESOLVED: {session['problem']}")
            print(f"{'=' * 60}")
            print(f"Solution: {solution}")
            print(f"Observations: {len(session['observations'])}")
            print(f"Hypotheses: {len(session['hypotheses'])}")
            print(f"Verifications: {len(session['verifications'])}")
            print(f"{'=' * 60}")

            return

    print(f"Session not found: {session_id}")


def list_sessions():
    """列出调试会话"""
    sessions = load_sessions()

    if not sessions:
        print("No debug sessions recorded.")
        return

    active = [s for s in sessions if s["status"] == "active"]
    resolved = [s for s in sessions if s["status"] == "resolved"]

    print(f"Debug Sessions: {len(active)} active, {len(resolved)} resolved")
    print()

    if active:
        print("Active:")
        for session in active:
            print(f"  [{session['session_id']}] {session['problem']}")
            print(f"    Phase: {session['phase']}")
            print(f"    Observations: {len(session['observations'])}")
            print()

    if resolved:
        print("Recently Resolved:")
        for session in resolved[-5:]:
            print(f"  [{session['session_id']}] {session['problem']}")
            if session.get("solution"):
                print(f"    Solution: {session['solution']['description'][:80]}")
            print()


def _rewrite_sessions(sessions: List[Dict]):
    """重写所有会话（用于更新）"""
    with open(DEBUG_SESSIONS_FILE, "w", encoding="utf-8") as f:
        for session in sessions:
            f.write(json.dumps(session, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "start":
        if len(sys.argv) < 3:
            print("Usage: systematic-debug.py start <problem>")
            return
        problem = " ".join(sys.argv[2:])
        start_session(problem)

    elif cmd == "note":
        if len(sys.argv) < 4:
            print("Usage: systematic-debug.py note <session_id> <observation>")
            return
        session_id = sys.argv[2]
        observation = " ".join(sys.argv[3:])
        add_observation(session_id, observation)

    elif cmd == "hypothesis":
        if len(sys.argv) < 4:
            print("Usage: systematic-debug.py hypothesis <session_id> <theory>")
            return
        session_id = sys.argv[2]
        hypothesis = " ".join(sys.argv[3:])
        add_hypothesis(session_id, hypothesis)

    elif cmd == "verify":
        if len(sys.argv) < 4:
            print("Usage: systematic-debug.py verify <session_id> <test> [result]")
            return
        session_id = sys.argv[2]
        test = sys.argv[3]
        result = sys.argv[4] if len(sys.argv) > 4 else ""
        verify_hypothesis(session_id, test, result)

    elif cmd == "resolve":
        if len(sys.argv) < 4:
            print("Usage: systematic-debug.py resolve <session_id> <solution>")
            return
        session_id = sys.argv[2]
        solution = " ".join(sys.argv[3:])
        resolve(session_id, solution)

    elif cmd == "list":
        list_sessions()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
