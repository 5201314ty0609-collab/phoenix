---
name: test-driven-development
description: Use when writing or modifying code to enforce strict TDD discipline with anti-rationalization mechanisms.
---

# 鲤鱼 TDD 强制执行

## 铁律

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

## 红-绿-重构循环

### RED（写测试）

1. 写一个最小测试
2. 验证它确实因预期原因失败
3. 如果测试通过，**停止** — 你不需要这个测试

### GREEN（写实现）

1. 写最简单的代码让测试通过
2. **禁止**添加额外功能
3. **禁止**优化代码

### REFACTOR（重构）

1. 仅在测试全绿后重构
2. 保持测试通过
3. 每次重构后运行测试

## 反合理化机制

### 常见借口 vs 反驳

| 借口 | 反驳 |
|------|------|
| "太简单不需要测试" | 简单代码也会坏，写测试只需 30 秒 |
| "以后再补测试" | 后补的测试立即通过，什么也证明不了 |
| "已经手动测过了" | 手动测试不可重复，没有记录 |
| "删掉 X 小时的工作太浪费" | 沉没成本谬误，保留未验证的代码才是真正的浪费 |
| "这个测试太慢了" | 慢测试比没有测试好，先让它工作再优化 |
| "我很有信心" | 信心不等于证据，需要运行的测试 |
| "就这一次" | 没有"就这一次"，每次都是 precedent |

### 违规检测

**必须删除并重写的情况：**
- 在测试前写了实现代码
- 测试立即通过（无法验证实现正确性）
- 无法解释为何测试失败

**红旗信号：**
- "should work now"
- "I'm confident"
- "just this once"
- 验证前庆祝

### Bug 修复流程

1. 先写失败测试复现 bug
2. 验证测试确实失败
3. 修复 bug
4. 验证测试通过
5. 检查是否有类似 bug

## 验证先于完成

### 五步门控流程

1. **识别**：找到证明声明的命令
2. **运行**：新鲜运行完整命令
3. **阅读**：检查所有输出，计数失败
4. **验证**：确认输出实际支持声明
5. **声明**：只有此时才能发表声明

### 禁止的短语

- "should work now"
- "I'm confident"
- "just this once"
- "this time for sure"

## 与鲤鱼的集成

1. **liyu-correction-lifecycle.py** — 违规时触发纠正
2. **liyu-identity-drift.py** — 检测 robot mode
3. **liyu-framework-promoter.py** — TDD 技能晋升时检查规范

## Domains

tdd, testing, quality, discipline

## Evolution History

- Created: 2026-07-10 from obra/superpowers
- Source: Superpowers TDD 强制执行机制
