# 鲤鱼 AIOS 主题系统

一个完整的暗色主题系统，支持渐变、发光、玻璃态等丰富视觉效果。

## 文件结构

```
liyu/
├── theme-system.css        # 主题变量和基础样式 (16KB)
├── visual-effects.css      # 视觉效果库 (12KB)
├── theme-manager.js        # 主题切换 JavaScript (8KB)
├── DARK-THEME-SPEC.md      # 暗色主题设计规范 (15KB)
├── THEME-SYSTEM-README.md  # 本文件
└── theme-demo.html         # 演示页面 (20KB)
```

## 特性

### 1. 完整的主题系统

- **暗色主题** (默认) - 专业、护眼、现代
- **亮色主题** - 清晰、明亮、友好
- **自动主题** - 跟随系统偏好
- **高对比度模式** - 增强可访问性
- **减少动画模式** - 尊重用户偏好

### 2. OKLCH 色彩空间

使用 OKLCH 色彩空间，具有以下优势：

- 感知均匀 - 相同数值变化产生相同视觉差异
- 跨设备一致 - 在不同显示器上表现一致
- 广色域支持 - 支持 P3 和 Rec.2020 色域

### 3. 丰富的视觉效果

#### 渐变效果
- 品牌渐变 (`gradient-brand`)
- 强调渐变 (`gradient-accent`)
- 网格渐变 (`gradient-mesh`)
- 渐变文字 (`gradient-text`)
- 渐变边框 (`gradient-border`)

#### 发光效果
- 品牌发光 (`glow-brand`)
- 强调发光 (`glow-accent`)
- 脉冲发光 (`glow-brand-pulse`)
- 悬停发光 (`glow-hover`)

#### 玻璃态效果
- 标准玻璃态 (`glass`)
- 微妙玻璃态 (`glass-subtle`)
- 强玻璃态 (`glass-strong`)
- 玻璃态卡片 (`glass-card`)
- 玻璃态导航栏 (`glass-nav`)

#### 动画效果
- 淡入 (`fade-in`, `fade-in-up`, `fade-in-down`)
- 缩放 (`scale-in`)
- 弹跳 (`bounce-in`)
- 浮动 (`float`)
- 脉冲 (`pulse`)
- 闪烁 (`shimmer`)

#### 交互效果
- 悬停提升 (`hover-lift`)
- 悬停缩放 (`hover-scale`)
- 悬停发光 (`hover-glow`)
- 悬停边框 (`hover-border`)
- 焦点环 (`focus-ring`)

### 4. 完整的设计系统

- **间距系统** - 4px 基准网格
- **圆角系统** - 从 4px 到 9999px
- **排版系统** - 完整的字体、字号、行高
- **阴影系统** - 多层次阴影，暗色主题优化
- **动画系统** - 丰富的过渡和动画曲线
- **Z-Index 系统** - 清晰的层级管理

### 5. 可访问性支持

- WCAG 2.1 AA 对比度标准
- 键盘导航支持
- 屏幕阅读器支持
- 减少动画偏好
- 高对比度模式

## 快速开始

### 1. 引入文件

```html
<head>
  <link rel="stylesheet" href="theme-system.css">
  <link rel="stylesheet" href="visual-effects.css">
  <script src="theme-manager.js"></script>
</head>
```

### 2. 设置主题

```html
<!-- 默认暗色主题 -->
<html data-theme="dark">

<!-- 亮色主题 -->
<html data-theme="light">

<!-- 自动主题 (跟随系统) -->
<html data-theme="auto">
```

### 3. 创建主题切换按钮

```html
<!-- 自动初始化 -->
<div data-theme-toggle="icon" data-theme-size="md"></div>

<!-- 或者手动初始化 -->
<div id="theme-container"></div>
<script>
  const toggle = new ThemeToggle('#theme-container', {
    style: 'dropdown',
    size: 'md'
  });
</script>
```

### 4. 应用视觉效果

```html
<!-- 渐变背景 -->
<div class="gradient-brand">内容</div>

<!-- 发光按钮 -->
<button class="btn btn-primary glow-brand">点击</button>

<!-- 玻璃态卡片 -->
<div class="glass-card">
  <h3>标题</h3>
  <p>内容</p>
</div>

<!-- 交互效果 -->
<div class="card hover-lift hover-glow">
  悬停查看效果
</div>
```

## 使用示例

### 示例 1: 导航栏

```html
<nav class="glass-nav">
  <div class="logo gradient-text">鲤鱼</div>
  <div class="nav-links">
    <a href="#" class="hover-border">首页</a>
    <a href="#" class="hover-border">功能</a>
    <a href="#" class="hover-border">关于</a>
  </div>
</nav>
```

### 示例 2: 卡片

```html
<div class="glass-card hover-lift">
  <h3 class="gradient-text">标题</h3>
  <p class="text-secondary">内容描述</p>
  <button class="btn btn-accent glow-accent-hover">
    了解更多
  </button>
</div>
```

### 示例 3: Hero 区域

```html
<section class="hero">
  <h1 class="gradient-text-demo">鲤鱼 AIOS</h1>
  <p class="hero-subtitle">专业、现代的 AI 操作系统</p>
  <div class="hero-buttons">
    <button class="btn btn-accent glow-accent">开始使用</button>
    <button class="btn btn-ghost">查看文档</button>
  </div>
</section>
```

### 示例 4: 状态指示器

```html
<div class="badge badge-success">
  <span class="gradient-dot gradient-dot-pulse"></span>
  系统正常
</div>
```

## API 参考

### ThemeManager

```javascript
const themeManager = new ThemeManager({
  storageKey: 'liyu-theme',  // 本地存储键
  defaultTheme: 'dark',         // 默认主题
  transitionDuration: 300,      // 过渡动画时长 (ms)
  onThemeChange: (theme, effectiveTheme) => {
    console.log(`主题切换: ${theme}`);
  }
});

// 方法
themeManager.applyTheme('dark');      // 应用主题
themeManager.toggleDarkLight();       // 切换暗色/亮色
themeManager.getTheme();              // 获取当前主题
themeManager.getEffectiveTheme();     // 获取生效主题
themeManager.setHighContrast(true);   // 设置高对比度
themeManager.setReduceMotion(true);   // 设置减少动画
themeManager.getSystemPreferences();  // 获取系统偏好
```

### ThemeToggle

```javascript
const toggle = new ThemeToggle('#container', {
  themeManager: themeManager,  // 主题管理器实例
  style: 'icon',               // 样式: icon, button, dropdown
  size: 'md'                   // 大小: sm, md, lg
});
```

## 自定义

### 修改颜色

```css
:root {
  /* 修改品牌色 */
  --color-brand-500: oklch(55% 0.16 242);

  /* 修改强调色 */
  --color-accent-500: oklch(62% 0.20 57);

  /* 修改背景色 */
  --bg-base: oklch(14% 0.02 250);
}
```

### 添加新效果

```css
/* 自定义发光效果 */
.glow-custom {
  box-shadow: 0 0 20px oklch(50% 0.16 300 / 0.3),
              0 0 40px oklch(50% 0.16 300 / 0.1);
}

/* 自定义渐变 */
.gradient-custom {
  background: linear-gradient(135deg,
    oklch(50% 0.16 300),
    oklch(60% 0.14 280)
  );
}
```

## 设计原则

### 1. 背景层次

- 使用 3-4 层背景深度
- 避免纯黑 (#000000)
- 每层差异 3-5% 亮度
- 使用冷色调增加专业感

### 2. 文字对比度

- 主要文字: 对比度 ≥ 7:1 (理想 15:1)
- 次要文字: 对比度 ≥ 4.5:1
- 三级文字: 对比度 ≥ 3:1
- 禁用文字: 对比度 ≥ 2:1

### 3. 色彩饱和度

- 暗色主题降低饱和度 10-20%
- 避免高饱和色大面积使用
- 强调色小面积点缀

### 4. 阴影与发光

- 暗色主题使用更深的阴影
- 阴影透明度提高到 0.3-0.45
- 使用发光效果替代传统阴影

### 5. 渐变与深度

- 使用微妙渐变增加深度
- 避免过于强烈的渐变
- 径向渐变创造焦点

## 性能优化

### 1. 使用 will-change

```css
.animated-element {
  will-change: transform, opacity;
}
```

### 2. 使用 GPU 加速

```css
.gpu-accelerated {
  transform: translateZ(0);
  backface-visibility: hidden;
}
```

### 3. 使用 contain

```css
.isolated-component {
  contain: layout paint;
}
```

### 4. 减少动画

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## 浏览器支持

- Chrome 111+
- Firefox 113+
- Safari 15.4+
- Edge 111+

OKLCH 色彩空间需要现代浏览器支持，旧版浏览器会自动回退到 sRGB。

## 更新日志

### v1.0.0 (2026-06-22)

- 初始发布
- 暗色/亮色/自动主题
- OKLCH 色彩空间
- 渐变、发光、玻璃态效果
- 完整的设计系统
- 主题切换 JavaScript
- 演示页面

## 许可证

MIT License

## 作者

鲤鱼 AIOS Design System

## 相关资源

- [暗色主题设计规范](DARK-THEME-SPEC.md)
- [演示页面](theme-demo.html)
- [WCAG 2.1 AA 标准](https://www.w3.org/WAI/WCAG21/quickref/)
- [OKLCH 色彩空间](https://oklch.com/)
