#!/bin/bash
# === PHOENIX ContextCompaction Hook v1.0 ===
# 上下文压缩时触发，保存关键状态并生成压缩摘要
#
# 功能：
#   1. 保存当前状态到文件系统
#   2. 记录压缩前的关键信息
#   3. 更新 O2 指标
#   4. 生成压缩摘要
#
# 输入 (stdin): JSON with session_id, context_usage, message_count, compression_type
# 输出: JSON with decision, reason, compaction_summary

set -euo pipefail

PHOENIX="$HOME/.claude/phoenix"
SENSES_DIR="$PHOENIX/senses"
COMPACTION_LOG="$PHOENIX/compaction-log.jsonl"

# 读取输入
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
CONTEXT_USAGE=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('context_usage', 0))" 2>/dev/null || echo "0")
MESSAGE_COUNT=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message_count', 0))" 2>/dev/null || echo "0")
COMPRESSION_TYPE=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('compression_type', 'auto'))" 2>/dev/null || echo "auto")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 保存当前状态
save_current_state() {
    local state_file="$PHOENIX/session-state.json"

    python3 << PYEOF
import json
from datetime import datetime, timezone

state_file = "$state_file"
try:
    with open(state_file) as f:
        state = json.load(f)
except:
    state = {"current": {"active_concerns": [], "open_threads": [], "mood": "正常", "session_count": 0}}

# 更新压缩信息
state["last_compaction"] = {
    "timestamp": "$TIMESTAMP",
    "session_id": "$SESSION_ID",
    "context_usage": $CONTEXT_USAGE,
    "message_count": $MESSAGE_COUNT,
    "compression_type": "$COMPRESSION_TYPE"
}

state["updated_at"] = datetime.now(timezone.utc).isoformat()

with open(state_file, "w") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(json.dumps({"status": "saved", "state_keys": list(state.keys())}))
PYEOF
}

# 更新 O2 指标
update_o2_metrics() {
    local o2_file="$SENSES_DIR/o2.json"

    if [ ! -f "$o2_file" ]; then
        echo '{"trace_event":"token_pressure","status":"normal","metrics":{"usage_percent":0}}' > "$o2_file"
    fi

    python3 << PYEOF
import json
from datetime import datetime, timezone

o2_file = "$o2_file"
try:
    with open(o2_file) as f:
        data = json.load(f)
except:
    data = {"trace_event": "token_pressure", "status": "normal", "metrics": {"usage_percent": 0}}

# 更新指标
data["metrics"]["usage_percent"] = $CONTEXT_USAGE
data["metrics"]["message_count"] = $MESSAGE_COUNT
data["last_updated"] = datetime.now(timezone.utc).isoformat()
data["last_compaction"] = "$TIMESTAMP"

# 更新状态
if $CONTEXT_USAGE >= 85:
    data["status"] = "critical"
    data["recommendation"] = "immediate_compaction"
elif $CONTEXT_USAGE >= 70:
    data["status"] = "warning"
    data["recommendation"] = "consider_compaction"
else:
    data["status"] = "normal"
    data["recommendation"] = "continue"

with open(o2_file, "w") as f:
    json.dump(data, f, indent=2)

print(json.dumps({"status": data["status"], "usage_percent": $CONTEXT_USAGE}))
PYEOF
}

# 生成压缩摘要
generate_compaction_summary() {
    python3 << PYEOF
import json

# 读取最近的工具调用历史
try:
    with open("$PHOENIX/tool-guard-history.jsonl") as f:
        lines = f.readlines()[-10:]  # 最近 10 条
        recent_tools = []
        for line in lines:
            try:
                entry = json.loads(line)
                recent_tools.append(entry.get("tool", "unknown"))
            except:
                pass
except:
    recent_tools = []

# 统计工具使用
tool_counts = {}
for tool in recent_tools:
    tool_counts[tool] = tool_counts.get(tool, 0) + 1

summary = {
    "compression_type": "$COMPRESSION_TYPE",
    "context_usage_before": $CONTEXT_USAGE,
    "message_count": $MESSAGE_COUNT,
    "recent_tools": tool_counts,
    "recommendations": []
}

# 生成建议
if $CONTEXT_USAGE > 80:
    summary["recommendations"].append("考虑减少工具调用频率")
    summary["recommendations"].append("使用脚本替代多次工具调用")

if $MESSAGE_COUNT > 50:
    summary["recommendations"].append("会话消息较多，考虑开启新会话")

if len(tool_counts) > 5:
    summary["recommendations"].append("工具使用多样化，检查是否有冗余调用")

print(json.dumps(summary, ensure_ascii=False))
PYEOF
}

# 记录压缩日志
log_compaction() {
    local summary="$1"
    cat >> "$COMPACTION_LOG" << EOF
{"timestamp":"$TIMESTAMP","session_id":"$SESSION_ID","context_usage":$CONTEXT_USAGE,"message_count":$MESSAGE_COUNT,"compression_type":"$COMPRESSION_TYPE","summary":$summary}
EOF
}

# 主流程
main() {
    # 保存当前状态
    state_result=$(save_current_state)

    # 更新 O2 指标
    o2_result=$(update_o2_metrics)

    # 生成压缩摘要
    summary=$(generate_compaction_summary)

    # 记录日志
    log_compaction "$summary"

    # 生成输出
    python3 << PYEOF
import json

session_id = "$SESSION_ID"
context_usage = $CONTEXT_USAGE
message_count = $MESSAGE_COUNT
compression_type = "$COMPRESSION_TYPE"
summary = $summary
o2_result = $o2_result

output = {
    "decision": "allow",
    "reason": f"上下文压缩: {context_usage}% 使用率, {message_count} 条消息",
    "hookSpecificOutput": {
        "hookEventName": "ContextCompaction",
        "session_id": session_id,
        "context_usage": context_usage,
        "message_count": message_count,
        "compression_type": compression_type,
        "compaction_summary": summary,
        "o2_status": o2_result.get("status", "unknown"),
        "recommendations": summary.get("recommendations", [])
    }
}

print(json.dumps(output, ensure_ascii=False, indent=2))
PYEOF
}

main
