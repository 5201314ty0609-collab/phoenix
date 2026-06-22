#!/bin/bash
# === PHOENIX AgentSpawn Hook v1.0 ===
# 子 Agent 启动时触发，注册 Agent 并初始化协调
#
# 功能：
#   1. 注册 Agent 到协调系统
#   2. 写入心跳文件
#   3. 分配 Agent ID
#   4. 记录启动时间
#
# 输入 (stdin): JSON with agent_type, agent_name, task_description, parent_agent
# 输出: JSON with decision, reason, agent_id, coordination_info

set -euo pipefail

PHOENIX="$HOME/.claude/phoenix"
COORD_DIR="/tmp/phoenix-coordination"
HEARTBEAT_DIR="$PHOENIX/heartbeats"
AGENT_LOG="$PHOENIX/agent-lifecycle.jsonl"

# 读取输入
INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('agent_type', 'specialist'))" 2>/dev/null || echo "specialist")
AGENT_NAME=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('agent_name', 'unnamed'))" 2>/dev/null || echo "unnamed")
TASK_DESC=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_description', ''))" 2>/dev/null || echo "")
PARENT_AGENT=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('parent_agent', 'main'))" 2>/dev/null || echo "main")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
AGENT_ID="agent_$(date +%s)_$$"

# 初始化协调目录
init_coordination() {
    mkdir -p "$COORD_DIR"/{agent_locks,completed,agents}

    # 确保注册文件存在
    if [ ! -f "$COORD_DIR/agent_registry.json" ]; then
        echo '{"agents":[]}' > "$COORD_DIR/agent_registry.json"
    fi
}

# 注册 Agent
register_agent() {
    python3 << PYEOF
import json
from datetime import datetime, timezone

registry_file = "$COORD_DIR/agent_registry.json"
try:
    with open(registry_file) as f:
        registry = json.load(f)
except:
    registry = {"agents": []}

# 检查是否已注册
agent_id = "$AGENT_ID"
for agent in registry["agents"]:
    if agent.get("agent_id") == agent_id:
        print(json.dumps({"status": "already_registered", "agent_id": agent_id}))
        exit(0)

# 注册新 Agent
new_agent = {
    "agent_id": agent_id,
    "agent_type": "$AGENT_TYPE",
    "agent_name": "$AGENT_NAME",
    "task_description": """$TASK_DESC""",
    "parent_agent": "$PARENT_AGENT",
    "status": "active",
    "started_at": "$TIMESTAMP",
    "last_heartbeat": "$TIMESTAMP"
}

registry["agents"].append(new_agent)

with open(registry_file, "w") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print(json.dumps({"status": "registered", "agent_id": agent_id, "total_agents": len(registry["agents"])}))
PYEOF
}

# 写入心跳文件
write_heartbeat() {
    mkdir -p "$HEARTBEAT_DIR"

    cat > "$HEARTBEAT_DIR/${AGENT_ID}.heartbeat" << EOF
{
  "agent_id": "$AGENT_ID",
  "agent_type": "$AGENT_TYPE",
  "agent_name": "$AGENT_NAME",
  "status": "active",
  "started_at": "$TIMESTAMP",
  "timestamp": "$TIMESTAMP",
  "parent_agent": "$PARENT_AGENT",
  "task_description": "$(echo "$TASK_DESC" | head -c 100)"
}
EOF
}

# 创建协调锁
create_coordination_lock() {
    if [ ! -d "$COORD_DIR/agent_locks" ]; then
        mkdir -p "$COORD_DIR/agent_locks"
    fi

    # 生成任务 ID
    TASK_ID="task_$(date +%s)"

    cat > "$COORD_DIR/agent_locks/${AGENT_ID}.lock" << EOF
{
  "agent_id": "$AGENT_ID",
  "task_id": "$TASK_ID",
  "task_description": """$TASK_DESC""",
  "acquired_at": "$TIMESTAMP",
  "expires_at": "$(date -u -v+2H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "active"
}
EOF

    echo "$TASK_ID"
}

# 记录 Agent 生命周期事件
log_agent_event() {
    local event_type="$1"
    local details="$2"

    cat >> "$AGENT_LOG" << EOF
{"timestamp":"$TIMESTAMP","agent_id":"$AGENT_ID","event":"$event_type","agent_type":"$AGENT_TYPE","agent_name":"$AGENT_NAME","parent_agent":"$PARENT_AGENT","details":$details}
EOF
}

# 主流程
main() {
    # 初始化协调
    init_coordination

    # 注册 Agent
    register_result=$(register_agent)

    # 写入心跳
    write_heartbeat

    # 创建协调锁
    task_id=$(create_coordination_lock)

    # 记录事件
    log_agent_event "spawn" "{\"task_id\":\"$task_id\",\"register_result\":$register_result}"

    # 生成输出
    python3 << PYEOF
import json

agent_id = "$AGENT_ID"
agent_type = "$AGENT_TYPE"
agent_name = "$AGENT_NAME"
task_desc = """$TASK_DESC"""
parent_agent = "$PARENT_AGENT"
task_id = "$task_id"
register_result = $register_result

output = {
    "decision": "allow",
    "reason": f"Agent {agent_name} 已启动，任务 ID: {task_id}",
    "hookSpecificOutput": {
        "hookEventName": "AgentSpawn",
        "agent_id": agent_id,
        "agent_type": agent_type,
        "agent_name": agent_name,
        "task_id": task_id,
        "parent_agent": parent_agent,
        "task_description": task_desc[:200],
        "coordination": {
            "heartbeat_file": "$HEARTBEAT_DIR/${agent_id}.heartbeat",
            "lock_file": "$COORD_DIR/agent_locks/${agent_id}.lock",
            "registry_file": "$COORD_DIR/agent_registry.json"
        },
        "register_status": register_result.get("status", "unknown"),
        "total_agents": register_result.get("total_agents", 0)
    }
}

print(json.dumps(output, ensure_ascii=False, indent=2))
PYEOF
}

main
