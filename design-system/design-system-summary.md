# 鲤鱼 AIOS 设计系统摘要

> 完整的设计系统概览和快速参考

---

## 设计系统概述

鲤鱼 AIOS 设计系统是一个专为 AI Agent 系统打造的现代化设计语言，采用 **Dark Luxury + Swiss International** 风格，强调专业性、智能感和克制美。

---

## 核心设计原则

1. **功能优先** — 设计服务于功能，装饰为辅
2. **信息清晰** — 层次分明，重点突出
3. **交互自然** — 反馈及时，操作直觉
4. **视觉克制** — 避免过度设计，保持专业

---

## Design Dials

| Dial | 值 | 含义 |
|------|-----|------|
| **DESIGN_VARIANCE** | 6 | 偏移布局，混合对齐，有层次但不极端 |
| **MOTION_INTENSITY** | 5 | 流畅 CSS 过渡，适度滚动触发动画 |
| **VISUAL_DENSITY** | 5 | 标准密度，信息适中，呼吸感良好 |

---

## 颜色系统

### 主色调

- **Primary**: 深蓝系 (#406EFF) — 专业、可信
- **Accent**: 青色系 (#22D3EE) — 科技、智能
- **Neutral**: 灰色系 — 中性、平衡

### 语义色

- **Success**: 绿色 (#22C55E) — 成功、确认
- **Warning**: 琥珀 (#F59E0B) — 警告、注意
- **Error**: 红色 (#EF4444) — 错误、危险
- **Info**: 蓝色 (#3B82F6) — 信息、帮助

### 表面色

- **Page**: #0A0A0A (深黑)
- **Card**: #171717 (深灰)
- **Input**: #262626 (中灰)

---

## 字体系统

### 字体家族

- **主字体**: Geist (或 Inter) — 现代无衬线
- **等宽字体**: Geist Mono (或 JetBrains Mono) — 代码显示

### 字号体系

```
Display: 60px (标题强调)
H1: 48px (页面标题)
H2: 36px (区域标题)
H3: 24px (子标题)
H4: 20px (小标题)
Body Large: 18px
Body: 16px (正文)
Body Small: 14px
Caption: 12px
```

### 字重

- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

---

## 间距系统

基于 4px 网格：

```
space-1: 4px
space-2: 8px
space-3: 12px
space-4: 16px
space-5: 20px
space-6: 24px
space-8: 32px
space-10: 40px
space-12: 48px
space-16: 64px
space-20: 80px
```

---

## 圆角系统

```
radius-sm: 4px (小元素)
radius-md: 8px (按钮、输入框)
radius-lg: 12px (卡片)
radius-xl: 16px (弹窗)
radius-full: 9999px (圆形)
```

---

## 核心组件

### 1. 按钮 (Button)

**变体**:
- Primary: 主要操作，实心填充
- Secondary: 次要操作，描边样式
- Ghost: 辅助操作，透明背景
- Danger: 危险操作，红色系

**尺寸**:
- Small: 32px 高
- Medium: 40px 高
- Large: 48px 高

### 2. 输入框 (Input)

**变体**:
- Text: 单行文本
- Password: 密码输入
- Email: 邮箱输入
- Textarea: 多行文本

**状态**:
- Default → Hover → Focus → Filled → Error → Disabled

### 3. 卡片 (Card)

**变体**:
- Default: 边框样式
- Elevated: 阴影效果
- Filled: 背景填充
- Interactive: 可点击，悬停效果
- Glass: 玻璃拟态

### 4. 导航 (Navigation)

**组件**:
- TopNav: 顶部导航栏
- Sidebar: 侧边导航
- Tabs: 标签页
- Breadcrumb: 面包屑
- BottomNav: 底部导航（移动端）

### 5. 弹窗 (Modal)

**变体**:
- Dialog: 通用对话框
- Alert: 警示信息
- Drawer: 侧边抽屉
- Sheet: 底部表单（移动端）

### 6. 数据展示

**组件**:
- StatCard: 统计卡片
- Table: 数据表格
- StatusBadge: 状态徽章
- ProgressBar: 进度条
- Tag: 标签
- List: 列表

---

## 布局系统

### 网格

- 12 列网格
- 24px 间距
- 响应式断点: 375px, 768px, 1024px, 1440px

### 页面布局

```
Dashboard: TopNav + Sidebar + Main Content
Mobile: TopNav + Content + BottomNav
```

---

## 动画规范

### 时长

- Instant: 0ms
- Fast: 100ms
- Normal: 200ms
- Slow: 300ms

### 缓动

- ease-out: 元素进入
- ease-in: 元素退出
- ease-in-out: 状态变化
- spring: 强调动画

---

## 无障碍

### 对比度

- 正文: >= 4.5:1 (WCAG AA)
- 大号文本: >= 3:1
- 交互元素: >= 3:1

### 焦点状态

```css
:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}
```

---

## 文件结构

```
design-system/
├── liyu-design-system.md    # 主规范文档
├── design-system-summary.md    # 摘要（本文件）
├── components/
│   ├── button.md               # 按钮组件
│   ├── input.md                # 输入框组件
│   ├── card.md                 # 卡片组件
│   ├── navigation.md           # 导航组件
│   ├── modal.md                # 弹窗组件
│   └── data-display.md         # 数据展示组件
└── specs/
    ├── figma-setup-guide.md    # Figma 设置指南
    └── page-examples.md        # 页面设计示例
```

---

## 快速参考

### 颜色 Token

```css
--color-primary-500: oklch(60% 0.18 250);
--color-accent-500: oklch(65% 0.15 190);
--text-primary: var(--color-neutral-50);
--text-secondary: var(--color-neutral-400);
--bg-page: var(--color-neutral-950);
--bg-card: var(--color-neutral-900);
```

### 常用间距

```css
--space-2: 0.5rem;   /* 8px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

### 组件样式

```css
/* 卡片 */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* 按钮 */
.button--primary {
  background: var(--color-primary-500);
  color: white;
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
}
```

---

## 设计决策

### 为什么避免 AI 紫色？

AI 紫色 (#7C3AED) 已成为 AI 产品的视觉陈词滥调。鲤鱼 选择深蓝+青色组合，传达专业性和独特性。

### 为什么选择暗色主题？

- 减少视觉疲劳（长时间使用）
- 数据可视化更突出
- 符合开发者审美偏好

### 为什么使用 4px 网格？

- 一致的间距系统
- 便于开发实现
- 响应式友好

---

## 下一步

1. **在 Figma 中创建设计系统**
   - 按照 `figma-setup-guide.md` 设置变量和样式
   - 创建核心组件库

2. **设计核心页面**
   - 参考 `page-examples.md` 的布局
   - 应用设计系统

3. **与开发同步**
   - 使用 Dev Mode 交接
   - 同步 Design Tokens

4. **持续迭代**
   - 收集反馈
   - 优化组件
   - 更新文档

---

*设计系统版本: 1.0.0*
*最后更新: 2026-06-19*
