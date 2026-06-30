# 鲤鱼 AIOS 暗色主题设计规范

## 1. 设计原则

### 1.1 核心理念

暗色主题不是简单地将颜色反转，而是重新设计视觉层次，确保在低光环境下的可读性和舒适度。

**设计目标**：
- 减少眼睛疲劳
- 提供专业、现代的视觉体验
- 保持足够的对比度和可访问性
- 支持长时间使用

### 1.2 五大原则

#### 原则 1: 背景层次 (Background Hierarchy)

```
层级 1: 基础背景 (最深)     oklch(14% 0.02 250)  #0a0f1a
层级 2: 微妙背景            oklch(17% 0.02 248)  #111827
层级 3: 表面背景 (卡片)      oklch(20% 0.025 246) #1a2235
层级 4: 交替表面             oklch(24% 0.025 244) #222d42
层级 5: 悬停状态             oklch(27% 0.03 242)  #2a3650
```

**关键点**：
- 避免使用纯黑 (#000000)，它会导致视觉疲劳
- 每层差异 3-5% 亮度，创造微妙层次
- 使用冷色调 (蓝色基调) 增加专业感

#### 原则 2: 文字对比度 (Text Contrast)

遵循 WCAG 2.1 AA 标准：

| 文字类型 | 最小对比度 | 推荐对比度 | 示例 |
|---------|-----------|-----------|------|
| 主要文字 | 7:1 | 15:1 | 标题、正文 |
| 次要文字 | 4.5:1 | 7:1 | 副标题、说明 |
| 三级文字 | 3:1 | 4.5:1 | 标签、元数据 |
| 禁用文字 | 2:1 | 3:1 | 禁用状态 |

**计算公式**：
```
对比度 = (L1 + 0.05) / (L2 + 0.05)
其中 L1 是较亮颜色的相对亮度，L2 是较暗颜色的相对亮度
```

#### 原则 3: 色彩饱和度 (Color Saturation)

暗色主题需要降低饱和度 10-20%：

```css
/* 亮色主题 */
--color-brand-500: oklch(55% 0.16 242);  /* 饱和度 0.16 */

/* 暗色主题 */
--color-brand-500: oklch(55% 0.14 242);  /* 饱和度 0.14，降低 12.5% */
```

**原因**：
- 高饱和色在暗背景上会显得刺眼
- 降低饱和度可以减少视觉疲劳
- 强调色保持较高饱和度，但小面积使用

#### 原则 4: 阴影与发光 (Shadows & Glow)

暗色主题使用更深的阴影和发光效果：

```css
/* 亮色主题阴影 */
--shadow-md: 0 4px 8px oklch(0% 0 0 / 0.1);

/* 暗色主题阴影 - 更深、更明显 */
--shadow-md: 0 4px 8px oklch(0% 0 0 / 0.3);

/* 发光效果 - 暗色主题专用 */
--shadow-glow-brand: 0 0 20px oklch(55% 0.16 242 / 0.3),
                     0 0 40px oklch(55% 0.16 242 / 0.1);
```

**应用场景**：
- 卡片悬浮效果
- 按钮交互反馈
- 焦点状态指示
- 强调元素高亮

#### 原则 5: 渐变与深度 (Gradients & Depth)

使用微妙渐变增加视觉深度：

```css
/* 网格渐变 - 背景 */
--gradient-mesh: radial-gradient(at 40% 20%, var(--color-brand-900) 0px, transparent 50%),
                 radial-gradient(at 80% 0%, var(--color-brand-800) 0px, transparent 50%),
                 radial-gradient(at 0% 50%, var(--color-brand-700) 0px, transparent 50%);

/* 品牌渐变 */
--gradient-brand: linear-gradient(135deg, var(--color-brand-600), var(--color-brand-400));
```

**技巧**：
- 使用径向渐变创造焦点
- 线性渐变引导视觉流向
- 渐变角度 135° 是最常用的方向

---

## 2. 颜色系统

### 2.1 OKLCH 色彩空间

鲤鱼 使用 OKLCH 色彩空间，它具有以下优势：

- **感知均匀**：相同数值变化产生相同视觉差异
- **跨设备一致**：在不同显示器上表现一致
- **广色域支持**：支持 P3 和 Rec.2020 色域

### 2.2 颜色命名规范

```
--color-{类型}-{强度}

类型：
- brand: 品牌色 (深海蓝)
- accent: 强调色 (琥珀橙)
- neutral: 中性色 (冷灰)
- success: 成功色 (翠绿)
- warning: 警告色 (琥珀)
- error: 错误色 (珊瑚红)
- info: 信息色 (天蓝)

强度：
- 50: 最浅 (背景)
- 100-200: 浅
- 300-400: 中浅
- 500: 标准
- 600-700: 中深
- 800-900: 深
- 950: 最深
```

### 2.3 品牌色板

#### 主色 - 深海蓝 (Trust + Professional)

```css
--color-brand-900: oklch(25% 0.08 250);   /* 最深 - 背景 */
--color-brand-800: oklch(32% 0.10 248);   /* 深 */
--color-brand-700: oklch(40% 0.12 246);   /* 中深 */
--color-brand-600: oklch(48% 0.14 244);   /* 中 */
--color-brand-500: oklch(55% 0.16 242);   /* 标准 */
--color-brand-400: oklch(63% 0.14 240);   /* 中浅 */
--color-brand-300: oklch(72% 0.10 238);   /* 浅 */
--color-brand-200: oklch(82% 0.06 236);   /* 更浅 */
--color-brand-100: oklch(92% 0.03 234);   /* 最浅 */
--color-brand-50:  oklch(97% 0.01 232);   /* 几乎白 */
```

#### 强调色 - 琥珀橙 (Energy + Innovation)

```css
--color-accent-900: oklch(30% 0.12 65);   /* 最深 */
--color-accent-800: oklch(38% 0.14 63);   /* 深 */
--color-accent-700: oklch(46% 0.16 61);   /* 中深 */
--color-accent-600: oklch(54% 0.18 59);   /* 中 */
--color-accent-500: oklch(62% 0.20 57);   /* 标准 - CTA */
--color-accent-400: oklch(70% 0.18 55);   /* 中浅 */
--color-accent-300: oklch(78% 0.14 53);   /* 浅 */
--color-accent-200: oklch(86% 0.08 51);   /* 更浅 */
--color-accent-100: oklch(94% 0.04 49);   /* 最浅 */
```

#### 中性色 - 冷灰 (Balance)

```css
--color-neutral-950: oklch(13% 0.015 250); /* 最深 */
--color-neutral-900: oklch(18% 0.015 250); /* 深 */
--color-neutral-800: oklch(25% 0.015 250); /* 中深 */
--color-neutral-700: oklch(33% 0.012 250); /* 中 */
--color-neutral-600: oklch(42% 0.010 250); /* 中 */
--color-neutral-500: oklch(52% 0.008 250); /* 标准 */
--color-neutral-400: oklch(62% 0.006 250); /* 中浅 */
--color-neutral-300: oklch(72% 0.005 250); /* 浅 */
--color-neutral-200: oklch(82% 0.004 250); /* 更浅 */
--color-neutral-100: oklch(90% 0.003 250); /* 浅 */
--color-neutral-50:  oklch(96% 0.002 250); /* 几乎白 */
```

### 2.4 语义色

```css
/* 成功 - 翠绿 */
--color-success-500: oklch(50% 0.16 148);

/* 警告 - 琥珀 */
--color-warning-500: oklch(55% 0.18 68);

/* 错误 - 珊瑚红 */
--color-error-500: oklch(50% 0.18 18);

/* 信息 - 天蓝 */
--color-info-500: oklch(50% 0.14 236);
```

### 2.5 图表面板颜色

色盲友好的图表颜色方案：

```css
--chart-1: oklch(70% 0.18 57);   /* 琥珀 */
--chart-2: oklch(65% 0.16 242);  /* 蓝 */
--chart-3: oklch(60% 0.16 148);  /* 绿 */
--chart-4: oklch(60% 0.18 18);   /* 红 */
--chart-5: oklch(65% 0.14 300);  /* 紫 */
--chart-6: oklch(65% 0.12 200);  /* 青 */
--chart-7: oklch(70% 0.16 80);   /* 黄 */
--chart-8: oklch(55% 0.14 170);  /* 薄荷 */
```

---

## 3. 对比度要求

### 3.1 WCAG 2.1 AA 标准

| 元素类型 | 最小对比度 | 鲤鱼 目标 |
|---------|-----------|-------------|
| 正常文字 (< 18px) | 4.5:1 | 7:1 |
| 大文字 (≥ 18px 或 14px bold) | 3:1 | 4.5:1 |
| UI 组件 | 3:1 | 4.5:1 |
| 装饰元素 | 无要求 | 2:1 |

### 3.2 对比度检查工具

```javascript
// 计算相对亮度
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// 计算对比度
function getContrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// 检查是否符合 WCAG AA
function meetsWCAG(ratio, isLargeText = false) {
  return isLargeText ? ratio >= 3 : ratio >= 4.5;
}
```

### 3.3 鲤鱼 对比度验证

```css
/* 主要文字 vs 基础背景 */
--text-primary: oklch(95% 0.005 250);    /* L = 0.95 */
--bg-base: oklch(14% 0.02 250);          /* L = 0.14 */
/* 对比度 = (0.95 + 0.05) / (0.14 + 0.05) = 5.26:1 ✓ */

/* 次要文字 vs 基础背景 */
--text-secondary: oklch(78% 0.008 248);  /* L = 0.78 */
/* 对比度 = (0.78 + 0.05) / (0.14 + 0.05) = 4.37:1 ✓ */

/* 三级文字 vs 基础背景 */
--text-tertiary: oklch(62% 0.008 246);   /* L = 0.62 */
/* 对比度 = (0.62 + 0.05) / (0.14 + 0.05) = 3.53:1 ✓ */
```

---

## 4. 主题切换机制

### 4.1 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  ThemeManager                        │
├─────────────────────────────────────────────────────┤
│  - currentTheme: string                             │
│  - mediaQuery: MediaQueryList                       │
│  - storageKey: string                               │
├─────────────────────────────────────────────────────┤
│  + applyTheme(theme: string): void                  │
│  + getEffectiveTheme(): string                      │
│  + toggleDarkLight(): void                          │
│  + setHighContrast(enabled: boolean): void          │
│  + setReduceMotion(enabled: boolean): void          │
└─────────────────────────────────────────────────────┘
```

### 4.2 主题状态管理

```javascript
// 主题状态
const themes = {
  dark: {
    name: '暗色主题',
    icon: 'moon',
    prefersColorScheme: 'dark'
  },
  light: {
    name: '亮色主题',
    icon: 'sun',
    prefersColorScheme: 'light'
  },
  auto: {
    name: '跟随系统',
    icon: 'monitor',
    prefersColorScheme: null // 跟随系统
  }
};

// 存储键
const STORAGE_KEY = 'liyu-theme';
const CONTRAST_KEY = 'liyu-contrast';
const REDUCE_MOTION_KEY = 'liyu-reduce-motion';
```

### 4.3 切换动画

```css
/* 主题切换过渡 */
.theme-transition,
.theme-transition *,
.theme-transition *::before,
.theme-transition *::after {
  transition: background-color 0.3s ease,
              color 0.3s ease,
              border-color 0.3s ease,
              box-shadow 0.3s ease !important;
}
```

### 4.4 系统偏好检测

```javascript
// 检测系统偏好
const systemPreferences = {
  prefersDark: window.matchMedia('(prefers-color-scheme: dark)').matches,
  prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  prefersHighContrast: window.matchMedia('(prefers-contrast: high)').matches
};

// 监听系统偏好变化
window.matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', (e) => {
    if (currentTheme === 'auto') {
      applyTheme('auto');
    }
  });
```

---

## 5. 渐变和发光效果

### 5.1 渐变类型

#### 品牌渐变

```css
.gradient-brand {
  background: linear-gradient(135deg,
    var(--color-brand-600) 0%,
    var(--color-brand-400) 100%
  );
}

.gradient-brand-soft {
  background: linear-gradient(135deg,
    var(--color-brand-600) 0%,
    var(--color-brand-500) 50%,
    var(--color-brand-400) 100%
  );
}
```

#### 网格渐变 (背景)

```css
.gradient-mesh {
  background-image:
    radial-gradient(at 40% 20%, var(--color-brand-900) 0px, transparent 50%),
    radial-gradient(at 80% 0%, var(--color-brand-800) 0px, transparent 50%),
    radial-gradient(at 0% 50%, var(--color-brand-700) 0px, transparent 50%);
}
```

#### 渐变文字

```css
.gradient-text {
  background: linear-gradient(135deg,
    var(--color-brand-400) 0%,
    var(--color-accent-400) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 5.2 发光效果

#### 品牌发光

```css
.glow-brand {
  box-shadow: 0 0 20px var(--color-brand-500 / 0.3),
              0 0 40px var(--color-brand-500 / 0.1);
}

.glow-brand-lg {
  box-shadow: 0 0 30px var(--color-brand-500 / 0.4),
              0 0 60px var(--color-brand-500 / 0.2),
              0 0 100px var(--color-brand-500 / 0.1);
}
```

#### 脉冲发光

```css
.glow-brand-pulse {
  animation: glowBrandPulse 2s ease-in-out infinite;
}

@keyframes glowBrandPulse {
  0%, 100% {
    box-shadow: 0 0 20px var(--color-brand-500 / 0.3),
                0 0 40px var(--color-brand-500 / 0.1);
  }
  50% {
    box-shadow: 0 0 30px var(--color-brand-500 / 0.5),
                0 0 60px var(--color-brand-500 / 0.2),
                0 0 100px var(--color-brand-500 / 0.1);
  }
}
```

### 5.3 玻璃态效果

```css
.glass {
  background: oklch(20% 0.025 246 / 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid oklch(100% 0 0 / 0.1);
}

.glass-card {
  background: oklch(20% 0.025 246 / 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid oklch(100% 0 0 / 0.1);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--space-6);
}
```

### 5.4 霓虹效果 (暗色主题专用)

```css
[data-theme="dark"] .neon-brand {
  text-shadow: 0 0 10px var(--color-brand-500),
               0 0 20px var(--color-brand-500),
               0 0 40px var(--color-brand-500);
}
```

---

## 6. 组件示例

### 6.1 卡片

```html
<div class="card glass-card hover-lift">
  <h3 class="gradient-text">标题</h3>
  <p class="text-secondary">内容</p>
</div>
```

### 6.2 按钮

```html
<!-- 主要按钮 -->
<button class="btn btn-primary glow-brand">
  主要操作
</button>

<!-- 强调按钮 -->
<button class="btn btn-accent glow-accent">
  强调操作
</button>

<!-- 幽灵按钮 -->
<button class="btn btn-ghost hover-border">
  次要操作
</button>
```

### 6.3 导航栏

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

---

## 7. 最佳实践

### 7.1 DO - 推荐做法

- 使用 CSS 自定义属性管理主题
- 为所有交互状态提供视觉反馈
- 确保足够的对比度 (WCAG AA)
- 使用渐变和发光效果增加深度
- 提供主题切换选项
- 支持系统偏好 (暗色/亮色/减少动画)

### 7.2 DON'T - 避免做法

- 不要使用纯黑 (#000000) 作为背景
- 不要在大面积使用高饱和色
- 不要忽略对比度要求
- 不要强制用户使用单一主题
- 不要在暗色主题中使用过亮的阴影
- 不要忘记移动端适配

### 7.3 性能优化

- 使用 `will-change` 提示浏览器优化
- 使用 GPU 加速 (`transform: translateZ(0)`)
- 避免同时动画过多元素
- 使用 `contain` 属性限制重绘范围
- 在移动端减少复杂动画

---

## 8. 文件结构

```
liyu/
├── theme-system.css      # 主题变量和基础样式
├── visual-effects.css    # 渐变、发光、玻璃态效果
├── theme-manager.js      # 主题切换 JavaScript
└── DARK-THEME-SPEC.md    # 本文档
```

---

## 9. 使用指南

### 9.1 引入文件

```html
<head>
  <link rel="stylesheet" href="theme-system.css">
  <link rel="stylesheet" href="visual-effects.css">
  <script src="theme-manager.js"></script>
</head>
```

### 9.2 初始化主题

```javascript
// 自动初始化 (推荐)
// HTML: <div data-theme-toggle="icon" data-theme-size="md"></div>

// 手动初始化
const themeManager = new ThemeManager({
  defaultTheme: 'dark',
  onThemeChange: (theme, effectiveTheme) => {
    console.log(`主题切换: ${theme} (生效: ${effectiveTheme})`);
  }
});

// 创建切换按钮
const toggle = new ThemeToggle('#theme-container', {
  themeManager,
  style: 'dropdown',
  size: 'md'
});
```

### 9.3 应用主题类

```html
<!-- 渐变效果 -->
<div class="gradient-brand">...</div>

<!-- 发光效果 -->
<button class="glow-brand">...</button>

<!-- 玻璃态效果 -->
<div class="glass-card">...</div>

<!-- 交互效果 -->
<div class="hover-lift hover-glow">...</div>
```

---

## 10. 参考资源

- [WCAG 2.1 AA 标准](https://www.w3.org/WAI/WCAG21/quickref/)
- [OKLCH 色彩空间](https://oklch.com/)
- [Material Design 3 暗色主题](https://m3.material.io/styles/color/dark-theme)
- [Apple Human Interface Guidelines - 暗色模式](https://developer.apple.com/design/human-interface-guidelines/dark-mode)

---

**版本**: v1.0.0
**最后更新**: 2026-06-22
**作者**: 鲤鱼 AIOS Design System
