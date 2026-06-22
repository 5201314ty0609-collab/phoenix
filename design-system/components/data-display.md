# 数据展示组件 (Data Display)

> 组件类型: 数据可视化
> 最后更新: 2026-06-19

---

## 概述

数据展示组件用于在 PHOENIX 仪表盘中呈现各种数据，包括统计卡片、表格、图表和状态指示器。

---

## 1. 统计卡片 (Stat Card)

### 结构

```html
<div class="stat-card">
  <div class="stat-card__header">
    <span class="stat-card__label">总任务数</span>
    <span class="stat-card__badge stat-card__badge--up">+12%</span>
  </div>
  <div class="stat-card__value">1,234</div>
  <div class="stat-card__footer">
    <span class="stat-card__comparison">较上周</span>
  </div>
</div>
```

### 样式

```css
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.stat-card__label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.stat-card__badge {
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.stat-card__badge--up {
  color: var(--color-success);
  background: oklch(65% 0.18 145 / 10%);
}

.stat-card__badge--down {
  color: var(--color-error);
  background: oklch(60% 0.20 25 / 10%);
}

.stat-card__value {
  font-size: var(--text-4xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  font-family: var(--font-family-mono);
  line-height: var(--leading-none);
}

.stat-card__footer {
  margin-top: var(--space-2);
}

.stat-card__comparison {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
```

---

## 2. 数据表格 (Data Table)

### 结构

```html
<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        <th class="table__th">名称</th>
        <th class="table__th">状态</th>
        <th class="table__th">任务</th>
        <th class="table__th table__th--right">操作</th>
      </tr>
    </thead>
    <tbody>
      <tr class="table__row">
        <td class="table__td">
          <div class="table__cell-with-avatar">
            <img src="avatar.jpg" alt="" class="table__avatar" />
            <span>Code Reviewer</span>
          </div>
        </td>
        <td class="table__td">
          <span class="status-badge status-badge--active">运行中</span>
        </td>
        <td class="table__td">审查 PR #123</td>
        <td class="table__td table__td--right">
          <button class="button button--ghost button--sm">查看</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### 样式

```css
.table-container {
  overflow-x: auto;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table__th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--text-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
  background: var(--surface-secondary);
  border-bottom: 1px solid var(--border-default);
}

.table__th--right {
  text-align: right;
}

.table__row {
  transition: background var(--duration-fast) var(--ease-out);
}

.table__row:hover {
  background: var(--surface-tertiary);
}

.table__td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-default);
}

.table__td--right {
  text-align: right;
}

.table__cell-with-avatar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.table__avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
}
```

---

## 3. 状态指示器

### 状态徽章

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
}

.status-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
}

.status-badge--active {
  color: var(--color-success);
  background: oklch(65% 0.18 145 / 10%);
}

.status-badge--active::before {
  background: var(--color-success);
}

.status-badge--inactive {
  color: var(--text-tertiary);
  background: var(--surface-tertiary);
}

.status-badge--inactive::before {
  background: var(--text-tertiary);
}

.status-badge--error {
  color: var(--color-error);
  background: oklch(60% 0.20 25 / 10%);
}

.status-badge--error::before {
  background: var(--color-error);
}

.status-badge--warning {
  color: var(--color-warning);
  background: oklch(75% 0.15 75 / 10%);
}

.status-badge--warning::before {
  background: var(--color-warning);
}
```

---

## 4. 进度指示器

### 进度条

```html
<div class="progress">
  <div class="progress__header">
    <span class="progress__label">任务进度</span>
    <span class="progress__value">75%</span>
  </div>
  <div class="progress__track">
    <div class="progress__fill" style="width: 75%"></div>
  </div>
</div>
```

```css
.progress__header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.progress__label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.progress__value {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  font-family: var(--font-family-mono);
}

.progress__track {
  height: 8px;
  background: var(--surface-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress__fill {
  height: 100%;
  background: var(--color-primary-500);
  border-radius: var(--radius-full);
  transition: width var(--duration-slow) var(--ease-out);
}
```

---

## 5. 列表组件

### 基础列表

```html
<ul class="list">
  <li class="list__item">
    <div class="list__icon">
      <svg><!-- icon --></svg>
    </div>
    <div class="list__content">
      <span class="list__title">任务完成</span>
      <span class="list__description">Code Reviewer 完成了 PR #123 的审查</span>
    </div>
    <span class="list__time">2 分钟前</span>
  </li>
</ul>
```

```css
.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list__item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-default);
  transition: background var(--duration-fast) var(--ease-out);
}

.list__item:hover {
  background: var(--surface-tertiary);
}

.list__icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-tertiary);
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.list__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.list__title {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.list__description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.list__time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}
```

---

## 6. 标签 (Tag)

```html
<span class="tag">默认</span>
<span class="tag tag--primary">主要</span>
<span class="tag tag--success">成功</span>
<span class="tag tag--warning">警告</span>
<span class="tag tag--error">错误</span>
```

```css
.tag {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
  background: var(--surface-tertiary);
  color: var(--text-primary);
}

.tag--primary {
  background: oklch(60% 0.18 250 / 15%);
  color: var(--color-primary-400);
}

.tag--success {
  background: oklch(65% 0.18 145 / 15%);
  color: var(--color-success);
}

.tag--warning {
  background: oklch(75% 0.15 75 / 15%);
  color: var(--color-warning);
}

.tag--error {
  background: oklch(60% 0.20 25 / 15%);
  color: var(--color-error);
}
```

---

## 7. 空状态

```html
<div class="empty-state">
  <div class="empty-state__icon">
    <svg><!-- empty icon --></svg>
  </div>
  <h3 class="empty-state__title">暂无数据</h3>
  <p class="empty-state__description">还没有任何任务，创建一个开始吧</p>
  <button class="button button--primary">创建任务</button>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
}

.empty-state__icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-state__title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.empty-state__description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
  max-width: 300px;
}
```

---

## Figma 组件结构

```
Data Display/
├── StatCard/
├── Table/
│   ├── Default
│   ├── Compact
│   └── Striped
├── StatusBadge/
│   ├── Active
│   ├── Inactive
│   ├── Error
│   └── Warning
├── ProgressBar/
├── Tag/
│   ├── Default
│   ├── Primary
│   ├── Success
│   ├── Warning
│   └── Error
├── List/
└── EmptyState/
```
