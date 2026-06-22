# 按钮组件 (Button)

> 组件类型: 交互元素
> 最后更新: 2026-06-19

---

## 概述

按钮是用户与系统交互的主要触点。PHOENIX 按钮系统提供清晰的视觉层次和一致的交互反馈。

---

## 变体 (Variants)

### 1. 类型 (Type)

| 变体 | 用途 | 视觉特征 |
|------|------|----------|
| **Primary** | 主要操作 | 实心填充，高对比度 |
| **Secondary** | 次要操作 | 描边样式，中等对比度 |
| **Ghost** | 辅助操作 | 透明背景，低对比度 |
| **Danger** | 危险操作 | 红色系，警示用户 |
| **Link** | 链接样式 | 无边框，文字链接 |

### 2. 尺寸 (Size)

| 尺寸 | 高度 | 内边距 | 字号 | 图标尺寸 |
|------|------|--------|------|----------|
| **Small** | 32px | 8px 12px | 14px | 16px |
| **Medium** | 40px | 12px 16px | 14px | 16px |
| **Large** | 48px | 16px 24px | 16px | 20px |

### 3. 状态 (State)

| 状态 | 视觉变化 |
|------|----------|
| **Default** | 基础样式 |
| **Hover** | 背景色变亮/变暗 10% |
| **Active/Pressed** | 背景色变暗/变亮 10%，轻微缩放 |
| **Focus** | 焦点环 (2px accent 色) |
| **Disabled** | 透明度 50%，禁止光标 |
| **Loading** | 显示加载动画，禁用交互 |

---

## 设计规范

### Primary 按钮

```
背景: --color-primary-500
文字: --text-primary (白色)
圆角: --radius-md
边框: 无

Hover:
  背景: --color-primary-400

Active:
  背景: --color-primary-600

Disabled:
  背景: --color-primary-500 / 50%
  文字: --text-primary / 50%
```

### Secondary 按钮

```
背景: transparent
文字: --text-primary
边框: 1px solid --border-default
圆角: --radius-md

Hover:
  背景: --surface-tertiary
  边框: --border-hover

Active:
  背景: --surface-secondary
```

### Ghost 按钮

```
背景: transparent
文字: --text-secondary
边框: 无
圆角: --radius-md

Hover:
  背景: --surface-tertiary
  文字: --text-primary
```

### Danger 按钮

```
背景: --color-error
文字: 白色
边框: 无
圆角: --radius-md

Hover:
  背景: oklch(55% 0.20 25)  /* 更深的红色 */
```

---

## 图标按钮

### 图标位置

```
Leading Icon: 图标在文字左侧
Trailing Icon: 图标在文字右侧
Icon Only: 仅显示图标（正方形按钮）
```

### 图标间距

```
图标与文字间距: --space-2 (8px)
```

---

## 按钮组

```css
.button-group {
  display: flex;
  gap: var(--space-2);
}

/* 连接式按钮组 */
.button-group--connected {
  gap: 0;
}

.button-group--connected .button:not(:first-child) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.button-group--connected .button:not(:last-child) {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}
```

---

## 交互规范

### 点击反馈

- **即时反馈**: 背景色变化在 100ms 内完成
- **波纹效果**: 可选，仅在 Ghost 和 Secondary 按钮上使用
- **状态恢复**: Hover → Default 在 200ms 内完成

### 焦点管理

```css
.button:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}
```

### 加载状态

```html
<button class="button button--loading" disabled>
  <span class="button__spinner"></span>
  <span class="button__text">处理中...</span>
</button>
```

---

## 无障碍

- 所有按钮必须有明确的文字标签或 `aria-label`
- 禁用状态使用 `disabled` 属性，不仅依赖样式
- 图标按钮必须提供 `aria-label`
- 按钮必须可通过键盘激活 (Enter/Space)

---

## Figma 组件结构

```
Button/
├── Primary/
│   ├── Small/
│   │   ├── Default
│   │   ├── Hover
│   │   ├── Active
│   │   ├── Focus
│   │   ├── Disabled
│   │   └── Loading
│   ├── Medium/
│   └── Large/
├── Secondary/
├── Ghost/
├── Danger/
└── Link/
```

---

## 使用示例

### 基础用法

```html
<!-- 主按钮 -->
<button class="button button--primary">确认</button>

<!-- 带图标 -->
<button class="button button--primary">
  <svg><!-- icon --></svg>
  保存
</button>

<!-- 图标按钮 -->
<button class="button button--ghost button--icon" aria-label="设置">
  <svg><!-- icon --></svg>
</button>
```

### 最佳实践

1. 每个视图最多一个 Primary 按钮
2. 危险操作需要二次确认
3. 按钮文字使用动词（保存、删除、提交）
4. 避免使用"点击这里"
5. 加载状态禁用按钮防止重复提交
