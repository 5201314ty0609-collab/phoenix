# 卡片组件 (Card)

> 组件类型: 容器元素
> 最后更新: 2026-06-19

---

## 概述

卡片是 鲤鱼 界面中最常用的容器元素，用于组织和展示相关信息单元。

---

## 变体 (Variants)

### 1. 类型 (Type)

| 变体 | 用途 | 视觉特征 |
|------|------|----------|
| **Default** | 通用容器 | 边框样式 |
| **Elevated** | 浮层内容 | 阴影效果 |
| **Filled** | 强调内容 | 背景填充 |
| **Interactive** | 可点击卡片 | 悬停效果 |
| **Glass** | 玻璃拟态 | 毛玻璃效果 |

### 2. 尺寸 (Size)

| 尺寸 | 内边距 | 圆角 |
|------|--------|------|
| **Small** | 12px | 8px |
| **Medium** | 16px | 12px |
| **Large** | 24px | 16px |

---

## 设计规范

### Default 卡片

```
背景: --bg-card
边框: 1px solid --border-default
圆角: --radius-lg
内边距: --padding-card-md
```

### Elevated 卡片

```
背景: --bg-card
边框: 无
阴影: --shadow-lg
圆角: --radius-lg
内边距: --padding-card-md
```

### Filled 卡片

```
背景: --surface-tertiary
边框: 无
圆角: --radius-lg
内边距: --padding-card-md
```

### Interactive 卡片

```
背景: --bg-card
边框: 1px solid --border-default
圆角: --radius-lg
内边距: --padding-card-md
光标: pointer

Hover:
  边框: --border-hover
  阴影: --shadow-md
  transform: translateY(-2px)

Active:
  transform: translateY(0)
```

### Glass 卡片

```css
.card--glass {
  background: oklch(25% 0 0 / 60%);
  backdrop-filter: blur(12px);
  border: 1px solid oklch(100% 0 0 / 10%);
  border-radius: var(--radius-lg);
}
```

---

## 卡片结构

### 基础结构

```html
<article class="card">
  <div class="card__header">
    <h3 class="card__title">标题</h3>
    <p class="card__description">描述文本</p>
  </div>
  <div class="card__body">
    <!-- 内容 -->
  </div>
  <div class="card__footer">
    <!-- 操作按钮 -->
  </div>
</article>
```

### 带图片

```html
<article class="card">
  <div class="card__media">
    <img src="image.jpg" alt="描述" loading="lazy" />
  </div>
  <div class="card__content">
    <h3 class="card__title">标题</h3>
    <p class="card__description">描述</p>
  </div>
</article>
```

---

## 卡片样式

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--padding-card-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.card__header {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.card__title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  line-height: var(--leading-snug);
}

.card__description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-normal);
}

.card__media {
  margin: calc(-1 * var(--padding-card-md));
  margin-bottom: 0;
  overflow: hidden;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.card__media img {
  width: 100%;
  height: auto;
  display: block;
}

.card__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-top: auto;
}
```

---

## 卡片网格

### 自动填充网格

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--grid-gap);
}
```

### 固定列数

```css
.card-grid--2 { grid-template-columns: repeat(2, 1fr); }
.card-grid--3 { grid-template-columns: repeat(3, 1fr); }
.card-grid--4 { grid-template-columns: repeat(4, 1fr); }
```

---

## 特殊卡片

### 统计卡片

```html
<div class="stat-card">
  <div class="stat-card__icon">
    <svg><!-- icon --></svg>
  </div>
  <div class="stat-card__content">
    <span class="stat-card__label">总用户数</span>
    <span class="stat-card__value">12,345</span>
    <span class="stat-card__change stat-card__change--positive">
      +12.5%
    </span>
  </div>
</div>
```

### Agent 状态卡片

```html
<div class="agent-card">
  <div class="agent-card__header">
    <div class="agent-card__avatar">
      <svg><!-- agent icon --></svg>
    </div>
    <div class="agent-card__info">
      <h3 class="agent-card__name">Code Reviewer</h3>
      <span class="agent-card__status agent-card__status--active">
        运行中
      </span>
    </div>
  </div>
  <div class="agent-card__body">
    <p class="agent-card__task">正在审查 PR #123</p>
  </div>
  <div class="agent-card__footer">
    <button class="button button--ghost button--sm">查看</button>
    <button class="button button--ghost button--sm">暂停</button>
  </div>
</div>
```

---

## 交互规范

### 悬停效果

- 轻微上移: `translateY(-2px)`
- 阴影增强: `--shadow-md` → `--shadow-lg`
- 边框颜色变化: `--border-default` → `--border-hover`
- 过渡时间: 200ms

### 点击效果

- 轻微下移: `translateY(0)`
- 过渡时间: 100ms

---

## 无障碍

- 使用语义化标签: `<article>` 或 `<section>`
- 可点击卡片需要 `role="link"` 或 `tabindex="0"`
- 提供清晰的焦点指示器
- 卡片标题使用正确的标题层级

---

## Figma 组件结构

```
Card/
├── Default/
│   ├── Small
│   ├── Medium
│   └── Large
├── Elevated/
├── Filled/
├── Interactive/
├── Glass/
├── StatCard/
└── AgentCard/
```

---

## 最佳实践

1. **信息层次**: 标题 > 描述 > 元数据
2. **一致性**: 同一视图中的卡片保持相同尺寸
3. **留白**: 内容不要太拥挤
4. **操作位置**: 主要操作放在卡片底部右侧
5. **图片优化**: 使用 `loading="lazy"` 和明确的宽高
