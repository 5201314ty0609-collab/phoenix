# 鲤鱼 Hooks 系统分析与增强方案

## 当前系统分析

### 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Hook 生命周期                      │
├─────────────────────────────────────────────────────────────────┤
│  SessionStart → UserPromptSubmit → PreToolUse → Tool Execution  │
│       ↓              ↓                ↓              ↓           │
│  session-start.sh  auto-ingest.py  tool-guard.py   (Claude)     │
│       ↓              ↓                ↓              ↓           │
│  PostToolUse → Tool Output → ... → Stop                         │
│       ↓                              ↓                           │
│  realtime-monitor.py          session-stop.sh                    │
│  tool-guard.py                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 当前 Hooks 清单

| Hook | 脚本 | 功能 | 状态 |
|------|------|------|------|
| SessionStart | session-start.sh | 身份注入、记忆加载、进化状态 | ✅ 完善 |
| PreToolUse | tool-guard.py | 工具执行前防护检查 | ✅ 完善 |
| PostToolUse | tool-guard.py | 工具执行后观测统计 | ✅ 完善 |
| PostToolUse | realtime-monitor.py | 7-Sense 实时更新 | ⚠️ 数据不完整 |
| PostToolUse | sync-dashboard-data.py | 仪表盘数据同步 | ✅ 正常 |
| UserPromptSubmit | auto-ingest.py | 对话写入 NexSandglass | ✅ 正常 |
| Stop | session-stop.sh | 日记更新、会话记录 | ✅ 完善 |

### 优点

1. **完整的生命周期覆盖** - 5 个主要生命周期阶段都有钩子
2. **安全防护完善** - bash-guard.sh + tool-guard.py 双重防护
3. **智能会话管理** - session-start.sh 注入上下文、记忆、进化状态
4. **多 Agent 协调** - coordinate.sh 提供锁文件协调机制
5. **记忆持久化** - auto-ingest.py 将对话写入 NexSandglass
6. **工具循环防护** - tool-guard.py 三层检测（精确失败、同工具失败、无进展）

### 缺点

1. **缺少错误处理钩子** - 没有专门处理工具执行失败的钩子
2. **缺少上下文管理钩子** - 没有上下文压缩时的处理
3. **缺少 Agent 生命周期钩子** - 子 Agent 启动/完成没有专门处理
4. **触发条件不够智能** - matcher 大多为空，缺乏条件触发
5. **反馈机制有限** - 缺少用户通知和状态指示
6. **监控数据不完整** - realtime-monitor.py 使用硬编码默认值

---

## 增强方案

### 1. 新增生命周期钩子

#### 1.1 ToolError Hook
**触发时机**: 工具执行抛出异常时
**功能**:
- 记录错误详情到 nociception
- 提供错误恢复建议
- 更新错误级联计数
- 通知用户错误状态

#### 1.2 ContextCompaction Hook
**触发时机**: 上下文压缩发生时
**功能**:
- 保存当前状态到文件系统
- 记录压缩前的关键信息
- 更新 O2 指标
- 生成压缩摘要

#### 1.3 AgentSpawn Hook
**触发时机**: 子 Agent 启动时
**功能**:
- 注册 Agent 到协调系统
- 写入心跳文件
- 分配 Agent ID
- 记录启动时间

#### 1.4 AgentComplete Hook
**触发时机**: 子 Agent 完成时
**功能**:
- 释放协调锁
- 记录完成状态
- 更新 Agent 统计
- 清理心跳文件

#### 1.5 MemoryFlush Hook
**触发时机**: 记忆系统刷新时
**功能**:
- 同步记忆到知识库
- 更新衰减分数
- 清理过期记忆
- 生成记忆摘要

#### 1.6 EvolutionCycle Hook
**触发时机**: 进化周期运行时
**功能**:
- 记录进化事件
- 更新框架状态
- 生成进化报告
- 通知用户进化结果

### 2. 智能触发条件

#### 2.1 基于工具类型的条件匹配
```json
{
  "matcher": "Bash",
  "condition": "command.startsWith('git') || command.startsWith('npm')",
  "hooks": [...]
}
```

#### 2.2 基于错误严重级别的触发
```json
{
  "matcher": "",
  "condition": "is_error && error_count >= 3",
  "hooks": [...]
}
```

#### 2.3 基于上下文压力的触发
```json
{
  "matcher": "",
  "condition": "context_usage > 80",
  "hooks": [...]
}
```

#### 2.4 基于时间间隔的触发
```json
{
  "matcher": "",
  "condition": "time_since_last_action > 300",
  "hooks": [...]
}
```

### 3. 丰富的反馈机制

#### 3.1 用户通知系统
- 错误恢复建议
- 性能警告
- 进化状态更新
- 记忆同步状态

#### 3.2 状态指示器
- 上下文使用率
- 工具执行成功率
- 错误级联状态
- Agent 协调状态

#### 3.3 错误恢复建议
- 自动重试策略
- 替代工具推荐
- 参数修正建议
- 上下文压缩建议

---

## 实现计划

### Phase 1: 核心钩子增强 (1-2 天)
- [ ] 实现 ToolError 钩子
- [ ] 实现 ContextCompaction 钩子
- [ ] 增强 realtime-monitor.py 数据收集
- [ ] 更新 settings.json 配置

### Phase 2: Agent 生命周期 (2-3 天)
- [ ] 实现 AgentSpawn 钩子
- [ ] 实现 AgentComplete 钩子
- [ ] 集成 coordinate.sh 协调系统
- [ ] 添加 Agent 心跳监控

### Phase 3: 智能触发 (3-4 天)
- [ ] 实现条件匹配引擎
- [ ] 添加上下文压力检测
- [ ] 实现时间间隔触发
- [ ] 优化 matcher 语法

### Phase 4: 反馈机制 (4-5 天)
- [ ] 实现用户通知系统
- [ ] 添加状态指示器
- [ ] 实现错误恢复建议
- [ ] 优化性能警告

---

## 技术细节

### Hook 输入输出格式

#### 标准输入格式
```json
{
  "tool_name": "Bash",
  "tool_input": {"command": "ls -la"},
  "tool_output": "...",
  "is_error": false,
  "session_id": "session-xxx",
  "timestamp": "2026-06-19T00:00:00Z"
}
```

#### 标准输出格式
```json
{
  "decision": "allow|warn|block|halt",
  "reason": "说明",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "permissionDecision": "allow|deny",
    "permissionDecisionReason": "说明"
  }
}
```

### 错误码定义

| 错误码 | 含义 | 处理方式 |
|--------|------|----------|
| E001 | 工具执行超时 | 重试或换工具 |
| E002 | 参数验证失败 | 修正参数 |
| E003 | 权限不足 | 提升权限或换方式 |
| E004 | 资源不可用 | 等待或换资源 |
| E005 | 上下文溢出 | 压缩上下文 |
| E006 | 循环检测 | 强制中断 |
| E007 | 级联错误 | 暂停并分析 |

### 性能指标

| 指标 | 目标 | 当前 |
|------|------|------|
| Hook 执行延迟 | < 100ms | ~50ms |
| 错误检测准确率 | > 95% | ~90% |
| 误报率 | < 5% | ~8% |
| 内存占用 | < 50MB | ~30MB |

---

## 风险评估

### 高风险
- **性能影响**: 新增钩子可能增加执行延迟
- **兼容性**: 新钩子可能与现有钩子冲突
- **稳定性**: 复杂条件可能导致误判

### 中风险
- **维护成本**: 更多钩子意味着更多维护工作
- **调试难度**: 复杂触发条件增加调试难度
- **资源消耗**: 更多监控增加系统负载

### 低风险
- **学习曲线**: 新功能需要时间学习
- **文档更新**: 需要更新文档和示例

---

## 缓解措施

1. **性能优化**: 使用异步执行，避免阻塞主流程
2. **渐进式部署**: 先在测试环境验证，再逐步推广
3. **完善监控**: 添加钩子执行监控，及时发现问题
4. **文档完善**: 提供详细文档和示例
5. **回滚机制**: 保留旧版本配置，支持快速回滚
