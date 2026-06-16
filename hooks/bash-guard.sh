#!/bin/bash
# === PHOENIX Bash Guard — PreToolUse Hook v1.0 ===
# 吸收自 Kintsugi (github.com/arrowassassin/kintsugi) AST-level safety gate
#
# 在每次 Bash 工具调用前拦截并分类:
#   SAFE (exit 0)  — 只读/安全命令，放行
#   CAUTION (exit 0) — 有风险但非立即破坏，警告但放行
#   DANGER (exit 2) — 立即破坏性，阻断
#
# 集成 Nociception (痛觉): 重复危险尝试自动 CAUTION→DANGER 升级
#
# Claude Code hook 协议:
#   stdin:  {"tool_name": "Bash", "tool_input": {"command": "..."}}
#   stdout: {"decision": "...", "reason": "...", "hookSpecificOutput": {...}}
#   exit 0: allow | exit 2: block
#
# Usage in settings.json:
#   {
#     "matcher": "Bash",
#     "hooks": [{
#       "type": "command",
#       "command": "/Users/holyty/.claude/phoenix/hooks/bash-guard.sh"
#     }]
#   }

set -euo pipefail

GUARD_PY="$HOME/.claude/phoenix/phoenix-bash-guard.py"

# Ensure the Python module exists
if [ ! -f "$GUARD_PY" ]; then
    echo '{"decision":"allow","reason":"bash-guard: guard module not found, allowing","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
    exit 0
fi

# Delegate to Python guard module
exec python3 "$GUARD_PY" hook-pre
