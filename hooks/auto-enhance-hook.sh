#!/bin/bash
# 鲤鱼 Auto-Enhance Hook
# 集成自动增强系统到 鲤鱼 hooks 系统

set -e

鲤鱼_HOME="$HOME/.claude/liyu"
AUTO_ENHANCE="$鲤鱼_HOME/liyu-auto-enhance.py"
CONFIG_FILE="$鲤鱼_HOME/auto-enhance-config.json"
LOG_FILE="$鲤鱼_HOME/auto-enhance.log"

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查配置
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log "配置文件不存在，使用默认配置"
        return 1
    fi
    return 0
}

# 检查是否启用
is_enabled() {
    local feature=$1
    if ! check_config; then
        return 0  # 默认启用
    fi

    # 简单的配置检查
    if grep -q "\"$feature\": true" "$CONFIG_FILE" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Session Start Hook
session_start_hook() {
    log "Session Start Hook 触发"

    # 检查待处理任务
    if is_enabled "task_scheduling"; then
        log "检查待处理任务..."
        python3 "$AUTO_ENHANCE" schedule 2>/dev/null || true
    fi

    # 检查错误模式
    if is_enabled "error_recovery"; then
        log "分析错误模式..."
        python3 "$AUTO_ENHANCE" recover 2>/dev/null || true
    fi
}

# Session End Hook
session_end_hook() {
    log "Session End Hook 触发"

    # 运行记忆压缩
    if is_enabled "memory_compression"; then
        log "运行记忆压缩..."
        python3 "$AUTO_ENHANCE" compress 2>/dev/null || true
    fi

    # 技能发现
    if is_enabled "skill_discovery"; then
        log "运行技能发现..."
        python3 "$AUTO_ENHANCE" discover 2>/dev/null || true
    fi
}

# Tool Error Hook
tool_error_hook() {
    log "Tool Error Hook 触发"

    # 错误恢复分析
    if is_enabled "error_recovery"; then
        log "分析错误恢复策略..."
        python3 "$AUTO_ENHANCE" recover 2>/dev/null || true
    fi
}

# Post Tool Use Hook
post_tool_use_hook() {
    # 这个hook可能太频繁，只在特定条件下运行
    local tool_name=$1

    # 只在特定工具使用后触发
    case "$tool_name" in
        "Edit"|"Write")
            # 代码修改后检查规则优化
            if is_enabled "rule_optimization"; then
                # 限制频率，每小时最多一次
                local last_run_file="$鲤鱼_HOME/.last-rule-optimize"
                local now=$(date +%s)
                local last_run=0

                if [ -f "$last_run_file" ]; then
                    last_run=$(cat "$last_run_file")
                fi

                if [ $((now - last_run)) -gt 3600 ]; then
                    log "检查规则优化..."
                    python3 "$AUTO_ENHANCE" optimize-rules 2>/dev/null || true
                    echo "$now" > "$last_run_file"
                fi
            fi
            ;;
    esac
}

# 定时任务
scheduled_task() {
    local task_type=$1

    log "定时任务触发: $task_type"

    case "$task_type" in
        "skill_discovery")
            python3 "$AUTO_ENHANCE" discover >> "$LOG_FILE" 2>&1
            ;;
        "memory_compression")
            python3 "$AUTO_ENHANCE" compress >> "$LOG_FILE" 2>&1
            ;;
        "rule_optimization")
            python3 "$AUTO_ENHANCE" optimize-rules >> "$LOG_FILE" 2>&1
            ;;
        "error_analysis")
            python3 "$AUTO_ENHANCE" recover >> "$LOG_FILE" 2>&1
            ;;
        *)
            log "未知的定时任务类型: $task_type"
            ;;
    esac
}

# 主逻辑
case "$1" in
    "session-start")
        session_start_hook
        ;;
    "session-end")
        session_end_hook
        ;;
    "tool-error")
        tool_error_hook
        ;;
    "post-tool-use")
        post_tool_use_hook "$2"
        ;;
    "scheduled")
        scheduled_task "$2"
        ;;
    "dashboard")
        python3 "$AUTO_ENHANCE" dashboard
        ;;
    "auto")
        python3 "$AUTO_ENHANCE" auto
        ;;
    *)
        echo "用法: $0 {session-start|session-end|tool-error|post-tool-use|scheduled|dashboard|auto}"
        echo ""
        echo "命令:"
        echo "  session-start    会话开始时触发"
        echo "  session-end      会话结束时触发"
        echo "  tool-error       工具错误时触发"
        echo "  post-tool-use    工具使用后触发"
        echo "  scheduled        定时任务"
        echo "  dashboard        显示仪表盘"
        echo "  auto             运行所有增强功能"
        exit 1
        ;;
esac
