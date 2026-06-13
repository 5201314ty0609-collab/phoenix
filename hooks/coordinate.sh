#!/bin/bash
# === PHOENIX Coordinate v1.0 ===
# Prompt-as-Code 多 Agent 协调系统
# Agent 通过文件系统自组织，无需中央协调器
# 参考: Dicklesworthstone/claude_code_agent_farm
#
# 用法:
#   coordinate.sh init                    初始化协调目录
#   coordinate.sh claim <id> <desc>       声明工作（检查冲突→加锁→注册）
#   coordinate.sh release <id>            释放声明
#   coordinate.sh complete <id>           标记完成（移到完成日志）
#   coordinate.sh status                  查看协调状态
#   coordinate.sh cleanup                 清理过期锁（>2h）

set -euo pipefail
shopt -s nullglob

COORD_DIR="${PHOENIX_COORD_DIR:-/tmp/phoenix-coordination}"
AGENT_ID="${PHOENIX_AGENT_ID:-agent_$(date +%s)_$$}"
STALE_THRESHOLD_SEC=7200  # 2小时

init() {
    mkdir -p "$COORD_DIR"/{agent_locks,completed}
    echo "{\"created_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"agents\":[]}" > "$COORD_DIR/active_work_registry.json"
    echo "[]" > "$COORD_DIR/completed_work_log.json"
    echo "[]" > "$COORD_DIR/planned_work_queue.json"
    echo "PHOENIX 协调目录已初始化: $COORD_DIR"
}

_timestamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

_check_conflict() {
    local work_id="$1"
    # 检查是否有其他 agent 声明了相同的工作
    for lock in "$COORD_DIR/agent_locks/"*.lock; do
        [ -f "$lock" ] || continue
        local locked_id=$(python3 -c "import json; print(json.load(open('$lock')).get('work_id',''))" 2>/dev/null || echo "")
        if [ "$locked_id" = "$work_id" ]; then
            local lock_age=$(($(date +%s) - $(stat -f %m "$lock" 2>/dev/null || echo 0)))
            if [ "$lock_age" -lt "$STALE_THRESHOLD_SEC" ]; then
                return 0  # 冲突存在
            fi
        fi
    done
    return 1  # 无冲突
}

claim() {
    local work_id="${1:-}"
    local description="${2:-}"
    [ -z "$work_id" ] && { echo "用法: coordinate.sh claim <work-id> <description>"; exit 1; }

    init 2>/dev/null  # 确保目录存在

    if _check_conflict "$work_id"; then
        echo "❌ 冲突: '$work_id' 已被其他 Agent 声明"
        return 1
    fi

    # 创建锁文件
    local lock_file="$COORD_DIR/agent_locks/${AGENT_ID}_$(date +%s).lock"
    cat > "$lock_file" << EOF
{
    "agent_id": "$AGENT_ID",
    "work_id": "$work_id",
    "description": "$description",
    "claimed_at": "$(_timestamp)",
    "status": "working"
}
EOF

    # 更新注册表
    local reg_file="$COORD_DIR/active_work_registry.json"
    local ts=$(_timestamp)
    python3 -c "
import json
reg = json.load(open('$reg_file'))
reg['agents'].append({
    'agent_id': '$AGENT_ID', 'work_id': '$work_id', 'description': '$description',
    'started_at': '$ts', 'lock_file': '$lock_file'
})
json.dump(reg, open('$reg_file', 'w'), indent=2, ensure_ascii=False)
"

    echo "✅ Agent '$AGENT_ID' 已声明: $work_id — $description"
}

release() {
    local work_id="${1:-}"
    [ -z "$work_id" ] && { echo "用法: coordinate.sh release <work-id>"; exit 1; }

    for lock in "$COORD_DIR/agent_locks/"*.lock; do
        [ -f "$lock" ] || continue
        local lid=$(python3 -c "import json; print(json.load(open('$lock')).get('work_id',''))" 2>/dev/null || echo "")
        if [ "$lid" = "$work_id" ]; then
            rm "$lock"
            echo "🔓 已释放: $work_id"
            return 0
        fi
    done
    echo "⚠️  未找到 '$work_id' 的锁"
}

complete() {
    local work_id="${1:-}"
    [ -z "$work_id" ] && { echo "用法: coordinate.sh complete <work-id>"; exit 1; }

    # 移除锁
    release "$work_id" 2>/dev/null

    # 添加到完成日志
    local log_file="$COORD_DIR/completed_work_log.json"
    local ts=$(_timestamp)
    python3 -c "
import json
log = json.load(open('$log_file'))
log.append({'work_id': '$work_id', 'agent_id': '$AGENT_ID', 'completed_at': '$ts'})
json.dump(log, open('$log_file', 'w'), indent=2, ensure_ascii=False)
"

    echo "✅ 已完成: $work_id"
}

status() {
    echo "=== PHOENIX 协调状态 ==="
    echo "目录: $COORD_DIR"
    echo ""

    # 活跃锁
    echo "🔒 活跃锁:"
    local lock_count=0
    for lock in "$COORD_DIR/agent_locks/"*.lock; do
        [ -f "$lock" ] || continue
        lock_count=$((lock_count + 1))
        python3 -c "
import json, time, os
d = json.load(open('$lock'))
age = int(time.time() - os.path.getmtime('$lock'))
print(f\"  [{d['agent_id']}] {d['work_id']} — {d.get('description','?')} ({age}s ago)\")
"
    done
    [ "$lock_count" -eq 0 ] && echo "  (无)"

    # 完成日志
    echo ""
    echo "✅ 最近完成:"
    python3 -c "
import json
log = json.load(open('$COORD_DIR/completed_work_log.json'))
for entry in log[-5:]:
    print(f\"  [{entry['agent_id']}] {entry['work_id']} @ {entry['completed_at'][:19]}\")
" 2>/dev/null || echo "  (无)"

    # 待处理队列
    echo ""
    echo "📋 待处理:"
    python3 -c "
import json
queue = json.load(open('$COORD_DIR/planned_work_queue.json'))
for item in queue[-5:]:
    print(f\"  - {item.get('id','?')}: {item.get('desc','?')}\")
" 2>/dev/null || echo "  (无)"
}

cleanup() {
    local cleaned=0
    for lock in "$COORD_DIR/agent_locks/"*.lock; do
        [ -f "$lock" ] || continue
        local age=$(($(date +%s) - $(stat -f %m "$lock" 2>/dev/null || echo 0)))
        if [ "$age" -gt "$STALE_THRESHOLD_SEC" ]; then
            local wid=$(python3 -c "import json; print(json.load(open('$lock')).get('work_id','?'))" 2>/dev/null || echo "?")
            rm "$lock"
            echo "🧹 清理过期锁: $wid (${age}s 未活动)"
            cleaned=$((cleaned + 1))
        fi
    done
    [ "$cleaned" -eq 0 ] && echo "无过期锁需要清理"
}

# --- 主入口 ---
case "${1:-}" in
    init)     init ;;
    claim)    claim "${2:-}" "${3:-}" ;;
    release)  release "${2:-}" ;;
    complete) complete "${2:-}" ;;
    status)   status ;;
    cleanup)  cleanup ;;
    *)
        echo "PHOENIX Coordinate v1.0 — Prompt-as-Code 多 Agent 协调"
        echo ""
        echo "用法: coordinate.sh {init|claim|release|complete|status|cleanup}"
        echo ""
        echo "  init              初始化协调目录"
        echo "  claim <id> <desc> 声明工作（自动检测冲突+加锁）"
        echo "  release <id>      释放声明"
        echo "  complete <id>     标记完成"
        echo "  status            查看协调状态"
        echo "  cleanup           清理过期锁（>2h）"
        echo ""
        echo "环境变量:"
        echo "  PHOENIX_COORD_DIR  协调目录 (默认 /tmp/phoenix-coordination)"
        echo "  PHOENIX_AGENT_ID   Agent 标识 (默认自动生成)"
        ;;
esac
