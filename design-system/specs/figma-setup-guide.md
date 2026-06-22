# Figma 设置指南

> 为 PHOENIX AIOS 设计系统配置 Figma 工作环境

---

## 1. 文件结构

### 1.1 创建 Figma 项目

```
PHOENIX Design System/
├── 📄 Cover                    # 封面
├── 🎨 Foundations              # 基础元素
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   ├── Icons
│   └── Grid
├── 🧩 Components               # 组件库
│   ├── Buttons
│   ├── Inputs
│   ├── Cards
│   ├── Navigation
│   ├── Modals
│   └── Data Display
├── 📐 Patterns                 # 布局模式
├── 📱 Screens                  # 完整页面
└── 📖 Documentation            # 文档
```

### 1.2 命名规范

- **页面**: 使用 Emoji + 名称，便于快速识别
- **Frame**: 使用语义化名称，如 `Button/Primary/Default`
- **图层**: 使用有意义的名称，避免 `Frame 1`, `Group 2`

---

## 2. 变量系统 (Variables)

### 2.1 颜色变量

在 Figma 中创建以下变量集合：

**Collection: Colors**

```
Mode: Dark (默认)

Primitive:
  - primary-50: #F0F4FF
  - primary-100: #D9E2FF
  - primary-200: #B3C5FF
  - primary-300: #8DA8FF
  - primary-400: #668BFF
  - primary-500: #406EFF
  - primary-600: #3358DB
  - primary-700: #2642B7
  - primary-800: #1A2C93
  - primary-900: #0D166F

  - neutral-0: #FFFFFF
  - neutral-50: #FAFAFA
  - neutral-100: #F5F5F5
  - neutral-200: #E5E5E5
  - neutral-300: #D4D4D4
  - neutral-400: #A3A3A3
  - neutral-500: #737373
  - neutral-600: #525252
  - neutral-700: #404040
  - neutral-800: #262626
  - neutral-900: #171717
  - neutral-950: #0A0A0A

  - success: #22C55E
  - warning: #F59E0B
  - error: #EF4444
  - info: #3B82F6

Semantic:
  - bg-page: {neutral-950}
  - bg-card: {neutral-900}
  - bg-input: {neutral-800}

  - text-primary: {neutral-50}
  - text-secondary: {neutral-400}
  - text-tertiary: {neutral-500}
  - text-disabled: {neutral-600}

  - border-default: {neutral-800}
  - border-hover: {neutral-700}
  - border-focus: {primary-500}

  - interactive-default: {primary-500}
  - interactive-hover: {primary-400}
  - interactive-active: {primary-600}

Mode: Light

  - bg-page: {neutral-50}
  - bg-card: {neutral-0}
  - bg-input: {neutral-100}

  - text-primary: {neutral-900}
  - text-secondary: {neutral-500}
  - text-tertiary: {neutral-400}

  - border-default: {neutral-200}
  - border-hover: {neutral-300}
```

### 2.2 间距变量

**Collection: Spacing**

```
- space-0: 0
- space-1: 4
- space-2: 8
- space-3: 12
- space-4: 16
- space-5: 20
- space-6: 24
- space-8: 32
- space-10: 40
- space-12: 48
- space-16: 64
- space-20: 80
- space-24: 96
- space-32: 128
```

### 2.3 圆角变量

**Collection: Radius**

```
- radius-none: 0
- radius-sm: 4
- radius-md: 8
- radius-lg: 12
- radius-xl: 16
- radius-2xl: 20
- radius-full: 9999
```

### 2.4 字体变量

**Collection: Typography**

```
Font Families:
  - font-primary: Geist (或 Inter)
  - font-mono: Geist Mono (或 JetBrains Mono)

Font Sizes:
  - text-xs: 12
  - text-sm: 14
  - text-base: 16
  - text-lg: 18
  - text-xl: 20
  - text-2xl: 24
  - text-3xl: 30
  - text-4xl: 36
  - text-5xl: 48
  - text-6xl: 60

Font Weights:
  - weight-regular: 400
  - weight-medium: 500
  - weight-semibold: 600
  - weight-bold: 700
```

---

## 3. 文字样式 (Text Styles)

创建以下文字样式：

```
Heading/
  - Display: Geist Bold 60px / -2% tracking
  - H1: Geist Bold 48px / -1% tracking
  - H2: Geist Semibold 36px
  - H3: Geist Semibold 24px
  - H4: Geist Semibold 20px

Body/
  - Large: Geist Regular 18px / 1.5 line-height
  - Base: Geist Regular 16px / 1.5 line-height
  - Small: Geist Regular 14px / 1.5 line-height
  - XSmall: Geist Regular 12px / 1.5 line-height

Code/
  - Mono Base: Geist Mono Regular 16px / 1.5 line-height
  - Mono Small: Geist Mono Regular 14px / 1.5 line-height
```

---

## 4. 效果样式 (Effects)

### 4.1 阴影

```
Shadow/
  - sm: Drop Shadow 0 1px 2px rgba(0,0,0,0.3)
  - md: Drop Shadow 0 4px 6px rgba(0,0,0,0.4)
  - lg: Drop Shadow 0 10px 15px rgba(0,0,0,0.5)
  - xl: Drop Shadow 0 20px 25px rgba(0,0,0,0.6)
```

### 4.2 模糊

```
Blur/
  - sm: 4px
  - md: 8px
  - lg: 12px
  - xl: 16px
```

---

## 5. 网格系统

### 5.1 基础网格

```
Layout Grid:
  - Type: Columns
  - Count: 12
  - Gutter: 24
  - Margin: 24
  - Color: rgba(255,0,0,0.1)
```

### 5.2 断点参考

```
Frame Sizes:
  - Mobile Small: 320px
  - Mobile: 375px
  - Tablet: 768px
  - Desktop Small: 1024px
  - Desktop: 1440px
  - Desktop Large: 1920px
```

---

## 6. 组件创建指南

### 6.1 Auto Layout 设置

```
按钮:
  - Direction: Horizontal
  - Padding: 12px 16px (Medium)
  - Spacing: 8px (图标与文字)
  - Alignment: Center

卡片:
  - Direction: Vertical
  - Padding: 16px
  - Spacing: 16px (区块间距)

表单字段:
  - Direction: Vertical
  - Spacing: 8px (标签与输入框)
```

### 6.2 组件属性

使用 Figma 的 Component Properties：

```
Boolean: 显示/隐藏图标
Instance Swap: 替换图标组件
Text: 文本内容
Variant: 状态、尺寸、类型
```

### 6.3 命名规范

```
组件: Category/Component
变体: Property=Value, Property=Value
示例: Type=Primary, Size=Medium, State=Default

图层:
  - 结构: layout, container, wrapper
  - 内容: title, description, label
  - 交互: button, link, input
  - 装饰: icon, badge, indicator
```

---

## 7. 页面布局模板

### 7.1 Dashboard 布局

```
Frame: Dashboard (1440 x 900)

结构:
├── TopNav (1440 x 64)
├── Sidebar (280 x 836)
└── Main Content (1160 x 836)
    ├── Header (1160 x 64)
    └── Content (1160 x 772)
        ├── Stats Row (1160 x 120)
        ├── Chart (1160 x 400)
        └── Table (1160 x 252)
```

### 7.2 Agent Monitor 布局

```
Frame: Agent Monitor (1440 x 900)

结构:
├── TopNav (1440 x 64)
├── Sidebar (280 x 836)
└── Main Content (1160 x 836)
    ├── Header (1160 x 64)
    ├── Agent Grid (1160 x 400)
    │   └── Agent Cards (3 columns)
    └── Activity Feed (1160 x 372)
```

---

## 8. 导出规范

### 8.1 切图设置

```
图标:
  - 格式: SVG
  - 导出设置: Include "id" attribute

图片:
  - 格式: PNG 或 WebP
  - 分辨率: 1x, 2x
  - 命名: component-name@2x.png
```

### 8.2 开发者交接

使用 Figma Dev Mode：

1. **标注**: 自动显示间距、尺寸
2. **代码**: 提供 CSS/React 代码片段
3. **变量**: 显示对应的 Design Token
4. **检查**: 验证颜色对比度

---

## 9. 协作流程

### 9.1 分支策略

```
main        ← 发布版本
  └── dev   ← 开发分支
       ├── feature/button-update
       └── feature/new-dashboard
```

### 9.2 版本管理

- 使用 Figma 的 Branching 功能
- 重大更新创建分支
- 合并前进行设计审查
- 更新 Changelog

### 9.3 评审流程

1. 设计师创建/修改组件
2. 在 Figma 中添加评论
3. 团队成员审查
4. 修复问题后合并
5. 发布新版本

---

## 10. 工具推荐

### Figma 插件

- **Tokens Studio**: 同步 Design Tokens
- **Contrast**: 检查颜色对比度
- **Iconify**: 图标库
- **Content Reel**: 填充真实内容
- **Autoflow**: 连接流程线

### 外部工具

- **Style Dictionary**: 转换 Design Tokens
- **Figma API**: 自动化任务
- **Storybook**: 组件文档
