---
name: writing-skills
description: Use when creating or modifying skill files to ensure consistent quality and prevent Agent from skipping content.
---

# 鲤鱼技能编写规范

## 核心原则

技能是**强制性工作流，不是建议**。

## SKILL.md 结构

```yaml
---
name: skill-name
description: Use when [触发条件]. [可选：简要说明]
---
```

### YAML Frontmatter 规范

- `name`（必填）：技能名称，kebab-case
- `description`（必填）：最多 1024 字符，**必须以 "Use when..." 开头**
- **禁止**在 description 中写工作流总结（会导致 Agent 跳过阅读完整内容）

### 正文规范

1. **标题**：`# 技能名称`
2. **核心流程**：<200 词，用步骤列表
3. **详细说明**：用交叉引用，避免重复
4. **示例**：具体、可执行
5. **反模式**：常见错误和规避方法

## 技能分类

| 类型 | 说明 | 示例 |
|------|------|------|
| **techniques** | 具体方法 | TDD、代码审查 |
| **patterns** | 心智模型 | 设计模式、架构原则 |
| **references** | API 文档/指南 | 框架文档、CLI 参考 |

## Token 预算

- Getting-started 流程：<150 词
- 常用技能：<200 词
- 参考细节：用交叉引用或 `--help` 输出

## 质量检查清单

- [ ] description 以 "Use when..." 开头
- [ ] description 不包含工作流总结
- [ ] 核心流程 <200 词
- [ ] 使用交叉引用替代重复
- [ ] 示例具体可执行
- [ ] 包含反模式 section

## 反合理化机制

### 常见借口 vs 反驳

| 借口 | 反驳 |
|------|------|
| "这个技能太简单不需要" | 简单技能也需要规范，防止退化 |
| "我先写代码再补技能" | 技能是强制工作流，不是文档 |
| "这个技能只用一次" | 一次性技能也需要规范 |
| "我很有经验不需要规范" | 经验不能替代规范 |

### 违规信号

- description 不以 "Use when..." 开头
- 核心流程超过 200 词
- 没有交叉引用，内容重复
- 没有反模式 section

## 与鲤鱼的集成

1. **skill-registry.py** — 技能注册时检查规范
2. **liyu-framework-promoter.py** — 技能晋升时检查规范
3. **liyu-correction-lifecycle.py** — 违规时触发纠正

## Domains

skills, authoring, specification, quality

## Evolution History

- Created: 2026-07-10 from obra/superpowers
- Source: Superpowers 技能编写规范
