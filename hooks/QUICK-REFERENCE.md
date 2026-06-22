# PHOENIX Enhanced Hooks - 快速参考

## 新增 Hooks

| Hook | 触发时机 | 文件 | 功能 |
|------|----------|------|------|
| ToolError | 工具执行失败 | `tool-error.sh` | 错误处理、恢复建议 |
| ContextCompaction | 上下文压缩 | `context-compaction.sh` | 状态保存、O2 更新 |
| AgentSpawn | Agent 启动 | `agent-spawn.sh` | 注册、心跳、协调锁 |
| AgentComplete | Agent 完成 | `agent-complete.sh` | 释放锁、清理、统计 |
| MemoryFlush | 记忆刷新 | `phoenix-auto-memory.py` | 记忆同步、衰减更新 |
| EvolutionCycle | 进化周期 | 事件总线 | 进化记录、通知 |

## 常用命令

### 状态查看

```bash
# 系统状态概览
python3 ~/.claude/phoenix/hooks/status-indicator.py overview

# 健康分数
python3 ~/.claude/phoenix/hooks/status-indicator.py health

# 当前警告
python3 ~/.claude/phoenix/hooks/status-indicator.py warnings

# 趋势分析
python3 ~/.claude/phoenix/hooks/status-indicator.py trends --hours 24
```

### 通知管理

```bash
# 添加通知
python3 ~/.claude/phoenix/hooks/notification-center.py add <type> <priority> <message>

# 列出通知
python3 ~/.claude/phoenix/hooks/notification-center.py list [--priority high]

# 忽略通知
python3 ~/.claude/phoenix/hooks/notification-center.py dismiss <id>

# 通知统计
python3 ~/.claude/phoenix/hooks/notification-center.py stats
```

### 智能触发

```bash
# 评估触发条件
python3 ~/.claude/phoenix/hooks/smart-trigger.py evaluate <hook> <context_json>

# 查看触发条件
python3 ~/.claude/phoenix/hooks/smart-trigger.py conditions

# 触发统计
python3 ~/.claude/phoenix/hooks/smart-trigger.py stats
```

### 监控数据

```bash
# 实时监控
python3 ~/.claude/phoenix/hooks/realtime-monitor-v2.py

# Tool Guard 统计
python3 ~/.claude/phoenix/tool-guard.py stats

# 通知中心统计
python3 ~/.claude/phoenix/hooks/notification-center.py stats
```

## 通知类型

| 类型 | 描述 | 优先级 |
|------|------|--------|
| `error_recovery` | 错误恢复建议 | medium |
| `performance_warning` | 性能警告 | medium |
| `evolution_update` | 进化更新 | low |
| `memory_sync` | 记忆同步 | low |
| `agent_coordination` | Agent 协调 | low |
| `context_pressure` | 上下文压力 | medium |
| `security_alert` | 安全警报 | high |
| `system_status` | 系统状态 | low |

## 触发条件示例

```json
{
  "error_count >= 3": "错误级联",
  "context_usage > 80": "上下文压力",
  "idle_seconds > 300": "空闲超时",
  "same_tool_count >= 5": "重复调用",
  "active_agents > 5": "Agent 过多",
  "heartbeat_age > 120": "心跳过期"
}
```

## 配置文件

| 文件 | 用途 |
|------|------|
| `settings-enhanced.json` | 增强版配置 |
| `smart-trigger-config.json` | 触发条件配置 |
| `notification-preferences.json` | 通知偏好 |

## 日志文件

| 文件 | 内容 |
|------|------|
| `tool-error-log.jsonl` | 错误日志 |
| `notification-history.jsonl` | 通知历史 |
| `smart-trigger-history.jsonl` | 触发历史 |
| `agent-lifecycle.jsonl` | Agent 生命周期 |
| `compaction-log.jsonl` | 压缩日志 |

## 安装和测试

```bash
# 安装
cd ~/.claude/phoenix/hooks
./setup-enhanced-hooks.sh

# 测试
./setup-enhanced-hooks.sh --test

# 状态
./setup-enhanced-hooks.sh --status

# 清理
./setup-enhanced-hooks.sh --cleanup
```

## 健康分数说明

| 分数 | 等级 | 含义 |
|------|------|------|
| 90-100 | excellent | 优秀 |
| 75-89 | good | 良好 |
| 60-74 | fair | 一般 |
| 40-59 | poor | 较差 |
| 0-39 | critical | 严重 |

## 7-Sense 状态

| Sense | 正常 | 警告 | 严重 |
|-------|------|------|------|
| O2 | < 70% | 70-85% | > 85% |
| Nociception | < 3 错误 | 3-5 错误 | > 5 错误 |
| Chronos | < 1h | 1-2h | > 2h |
| Spatial | < 3/call | 3-5/call | > 5/call |
| Vestibular | < 70% | 70-80% | > 80% |
| Echo | < 0.1 | 0.1-0.3 | > 0.3 |
| Drift | < 20% | 20-30% | > 30% |

## 故障排除

### Hook 不执行

```bash
# 检查权限
ls -la ~/.claude/phoenix/hooks/*.sh

# 修复权限
chmod +x ~/.claude/phoenix/hooks/*.sh
chmod +x ~/.claude/phoenix/hooks/*.py
```

### 通知不显示

```bash
# 检查偏好
python3 ~/.claude/phoenix/hooks/notification-center.py preferences

# 检查队列
python3 ~/.claude/phoenix/hooks/notification-center.py list --limit 50
```

### 触发不工作

```bash
# 启用调试
python3 -c "
import json
f = '/Users/holyty/.claude/phoenix/smart-trigger-config.json'
c = json.load(open(f))
c['global_settings']['enable_debug'] = True
json.dump(c, open(f, 'w'), indent=2)
"

# 重新测试
python3 ~/.claude/phoenix/hooks/smart-trigger.py evaluate TestHook '{"test":true}'
```

## 性能目标

| 指标 | 目标 |
|------|------|
| Hook 延迟 | < 100ms |
| 通知响应 | < 50ms |
| 状态查询 | < 200ms |
| 内存占用 | < 50MB |

## 相关文档

- `ENHANCED-HOOKS-README.md` - 完整文档
- `HOOKS-ANALYSIS.md` - 分析文档
- `TEST-INSTRUCTIONS.md` - 测试说明
- `IMPLEMENTATION-SUMMARY.md` - 实现总结
