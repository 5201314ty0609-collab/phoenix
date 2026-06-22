# PHOENIX 动画设计规范 v1

> 创建日期: 2026-06-23
> 版本: v1.0.0
> 维护者: PHOENIX Design System

---

## 目录

1. [设计原则](#设计原则)
2. [时长系统](#时长系统)
3. [缓动函数](#缓动函数)
4. [动画类型](#动画类型)
5. [微交互设计](#微交互设计)
6. [性能优化](#性能优化)
7. [无障碍支持](#无障碍支持)
8. [使用指南](#使用指南)

---

## 设计原则

### 1. 性能优先

- 只动画 `transform`、`opacity`、`filter`、`clip-path`
- 避免动画 `width`、`height`、`top`、`left`、`margin`、`padding`
- 使用 `will-change` 优化，但及时移除
- 优先使用 CSS 动画，复杂序列用 JS

### 2. 语义清晰

- 动画传达含义：进入、退出、强调、反馈
- 一致的动画语言：相同操作使用相同动画
- 动画服务于功能，不是装饰

### 3. 物理直觉

- 遵循现实世界运动规律
- 加速进入，减速退出
- 弹性效果用于强调
- 避免线性动画（机械感）

### 4. 愉悦感

- 微交互增加产品个性
- 适度的弹性动画
- 即时反馈用户操作
- 避免过度动画（眩晕）

### 5. 无障碍

- 尊重 `prefers-reduced-motion`
- 提供动画开关
- 确保动画不影响可读性
- 避免闪烁（癫痫风险）

---

## 时长系统

### 感知时间心理学

| 时长 | 名称 | 用途 | 感知 |
|------|------|------|------|
| 100ms | instant | 微反馈（按钮、开关） | 即时 |
| 150ms | fast | 小过渡（颜色、阴影） | 快速 |
| 250ms | normal | 标准过渡（淡入、滑动） | 自然 |
| 350ms | moderate | 中等过渡（面板、展开） | 舒适 |
| 500ms | slow | 大型过渡（模态框） | 从容 |
| 700ms | page | 页面级过渡 | 明显 |
| 1000ms | dramatic | 特殊效果 | 戏剧性 |

### 选择原则

```
100ms  → 按钮点击、开关切换
150ms  → 悬停颜色变化、阴影变化
250ms  → 元素进入/退出、淡入淡出
350ms  → 面板展开、下拉菜单
500ms  → 模态框、大型容器
700ms  → 页面路由切换
1000ms → 特殊强调效果
```

---

## 缓动函数

### 物理运动模型

```
标准缓动: cubic-bezier(0.4, 0, 0.2, 1)
  → 大多数过渡，自然感

进入缓动: cubic-bezier(0, 0, 0.2, 1)
  → 元素出现，快速加速，缓慢停止

退出缓动: cubic-bezier(0.4, 0, 1, 1)
  → 元素消失，缓慢加速，快速退出

弹性缓动: cubic-bezier(0.34, 1.56, 0.64, 1)
  → 强调效果，轻微过冲

弹簧缓动: cubic-bezier(0.22, 1.6, 0.36, 1)
  → 活泼效果，明显过冲
```

### 使用场景

| 缓动 | 场景 | 示例 |
|------|------|------|
| standard | 大多数过渡 | 颜色、阴影、位移 |
| enter | 元素出现 | 淡入、滑入 |
| exit | 元素消失 | 淡出、滑出 |
| bounce | 强调 | 按钮点击、成功反馈 |
| spring | 活泼 | 下拉菜单、弹窗 |
| linear | 均匀 | 进度条、旋转 |

---

## 动画类型

### 1. 进入动画 (Enter)

```css
/* 淡入 */
.fade-in { animation: fadeIn 250ms ease-out forwards; }

/* 滑入 */
.slide-up { animation: slideUp 250ms ease-out forwards; }

/* 缩放进入 */
.scale-in { animation: scaleIn 250ms bounce forwards; }

/* 淡入 + 滑动 */
.fade-slide-up { animation: fadeSlideUp 350ms ease-out forwards; }
```

### 2. 退出动画 (Exit)

```css
/* 淡出 */
.fade-out { animation: fadeOut 150ms ease-in forwards; }

/* 缩放退出 */
.scale-out { animation: scaleOut 150ms ease-in forwards; }
```

### 3. 强调动画 (Emphasis)

```css
/* 脉冲 */
.pulse { animation: pulse 2s ease-in-out infinite; }

/* 摇晃 */
.shake { animation: shake 0.5s bounce; }

/* 弹跳 */
.bounce { animation: bounce 1s bounce infinite; }
```

### 4. 加载动画 (Loading)

```css
/* 旋转 */
.spinner { animation: spin 0.8s linear infinite; }

/* 骨架屏 */
.skeleton { animation: skeleton 1.5s ease-in-out infinite; }

/* 进度条 */
.progress { animation: progressShimmer 2s linear infinite; }
```

### 5. 序列动画 (Sequence)

```css
/* 交错容器 */
.stagger > * { animation: fadeSlideUp 250ms ease-out forwards; }
.stagger > *:nth-child(1) { animation-delay: 0ms; }
.stagger > *:nth-child(2) { animation-delay: 80ms; }
.stagger > *:nth-child(3) { animation-delay: 160ms; }
```

---

## 微交互设计

### 按钮

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 悬停 | translateY(-1px) + shadow | 150ms | standard |
| 点击 | translateY(0) + scale(0.98) | 100ms | standard |
| 焦点 | outline pulse | 1.5s | standard |
| 加载 | spinner | 800ms | linear |
| 成功 | scale pulse | 600ms | bounce |
| 错误 | shake | 500ms | bounce |

### 输入框

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 悬停 | border-color | 150ms | standard |
| 焦点 | border-color + box-shadow | 150ms | standard |
| 验证 | border-color | 150ms | standard |
| 错误 | shake | 300ms | bounce |
| 浮动标签 | top + scale | 150ms | standard |

### 卡片

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 悬停 | translateY(-4px) + shadow | 250ms | standard |
| 点击 | scale(0.98) | 100ms | standard |
| 选中 | border-color | 150ms | standard |

### 开关

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 切换 | translateX + background | 150ms | bounce |
| 点击 | knob width | 100ms | standard |

### 复选框

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 选中 | background + checkmark | 200ms | bounce |
| 点击 | scale(0.9) | 100ms | standard |

### 进度条

| 状态 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 进度 | width | 350ms | standard |
| 闪光 | translateX | 2s | linear |
| 脉冲 | opacity | 2s | standard |

---

## 性能优化

### GPU 加速

```css
/* 触发 GPU 加速 */
.accelerated {
  transform: translateZ(0);
  backface-visibility: hidden;
}

/* 临时优化 */
.will-animate {
  will-change: transform;
}

/* 动画结束后移除 */
.animated {
  will-change: auto;
}
```

### 动画属性优先级

```
第一梯队（合成层）:
  transform: translate, scale, rotate
  opacity

第二梯队（谨慎使用）:
  filter: blur, brightness
  clip-path

第三梯队（避免）:
  width, height
  top, left, right, bottom
  margin, padding
  border-width
```

### 60fps 检查清单

- [ ] 只动画 transform 和 opacity
- [ ] 使用 will-change 但及时移除
- [ ] 避免布局抖动
- [ ] 使用 requestAnimationFrame
- [ ] 批量 DOM 读写
- [ ] 避免强制同步布局

---

## 无障碍支持

### prefers-reduced-motion

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

### JavaScript 检测

```javascript
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion) {
  // 禁用或简化动画
}
```

### 无障碍检查清单

- [ ] 尊重 prefers-reduced-motion
- [ ] 提供动画开关选项
- [ ] 避免闪烁（3次/秒）
- [ ] 确保动画不影响可读性
- [ ] 焦点状态清晰可见
- [ ] 屏幕阅读器友好

---

## 使用指南

### CSS 动画

```html
<!-- 基础动画 -->
<div class="animate-fade-in">内容</div>
<div class="animate-slide-up">内容</div>
<div class="animate-scale-in">内容</div>

<!-- 序列动画 -->
<div class="animate-stagger">
  <div>项目 1</div>
  <div>项目 2</div>
  <div>项目 3</div>
</div>

<!-- 过渡 -->
<button class="transition-all btn-hover-lift">
  悬停我
</button>

<!-- 微交互 -->
<button class="btn btn-ripple">点击我</button>
<div class="card card-lift">悬停我</div>
```

### Framer Motion

```tsx
import { motion } from 'framer-motion';
import { fadeVariants, staggerContainer } from './framer-motion';

// 基础动画
<motion.div
  initial="hidden"
  animate="visible"
  exit="exit"
  variants={fadeVariants}
>
  内容
</motion.div>

// 序列动画
<motion.div
  initial="hidden"
  animate="visible"
  variants={staggerContainer}
>
  {items.map((item, i) => (
    <motion.div key={i} variants={staggerItem}>
      {item}
    </motion.div>
  ))}
</motion.div>

// 交互动画
<motion.button
  whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
  whileTap={{ y: 0, scale: 0.98 }}
>
  悬停我
</motion.button>

// 视口动画
<motion.div
  initial="hidden"
  whileInView="visible"
  viewport={{ once: true, amount: 0.2 }}
  variants={fadeSlideUpVariants}
>
  滚动到我
</motion.div>
```

### 动画组合模式

```tsx
// 页面进入
const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] }
};

// 列表加载
const listAnimation = {
  container: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  },
  item: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }
};

// 模态框
const modalAnimation = {
  overlay: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  content: {
    initial: { opacity: 0, scale: 0.95, y: 10 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.95, y: 10 }
  }
};
```

---

## 文件结构

```
/Users/holyty/.claude/phoenix/
├── animation-system.css      # CSS 动画系统
├── framer-motion.ts          # Framer Motion 配置
├── micro-interactions.css    # 微交互样式
└── ANIMATION-DESIGN-SPEC.md  # 本文档
```

---

## 更新日志

### v1.0.0 (2026-06-23)

- 初始版本发布
- CSS 动画系统
- Framer Motion 配置
- 微交互样式
- 设计规范文档

---

## 参考资源

- [Material Design Motion](https://m3.material.io/styles/motion/overview)
- [Apple Human Interface Guidelines - Animation](https://developer.apple.com/design/human-interface-guidelines/animation)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [CSS Animations MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations)
- [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)
