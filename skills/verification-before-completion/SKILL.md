---
name: verification-before-completion
description: Use before claiming a task is complete to ensure evidence-based verification.
---

# 鲤鱼验证先于完成

## 铁律

**Evidence before claims, always**

## 五步门控流程

### 1. 识别

找到证明声明的命令：
- 测试命令：`pytest`, `jest`, `go test`
- 构建命令：`npm run build`, `cargo build`
- 类型检查：`tsc --noEmit`, `mypy`
- Lint：`eslint`, `ruff`

### 2. 运行

新鲜运行完整命令：
- **禁止**使用缓存结果
- **禁止**跳过任何步骤
- **禁止**假设"应该没问题"

### 3. 阅读

检查所有输出：
- 计数失败
- 检查退出码
- 阅读错误消息

### 4. 验证

确认输出实际支持声明：
- 测试通过 ≠ 代码正确
- 构建成功 ≠ 功能正常
- 类型检查通过 ≠ 无运行时错误

### 5. 声明

只有此时才能发表声明：
- "测试通过" — 必须有测试输出
- "构建成功" — 必须有构建输出
- "功能正常" — 必须有验证输出

## 禁止的短语

- "should work now"
- "I'm confident"
- "just this once"
- "this time for sure"
- "I've checked it"
- "it looks good"

## 红旗信号

- 验证前庆祝
- 无法解释为何测试失败
- 跳过验证步骤
- 使用缓存结果

## 与鲤鱼的集成

1. **liyu-correction-lifecycle.py** — 违规时触发纠正
2. **liyu-identity-drift.py** — 检测 robot mode
3. **liyu-framework-promoter.py** — 验证技能晋升时检查规范

## Domains

verification, completion, quality, discipline

## Evolution History

- Created: 2026-07-10 from obra/superpowers
- Source: Superpowers 验证先于完成机制
