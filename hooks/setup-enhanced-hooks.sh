#!/bin/bash
# === PHOENIX Enhanced Hooks Setup ===
# 一键设置增强版 hooks 系统
#
# 用法：
#   ./setup-enhanced-hooks.sh           # 完整安装
#   ./setup-enhanced-hooks.sh --test    # 测试模式
#   ./setup-enhanced-hooks.sh --status  # 查看状态

set -euo pipefail

PHOENIX="$HOME/.claude/phoenix"
HOOKS_DIR="$PHOENIX/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SETTINGS_BACKUP="$HOME/.claude/settings.json.backup"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi

    # 检查 Python 版本
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_success "Python 版本: $python_version"

    # 检查 jq (可选)
    if command -v jq &> /dev/null; then
        print_success "jq 已安装"
    else
        print_warning "jq 未安装 (可选，用于 JSON 处理)"
    fi
}

# 设置权限
setup_permissions() {
    print_info "设置脚本权限..."

    chmod +x "$HOOKS_DIR"/*.sh
    chmod +x "$HOOKS_DIR"/*.py

    print_success "权限设置完成"
}

# 备份当前配置
backup_settings() {
    if [ -f "$SETTINGS_FILE" ]; then
        print_info "备份当前配置..."
        cp "$SETTINGS_FILE" "$SETTINGS_BACKUP"
        print_success "配置已备份到: $SETTINGS_BACKUP"
    fi
}

# 更新配置
update_settings() {
    print_info "更新配置文件..."

    # 检查增强版配置是否存在
    if [ ! -f "$HOOKS_DIR/../settings-enhanced.json" ]; then
        print_error "增强版配置文件不存在"
        exit 1
    fi

    # 备份并替换
    backup_settings
    cp "$HOOKS_DIR/../settings-enhanced.json" "$SETTINGS_FILE"

    print_success "配置已更新"
}

# 测试 hooks
test_hooks() {
    print_info "测试 hooks..."

    # 测试 ToolError hook
    echo '{"tool_name":"Bash","error_message":"test error","error_type":"test"}' | \
        bash "$HOOKS_DIR/tool-error.sh" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "ToolError hook 测试通过"
    else
        print_error "ToolError hook 测试失败"
    fi

    # 测试 ContextCompaction hook
    echo '{"session_id":"test","context_usage":85,"message_count":50,"compression_type":"auto"}' | \
        bash "$HOOKS_DIR/context-compaction.sh" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "ContextCompaction hook 测试通过"
    else
        print_error "ContextCompaction hook 测试失败"
    fi

    # 测试 AgentSpawn hook
    echo '{"agent_type":"test","agent_name":"test-agent","task_description":"test task"}' | \
        bash "$HOOKS_DIR/agent-spawn.sh" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "AgentSpawn hook 测试通过"
    else
        print_error "AgentSpawn hook 测试失败"
    fi

    # 测试 Smart Trigger
    python3 "$HOOKS_DIR/smart-trigger.py" evaluate TestHook '{"test": true}' > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Smart Trigger 测试通过"
    else
        print_error "Smart Trigger 测试失败"
    fi

    # 测试 Notification Center
    python3 "$HOOKS_DIR/notification-center.py" stats > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Notification Center 测试通过"
    else
        print_error "Notification Center 测试失败"
    fi

    # 测试 Status Indicator
    python3 "$HOOKS_DIR/status-indicator.py" health > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Status Indicator 测试通过"
    else
        print_error "Status Indicator 测试失败"
    fi

    print_success "所有测试完成"
}

# 显示状态
show_status() {
    print_info "系统状态..."
    echo ""

    # 显示 hooks 目录
    echo "=== Hooks 目录 ==="
    ls -lh "$HOOKS_DIR"/*.sh "$HOOKS_DIR"/*.py 2>/dev/null | awk '{print $9, $5}'
    echo ""

    # 显示配置状态
    echo "=== 配置状态 ==="
    if [ -f "$SETTINGS_FILE" ]; then
        echo "settings.json: 存在"
        # 检查是否包含增强 hooks
        if grep -q "tool-error.sh" "$SETTINGS_FILE" 2>/dev/null; then
            echo "增强 hooks: 已启用"
        else
            echo "增强 hooks: 未启用"
        fi
    else
        echo "settings.json: 不存在"
    fi
    echo ""

    # 显示通知状态
    echo "=== 通知状态 ==="
    if [ -f "$PHOENIX/notifications.json" ]; then
        python3 "$HOOKS_DIR/notification-center.py" stats 2>/dev/null || echo "无法读取通知状态"
    else
        echo "无通知数据"
    fi
    echo ""

    # 显示健康状态
    echo "=== 健康状态 ==="
    python3 "$HOOKS_DIR/status-indicator.py" health 2>/dev/null || echo "无法读取健康状态"
}

# 清理旧文件
cleanup_old_files() {
    print_info "清理旧文件..."

    # 清理旧的心跳文件
    if [ -d "$PHOENIX/heartbeats" ]; then
        find "$PHOENIX/heartbeats" -name "*.heartbeat" -mtime +7 -delete 2>/dev/null || true
        print_success "清理旧心跳文件"
    fi

    # 清理旧的通知
    if [ -f "$PHOENIX/notifications.json" ]; then
        python3 "$HOOKS_DIR/notification-center.py" auto-dismiss > /dev/null 2>&1 || true
        print_success "清理过期通知"
    fi

    # 清理旧的触发历史
    if [ -f "$PHOENIX/smart-trigger-history.jsonl" ]; then
        # 保留最近 1000 行
        tail -1000 "$PHOENIX/smart-trigger-history.jsonl" > "$PHOENIX/smart-trigger-history.jsonl.tmp" 2>/dev/null || true
        mv "$PHOENIX/smart-trigger-history.jsonl.tmp" "$PHOENIX/smart-trigger-history.jsonl" 2>/dev/null || true
        print_success "清理触发历史"
    fi
}

# 主函数
main() {
    echo "═══════════════════════════════════════════"
    echo "  PHOENIX Enhanced Hooks Setup v1.0"
    echo "═══════════════════════════════════════════"
    echo ""

    # 解析参数
    case "${1:-}" in
        --test)
            test_hooks
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --cleanup)
            cleanup_old_files
            exit 0
            ;;
        "")
            # 完整安装
            ;;
        *)
            echo "用法: $0 [--test|--status|--cleanup]"
            exit 1
            ;;
    esac

    # 执行安装步骤
    check_dependencies
    setup_permissions
    update_settings
    cleanup_old_files

    echo ""
    echo "═══════════════════════════════════════════"
    print_success "增强版 hooks 系统安装完成！"
    echo "═══════════════════════════════════════════"
    echo ""
    echo "新增功能："
    echo "  ✅ ToolError - 工具执行错误处理"
    echo "  ✅ ContextCompaction - 上下文压缩处理"
    echo "  ✅ AgentSpawn - Agent 启动注册"
    echo "  ✅ AgentComplete - Agent 完成处理"
    echo "  ✅ Smart Trigger - 智能触发条件"
    echo "  ✅ Notification Center - 通知系统"
    echo "  ✅ Status Indicator - 状态指示器"
    echo "  ✅ Realtime Monitor v2 - 增强监控"
    echo ""
    echo "使用命令："
    echo "  $0 --test     # 测试 hooks"
    echo "  $0 --status   # 查看状态"
    echo "  $0 --cleanup  # 清理旧文件"
    echo ""
    echo "配置文件："
    echo "  $SETTINGS_FILE"
    echo "  $PHOENIX/smart-trigger-config.json"
    echo "  $PHOENIX/notification-preferences.json"
}

main
