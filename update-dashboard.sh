#!/bin/bash
# PHOENIX Dashboard 一键更新脚本
# 同步数据 + 清除缓存 + 提示刷新

PHOENIX_HOME="$HOME/.claude/phoenix"

echo "🔄 PHOENIX Dashboard 更新"
echo "========================"

# 1. 同步数据到 FALLBACK
echo ""
echo "📊 同步实时数据..."
python3 "$PHOENIX_HOME/sync-dashboard-data.py"

# 2. 检查服务器状态
echo ""
if lsof -i :8765 > /dev/null 2>&1; then
    echo "✓ 服务器运行中: http://127.0.0.1:8765/viz"
else
    echo "⚠ 服务器未运行"
    echo "  启动: ~/.claude/phoenix/start-server.sh -b"
fi

# 3. 提示刷新
echo ""
echo "📝 请刷新浏览器页面:"
echo "   - 本地: http://127.0.0.1:8765/viz"
echo "   - 或按 Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows) 强制刷新"
echo ""
echo "✅ 更新完成"
