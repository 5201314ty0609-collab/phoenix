# GNAP Migration Guide — Lock-File to Structured Protocol

当前 鲤鱼 的协调模式 → GNAP 结构化协议迁移路径。

## Current State (Pre-GNAP)

鲤鱼 已有以下协调机制（吸收自 disler/observability + agent-farm + community-agents）：

```
~/.claude/liyu/
├── heartbeats/
│   └── <agent-id>.heartbeat       # 纯文本心跳
├── coordination/
│   └── agent_locks/
│       └── <id>.lock               # 空锁文件（2h 过期）
└── hooks/
    └── session-stop.sh             # Stop-hook guard
```

## Target State (GNAP)

```
~/.claude/liyu/.gnap/
├── agents/
│   └── <agent-id>.json             # 结构化 Agent 注册
├── tasks/
│   └── <task-id>.json              # 任务定义 + 状态机
├── runs/
│   └── <run-id>.json               # 执行记录 + 指标
├── messages/
│   └── <run-id>/
│       └── <seq>.json              # 消息序列（replay/debug）
├── locks/
│   └── <task-id>.lock              # 结构化锁（含 heartbeat 续期）
├── heartbeats/
│   └── <agent-id>.heartbeat        # JSON 格式心跳
└── audit.log                        # Git log 审计追踪
```

## Phase 1: Coexistence (Week 1)

**目标**: 保持现有系统不变，新增 GNAP 目录。

```bash
# 创建 .gnap 结构
mkdir -p ~/.claude/liyu/.gnap/{agents,tasks,runs,messages,locks,heartbeats}

# 初始化 git 追踪
cd ~/.claude/liyu/.gnap
git init
git add -A
git commit -m "feat: initialize GNAP coordination directory"
```

- 现有 lock 文件继续工作
- 新 Agent 可选使用 GNAP lock schema
- 两种格式并行，无冲突

## Phase 2: New Agents Use GNAP (Week 2)

**目标**: 所有新创建的 Agent 使用 GNAP schema。

### 注册 Agent

```bash
# 新 Agent 启动时注册
cat > .gnap/agents/code-reviewer.json << 'EOF'
{
  "agent_id": "code-reviewer",
  "name": "Code Reviewer",
  "type": "specialist",
  "capabilities": ["code-review", "security-check"],
  "max_concurrent_tasks": 2,
  "status": "idle",
  "registered_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_heartbeat": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git -C .gnap add agents/code-reviewer.json
git -C .gnap commit -m "agent: register code-reviewer"
```

### 创建任务

```bash
# 使用 task.json 模板
cp ~/.claude/liyu/planning/gnap-template/task.json .gnap/tasks/task-review-auth.json
# 编辑填充实际值
git -C .gnap add tasks/task-review-auth.json
git -C .gnap commit -m "task: create review-auth (agent:code-reviewer)"
```

### 获取锁

```bash
# 结构化锁（含心跳信息）
cat > .gnap/locks/task-review-auth.lock << 'EOF'
{
  "task_id": "task-review-auth",
  "acquired_by": "code-reviewer",
  "acquired_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "expires_at": "$(date -u -v+2H +%Y-%m-%dT%H:%M:%SZ)",
  "heartbeat_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
```

## Phase 3: Migrate Existing Patterns (Week 3)

**目标**: 迁移现有 heartbeat 和 lock 到 GNAP 格式。

### Heartbeat 迁移

Before (plain text):
```
main working 2026-06-17T00:05:00Z
```

After (JSON):
```json
{
  "agent_id": "main",
  "status": "working",
  "timestamp": "2026-06-17T00:05:00Z",
  "context_pct": 45.2,
  "active_task": "task-abc123",
  "sequence": 42
}
```

### Lock 迁移

Before (empty file):
```
/coordination/agent_locks/task-abc.lock  (空文件)
```

After (JSON):
```json
{
  "task_id": "task-abc",
  "acquired_by": "code-reviewer",
  "acquired_at": "2026-06-17T00:00:00Z",
  "expires_at": "2026-06-17T02:00:00Z",
  "heartbeat_at": "2026-06-17T00:02:00Z"
}
```

### 迁移脚本

```bash
#!/bin/bash
# 将旧锁迁移到 GNAP 格式
for lock in ~/.claude/liyu/coordination/agent_locks/*.lock; do
  task_id=$(basename "$lock" .lock)
  echo "{\"task_id\":\"$task_id\",\"acquired_by\":\"unknown\",\"acquired_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"expires_at\":\"$(date -u -v+2H +%Y-%m-%dT%H:%M:%SZ)\"}" \
    > ".gnap/locks/$task_id.lock"
done
```

## Phase 4: Git-Native Audit (Week 4)

**目标**: 启用 git log 作为审计追踪。

```bash
# 审计某 Agent 的所有操作
git -C .gnap log --oneline --grep="agent:code-reviewer"

# 查看任务生命周期
git -C .gnap log --oneline -- tasks/task-review-auth.json

# 生成审计报告
git -C .gnap log --format="%h %ad %s" --date=short -- tasks/ | head -20
```

### 自动化审计 Hook

```bash
# PostToolUse hook: 每次写 .gnap/ 时自动 commit
# ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "if echo \"$FILE_PATH\" | grep -q '.gnap/'; then cd ~/.claude/liyu && git -C .gnap add -A && git -C .gnap diff --cached --quiet || git -C .gnap commit -m \"gnap: auto-audit $FILE_PATH\"; fi"
      }
    ]
  }
}
```

## Rollback Plan

如需回滚到 pre-GNAP 状态：
1. 保留 `.gnap/` 目录（历史审计数据）
2. 恢复旧 lock 文件路径的使用
3. Agent 回退到空 lock 文件模式
4. Heartbeat 回退到纯文本格式

GNAP 设计为**非破坏性叠加** —— 旧格式始终可用。

## Quick Reference

| Action | Old Way | GNAP Way |
|--------|---------|----------|
| Get lock | `touch locks/task.lock` | Write structured JSON with expiry |
| Heartbeat | `echo "status" > .heartbeat` | Write JSON with seq + context_pct |
| Task done | Remove lock file | Update task.json status → completed |
| Audit | None | `git log -- .gnap/` |
| Find agent | None | Read `.gnap/agents/<id>.json` |
