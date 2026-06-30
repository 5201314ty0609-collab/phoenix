#!/bin/bash
# === 鲤鱼 AgentComplete Hook v1.0 ===
# 子 Agent 完成时触发，释放协调锁并记录完成状态
#
# 功能：
#   1. 释放协调锁
#   2. 记录完成状态
#   3. 更新 Agent 统计
#   4. 清理心跳文件
#
# 输入 (stdin): JSON with agent_id, status, result_summary, duration_seconds
# 输出: JSON with decision, reason, completion_info

set -euo pipefail

鲤鱼="$HOME/.claude/liyu"
COORD_DIR="/tmp/liyu-coordination"
HEARTBEAT_DIR="$鲤鱼/heartbeats"
AGENT_LOG="$鲤鱼/agent-lifecycle.jsonl"

# 读取输入
INPUT=$(cat)
AGENT_ID=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('agent_id', ''))" 2>/dev/null || echo "")
STATUS=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'completed'))" 2>/dev/null || echo "completed")
RESULT_SUMMARY=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result_summary', ''))" 2>/dev/null || echo "")
DURATION_SECONDS=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('duration_seconds', 0))" 2>/dev/null || echo "0")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 验证 Agent ID
if [ -z "$AGENT_ID" ]; then
    echo '{"decision":"allow","reason":"No agent_id provided, skipping","hookSpecificOutput":{"hookEventName":"AgentComplete","status":"skipped"}}'
    exit 0
fi

# 释放协调锁
release_coordination_lock() {
    local lock_file="$COORD_DIR/agent_locks/${AGENT_ID}.lock"

    if [ -f "$lock_file" ]; then
        # 记录锁信息后删除
        lock_info=$(cat "$lock_file")
        rm "$lock_file"
        echo "$lock_info"
    else
        echo "{}"
    fi
}

# 更新 Agent 注册表
update_agent_registry() {
    local lock_info="$1"

    python3 << PYEOF
import json
from datetime import datetime, timezone

registry_file = "$COORD_DIR/agent_registry.json"
try:
    with open(registry_file) as f:
        registry = json.load(f)
except:
    registry = {"agents": []}

agent_id = "$AGENT_ID"
status = "$STATUS"
result_summary = """$RESULT_SUMMARY"""
duration = $DURATION_SECONDS

# 查找并更新 Agent
for agent in registry["agents"]:
    if agent.get("agent_id") == agent_id:
        agent["status"] = status
        agent["completed_at"] = "$TIMESTAMP"
        agent["duration_seconds"] = duration
        agent["result_summary"] = result_summary[:200]
        break

with open(registry_file, "w") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

# 统计信息
active_agents = len([a for a in registry["agents"] if a.get("status") == "active"])
completed_agents = len([a for a in registry["agents"] if a.get("status") in ("completed", "failed")])

print(json.dumps({
    "status": "updated",
    "active_agents": active_agents,
    "completed_agents": completed_agents,
    "total_agents": len(registry["agents"])
}))
PYEOF
}

# 添加到完成日志
add_to_completion_log() {
    local lock_info="$1"
    local registry_stats="$2"

    local completed_log="$COORD_DIR/completed_work_log.json"

    if [ ! -f "$completed_log" ]; then
        echo '[]' > "$completed_log"
    fi

    python3 << PYEOF
import json

completed_log = "$completed_log"
try:
    with open(completed_log) as f:
        log = json.load(f)
except:
    log = []

agent_id = "$AGENT_ID"
status = "$STATUS"
result_summary = """$RESULT_SUMMARY"""
duration = $DURATION_SECONDS
lock_info = $lock_info
registry_stats = $registry_stats

entry = {
    "agent_id": agent_id,
    "status": status,
    "completed_at": "$TIMESTAMP",
    "duration_seconds": duration,
    "result_summary": result_summary[:200],
    "task_id": lock_info.get("task_id", "unknown"),
    "task_description": lock_info.get("task_description", "")[:100]
}

log.append(entry)

# 保留最近 100 条记录
if len(log) > 100:
    log = log[-100:]

with open(completed_log, "w") as f:
    json.dump(log, f, indent=2, ensure_ascii=False)

print(json.dumps({"status": "logged", "total_completions": len(log)}))
PYEOF
}

# 清理心跳文件
cleanup_heartbeat() {
    local heartbeat_file="$HEARTBEAT_DIR/${AGENT_ID}.heartbeat"

    if [ -f "$heartbeat_file" ]; then
        # 读取最后心跳信息
        last_heartbeat=$(cat "$heartbeat_file")
        rm "$heartbeat_file"
        echo "$last_heartbeat"
    else
        echo "{}"
    fi
}

# 记录 Agent 生命周期事件
log_agent_event() {
    local event_type="$1"
    local details="$2"

    cat >> "$AGENT_LOG" << EOF
{"timestamp":"$TIMESTAMP","agent_id":"$AGENT_ID","event":"$event_type","status":"$STATUS","duration_seconds":$DURATION_SECONDS,"details":$details}
EOF
}

# 计算执行统计
calculate_execution_stats() {
    python3 << PYEOF
import json

# 读取 Agent 注册信息
registry_file = "$COORD_DIR/agent_registry.json"
try:
    with open(registry_file) as f:
        registry = json.load(f)
except:
    registry = {"agents": []}

agent_id = "$AGENT_ID"
agent_info = None
for agent in registry["agents"]:
    if agent.get("agent_id") == agent_id:
        agent_info = agent
        break

if not agent_info:
    print(json.dumps({"error": "Agent not found"}))
    exit(0)

# 计算统计
started_at = agent_info.get("started_at", "")
completed_at = "$TIMESTAMP"
duration = $DURATION_SECONDS

# 状态统计
status = "$STATUS"
success = status == "completed"

stats = {
    "agent_id": agent_id,
    "agent_type": agent_info.get("agent_type", "unknown"),
    "agent_name": agent_info.get("agent_name", "unknown"),
    "started_at": started_at,
    "completed_at": completed_at,
    "duration_seconds": duration,
    "status": status,
    "success": success,
    "result_summary": """$RESULT_SUMMARY"""[:200],
    "task_id": agent_info.get("task_id", "unknown")
}

print(json.dumps(stats, ensure_ascii=False))
PYEOF
}

# 主流程
main() {
    # 释放协调锁
    lock_info=$(release_coordination_lock)

    # 更新 Agent 注册表
    registry_stats=$(update_agent_registry "$lock_info")

    # 添加到完成日志
    completion_log_result=$(add_to_completion_log "$lock_info" "$registry_stats")

    # 清理心跳文件
    last_heartbeat=$(cleanup_heartbeat)

    # 计算执行统计
    execution_stats=$(calculate_execution_stats)

    # 记录事件
    log_agent_event "complete" "$execution_stats"

    # 生成输出
    python3 << PYEOF
import json

agent_id = "$AGENT_ID"
status = "$STATUS"
result_summary = """$RESULT_SUMMARY"""
duration = $DURATION_SECONDS
execution_stats = $execution_stats
registry_stats = $registry_stats
completion_log_result = $completion_log_result

output = {
    "decision": "allow",
    "reason": f"Agent {agent_id} 已完成，状态: {status}，耗时: {duration}秒",
    "hookSpecificOutput": {
        "hookEventName": "AgentComplete",
        "agent_id": agent_id,
        "status": status,
        "duration_seconds": duration,
        "result_summary": result_summary[:200],
        "execution_stats": execution_stats,
        "coordination": {
            "active_agents": registry_stats.get("active_agents", 0),
            "completed_agents": registry_stats.get("completed_agents", 0),
            "total_completions": completion_log_result.get("total_completions", 0)
        },
        "success": status == "completed"
    }
}

print(json.dumps(output, ensure_ascii=False, indent=2))
PYEOF
}

main
