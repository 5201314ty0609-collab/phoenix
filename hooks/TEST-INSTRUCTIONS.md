# PHOENIX Enhanced Hooks 测试说明

由于权限限制，需要手动运行测试。请按照以下步骤进行测试。

## 快速测试

运行安装脚本的测试模式：

```bash
cd ~/.claude/phoenix/hooks
./setup-enhanced-hooks.sh --test
```

## 手动测试各个 Hooks

### 1. 测试 ToolError Hook

```bash
echo '{"tool_name":"Bash","error_message":"permission denied","error_type":"permission"}' | \
  bash ~/.claude/phoenix/hooks/tool-error.sh
```

**预期输出**: JSON 包含 decision, reason, recovery_suggestions

### 2. 测试 ContextCompaction Hook

```bash
echo '{"session_id":"test-123","context_usage":85,"message_count":50,"compression_type":"auto"}' | \
  bash ~/.claude/phoenix/hooks/context-compaction.sh
```

**预期输出**: JSON 包含 decision, reason, compaction_summary

### 3. 测试 AgentSpawn Hook

```bash
echo '{"agent_type":"specialist","agent_name":"test-agent","task_description":"测试任务","parent_agent":"main"}' | \
  bash ~/.claude/phoenix/hooks/agent-spawn.sh
```

**预期输出**: JSON 包含 agent_id, coordination 信息

### 4. 测试 AgentComplete Hook

```bash
echo '{"agent_id":"agent_test_123","status":"completed","result_summary":"测试完成","duration_seconds":60}' | \
  bash ~/.claude/phoenix/hooks/agent-complete.sh
```

**预期输出**: JSON 包含 completion_info, coordination 统计

### 5. 测试 Smart Trigger

```bash
# 评估触发条件
python3 ~/.claude/phoenix/hooks/smart-trigger.py evaluate TestHook '{"error_count":3}'

# 查看触发条件
python3 ~/.claude/phoenix/hooks/smart-trigger.py conditions

# 查看触发统计
python3 ~/.claude/phoenix/hooks/smart-trigger.py stats
```

### 6. 测试 Notification Center

```bash
# 添加通知
python3 ~/.claude/phoenix/hooks/notification-center.py add error_recovery high "测试错误恢复通知"

# 列出通知
python3 ~/.claude/phoenix/hooks/notification-center.py list

# 查看统计
python3 ~/.claude/phoenix/hooks/notification-center.py stats
```

### 7. 测试 Status Indicator

```bash
# 显示状态概览
python3 ~/.claude/phoenix/hooks/status-indicator.py overview

# 显示健康分数
python3 ~/.claude/phoenix/hooks/status-indicator.py health

# 显示趋势分析
python3 ~/.claude/phoenix/hooks/status-indicator.py trends --hours 24

# 显示当前警告
python3 ~/.claude/phoenix/hooks/status-indicator.py warnings
```

### 8. 测试 Realtime Monitor v2

```bash
python3 ~/.claude/phoenix/hooks/realtime-monitor-v2.py
```

**预期输出**: JSON 包含 health_score, sense_statuses, metrics_summary

## 查看系统状态

```bash
./setup-enhanced-hooks.sh --status
```

## 清理旧文件

```bash
./setup-enhanced-hooks.sh --cleanup
```

## 检查配置

### 检查 settings.json

```bash
cat ~/.claude/settings.json | python3 -m json.tool | grep -A5 "ToolError"
```

### 检查智能触发配置

```bash
cat ~/.claude/phoenix/smart-trigger-config.json | python3 -m json.tool
```

### 检查通知偏好

```bash
cat ~/.claude/phoenix/notification-preferences.json | python3 -m json.tool
```

## 查看日志

### 错误日志

```bash
tail -20 ~/.claude/phoenix/tool-error-log.jsonl
```

### 通知历史

```bash
tail -20 ~/.claude/phoenix/notification-history.jsonl
```

### 触发历史

```bash
tail -20 ~/.claude/phoenix/smart-trigger-history.jsonl
```

### Agent 生命周期

```bash
tail -20 ~/.claude/phoenix/agent-lifecycle.jsonl
```

### 压缩日志

```bash
tail -20 ~/.claude/phoenix/compaction-log.jsonl
```

## 故障排除

### 问题: Hook 执行失败

```bash
# 检查权限
ls -la ~/.claude/phoenix/hooks/*.sh

# 修复权限
chmod +x ~/.claude/phoenix/hooks/*.sh
chmod +x ~/.claude/phoenix/hooks/*.py
```

### 问题: 通知不显示

```bash
# 检查通知队列
python3 ~/.claude/phoenix/hooks/notification-center.py list --limit 50

# 检查通知偏好
python3 ~/.claude/phoenix/hooks/notification-center.py preferences
```

### 问题: 智能触发不工作

```bash
# 启用调试模式
python3 -c "
import json
config_file = '/Users/holyty/.claude/phoenix/smart-trigger-config.json'
with open(config_file) as f:
    config = json.load(f)
config['global_settings']['enable_debug'] = True
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
print('调试模式已启用')
"

# 再次测试
python3 ~/.claude/phoenix/hooks/smart-trigger.py evaluate TestHook '{"error_count":3}'
```

### 问题: 监控数据不准确

```bash
# 检查 Tool Guard 状态
python3 ~/.claude/phoenix/tool-guard.py stats

# 检查 Sense 文件
ls -la ~/.claude/phoenix/senses/

# 手动更新监控
python3 ~/.claude/phoenix/hooks/realtime-monitor-v2.py
```

## 完整测试流程

1. 运行安装脚本:
   ```bash
   ./setup-enhanced-hooks.sh
   ```

2. 运行测试:
   ```bash
   ./setup-enhanced-hooks.sh --test
   ```

3. 查看状态:
   ```bash
   ./setup-enhanced-hooks.sh --status
   ```

4. 手动测试各个功能（参考上面的命令）

5. 检查日志文件确保正常工作

6. 清理测试数据:
   ```bash
   ./setup-enhanced-hooks.sh --cleanup
   ```

## 预期结果

### 成功指标

- 所有 hook 脚本返回有效的 JSON
- 通知系统正常添加和列出通知
- 智能触发引擎正确评估条件
- 状态指示器显示健康分数
- 监控数据实时更新

### 性能指标

- Hook 执行时间 < 100ms
- 通知添加时间 < 50ms
- 状态查询时间 < 200ms
- 内存占用 < 50MB

## 下一步

测试完成后，可以：

1. 将增强版配置应用到正式环境
2. 根据实际使用情况调整触发条件
3. 优化通知偏好设置
4. 监控系统运行状态
5. 根据反馈持续改进
