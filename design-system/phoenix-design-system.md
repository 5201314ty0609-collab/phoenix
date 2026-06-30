# 鲤鱼 AIOS 设计系统规范

> 版本: 1.0.0
> 创建日期: 2026-06-19
> 风格方向: Dark Luxury + Swiss International
> Design Dials: VARIANCE=6 | MOTION=5 | DENSITY=5

---

## 1. 设计哲学

### 1.1 核心原则

鲤鱼 AIOS 是一个自进化 AI Agent 系统，设计语言需要传达：
- **专业性** — 技术可信，操作精准
- **智能感** — AI 驱动，数据可视化
- **克制美** — 信息密度适中，不浮夸

### 1.2 Design Dials 设定

| Dial | 值 | 含义 |
|------|-----|------|
| **DESIGN_VARIANCE** | 6 | 偏移布局，混合对齐，有层次但不极端 |
| **MOTION_INTENSITY** | 5 | 流畅 CSS 过渡，适度滚动触发动画 |
| **VISUAL_DENSITY** | 5 | 标准密度，信息适中，呼吸感良好 |

### 1.3 风格方向

**Dark Luxury + Swiss International**
- 深色主色调，营造专业科技感
- Swiss 风格的网格系统和排版
- 克制的装饰，功能优先
- 避免 AI 紫色（LILA RULE）

---

## 2. 颜色系统 (Color Tokens)

### 2.1 基础色板

```css
/* 主色调 - 深蓝系 */
--color-primary-50: oklch(98% 0.02 250);
--color-primary-100: oklch(95% 0.04 250);
--color-primary-200: oklch(90% 0.06 250);
--color-primary-300: oklch(80% 0.10 250);
--color-primary-400: oklch(70% 0.14 250);
--color-primary-500: oklch(60% 0.18 250);  /* 主色 */
--color-primary-600: oklch(50% 0.16 250);
--color-primary-700: oklch(40% 0.14 250);
--color-primary-800: oklch(30% 0.12 250);
--color-primary-900: oklch(20% 0.10 250);

/* 中性色 - 灰系 */
--color-neutral-0: oklch(100% 0 0);      /* 纯白 */
--color-neutral-50: oklch(98% 0 0);
--color-neutral-100: oklch(96% 0 0);
--color-neutral-200: oklch(92% 0 0);
--color-neutral-300: oklch(87% 0 0);
--color-neutral-400: oklch(70% 0 0);
--color-neutral-500: oklch(55% 0 0);
--color-neutral-600: oklch(45% 0 0);
--color-neutral-700: oklch(35% 0 0);
--color-neutral-800: oklch(25% 0 0);
--color-neutral-900: oklch(15% 0 0);
--color-neutral-950: oklch(10% 0 0);      /* 深黑 */

/* 语义色 */
--color-success: oklch(65% 0.18 145);     /* 绿色 - 成功 */
--color-warning: oklch(75% 0.15 75);      /* 琥珀 - 警告 */
--color-error: oklch(60% 0.20 25);        /* 红色 - 错误 */
--color-info: oklch(65% 0.15 230);        /* 蓝色 - 信息 */

/* 强调色 - 青色系（避免 AI 紫色） */
--color-accent-400: oklch(75% 0.12 190);
--color-accent-500: oklch(65% 0.15 190);  /* 主强调色 */
--color-accent-600: oklch(55% 0.13 190);
```

### 2.2 语义颜色映射

```css
/* 表面颜色 */
--surface-primary: var(--color-neutral-950);
--surface-secondary: var(--color-neutral-900);
--surface-tertiary: var(--color-neutral-800);
--surface-elevated: var(--color-neutral-800);

/* 文本颜色 */
--text-primary: var(--color-neutral-50);
--text-secondary: var(--color-neutral-400);
--text-tertiary: var(--color-neutral-500);
--text-disabled: var(--color-neutral-600);

/* 交互状态 */
--interactive-default: var(--color-primary-500);
--interactive-hover: var(--color-primary-400);
--interactive-active: var(--color-primary-600);
--interactive-focus: var(--color-accent-500);

/* 边框 */
--border-default: var(--color-neutral-800);
--border-hover: var(--color-neutral-700);
--border-focus: var(--color-accent-500);
```

### 2.3 暗色/亮色模式

```css
/* 暗色模式（默认） */
[data-theme="dark"] {
  --bg-page: var(--color-neutral-950);
  --bg-card: var(--color-neutral-900);
  --bg-input: var(--color-neutral-800);
  --text-on-dark: var(--color-neutral-50);
}

/* 亮色模式 */
[data-theme="light"] {
  --bg-page: var(--color-neutral-50);
  --bg-card: var(--color-neutral-0);
  --bg-input: var(--color-neutral-100);
  --text-on-light: var(--color-neutral-900);
}
```

---

## 3. 字体系统 (Typography Tokens)

### 3.1 字体家族

```css
/* 主字体 - 现代无衬线 */
--font-family-primary: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* 等宽字体 - 代码显示 */
--font-family-mono: 'Geist Mono', 'JetBrains Mono', 'Fira Code', monospace;

/* 显示字体 - 标题强调 */
--font-family-display: 'Geist', -apple-system, sans-serif;
```

### 3.2 字号体系

```css
/* 基于 4px 网格的字号系统 */
--text-xs: clamp(0.625rem, 0.6rem + 0.125vw, 0.75rem);      /* 10-12px */
--text-sm: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);       /* 12-14px */
--text-base: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);       /* 14-16px */
--text-lg: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);           /* 16-18px */
--text-xl: clamp(1.125rem, 1rem + 0.625vw, 1.25rem);        /* 18-20px */
--text-2xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);        /* 20-24px */
--text-3xl: clamp(1.5rem, 1.3rem + 1vw, 1.875rem);          /* 24-30px */
--text-4xl: clamp(1.875rem, 1.5rem + 1.875vw, 2.25rem);     /* 30-36px */
--text-5xl: clamp(2.25rem, 1.8rem + 2.25vw, 3rem);          /* 36-48px */
--text-6xl: clamp(2.5rem, 2rem + 2.5vw, 3.75rem);           /* 40-60px */
```

### 3.3 字重

```css
--font-weight-regular: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### 3.4 行高

```css
--leading-none: 1;
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;
```

### 3.5 排版样式组合

```css
/* 显示标题 */
.heading-display {
  font-family: var(--font-family-display);
  font-size: var(--text-6xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
}

/* 页面标题 */
.heading-1 {
  font-family: var(--font-family-display);
  font-size: var(--text-5xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.01em;
}

/* 区域标题 */
.heading-2 {
  font-family: var(--font-family-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--leading-snug);
}

/* 子标题 */
.heading-3 {
  font-family: var(--font-family-primary);
  font-size: var(--text-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--leading-snug);
}

/* 正文 */
.body-base {
  font-family: var(--font-family-primary);
  font-size: var(--text-base);
  font-weight: var(--font-weight-regular);
  line-height: var(--leading-normal);
}

/* 小字 */
.body-small {
  font-family: var(--font-family-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-regular);
  line-height: var(--leading-normal);
}

/* 代码 */
.code {
  font-family: var(--font-family-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-regular);
  line-height: var(--leading-relaxed);
}
```

---

## 4. 间距系统 (Spacing Tokens)

### 4.1 基础间距

```css
/* 基于 4px 网格 */
--space-0: 0;
--space-1: 0.25rem;    /* 4px */
--space-2: 0.5rem;     /* 8px */
--space-3: 0.75rem;    /* 12px */
--space-4: 1rem;       /* 16px */
--space-5: 1.25rem;    /* 20px */
--space-6: 1.5rem;     /* 24px */
--space-8: 2rem;       /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-20: 5rem;      /* 80px */
--space-24: 6rem;      /* 96px */
--space-32: 8rem;      /* 128px */
```

### 4.2 组件间距

```css
/* 按钮内边距 */
--padding-button-sm: var(--space-2) var(--space-3);
--padding-button-md: var(--space-3) var(--space-4);
--padding-button-lg: var(--space-4) var(--space-6);

/* 卡片内边距 */
--padding-card-sm: var(--space-3);
--padding-card-md: var(--space-4);
--padding-card-lg: var(--space-6);

/* 输入框内边距 */
--padding-input: var(--space-3) var(--space-4);

/* 区域间距 */
--section-gap: var(--space-16);
--grid-gap: var(--space-6);
```

### 4.3 响应式间距

```css
/* 移动端更紧凑 */
@media (max-width: 768px) {
  :root {
    --section-gap: var(--space-10);
    --grid-gap: var(--space-4);
  }
}
```

---

## 5. 圆角系统 (Border Radius)

```css
--radius-none: 0;
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-2xl: 1.25rem;   /* 20px */
--radius-full: 9999px;
```

---

## 6. 阴影系统 (Shadow Tokens)

```css
/* 暗色模式阴影 */
--shadow-sm: 0 1px 2px oklch(0% 0 0 / 0.3);
--shadow-md: 0 4px 6px oklch(0% 0 0 / 0.4);
--shadow-lg: 0 10px 15px oklch(0% 0 0 / 0.5);
--shadow-xl: 0 20px 25px oklch(0% 0 0 / 0.6);

/* 发光效果（用于强调） */
--glow-primary: 0 0 20px oklch(60% 0.18 250 / 0.3);
--glow-accent: 0 0 20px oklch(65% 0.15 190 / 0.3);
```

---

## 7. 动画系统 (Animation Tokens)

### 7.1 时长

```css
--duration-instant: 0ms;
--duration-fast: 100ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
--duration-slower: 500ms;
```

### 7.2 缓动函数

```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### 7.3 动画组合

```css
/* 淡入 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 滑入 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 缩放进入 */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### 7.4 减弱动效支持

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. 断点系统 (Breakpoints)

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### 8.1 响应式策略

- **Mobile-first**: 默认样式为移动端
- **渐进增强**: 通过 `min-width` 媒体查询添加桌面特性
- **关键断点**: 375px (手机), 768px (平板), 1024px (小桌面), 1440px (桌面)

---

## 9. 图标系统

### 9.1 图标规范

- **风格**: 线性图标 (Stroke)，2px 描边
- **尺寸**: 16px, 20px, 24px, 32px
- **颜色**: 继承父元素颜色
- **库**: Lucide Icons 或自定义图标集

### 9.2 图标尺寸 Token

```css
--icon-size-sm: 16px;
--icon-size-md: 20px;
--icon-size-lg: 24px;
--icon-size-xl: 32px;
```

---

## 10. 网格系统

### 10.1 基础网格

```css
/* 12 列网格 */
--grid-columns: 12;
--grid-gutter: var(--space-6);
--grid-margin: var(--space-6);

/* 最大宽度 */
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
```

### 10.2 布局模式

```css
/* 卡片网格 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--grid-gap);
}

/* 仪表盘布局 */
.dashboard-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 64px 1fr;
  min-height: 100vh;
}
```

---

## 11. 无障碍规范

### 11.1 对比度要求

- **正文文本**: 对比度 >= 4.5:1 (WCAG AA)
- **大号文本**: 对比度 >= 3:1
- **交互元素**: 对比度 >= 3:1

### 11.2 焦点状态

```css
/* 可见的焦点指示器 */
:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}

/* 键盘导航 */
:focus:not(:focus-visible) {
  outline: none;
}
```

### 11.3 语义化 HTML

```html
<!-- 正确 -->
<header role="banner">
<nav role="navigation" aria-label="主导航">
<main role="main">
<aside role="complementary">
<footer role="contentinfo">
```

---

## 12. Figma 文件组织

### 12.1 页面结构

```
鲤鱼 Design System/
├── 📄 Cover                    # 封面和版本信息
├── 🎨 Foundations              # 基础元素
│   ├── Colors                  # 颜色系统
│   ├── Typography              # 字体系统
│   ├── Spacing                 # 间距系统
│   ├── Icons                   # 图标库
│   └── Grid                    # 网格系统
├── 🧩 Components               # 组件库
│   ├── Buttons                 # 按钮
│   ├── Inputs                  # 输入框
│   ├── Cards                   # 卡片
│   ├── Navigation              # 导航
│   ├── Modals                  # 弹窗
│   └── Data Display            # 数据展示
├── 📐 Patterns                 # 布局模式
│   ├── Page Layouts            # 页面布局
│   ├── Form Patterns           # 表单模式
│   └── Dashboard Patterns      # 仪表盘模式
├── 📱 Screens                  # 完整页面
│   ├── Landing                 # 着陆页
│   ├── Dashboard               # 仪表盘
│   ├── Agent Monitor           # Agent 监控
│   └── Settings                # 设置页
└── 📖 Documentation            # 使用文档
    ├── Getting Started         # 快速开始
    ├── Component Guidelines    # 组件指南
    └── Changelog               # 更新日志
```

### 12.2 命名规范

```
组件命名: Category/Component/State
示例: Button/Primary/Default
示例: Button/Primary/Hover
示例: Input/Text/Default
示例: Input/Text/Error

图层命名: 语义化名称
正确: Header, Nav, Card, Button
错误: Frame 1, Group 2, Rectangle 3
```

### 12.3 组件属性

```
Boolean: 显示/隐藏子元素
Instance Swap: 替换图标/组件
Text: 文本内容
Variant: 状态/类型变体
```

---

## 13. 组件设计规范

详见 `components/` 目录下的独立组件文档：
- `button.md` — 按钮组件
- `input.md` — 输入框组件
- `card.md` — 卡片组件
- `navigation.md` — 导航组件
- `modal.md` — 弹窗组件
- `data-display.md` — 数据展示组件

---

## 14. 设计稿导出规范

### 14.1 切图规范

- **格式**: SVG (图标), PNG (图片), WebP (照片)
- **分辨率**: 1x, 2x, 3x
- **命名**: `component-state-size@2x.png`

### 14.2 开发者交接

- 使用 Figma Dev Mode
- 标注间距、尺寸、颜色
- 提供 CSS 代码片段
- 标注交互状态

---

## 附录 A: 颜色对比度速查表

| 前景 | 背景 | 对比度 | WCAG AA | WCAG AAA |
|------|------|--------|---------|----------|
| #FAFAFA | #0A0A0A | 18.5:1 | Pass | Pass |
| #A3A3A3 | #0A0A0A | 7.2:1 | Pass | Pass |
| #525252 | #0A0A0A | 3.1:1 | Pass (大文本) | Fail |
| #2563EB | #0A0A0A | 5.8:1 | Pass | Pass |

---

## 附录 B: 设计决策记录

### 为什么避免 AI 紫色？

AI 紫色 (#7C3AED) 已成为 AI 产品的视觉陈词滥调。鲤鱼 选择深蓝+青色组合，传达：
- 专业性和技术可信度
- 独特的品牌识别
- 避免与竞品视觉混淆

### 为什么选择 Dark Luxury 风格？

- AI Agent 系统通常长时间使用，暗色减少视觉疲劳
- 深色背景让数据可视化更突出
- 符合开发者和技术用户的审美偏好

---

*文档维护: 此文件由 鲤鱼 设计系统管理，版本更新通过 git 记录。*
