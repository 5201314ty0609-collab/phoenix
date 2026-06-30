# 鲤鱼 AIOS 样式系统

基于 Tailwind CSS v4 + 自定义设计令牌的完整样式系统。

## 目录结构

```
styles/
├── tailwind.config.ts       # Tailwind 配置（主题、插件）
├── globals.css              # 全局入口（导入所有模块）
├── README.md                # 本文件
│
├── tokens/                  # 设计令牌 (CSS 自定义属性)
│   ├── colors.css           # 颜色系统（主题切换）
│   ├── typography.css       # 排版系统（字号、行高、字重）
│   └── spacing.css          # 间距系统（网格、语义间距）
│
├── base/                    # 基础样式
│   ├── reset.css            # CSS 重置
│   └── typography-base.css  # 排版基础（标题、正文、代码）
│
├── components/              # 组件样式
│   ├── buttons.css          # 按钮系统（变体、尺寸、状态）
│   ├── cards.css            # 卡片系统（基础、高架、玻璃）
│   ├── forms.css            # 表单系统（输入、选择、开关）
│   └── badges.css           # 徽章系统（颜色、尺寸、变体）
│
└── utilities/               # 工具类
    ├── effects.css          # 视觉效果（玻璃、渐变、发光）
    └── layout.css           # 布局（容器、网格、堆叠）
```

## 设计理念

| 决策 | 选择 | 原因 |
|------|------|------|
| 主色 | 深蓝 (hsl 220) | 信任、专业 |
| 辅助色 | 橙色 (hsl 25) | 能量、创新 |
| 基准网格 | 4px | 一致性 |
| 暗色主题 | 默认 | 系统管理工具 |
| 排版比例 | Major Third (1.25) | 清晰层次 |
| 中文行高 | 1.75 | 可读性 |
| 触摸目标 | 44px min | WCAG 2.5.5 |

## 使用方式

### 1. Tailwind CSS 类（推荐）

```html
<!-- 颜色 -->
<div class="bg-surface text-text border border-border">内容</div>
<div class="bg-primary-500 text-white">主色背景</div>
<div class="text-accent-500">强调色文字</div>

<!-- 间距 -->
<div class="p-4 mb-6 gap-grid">间距</div>
<section class="py-section">响应式区域</section>

<!-- 排版 -->
<h1 class="text-hero font-display font-bold">标题</h1>
<p class="text-body leading-chinese">中文正文</p>

<!-- 动画 -->
<div class="animate-fade-in-up delay-200">淡入</div>
```

### 2. 组件类

```html
<!-- 按钮 -->
<button class="btn btn-primary">主要按钮</button>
<button class="btn btn-accent btn-lg">大号强调</button>
<button class="btn btn-ghost btn-sm">小号幽灵</button>
<button class="btn btn-outline-primary">轮廓</button>
<button class="btn btn-loading">加载中</button>

<!-- 卡片 -->
<div class="card">
  <div class="card-header">
    <h3>标题</h3>
    <span class="badge badge-success">正常</span>
  </div>
  <div class="card-body">内容</div>
  <div class="card-footer">
    <button class="btn btn-ghost btn-sm">取消</button>
    <button class="btn btn-primary btn-sm">确认</button>
  </div>
</div>

<!-- 统计卡片 -->
<div class="card-stat">
  <p class="stat-label">活跃用户</p>
  <p class="stat-value">12,345</p>
  <p class="stat-change positive">+12.5%</p>
</div>

<!-- 表单 -->
<div class="form-group">
  <label class="form-label required">邮箱</label>
  <input class="form-input" type="email" placeholder="name@example.com">
  <p class="form-help">不会分享给第三方</p>
</div>

<div class="form-group">
  <label class="form-label">通知</label>
  <label class="form-switch">
    <input type="checkbox" checked>
    <span class="form-switch-track"></span>
    <span>开启推送</span>
  </label>
</div>

<!-- 徽章 -->
<span class="badge badge-dot badge-success">在线</span>
<span class="badge badge-outline badge-primary">标签</span>
```

### 3. 视觉效果

```html
<!-- 玻璃效果 -->
<div class="glass rounded-xl p-6">毛玻璃</div>

<!-- 渐变文字 -->
<h1 class="text-gradient-primary text-hero">渐变标题</h1>

<!-- 发光效果 -->
<div class="glow-accent rounded-lg p-4">发光卡片</div>

<!-- 骨架屏 -->
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-text w-3/5"></div>
```

### 4. 布局

```html
<!-- 页面容器 -->
<div class="container-page">
  <section class="section">
    <div class="grid-3">
      <div class="card">1</div>
      <div class="card">2</div>
      <div class="card">3</div>
    </div>
  </section>
</div>

<!-- Bento 网格 -->
<div class="grid-bento">
  <div class="card col-span-2 row-span-2">大卡片</div>
  <div class="card">小卡片</div>
  <div class="card">小卡片</div>
</div>

<!-- 堆叠间距 -->
<div class="stack-lg">
  <div>项目 1</div>
  <div>项目 2</div>
  <div>项目 3</div>
</div>
```

## 主题切换

```html
<!-- 暗色（默认） -->
<html data-theme="dark">

<!-- 亮色 -->
<html data-theme="light">

<!-- 跟随系统 -->
<html data-theme="auto">
```

通过 JS 切换：

```typescript
document.documentElement.setAttribute('data-theme', 'light');
```

## 断点

| 名称 | 宽度 | 设备 |
|------|------|------|
| xs | 320px | 小手机 |
| sm | 375px | iPhone SE |
| md | 768px | iPad |
| lg | 1024px | iPad Pro |
| xl | 1280px | 桌面 |
| 2xl | 1440px | 大桌面 |
| 3xl | 1920px | 全高清 |

条件断点：
- `portrait` / `landscape` — 方向
- `touch` / `mouse` — 指针类型
- `reduced-motion` — 减少动画

## WCAG 合规

- 文字对比度 >= 4.5:1 (AA)
- 大文字对比度 >= 3:1 (AA)
- 触摸目标 >= 44px (2.5.5)
- 焦点可见 (2.4.7)
- 减少动画支持 (2.3.3)
- 语义化 HTML 结构

## 与现有系统的关系

本样式系统基于已有的三个 CSS 文件升级：
- `color-system.css` -> `tokens/colors.css` + Tailwind 主题
- `typography-system.css` -> `tokens/typography.css` + Tailwind 主题
- `spacing-system.css` -> `tokens/spacing.css` + Tailwind 主题

原有 CSS 文件可继续使用，新系统提供更丰富的组件和 Tailwind 集成。
