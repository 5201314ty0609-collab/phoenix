#!/bin/bash
# 鲤鱼 NexSandglass — SessionStart 记忆注入
# 每次会话开始时，用 NexSandglass 蒸馏上下文替代 MEMORY.md 全量加载
# 目标: <300 tokens vs 原 8,000+ tokens

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
鲤鱼_HOME="$HOME/.claude/liyu"
CONTEXT_FILE="$鲤鱼_HOME/nexsandglass/session-context.md"

# Generate hybrid context
python3 "$鲤鱼_HOME/nexsandglass.py" hybrid > "$CONTEXT_FILE" 2>/dev/null || true

# Output for Claude Code session context
if [ -f "$CONTEXT_FILE" ]; then
    cat "$CONTEXT_FILE"
fi
