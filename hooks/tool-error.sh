#!/bin/bash
# === 鲤鱼 ToolError Hook v1.0 ===
# 工具执行失败时触发，记录错误详情并提供恢复建议
#
# 功能：
#   1. 记录错误到 nociception 系统
#   2. 更新错误级联计数
#   3. 提供错误恢复建议
#   4. 通知用户错误状态
#
# 输入 (stdin): JSON with tool_name, tool_input, error_message, error_type
# 输出: JSON with decision, reason, recovery_suggestions

set -euo pipefail

鲤鱼="$HOME/.claude/liyu"
SENSES_DIR="$鲤鱼/senses"
ERROR_LOG="$鲤鱼/tool-error-log.jsonl"

# 读取输入
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tool_name', 'unknown'))" 2>/dev/null || echo "unknown")
ERROR_MSG=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_message', ''))" 2>/dev/null || echo "")
ERROR_TYPE=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_type', 'unknown'))" 2>/dev/null || echo "unknown")
TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).get('tool_input', {})))" 2>/dev/null || echo "{}")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 错误恢复建议引擎
get_recovery_suggestions() {
    local tool="$1"
    local error_type="$2"
    local error_msg="$3"

    suggestions=()

    # 基于工具类型的建议
    case "$tool" in
        "Bash")
            suggestions+=("检查命令语法是否正确")
            suggestions+=("验证命令是否在 PATH 中")
            if [[ "$error_msg" == *"permission"* ]]; then
                suggestions+=("尝试使用 sudo 或检查文件权限")
            fi
            if [[ "$error_msg" == *"not found"* ]]; then
                suggestions+=("安装缺失的命令或检查拼写")
            fi
            ;;
        "Read")
            suggestions+=("检查文件路径是否正确")
            suggestions+=("验证文件是否存在")
            suggestions+=("检查文件权限")
            ;;
        "Write"|"Edit")
            suggestions+=("检查目标目录是否存在")
            suggestions+=("验证写入权限")
            suggestions+=("检查磁盘空间")
            ;;
        "WebFetch"|"WebSearch")
            suggestions+=("检查网络连接")
            suggestions+=("验证 URL 格式")
            suggestions+=("尝试使用代理")
            ;;
    esac

    # 基于错误类型的建议
    case "$error_type" in
        "timeout")
            suggestions+=("增加超时时间")
            suggestions+=("检查网络连接")
            suggestions+=("尝试分块处理")
            ;;
        "permission")
            suggestions+=("提升权限或使用管理员账户")
            suggestions+=("检查文件/目录权限")
            ;;
        "not_found")
            suggestions+=("验证资源路径")
            suggestions+=("检查资源是否已删除")
            ;;
        "network")
            suggestions+=("检查网络连接")
            suggestions+=("尝试使用代理")
            suggestions+=("稍后重试")
            ;;
    esac

    # 默认建议
    if [ ${#suggestions[@]} -eq 0 ]; then
        suggestions+=("检查输入参数")
        suggestions+=("查看详细错误日志")
        suggestions+=("尝试替代方法")
    fi

    # 转换为 JSON 数组
    printf '%s\n' "${suggestions[@]}" | python3 -c "
import sys, json
suggestions = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(suggestions))
"
}

# 更新 nociception 指标
update_nociception() {
    local nociception_file="$SENSES_DIR/nociception.json"

    if [ ! -f "$nociception_file" ]; then
        echo '{"trace_event":"error_cascade","status":"normal","metrics":{"error_count":0}}' > "$nociception_file"
    fi

    python3 << PYEOF
import json
from datetime import datetime, timezone

nociception_file = "$nociception_file"
try:
    with open(nociception_file) as f:
        data = json.load(f)
except:
    data = {"trace_event": "error_cascade", "status": "normal", "metrics": {"error_count": 0}}

# 更新错误计数
error_count = data.get("metrics", {}).get("error_count", 0) + 1
data["metrics"]["error_count"] = error_count
data["last_updated"] = datetime.now(timezone.utc).isoformat()

# 更新状态
if error_count >= 5:
    data["status"] = "critical"
elif error_count >= 3:
    data["status"] = "warning"
else:
    data["status"] = "normal"

# 添加警告
warnings = data.get("warnings", [])
if error_count >= 3:
    warnings.append(f"错误级联: {error_count} 次错误在短时间内发生")
    data["warnings"] = warnings[-5:]  # 保留最近 5 条

with open(nociception_file, "w") as f:
    json.dump(data, f, indent=2)

print(json.dumps({"status": data["status"], "error_count": error_count}))
PYEOF
}

# 记录错误日志
log_error() {
    cat >> "$ERROR_LOG" << EOF
{"timestamp":"$TIMESTAMP","tool":"$TOOL_NAME","error_type":"$ERROR_TYPE","error_message":"$(echo "$ERROR_MSG" | head -c 200)","tool_input":$TOOL_INPUT}
EOF
}

# 主流程
main() {
    # 记录错误
    log_error

    # 更新 nociception
    nociception_result=$(update_nociception)

    # 获取恢复建议
    suggestions=$(get_recovery_suggestions "$TOOL_NAME" "$ERROR_TYPE" "$ERROR_MSG")

    # 生成输出
    python3 << PYEOF
import json

tool_name = "$TOOL_NAME"
error_type = "$ERROR_TYPE"
error_msg = """$ERROR_MSG"""
suggestions = $suggestions
nociception = $nociception_result

output = {
    "decision": "allow",
    "reason": f"工具 {tool_name} 执行失败: {error_msg[:100]}",
    "hookSpecificOutput": {
        "hookEventName": "ToolError",
        "error_type": error_type,
        "error_message": error_msg[:200],
        "recovery_suggestions": suggestions,
        "nociception_status": nociception.get("status", "unknown"),
        "error_count": nociception.get("error_count", 0)
    }
}

print(json.dumps(output, ensure_ascii=False, indent=2))
PYEOF
}

main
