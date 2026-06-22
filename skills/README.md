# PHOENIX Skills System v2.0

PHOENIX 的轻量级技能系统，从 5 个基础技能扩展为 13 个专业技能，支持管道组合、学习推荐、使用追踪。

## Architecture

```
phoenix-skill.py (统一入口)
    |
    +-- skills/                 # 技能模块
    |   +-- code-tidy.py        # 代码整理
    |   +-- verify-completion.py # 完成验证
    |   +-- complexity-analyzer.py # 复杂度分析
    |   +-- security-audit.py   # 安全审计
    |   +-- systematic-debug.py # 系统调试
    |   +-- dispatch-parallel.py # 并行分派
    |   +-- pr-prep.py          # PR 准备
    |   +-- knowledge-sync.py   # 知识同步
    |   +-- doc-gen.py          # 文档生成
    |   +-- health-check.py     # 健康检查
    |   +-- skill-pipeline.py   # 管道引擎
    |   +-- skill-learn.py      # 学习系统
    |
    +-- skill-registry.py       # 依赖/冲突管理
    +-- pipelines.json          # 管道定义
    +-- skill-usage.jsonl       # 使用记录
    +-- pipeline-history.jsonl  # 管道执行历史
```

## Skills (13 total)

### Code Quality

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `code-tidy` | 清理未使用 import、注释代码、排序 | `--dry-run` |
| `verify` | 语法检查、常见问题检测 | `--strict` |
| `complexity` | 圈复杂度、函数长度、嵌套深度分析 | `--threshold N`, `--json` |

### Security

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `security` | 硬编码密钥、SQL 注入、XSS、路径遍历扫描 | `--strict`, `--json` |

### Workflow

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `debug` | 4 阶段根因调试 | `start`, `note`, `hypothesis`, `verify`, `resolve` |
| `dispatch` | 并行任务分析与分派 | `analyze`, `plan`, `execute` |
| `pr-prep` | PR 描述、变更摘要、检查清单 | `summary`, `description`, `checklist`, `diff` |

### Testing

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `mutation-gate` | TDD 变体验证 | `run`, `check`, `fix-prompt` |

### Knowledge

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `knowledge-sync` | memory/ 到 SQLite 同步 | `sync`, `status`, `rebuild` |
| `doc-gen` | docstring 添加、README 生成、API 文档 | `docstrings`, `readme`, `api` |

### System

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `health` | 系统健康检查 | `quick`, `--json` |

### Meta

| Skill | Description | Key Flags |
|-------|-------------|-----------|
| `pipeline` | 技能管道组合与执行 | `run`, `list`, `define`, `run-pipeline`, `history` |
| `learn` | 使用追踪、技能推荐、模式检测 | `record`, `recommend`, `stats`, `history`, `patterns`, `score` |

## Usage Examples

### Single Skill

```bash
# 代码整理
phoenix-skill.py code-tidy src/ --dry-run

# 安全审计
phoenix-skill.py security src/ --strict

# 复杂度分析
phoenix-skill.py complexity src/ --threshold 15

# 健康检查
phoenix-skill.py health quick
```

### Pipeline (链式执行)

```bash
# 预定义管道
phoenix-skill.py pipeline run-pipeline code-quality --target src/
phoenix-skill.py pipeline run-pipeline pre-commit --target src/
phoenix-skill.py pipeline run-pipeline security-review --target src/
phoenix-skill.py pipeline run-pipeline full-review --target src/

# 临时管道
phoenix-skill.py pipeline run code-tidy security-audit verify --target src/

# 定义自定义管道
phoenix-skill.py pipeline define my-check code-tidy security verify

# 查看管道历史
phoenix-skill.py pipeline history
```

### Learning & Recommendation

```bash
# 记录使用
phoenix-skill.py learn record security-audit success --context "pre-deploy check"
phoenix-skill.py learn record code-tidy failure --error "encoding issue"

# 获取推荐
phoenix-skill.py recommend "need to find security vulnerabilities"
phoenix-skill.py recommend "code quality check before merge"

# 查看统计
phoenix-skill.py learn stats

# 检测使用模式
phoenix-skill.py learn patterns

# 查看技能评分
phoenix-skill.py learn score security-audit
```

## Predefined Pipelines

| Pipeline | Steps | Use Case |
|----------|-------|----------|
| `code-quality` | tidy -> verify -> complexity | 日常代码质量检查 |
| `security-review` | security -> verify -> complexity | 安全审查 |
| `pre-commit` | tidy -> security -> verify | 提交前检查 |
| `full-review` | tidy -> security -> verify -> complexity -> doc-gen | 完整代码审查 |

## Integration with PHOENIX Ecosystem

### Reflection Engine
Skills 的执行结果自动记录到反思引擎：
```bash
phoenix-skill.py learn record <skill> <result> --context "task context"
```

### Observability
7-Sense 系统监控技能使用模式：
- **Spatial**: 文件变更追踪（code-tidy, verify）
- **Nociception**: 错误级联检测（security, complexity）
- **Echo**: 重复模式检测（learn patterns）

### Auto-Memory
技能使用模式自动捕获到 auto-memory：
- 频繁使用的技能组合 -> 建议创建管道
- 高失败率的技能 -> 触发调查
- 成功模式 -> 强化推荐权重

## Skill Learning Algorithm

### Scoring Formula
```
composite = success_rate * 40 + recency * 25 + frequency * 20 + trend * 15
```

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Success Rate | 40% | successes / total_uses |
| Recency | 25% | max(0, 1 - days_since_last_use / 30) |
| Frequency | 25% | min(1, total_uses / 20) |
| Trend | 15% | rising=1.0, stable=0.7, declining=0.3 |

### Pattern Detection
- **Frequent Combos**: Skills used within 5 minutes of each other
- **Error Clusters**: Skills with >30% failure rate
- **Time Patterns**: Skills consistently used at specific hours

### Recommendation
1. Keyword matching against skill context profiles
2. Historical score boost for proven skills
3. Trend adjustment for rising/declining skills

## Adding New Skills

1. Create `skills/<name>.py` with a `main()` function
2. Register in `phoenix-skill.py` SKILLS dict
3. Add context keywords to `skill-learn.py` SKILL_CONTEXT_KEYWORDS
4. Optionally add to predefined pipelines in `skill-pipeline.py`

```python
# In phoenix-skill.py SKILLS:
"my-skill": {
    "description": "What it does",
    "module": "my-skill",
    "usage": "my-skill <args>",
    "category": "quality",  # quality/security/workflow/testing/knowledge/system/meta
},
```
