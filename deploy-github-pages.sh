#!/bin/bash
# PHOENIX GitHub Pages 部署脚本
# 同步数据 + 提交 + 推送

PHOENIX_HOME="$HOME/.claude/phoenix"

echo "🚀 PHOENIX GitHub Pages 部署"
echo "============================"

# 1. 同步数据
echo ""
echo "📊 同步实时数据..."
python3 "$PHOENIX_HOME/sync-dashboard-data.py"

# 2. 更新版本号
echo ""
VERSION="1.3.0-$(date +%Y%m%d-%H%M)"
echo "🔖 更新版本号: $VERSION"

# 更新 index.html 版本
sed -i '' "s/name=\"version\" content=\"[^\"]*\"/name=\"version\" content=\"$VERSION\"/" "$PHOENIX_HOME/index.html"

# 更新 dashboard.html 版本
sed -i '' "s/name=\"version\" content=\"[^\"]*\"/name=\"version\" content=\"$VERSION\"/" "$PHOENIX_HOME/dashboard.html"

# 3. Git 操作
echo ""
echo "📦 提交更改..."
cd "$PHOENIX_HOME"
git add index.html dashboard.html dashboard-viz.html
git commit -m "chore: 更新 dashboard 数据 ($VERSION)

- 同步最新统计数据
- 更新版本号到 $VERSION
- 确保 GitHub Pages 显示最新数据

🤖 Auto-deployed by deploy-github-pages.sh"

echo ""
echo "⬆️  推送到 GitHub..."
git push origin main

echo ""
echo "✅ 部署完成！"
echo ""
echo "📝 GitHub Pages 需要 1-2 分钟更新"
echo "   访问: https://5201314ty0609-collab.github.io/phoenix/"
echo ""
echo "💡 如果浏览器显示旧数据，请强制刷新:"
echo "   - Mac: Cmd+Shift+R"
echo "   - Windows: Ctrl+Shift+R"
