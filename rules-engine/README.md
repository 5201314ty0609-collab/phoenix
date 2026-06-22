# PHOENIX Rules Engine v2.0

智能规则管理系统，提供动态加载、冲突检测、依赖管理和上下文感知。

## 核心特性

### 1. 动态规则加载
- 根据任务类型、语言和域名智能加载规则
- 基于相关性评分的优先级排序
- Token 预算控制，避免上下文溢出

### 2. 规则冲突检测
- 显式冲突声明检测
- 同域规则矛盾检测
- 触发条件重叠检测
- 优先级冲突检测

### 3. 规则依赖管理
- 显式依赖声明
- 依赖完整性验证
- 反向依赖追踪

### 4. 规则版本控制
- 版本号管理
- 创建/更新时间追踪
- 变更历史记录

### 5. 语义规则匹配
- 基于触发条件的匹配
- 基于域名的匹配
- 基于任务类型的匹配

### 6. 规则优先级
- 1-10 级优先级（10 = 最高）
- 基于 stage、enforcement、layer 的自动计算
- 冲突时的优先级仲裁

## 工具集

### Rule Engine (`rule_engine.py`)
核心规则引擎，提供分析、冲突检测、依赖查询和上下文匹配。

```bash
# 分析规则系统
python3 rule_engine.py analyze

# 检测规则冲突
python3 rule_engine.py conflicts

# 查看规则依赖
python3 rule_engine.py deps <rule-id>

# 获取上下文相关规则
python3 rule_engine.py context <task-type> [language] [domains...]

# 验证规则完整性
python3 rule_engine.py validate
```

### Rule Migrator (`rule_migrator.py`)
规则格式迁移工具，将现有规则迁移到新格式。

```bash
# 扫描需要迁移的规则
python3 rule_migrator.py scan

# 迁移单个规则
python3 rule_migrator.py migrate <rule-id>

# 迁移所有规则
python3 rule_migrator.py migrate-all

# 验证迁移结果
python3 rule_migrator.py validate <rule-id>
```

### Rule Manager (`rule_manager.py`)
规则生命周期管理工具。

```bash
# 创建新规则
python3 rule_manager.py create <rule-id> <category> [name] [layer] [priority]

# 更新规则
python3 rule_manager.py update <rule-id> [key=value...]

# 废弃规则
python3 rule_manager.py deprecate <rule-id> [reason]

# 删除规则
python3 rule_manager.py delete <rule-id> [--force]

# 列出规则
python3 rule_manager.py list [category] [layer] [stage]

# 统计信息
python3 rule_manager.py stats

# 提升规则阶段
python3 rule_manager.py promote <rule-id> <stage>
```

### Rule Health (`phoenix-rule-health.py`)
规则健康检查和优化建议。

```bash
# 生成健康报告
python3 phoenix-rule-health.py report

# 查看单个规则评分
python3 phoenix-rule-health.py score <rule-id>

# 优化建议
python3 phoenix-rule-health.py optimize

# 综合仪表盘
python3 phoenix-rule-health.py dashboard
```

## 规则格式

### 新格式（推荐）

```markdown
# Rule Title (PHOENIX Rule)

> Auto-generated rule from PHOENIX Evolution Engine
> Stage: active | Enforcement: rule file (Level 4)
> Version: 1.0.0
> Created: 2026-06-19
> Updated: 2026-06-19

## Metadata

- **Rule ID**: rule-id
- **Category**: coding-style
- **Priority**: 7
- **Layer**: phoenix
- **Languages**: all

## Trigger

When [specific condition].

## Dependencies

- dependency-rule-id

## Conflicts With

- conflicting-rule-id

## Supersedes

- superseded-rule-id

## Action

[Rule content]

## Domains

domain1, domain2
```

### 元数据字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| Rule ID | string | 规则唯一标识符 |
| Category | enum | 分类：coding-style, testing, security, performance, patterns, hooks, agents, git-workflow, design, evolution |
| Priority | int | 优先级 1-10，10 = 最高 |
| Layer | enum | 层级：common, phoenix, language-specific, translation |
| Languages | list | 适用语言，all 表示所有语言 |
| Version | string | 语义化版本号 |
| Created | date | 创建日期 |
| Updated | date | 最后更新日期 |
| Stage | enum | 阶段：draft, active, observed, validated, hardened |
| Enforcement | int | 强制执行级别 1-7 |
| Dependencies | list | 依赖的规则 ID |
| Conflicts With | list | 冲突的规则 ID |
| Supersedes | list | 被取代的规则 ID |
| Domains | list | 域名标签 |

## 规则生命周期

```
draft → active → observed → validated → hardened
                          ↘ deprecated
```

| 阶段 | 说明 | 条件 |
|------|------|------|
| draft | 草稿 | 新创建的规则 |
| active | 活跃 | 开始被使用 |
| observed | 观察中 | 3+ 次观察，>30% 成功率 |
| validated | 已验证 | 10+ 次观察，>60% 成功率，>70% 成功率 |
| hardened | 已固化 | 50+ 次观察，>90% 成功率，0 次矛盾 |
| deprecated | 已废弃 | 不再推荐使用 |

## 优先级计算

优先级基于以下因素自动计算：

```
priority = base + stage_bonus + enforcement_bonus + layer_bonus
```

| 因素 | 加成范围 |
|------|----------|
| Stage | +0 (draft) ~ +4 (hardened) |
| Enforcement Level | +0 (1-3) ~ +2 (6-7) |
| Layer | +0 (common) ~ +1 (phoenix) |

## 冲突检测

### 冲突类型

| 类型 | 说明 | 严重程度 |
|------|------|----------|
| explicit | 显式声明的冲突 | high |
| contradictory | 同域规则矛盾 | medium |
| overlapping | 触发条件重叠 | low |
| priority | 优先级冲突 | high |

### 冲突解决

1. **显式冲突**：使用 `Conflicts With` 声明，由用户决定优先级
2. **同域矛盾**：合并或拆分规则
3. **触发重叠**：合并触发条件或调整优先级
4. **优先级冲突**：调整 `Supersedes` 声明或优先级

## 上下文感知加载

### 匹配因素

| 因素 | 权重 | 说明 |
|------|------|------|
| 语言匹配 | 0.3 | 规则适用语言与当前语言匹配 |
| 域名匹配 | 0.3 | 规则域名与任务域名匹配 |
| 任务类型匹配 | 0.2 | 规则分类与任务类型匹配 |
| 优先级 | 0.2 | 规则优先级分数 |

### 加载策略

1. 计算所有规则的相关性分数
2. 按分数降序排序
3. 应用 Token 预算限制
4. 加载 top-N 规则

## 集成指南

### 与 PHOENIX Evolution Engine 集成

```python
from rule_engine import RuleEngine

engine = RuleEngine()

# 扫描规则
engine.registry.scan_rules()

# 获取上下文规则
matches = engine.context_matcher.get_relevant_rules(
    task_type="code-review",
    language="typescript",
    domains=["security", "testing"],
)

# 加载规则文件
for match in matches:
    if match.should_load:
        rule = engine.registry.get_rule(match.rule_id)
        # 加载规则内容...
```

### 与 Claude Code 集成

在 `.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "command": "python3 ~/.claude/phoenix/rules-engine/rule_engine.py context $TASK_TYPE $LANGUAGE",
        "description": "Load context-aware rules"
      }
    ]
  }
}
```

## 最佳实践

### 规则创建

1. 使用 `rule_manager.py create` 创建规则
2. 填写完整的元数据
3. 声明依赖和冲突
4. 设置合理的优先级

### 规则维护

1. 定期运行 `rule_engine.py validate` 检查完整性
2. 使用 `phoenix-rule-health.py report` 监控健康状态
3. 及时废弃不再使用的规则
4. 保持规则文档更新

### 规则优化

1. 运行 `phoenix-rule-health.py optimize` 获取优化建议
2. 合并重叠的规则
3. 简化过于复杂的规则
4. 删除未使用的规则

## 文件结构

```
~/.claude/phoenix/rules-engine/
├── README.md                    # 本文档
├── rule_engine.py              # 核心规则引擎
├── rule_migrator.py            # 规则格式迁移工具
├── rule_manager.py             # 规则生命周期管理
├── rule-template.md            # 规则模板
├── rule-registry.json          # 规则注册表
├── conflicts.jsonl             # 冲突日志
├── migration-log.jsonl         # 迁移日志
└── manager-log.jsonl           # 管理操作日志
```

## 与现有系统的关系

### 与 phoenix-rule-health.py 的关系

- `phoenix-rule-health.py` 专注于规则健康评分和优化建议
- `rule_engine.py` 提供更全面的规则管理功能
- 两者共享规则注册表数据

### 与 evolve.py 的关系

- `evolve.py` 负责框架发现和进化
- `rule_engine.py` 负责规则生命周期管理
- 框架进化到 validated 阶段后，由 `rule_engine.py` 管理

### 与 metacog-observer 的关系

- `metacog-observer` 检测重复模式
- 检测到的模式存储为框架
- 框架进化为规则后，由 `rule_engine.py` 管理

## 版本历史

- **v2.0.0** (2026-06-19): 重构为智能规则引擎
  - 添加动态规则加载
  - 添加冲突检测
  - 添加依赖管理
  - 添加上下文感知
- **v1.0.0** (2026-06-17): 初始版本
  - 基础规则健康检查
  - DSPy 风格优化评分
