# 导航组件 (Navigation)

> 组件类型: 导航元素
> 最后更新: 2026-06-19

---

## 概述

导航系统帮助用户在 PHOENIX 中定位和移动。包括顶部导航栏、侧边导航、标签页和面包屑。

---

## 1. 顶部导航栏 (Top Navigation)

### 结构

```html
<header class="topnav">
  <div class="topnav__brand">
    <svg class="topnav__logo"><!-- logo --></svg>
    <span class="topnav__title">PHOENIX</span>
  </div>

  <nav class="topnav__menu" aria-label="主导航">
    <a class="topnav__link topnav__link--active" href="/dashboard">
      仪表盘
    </a>
    <a class="topnav__link" href="/agents">
      Agents
    </a>
    <a class="topnav__link" href="/tasks">
      任务
    </a>
  </nav>

  <div class="topnav__actions">
    <button class="button button--ghost button--icon" aria-label="通知">
      <svg><!-- bell icon --></svg>
    </button>
    <div class="topnav__user">
      <img src="avatar.jpg" alt="用户头像" class="topnav__avatar" />
    </div>
  </div>
</header>
```

### 样式

```css
.topnav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 var(--space-6);
  background: var(--surface-primary);
  border-bottom: 1px solid var(--border-default);
  position: sticky;
  top: 0;
  z-index: 100;
}

.topnav__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.topnav__logo {
  width: 32px;
  height: 32px;
  color: var(--color-primary-500);
}

.topnav__title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.topnav__menu {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.topnav__link {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--duration-fast) var(--ease-out);
}

.topnav__link:hover {
  color: var(--text-primary);
  background: var(--surface-tertiary);
}

.topnav__link--active {
  color: var(--text-primary);
  background: var(--surface-tertiary);
}

.topnav__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.topnav__avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  object-fit: cover;
}
```

---

## 2. 侧边导航 (Sidebar)

### 结构

```html
<aside class="sidebar">
  <nav class="sidebar__nav" aria-label="侧边导航">
    <div class="sidebar__section">
      <span class="sidebar__heading">主要功能</span>
      <a class="sidebar__link sidebar__link--active" href="/dashboard">
        <svg class="sidebar__icon"><!-- icon --></svg>
        <span>仪表盘</span>
      </a>
      <a class="sidebar__link" href="/agents">
        <svg class="sidebar__icon"><!-- icon --></svg>
        <span>Agents</span>
      </a>
    </div>

    <div class="sidebar__section">
      <span class="sidebar__heading">系统</span>
      <a class="sidebar__link" href="/settings">
        <svg class="sidebar__icon"><!-- icon --></svg>
        <span>设置</span>
      </a>
    </div>
  </nav>
</aside>
```

### 样式

```css
.sidebar {
  width: 280px;
  height: 100%;
  background: var(--surface-primary);
  border-right: 1px solid var(--border-default);
  padding: var(--space-4);
  overflow-y: auto;
}

.sidebar__section {
  margin-bottom: var(--space-6);
}

.sidebar__heading {
  display: block;
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--duration-fast) var(--ease-out);
}

.sidebar__link:hover {
  color: var(--text-primary);
  background: var(--surface-tertiary);
}

.sidebar__link--active {
  color: var(--text-primary);
  background: var(--surface-tertiary);
  font-weight: var(--font-weight-medium);
}

.sidebar__icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
```

---

## 3. 标签页 (Tabs)

### 结构

```html
<div class="tabs">
  <div class="tabs__list" role="tablist">
    <button
      class="tabs__trigger tabs__trigger--active"
      role="tab"
      aria-selected="true"
      aria-controls="panel-1"
    >
      概览
    </button>
    <button
      class="tabs__trigger"
      role="tab"
      aria-selected="false"
      aria-controls="panel-2"
    >
      设置
    </button>
  </div>

  <div class="tabs__content">
    <div class="tabs__panel" id="panel-1" role="tabpanel">
      <!-- 内容 -->
    </div>
  </div>
</div>
```

### 样式

```css
.tabs__list {
  display: flex;
  border-bottom: 1px solid var(--border-default);
  gap: var(--space-1);
}

.tabs__trigger {
  padding: var(--space-3) var(--space-4);
  border-bottom: 2px solid transparent;
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.tabs__trigger:hover {
  color: var(--text-primary);
}

.tabs__trigger--active {
  color: var(--text-primary);
  border-bottom-color: var(--color-primary-500);
}

.tabs__panel {
  padding: var(--space-4) 0;
}
```

---

## 4. 面包屑 (Breadcrumb)

### 结构

```html
<nav class="breadcrumb" aria-label="面包屑">
  <ol class="breadcrumb__list">
    <li class="breadcrumb__item">
      <a class="breadcrumb__link" href="/">首页</a>
    </li>
    <li class="breadcrumb__separator" aria-hidden="true">
      <svg><!-- chevron-right --></svg>
    </li>
    <li class="breadcrumb__item">
      <a class="breadcrumb__link" href="/agents">Agents</a>
    </li>
    <li class="breadcrumb__separator" aria-hidden="true">
      <svg><!-- chevron-right --></svg>
    </li>
    <li class="breadcrumb__item breadcrumb__item--current" aria-current="page">
      Code Reviewer
    </li>
  </ol>
</nav>
```

### 样式

```css
.breadcrumb__list {
  display: flex;
  align-items: center;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: var(--space-2);
}

.breadcrumb__link {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-decoration: none;
}

.breadcrumb__link:hover {
  color: var(--text-primary);
  text-decoration: underline;
}

.breadcrumb__item--current {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.breadcrumb__separator {
  color: var(--text-tertiary);
}

.breadcrumb__separator svg {
  width: 16px;
  height: 16px;
}
```

---

## 5. 移动端导航

### 汉堡菜单

```html
<button class="hamburger" aria-label="打开菜单" aria-expanded="false">
  <span class="hamburger__line"></span>
  <span class="hamburger__line"></span>
  <span class="hamburger__line"></span>
</button>
```

### 底部导航栏

```html
<nav class="bottom-nav" aria-label="底部导航">
  <a class="bottom-nav__link bottom-nav__link--active" href="/dashboard">
    <svg class="bottom-nav__icon"><!-- icon --></svg>
    <span class="bottom-nav__label">首页</span>
  </a>
  <a class="bottom-nav__link" href="/agents">
    <svg class="bottom-nav__icon"><!-- icon --></svg>
    <span class="bottom-nav__label">Agents</span>
  </a>
  <a class="bottom-nav__link" href="/tasks">
    <svg class="bottom-nav__icon"><!-- icon --></svg>
    <span class="bottom-nav__label">任务</span>
  </a>
  <a class="bottom-nav__link" href="/settings">
    <svg class="bottom-nav__icon"><!-- icon --></svg>
    <span class="bottom-nav__label">设置</span>
  </a>
</nav>
```

### 样式

```css
.bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: var(--surface-primary);
  border-top: 1px solid var(--border-default);
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

@media (max-width: 768px) {
  .bottom-nav {
    display: flex;
  }
}

.bottom-nav__link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2);
  text-decoration: none;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.bottom-nav__link--active {
  color: var(--color-primary-500);
}

.bottom-nav__icon {
  width: 24px;
  height: 24px;
}
```

---

## 无障碍

1. 使用语义化标签: `<nav>`, `<header>`, `<aside>`
2. 提供 `aria-label` 区分多个导航
3. 当前页面使用 `aria-current="page"`
4. 标签页使用正确的 ARIA 属性
5. 确保键盘可导航

---

## Figma 组件结构

```
Navigation/
├── TopNav/
│   ├── Default
│   ├── WithSearch
│   └── Minimal
├── Sidebar/
│   ├── Expanded
│   ├── Collapsed
│   └── Mobile
├── Tabs/
│   ├── Default
│   ├── Pills
│   └── Underline
├── Breadcrumb/
└── BottomNav/
```
