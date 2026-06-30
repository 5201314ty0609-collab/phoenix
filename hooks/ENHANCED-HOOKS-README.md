# 鲤鱼 Enhanced Hooks System v1.0

## 概述

鲤鱼 Enhanced Hooks System 是对原有 hooks 系统的全面增强，提供了更完整的生命周期管理、智能触发条件、丰富的反馈机制和实时状态监控。

## 新增功能

### 1. 新增生命周期钩子

#### ToolError Hook
- **触发时机**: 工具执行抛出异常时
- **功能**: 记录错误详情、提供恢复建议、更新 nociception 指标
- **文件**: `hooks/tool-error.sh`

#### ContextCompaction Hook
- **触发时机**: 上下文压缩发生时
- **功能**: 保存当前状态、记录压缩信息、更新 O2 指标
- **文件**: `hooks/context-compaction.sh`

#### AgentSpawn Hook
- **触发时机**: 子 Agent 启动时
- **功能**: 注册 Agent、写入心跳、分配协调锁
- **文件**: `hooks/agent-spawn.sh`

#### AgentComplete Hook
- **触发时机**: 子 Agent 完成时
- **功能**: 释放协调锁、记录完成状态、清理心跳
- **文件**: `hooks/agent-complete.sh`

#### MemoryFlush Hook
- **触发时机**: 记忆系统刷新时
- **功能**: 同步记忆到知识库、更新衰减分数
- **集成**: 使用现有的 `liyu-auto-memory.py`

#### EvolutionCycle Hook
- **触发时机**: 进化周期运行时
- **功能**: 记录进化事件、通知用户进化结果
- **集成**: 使用现有的进化引擎

### 2. 智能触发条件引擎

#### Smart Trigger Engine
- **文件**: `hooks/smart-trigger.py`
- **配置**: `smart-trigger-config.json`
- **功能**:
  - 条件匹配引擎
  - 上下文压力检测
  - 时间间隔触发
  - 错误级联检测
  - 工具使用模式分析

#### 触发条件类型

| 类型 | 描述 | 示例 |
|------|------|------|
| tool_error | 工具执行错误 | `error_count >= 3` |
| context_pressure | 上下文压力 | `context_usage > 80` |
| time_based | 基于时间 | `idle_seconds > 300` |
| tool_patterns | 工具模式 | `same_tool_count >= 5` |
| agent_coordination | Agent 协调 | `active_agents > 5` |
| memory_management | 内存管理 | `memory_count > 1000` |

### 3. 用户通知系统

#### Notification Center
- **文件**: `hooks/notification-center.py`
- **配置**: `notification-preferences.json`
- **功能**:
  - 通知队列管理
  - 优先级排序
  - 通知去重
  - 自动过期
  - 静默时间

#### 通知类型

| 类型 | 描述 | 默认优先级 |
|------|------|------------|
| error_recovery | 错误恢复建议 | medium |
| performance_warning | 性能警告 | medium |
| evolution_update | 进化状态更新 | low |
| memory_sync | 记忆同步状态 | low |
| agent_coordination | Agent 协调 | low |
| context_pressure | 上下文压力 | medium |
| security_alert | 安全警报 | high |
| system_status | 系统状态 | low |

### 4. 状态指示器

#### Status Indicator
- **文件**: `hooks/status-indicator.py`
- **功能**:
  - 实时状态概览
  - 健康分数计算
  - 趋势分析
  - 预警系统
  - 状态导出

#### 健康分数计算

| Sense | 权重 | 正常 | 警告 | 严重 |
|-------|------|------|------|------|
| O2 (Vitality) | 25% | 0 | -10 | -25 |
| Nociception (Pain) | 30% | 0 | -15 | -30 |
| Chronos (Time) | 15% | 0 | -5 | -15 |
| Spatial (Workspace) | 10% | 0 | -5 | -10 |
| Vestibular (Balance) | 10% | 0 | -5 | -10 |
| Echo (Repetition) | 15% | 0 | -5 | -15 |
| Drift (Focus) | 10% | 0 | -5 | -10 |

### 5. 增强版实时监控

#### Realtime Monitor v2
- **文件**: `hooks/realtime-monitor-v2.py`
- **增强功能**:
  - 真实数据收集
  - 智能阈值调整
  - 趋势分析
  - 预测性警告
  - 性能指标追踪

## 文件结构

```
~/.claude/liyu/hooks/
├── tool-error.sh              # ToolError 钩子
├── context-compaction.sh      # ContextCompaction 钩子
├── agent-spawn.sh             # AgentSpawn 钩子
├── agent-complete.sh          # AgentComplete 钩子
├── smart-trigger.py           # 智能触发引擎
├── notification-center.py     # 通知中心
├── status-indicator.py        # 状态指示器
├── realtime-monitor-v2.py     # 增强版实时监控
├── setup-enhanced-hooks.sh    # 安装脚本
├── ENHANCED-HOOKS-README.md   # 本文档
├── HOOKS-ANALYSIS.md          # 分析文档
│
├── session-start.sh           # (原有) 会话开始
├── session-stop.sh            # (原有) 会话结束
├── bash-guard.sh              # (原有) Bash 安全防护
├── heartbeat.sh               # (原有) 心跳管理
├── coordinate.sh              # (原有) Agent 协调
├── auto-ingest.py             # (原有) 自动采集
├── realtime-monitor.py        # (原有) 实时监控
├── e2e-check.sh               # (原有) E2E 检查
└── nexsandglass-inject.sh     # (原有) NexSandglass 注入
```

## 配置文件

```
~/.claude/liyu/
├── settings-enhanced.json         # 增强版配置
├── smart-trigger-config.json      # 智能触发配置
├── notification-preferences.json  # 通知偏好
├── notifications.json             # 通知队列
├── notification-history.jsonl     # 通知历史
├── smart-trigger-history.jsonl    # 触发历史
├── agent-lifecycle.jsonl          # Agent 生命周期
├── tool-error-log.jsonl           # 错误日志
├── compaction-log.jsonl           # 压缩日志
└── monitor-metrics-history.jsonl  # 监控指标历史
```

## 快速开始

### 1. 安装增强版 hooks

```bash
cd ~/.claude/liyu/hooks
./setup-enhanced-hooks.sh
```

### 2. 测试 hooks

```bash
./setup-enhanced-hooks.sh --test
```

### 3. 查看状态

```bash
./setup-enhanced-hooks.sh --status
```

### 4. 清理旧文件

```bash
./setup-enhanced-hooks.sh --cleanup
```

## 使用示例

### 1. 添加通知

```bash
# 添加错误恢复通知
python3 ~/.claude/liyu/hooks/notification-center.py add error_recovery high "工具执行失败，建议检查参数"

# 添加性能警告
python3 ~/.claude/liyu/hooks/notification-center.py add performance_warning medium "上下文使用率超过 80%"
```

### 2. 查看通知

```bash
# 列出所有通知
python3 ~/.claude/liyu/hooks/notification-center.py list

# 列出高优先级通知
python3 ~/.claude/liyu/hooks/notification-center.py list --priority high

# 忽略通知
python3 ~/.claude/liyu/hooks/notification-center.py dismiss <notification_id>
```

### 3. 智能触发

```bash
# 评估触发条件
python3 ~/.claude/liyu/hooks/smart-trigger.py evaluate PostToolUse '{"tool_name":"Bash","error_count":3}'

# 查看触发条件
python3 ~/.claude/liyu/hooks/smart-trigger.py conditions

# 查看触发统计
python3 ~/.claude/liyu/hooks/smart-trigger.py stats
```

### 4. 状态指示器

```bash
# 显示状态概览
python3 ~/.claude/liyu/hooks/status-indicator.py overview

# 显示健康分数
python3 ~/.claude/liyu/hooks/status-indicator.py health

# 显示趋势分析
python3 ~/.claude/liyu/hooks/status-indicator.py trends --hours 24

# 显示当前警告
python3 ~/.claude/liyu/hooks/status-indicator.py warnings

# 导出状态数据
python3 ~/.claude/liyu/hooks/status-indicator.py export --format json
```

## 配置说明

### 智能触发配置

```json
{
  "conditions": {
    "tool_error": {
      "trigger": "ToolError",
      "rules": [
        {
          "name": "error_cascade",
          "condition": "error_count >= 3",
          "priority": "high"
        }
      ]
    }
  },
  "global_settings": {
    "cooldown_seconds": 30,
    "enable_debug": false
  }
}
```

### 通知偏好配置

```json
{
  "enabled_types": ["error_recovery", "performance_warning"],
  "min_priority": "medium",
  "max_notifications": 100,
  "auto_dismiss_after_hours": 24,
  "quiet_hours": {
    "enabled": false,
    "start": "22:00",
    "end": "08:00"
  }
}
```

## 监控指标

### 7-Sense 指标

| Sense | 指标 | 正常范围 | 警告阈值 | 严重阈值 |
|-------|------|----------|----------|----------|
| O2 | 上下文使用率 | < 70% | 70-85% | > 85% |
| Nociception | 错误级联 | < 3 | 3-5 | > 5 |
| Chronos | 会话时长 | < 1h | 1-2h | > 2h |
| Spatial | 文件变动 | < 3/call | 3-5/call | > 5/call |
| Vestibular | 工具多样性 | < 70% | 70-80% | > 80% |
| Echo | 模式重复 | < 0.1 | 0.1-0.3 | > 0.3 |
| Drift | 主题漂移 | < 20% | 20-30% | > 30% |

### Tool Guard 指标

| 指标 | 描述 | 警告阈值 | 阻断阈值 |
|------|------|----------|----------|
| exact_failures | 精确失败 | 2 | 4 |
| tool_failures | 工具失败 | 3 | 6 |
| no_progress | 无进展 | 2 | 4 |

## 故障排除

### 1. Hook 执行失败

```bash
# 检查 hook 权限
ls -la ~/.claude/liyu/hooks/*.sh

# 手动测试 hook
echo '{"tool_name":"Bash","error_message":"test"}' | bash ~/.claude/liyu/hooks/tool-error.sh

# 查看错误日志
cat ~/.claude/liyu/tool-error-log.jsonl
```

### 2. 通知不显示

```bash
# 检查通知偏好
python3 ~/.claude/liyu/hooks/notification-center.py preferences

# 检查通知队列
python3 ~/.claude/liyu/hooks/notification-center.py list

# 检查静默时间
python3 -c "import json; print(json.load(open('$HOME/.claude/liyu/notification-preferences.json'))['quiet_hours'])"
```

### 3. 智能触发不工作

```bash
# 检查触发配置
python3 ~/.claude/liyu/hooks/smart-trigger.py conditions

# 查看触发历史
tail -20 ~/.claude/liyu/smart-trigger-history.jsonl

# 启用调试模式
python3 -c "
import json
config = json.load(open('$HOME/.claude/liyu/smart-trigger-config.json'))
config['global_settings']['enable_debug'] = True
json.dump(config, open('$HOME/.claude/liyu/smart-trigger-config.json', 'w'), indent=2)
"
```

### 4. 监控数据不准确

```bash
# 检查 Tool Guard 状态
python3 ~/.claude/liyu/tool-guard.py stats

# 检查 Sense 文件
ls -la ~/.claude/liyu/senses/

# 手动更新监控
python3 ~/.claude/liyu/hooks/realtime-monitor-v2.py
```

## 性能优化

### 1. 减少 Hook 执行时间

- 使用异步执行避免阻塞
- 限制历史数据大小
- 使用缓存减少重复计算

### 2. 降低内存占用

- 定期清理过期数据
- 限制通知队列大小
- 压缩历史日志

### 3. 优化触发条件

- 使用合理的冷却时间
- 避免过于频繁的触发
- 优先处理高优先级条件

## 更新日志

### v1.0.0 (2026-06-19)
- 新增 ToolError, ContextCompaction, AgentSpawn, AgentComplete 钩子
- 实现智能触发条件引擎
- 实现用户通知系统
- 实现状态指示器
- 增强版实时监控
- 完整文档和安装脚本

## 贡献指南

1. 在 `hooks/` 目录下创建新的钩子脚本
2. 更新 `settings-enhanced.json` 配置
3. 更新 `smart-trigger-config.json` 触发条件
4. 更新本文档
5. 运行测试: `./setup-enhanced-hooks.sh --test`

## 许可证

鲤鱼 Enhanced Hooks System 是 鲤鱼 自进化 Agent 系统的一部分。
