# 鲤鱼 Dashboard 更新指南

## 问题描述

Dashboard 页面显示旧数据（如成本健康 71），但实际数据已更新（72）。

## 根本原因

1. **浏览器缓存** - 浏览器缓存了旧版本的 HTML 文件
2. **GitHub Pages 延迟** - GitHub Pages 需要 1-2 分钟更新
3. **缺少实时更新机制** - 静态页面没有自动刷新数据

## 解决方案

### 方案 1: 强制刷新浏览器（最快）

**Mac:**
```
Cmd + Shift + R
```

**Windows/Linux:**
```
Ctrl + Shift + R
```

**或者清除浏览器缓存:**
- Chrome: 设置 → 隐私和安全 → 清除浏览数据 → 缓存的图片和文件
- Firefox: 设置 → 隐私与安全 → 清除数据 → 缓存

### 方案 2: 使用一键更新脚本

```bash
# 更新所有 dashboard 数据并部署到 GitHub Pages
~/.claude/liyu/deploy-github-pages.sh
```

这个脚本会：
1. 同步最新数据到所有 HTML 文件
2. 更新版本号
3. 提交并推送到 GitHub
4. 等待 GitHub Pages 更新（1-2 分钟）

### 方案 3: 手动同步数据

```bash
# 仅同步数据（不部署）
~/.claude/liyu/sync-dashboard-data.py

# 或使用一键更新脚本
~/.claude/liyu/update-dashboard.sh
```

### 方案 4: 本地服务器（实时更新）

```bash
# 启动本地服务器
~/.claude/liyu/start-server.sh -b

# 访问本地版本（实时数据）
open http://127.0.0.1:8765/
open http://127.0.0.1:8765/dashboard.html
open http://127.0.0.1:8765/viz
```

本地服务器版本会自动从 API 获取最新数据，无需手动刷新。

## 自动同步机制

### PostToolUse Hook

每次工具调用后，系统会自动：
1. 更新 7-Sense 数据
2. 同步到所有 dashboard 文件
3. 保持数据一致性

配置位置：`~/.claude/settings.json`

### 定时同步（可选）

如果需要定期同步，可以添加 cron job：

```bash
# 每 5 分钟同步一次
*/5 * * * * cd ~/.claude/liyu && python3 sync-dashboard-data.py
```

## 验证数据一致性

### 检查本地文件

```bash
# 检查 index.html
grep "stat-cost-health" ~/.claude/liyu/index.html

# 检查 dashboard.html
grep "kpi-cost-health" ~/.claude/liyu/dashboard.html

# 检查 dashboard-viz.html FALLBACK
grep -A5 "const FALLBACK" ~/.claude/liyu/dashboard-viz.html
```

### 检查服务器 API

```bash
# 获取最新数据
curl -s http://127.0.0.1:8765/api/stats | jq '.cost_health'

# 或使用 Python
python3 -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/stats')); print(f'成本健康: {d[\"cost_health\"]}')"
```

### 检查 GitHub Pages

访问：https://5201314ty0609-collab.github.io/liyu/

如果显示旧数据：
1. 等待 1-2 分钟（GitHub Pages 部署延迟）
2. 强制刷新浏览器
3. 检查 GitHub Actions 状态

## 文件说明

| 文件 | 用途 | 更新方式 |
|------|------|---------|
| `index.html` | 首页 | 静态 + 动态更新 |
| `dashboard.html` | 仪表盘 | 静态 + 动态更新 |
| `dashboard-viz.html` | 实时监控 | FALLBACK + 实时连接 |
| `sync-dashboard-data.py` | 数据同步 | 自动/手动 |
| `update-dashboard.sh` | 一键更新 | 手动 |
| `deploy-github-pages.sh` | GitHub Pages 部署 | 手动 |

## 常见问题

### Q: 为什么本地文件已更新，但浏览器显示旧数据？

**A:** 浏览器缓存。强制刷新（Cmd+Shift+R / Ctrl+Shift+R）即可。

### Q: GitHub Pages 更新需要多久？

**A:** 通常 1-2 分钟。可以在 GitHub Actions 中查看部署状态。

### Q: 如何确保所有页面数据一致？

**A:** 使用 `~/.claude/liyu/sync-dashboard-data.py` 同步所有文件。

### Q: 本地服务器和 GitHub Pages 有什么区别？

**A:**
- **本地服务器**：实时数据，自动更新，需要运行 `server.py`
- **GitHub Pages**：静态数据，需要手动部署，但无需运行服务器

### Q: 如何自动部署到 GitHub Pages？

**A:** 使用 `~/.claude/liyu/deploy-github-pages.sh` 脚本，或设置 GitHub Actions 自动部署。

## 快速参考

```bash
# 1. 强制刷新浏览器（最快）
Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)

# 2. 一键更新并部署
~/.claude/liyu/deploy-github-pages.sh

# 3. 仅同步数据
~/.claude/liyu/sync-dashboard-data.py

# 4. 启动本地服务器
~/.claude/liyu/start-server.sh -b

# 5. 检查数据
curl -s http://127.0.0.1:8765/api/stats | jq '.cost_health'
```

## 联系支持

如果问题仍然存在：
1. 检查 GitHub Actions 是否成功
2. 查看浏览器控制台是否有错误
3. 验证服务器是否运行：`lsof -i :8765`
4. 检查文件权限：`ls -la ~/.claude/liyu/*.html`

---

**最后更新**: 2026-06-19
**版本**: 1.3.0
