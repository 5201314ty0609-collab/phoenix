#!/usr/bin/env python3
"""
PHOENIX Auto-Ingest Hook — 自动将对话喂入 NexSandglass
Claude Code UserPromptSubmit / SessionEnd hook 触发

读取 stdin 的 hook JSON，提取用户消息，写入沙粒 + 检测决策粒子。
同时通知 SSE 服务器有新数据到达。

Usage (in settings.json hook):
  python3 ~/.claude/phoenix/hooks/auto-ingest.py
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import time

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
sys.path.insert(0, str(PHOENIX_HOME))

# ── Ingest ─────────────────────────────────────────────────────────────────

def ingest_user_message(session_id: str, content: str, turn_id: str = "",
                        user_id: str = "holyty-founder") -> dict:
    """将一条用户消息喂入 NexSandglass 四层引擎，并检查用户升级"""
    try:
        from nexsandglass import NexSandglass
        ns = NexSandglass()
        result = ns.ingest(session_id, "user", content, turn_id)
        total_grains = ns.writer.count()

        # 检查用户升级
        promotion = None
        try:
            from user_manager import UserManager
            mgr = UserManager()
            promo = mgr.check_promotion(user_id, total_grains)
            if promo.get("changed"):
                promotion = promo
        except ImportError:
            pass

        # 通知 SSE 服务器
        _notify_sse({
            "event": "sand_ingested",
            "session_id": session_id,
            "user_id": user_id,
            "grain_id": result[0] if result else "",
            "decisions": result[1:] if len(result) > 1 else [],
            "total_grains": total_grains,
            "promotion": promotion,
        })

        return {
            "status": "ok",
            "grain_id": result[0],
            "decisions": result[1:],
            "total_grains": total_grains,
            "promotion": promotion,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ingest_assistant_message(session_id: str, content: str, turn_id: str = "") -> dict:
    """将助手回复也写入沙粒（用于完整上下文，但不做决策检测）"""
    try:
        from nexsandglass import NexSandglass
        ns = NexSandglass()
        result = ns.ingest(session_id, "assistant", content, turn_id)
        return {"status": "ok", "grain_id": result[0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── SSE Notification ───────────────────────────────────────────────────────

def _notify_sse(event: dict):
    """通知 SSE 服务器有新事件"""
    sse_file = PHOENIX_HOME / "nexsandglass" / "sse-events.jsonl"
    try:
        sse_file.parent.mkdir(parents=True, exist_ok=True)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(sse_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        # No input = test mode
        print(json.dumps({"status": "ok", "mode": "test", "message": "auto-ingest ready"}))
        return

    session_id = hook_input.get("session_id", f"session-{int(time.time())}")
    event_type = hook_input.get("hook_event", "")
    content = hook_input.get("prompt", "") or hook_input.get("user_message", "")

    if not content:
        # Try extracting from tool_input if it's a PostToolUse hook
        ti = hook_input.get("tool_input", {})
        content = ti.get("content", "") or ti.get("prompt", "")

    if not content:
        print(json.dumps({"status": "skip", "reason": "no content"}))
        return

    result = ingest_user_message(session_id, content)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
