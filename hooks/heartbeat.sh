#!/bin/bash
# === PHOENIX Heartbeat v1.0 ===
# 写入心跳文件，用于 O2/Chronos 监测子 Agent 健康状态
# 参考: Dicklesworthstone/claude_code_agent_farm
#
# 用法: heartbeat.sh <agent_id> [status]
#   agent_id: 唯一标识 (如 "main", "sub-review-1")
#   status: working | idle | error (默认 working)

AGENT_ID="${1:-main}"
STATUS="${2:-working}"
HEARTBEAT_DIR="$HOME/.claude/phoenix/heartbeats"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

mkdir -p "$HEARTBEAT_DIR"

cat > "$HEARTBEAT_DIR/${AGENT_ID}.heartbeat" << EOF
{
  "agent_id": "$AGENT_ID",
  "status": "$STATUS",
  "timestamp": "$TIMESTAMP",
  "context_pct": "${PHOENIX_CTX_PCT:-unknown}"
}
EOF
