# 鲤鱼 AIOS 设计系统

> 为 鲤鱼 自进化 AI Agent 系统打造的现代化设计语言

---

## 概述

鲤鱼 AIOS 设计系统提供了一套完整的设计规范和组件库，用于构建专业、智能、克制的 AI Agent 界面。

**风格方向**: Dark Luxury + Swiss International

**Design Dials**:
- DESIGN_VARIANCE: 6 (偏移布局，混合对齐)
- MOTION_INTENSITY: 5 (流畅 CSS 过渡)
- VISUAL_DENSITY: 5 (标准密度，信息适中)

---

## 文件结构

```
design-system/
├── README.md                          # 本文件
├── liyu-design-system.md           # 完整设计规范
├── design-system-summary.md           # 快速参考摘要
│
├── components/                        # 组件文档
│   ├── button.md                      # 按钮组件
│   ├── input.md                       # 输入框组件
│   ├── card.md                        # 卡片组件
│   ├── navigation.md                  # 导航组件
│   ├── modal.md                       # 弹窗组件
│   └── data-display.md                # 数据展示组件
│
├── tokens/                            # Design Tokens
│   ├── design-tokens.css              # CSS 变量
│   └── design-tokens.json             # JSON 格式 (Figma/Style Dictionary)
│
└── specs/                             # 规范文档
    ├── figma-setup-guide.md           # Figma 设置指南
    └── page-examples.md               # 页面设计示例
```

---

## 快速开始

### 1. 引入 Design Tokens

在项目中引入 CSS 变量：

```html
<link rel="stylesheet" href="design-tokens.css">
```

或在 CSS 中导入：

```css
@import './tokens/design-tokens.css';
```

### 2. 使用变量

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  color: var(--text-primary);
}

.button--primary {
  background: var(--color-primary-500);
  color: white;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  transition: background var(--duration-fast) var(--ease-out);
}

.button--primary:hover {
  background: var(--color-primary-400);
}
```

### 3. 响应式设计

```css
.grid {
  display: grid;
  gap: var(--grid-gap);
}

@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}

@media (min-width: 640px) and (max-width: 1023px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 639px) {
  .grid { grid-template-columns: 1fr; }
}
```

---

## 核心组件

### 按钮 (Button)

```html
<!-- 主按钮 -->
<button class="button button--primary">确认</button>

<!-- 次要按钮 -->
<button class="button button--secondary">取消</button>

<!-- 危险按钮 -->
<button class="button button--danger">删除</button>
```

### 卡片 (Card)

```html
<article class="card">
  <div class="card__header">
    <h3 class="card__title">标题</h3>
    <p class="card__description">描述文本</p>
  </div>
  <div class="card__body">内容</div>
  <div class="card__footer">
    <button class="button button--ghost">操作</button>
  </div>
</article>
```

### 输入框 (Input)

```html
<div class="form-field">
  <label class="form-label" for="email">邮箱</label>
  <input class="input" type="email" id="email" />
  <p class="form-help">输入您的邮箱地址</p>
</div>
```

---

## 颜色系统

### 主色调

- **Primary**: 深蓝系 — 专业、可信
- **Accent**: 青色系 — 科技、智能
- **Neutral**: 灰色系 — 中性、平衡

### 语义色

- **Success**: 绿色 — 成功、确认
- **Warning**: 琥珀 — 警告、注意
- **Error**: 红色 — 错误、危险
- **Info**: 蓝色 — 信息、帮助

### 使用原则

- 避免 AI 紫色 (#7C3AED)
- 暗色模式为默认
- 对比度符合 WCAG AA 标准

---

## 字体系统

### 字体家族

- **主字体**: Geist (或 Inter)
- **等宽字体**: Geist Mono (或 JetBrains Mono)

### 字号体系

基于 clamp() 实现响应式字号：
- Display: 40-60px
- H1: 36-48px
- H2: 30-36px
- Body: 14-16px

---

## 间距系统

基于 4px 网格：

```
space-1: 4px
space-2: 8px
space-3: 12px
space-4: 16px
space-6: 24px
space-8: 32px
```

---

## Figma 设置

按照 `specs/figma-setup-guide.md` 在 Figma 中创建设计系统：

1. 创建变量集合 (Colors, Spacing, Typography)
2. 设置文字样式
3. 创建组件库
4. 组织页面结构

---

## 设计原则

1. **功能优先** — 设计服务于功能
2. **信息清晰** — 层次分明，重点突出
3. **交互自然** — 反馈及时，操作直觉
4. **视觉克制** — 避免过度设计

---

## 无障碍

- 对比度符合 WCAG AA 标准
- 焦点状态清晰可见
- 键盘可导航
- 语义化 HTML

---

## 响应式设计

### 断点

- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px
- Desktop Large: 1440px

### 策略

- Mobile-first
- 渐进增强
- 内容优先级

---

## 动画规范

### 时长

- Fast: 100ms
- Normal: 200ms
- Slow: 300ms

### 缓动

- ease-out: 元素进入
- ease-in: 元素退出
- spring: 强调动画

### 减弱动效

支持 `prefers-reduced-motion` 媒体查询。

---

## 版本历史

- **1.0.0** (2026-06-19): 初始版本
  - 完整设计规范
  - 核心组件库
  - Design Tokens (CSS + JSON)
  - Figma 设置指南

---

## 相关链接

- [鲤鱼 主页](https://github.com/anthropics/claude-code)
- [Design Tokens W3C 规范](https://design-tokens.github.io/community-group/format/)
- [Figma 官方文档](https://help.figma.com/)

---

*鲤鱼 AIOS Design System v1.0.0*
