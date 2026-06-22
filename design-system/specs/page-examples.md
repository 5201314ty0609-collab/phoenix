# PHOENIX AIOS 页面设计示例

> 展示如何应用设计系统创建完整页面

---

## 1. 仪表盘页面 (Dashboard)

### 1.1 布局结构

```
┌─────────────────────────────────────────────────────┐
│  TopNav                                    [User]   │
├────────┬────────────────────────────────────────────┤
│        │  Header: 仪表盘                             │
│        ├────────────────────────────────────────────┤
│        │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│ Side-  │  │ 总任务 │ │ 活跃  │ │ 完成  │ │ 错误  │      │
│ bar    │  │ 1,234 │ │  45  │ │ 987  │ │  12  │      │
│        │  └──────┘ └──────┘ └──────┘ └──────┘      │
│        ├────────────────────────────────────────────┤
│        │  ┌────────────────────────────────────┐   │
│        │  │        任务趋势图表                  │   │
│        │  │                                    │   │
│        │  └────────────────────────────────────┘   │
│        ├────────────────────────────────────────────┤
│        │  ┌────────────────────────────────────┐   │
│        │  │        最近活动列表                  │   │
│        │  └────────────────────────────────────┘   │
└────────┴────────────────────────────────────────────┘
```

### 1.2 设计规范

**统计卡片网格**
```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
}

/* 响应式 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
```

**图表区域**
```css
.chart-section {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-top: var(--space-6);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
```

---

## 2. Agent 监控页面

### 2.1 布局结构

```
┌─────────────────────────────────────────────────────┐
│  TopNav                                    [User]   │
├────────┬────────────────────────────────────────────┤
│        │  Header: Agents                 [+ 创建]   │
│        ├────────────────────────────────────────────┤
│        │  ┌─────────────────────────────────────┐  │
│ Side-  │  │  [全部] [运行中] [空闲] [错误]       │  │
│ bar    │  └─────────────────────────────────────┘  │
│        ├────────────────────────────────────────────┤
│        │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│        │  │ Agent 1  │ │ Agent 2  │ │ Agent 3  │  │
│        │  │ ● 运行中  │ │ ○ 空闲   │ │ ● 运行中  │  │
│        │  │ 审查 PR  │ │ 等待任务 │ │ 执行测试 │  │
│        │  └──────────┘ └──────────┘ └──────────┘  │
│        │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│        │  │ Agent 4  │ │ Agent 5  │ │ Agent 6  │  │
│        │  │ ⚠ 警告   │ │ ○ 空闲   │ │ ✕ 错误   │  │
│        │  │ 内存高   │ │ 等待任务 │ │ 连接失败 │  │
│        │  └──────────┘ └──────────┘ └──────────┘  │
└────────┴────────────────────────────────────────────┘
```

### 2.2 Agent 卡片设计

```css
.agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all var(--duration-fast) var(--ease-out);
}

.agent-card:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.agent-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.agent-card__avatar {
  width: 40px;
  height: 40px;
  background: var(--surface-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-card__name {
  font-size: var(--text-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.agent-card__status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
}

.agent-card__status--active {
  color: var(--color-success);
}

.agent-card__status--idle {
  color: var(--text-tertiary);
}

.agent-card__status--error {
  color: var(--color-error);
}

.agent-card__task {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.agent-card__footer {
  display: flex;
  gap: var(--space-2);
  margin-top: auto;
}
```

---

## 3. 设置页面

### 3.1 布局结构

```
┌─────────────────────────────────────────────────────┐
│  TopNav                                    [User]   │
├────────┬────────────────────────────────────────────┤
│        │  Header: 设置                               │
│        ├────────────────────────────────────────────┤
│        │  ┌─────────────────────────────────────┐  │
│ Side-  │  │  [通用] [Agent] [通知] [安全] [高级] │  │
│ bar    │  └─────────────────────────────────────┘  │
│        ├────────────────────────────────────────────┤
│        │  通用设置                                   │
│        │                                             │
│        │  ┌────────────────────────────────────┐   │
│        │  │ 主题        [暗色 ▼]                │   │
│        │  │ 语言        [中文 ▼]                │   │
│        │  │ 时区        [UTC+8 ▼]              │   │
│        │  └────────────────────────────────────┘   │
│        │                                             │
│        │  Agent 设置                                 │
│        │                                             │
│        │  ┌────────────────────────────────────┐   │
│        │  │ 默认模型    [mimo-v2.5-pro ▼]      │   │
│        │  │ 并发数      [4]                     │   │
│        │  │ 超时时间    [300 秒]                │   │
│        │  └────────────────────────────────────┘   │
│        │                                             │
│        │  [保存更改]                                 │
└────────┴────────────────────────────────────────────┘
```

### 3.2 表单设计

```css
.settings-section {
  margin-bottom: var(--space-8);
}

.settings-section__title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border-default);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--space-4);
  align-items: start;
}

.form-row__label {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  padding-top: var(--space-3);
}

.form-row__description {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}
```

---

## 4. 任务详情页面

### 4.1 布局结构

```
┌─────────────────────────────────────────────────────┐
│  TopNav                                    [User]   │
├────────┬────────────────────────────────────────────┤
│        │  首页 > 任务 > 任务详情                      │
│        ├────────────────────────────────────────────┤
│        │  任务: 代码审查 PR #123                      │
│        │  状态: ● 运行中                              │
│        ├────────────────────────────────────────────┤
│        │  ┌────────────────────┐ ┌──────────────┐  │
│ Side-  │  │                    │ │ 任务信息      │  │
│ bar    │  │   代码差异视图      │ │              │  │
│        │  │                    │ │ Agent:       │  │
│        │  │                    │ │ Code Reviewer│  │
│        │  │                    │ │              │  │
│        │  │                    │ │ 开始时间:    │  │
│        │  │                    │ │ 2 分钟前     │  │
│        │  │                    │ │              │  │
│        │  │                    │ │ [暂停] [停止] │  │
│        │  └────────────────────┘ └──────────────┘  │
│        ├────────────────────────────────────────────┤
│        │  审查结果                                    │
│        │  ┌────────────────────────────────────┐   │
│        │  │ 发现 3 个问题                        │   │
│        │  │ • 第 45 行: 缺少错误处理              │   │
│        │  │ • 第 78 行: 命名不规范               │   │
│        │  │ • 第 102 行: 性能优化建议            │   │
│        │  └────────────────────────────────────┘   │
└────────┴────────────────────────────────────────────┘
```

---

## 5. 响应式设计示例

### 5.1 移动端适配

**导航切换**
```css
/* 桌面端显示侧边栏 */
@media (min-width: 1024px) {
  .sidebar {
    display: block;
  }
  .bottom-nav {
    display: none;
  }
}

/* 移动端隐藏侧边栏，显示底部导航 */
@media (max-width: 1023px) {
  .sidebar {
    display: none;
  }
  .bottom-nav {
    display: flex;
  }
}
```

**卡片网格**
```css
.agent-grid {
  display: grid;
  gap: var(--space-4);
}

/* 桌面: 3 列 */
@media (min-width: 1024px) {
  .agent-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 平板: 2 列 */
@media (min-width: 640px) and (max-width: 1023px) {
  .agent-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 手机: 1 列 */
@media (max-width: 639px) {
  .agent-grid {
    grid-template-columns: 1fr;
  }
}
```

### 5.2 内容优先级

移动端隐藏次要信息：
```css
.mobile-hidden {
  display: block;
}

@media (max-width: 768px) {
  .mobile-hidden {
    display: none;
  }
}

.mobile-only {
  display: none;
}

@media (max-width: 768px) {
  .mobile-only {
    display: block;
  }
}
```

---

## 6. 交互状态示例

### 6.1 加载状态

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface-tertiary) 25%,
    var(--surface-secondary) 50%,
    var(--surface-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: var(--radius-md);
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

### 6.2 空状态

```html
<div class="empty-state">
  <svg class="empty-state__icon"><!-- illustration --></svg>
  <h3 class="empty-state__title">还没有 Agent</h3>
  <p class="empty-state__description">
    创建你的第一个 Agent 开始自动化工作
  </p>
  <button class="button button--primary">
    <svg><!-- plus icon --></svg>
    创建 Agent
  </button>
</div>
```

### 6.3 错误状态

```html
<div class="error-state">
  <svg class="error-state__icon"><!-- error illustration --></svg>
  <h3 class="error-state__title">加载失败</h3>
  <p class="error-state__description">
    无法连接到服务器，请检查网络后重试
  </p>
  <button class="button button--secondary">重试</button>
</div>
```

---

## 7. Figma 文件组织建议

### 7.1 页面命名

```
📄 Cover
🎨 Foundations
🧩 Components
📐 Dashboard/
  - Dashboard - Desktop
  - Dashboard - Tablet
  - Dashboard - Mobile
📐 Agents/
  - Agent List - Desktop
  - Agent Detail - Desktop
  - Agent List - Mobile
📐 Settings/
  - Settings - Desktop
  - Settings - Mobile
📐 Tasks/
  - Task List
  - Task Detail
📖 Documentation
```

### 7.2 Frame 命名

```
Dashboard/
├── Desktop (1440 x 900)
│   ├── Default
│   ├── Loading
│   ├── Empty
│   └── Error
├── Tablet (768 x 1024)
└── Mobile (375 x 812)
```

---

## 8. 设计审查清单

在完成页面设计后，检查以下内容：

- [ ] 颜色使用符合 Design Token
- [ ] 间距遵循 4px 网格
- [ ] 字体使用定义的文字样式
- [ ] 组件使用正确的变体
- [ ] 交互状态完整（Default, Hover, Active, Focus, Disabled）
- [ ] 响应式适配（320px, 768px, 1024px, 1440px）
- [ ] 无障碍（对比度、焦点指示器）
- [ ] 加载/空/错误状态
- [ ] 无 AI 紫色 (#7C3AED)
- [ ] 无 em-dash 或 en-dash
