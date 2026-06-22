# PHOENIX AIOS Component Library

基于原子设计方法论的 React 组件库，融合了 Radix UI 和 React Aria 的设计理念。

## 架构特点

### 1. 原子设计（Atomic Design）

```
Atoms        → 最小可复用单元 (Button, Input, Badge, Label)
Molecules    → 原子组合 (FormField, SearchBar)
Organisms    → 复杂 UI 区块 (Dialog, Toggle)
Templates    → 页面骨架
Pages        → 具体页面实例
```

### 2. 无头组件模式（Headless Components）

Hooks 提供行为逻辑，组件提供默认 UI，开发者可以完全自定义渲染：

```tsx
// 使用无头 Hook
const { checked, getSwitchProps } = useToggle({ onChange: handler });

// 自定义 UI
<button {...getSwitchProps()} className="my-custom-toggle">
  {checked ? 'ON' : 'OFF'}
</button>
```

### 3. 复合组件模式（Compound Components）

通过 Context 实现隐式状态共享，提供灵活的组合 API：

```tsx
<Dialog.Root>
  <Dialog.Trigger asChild>
    <Button>Open</Button>
  </Dialog.Trigger>
  <Dialog.Portal>
    <Dialog.Overlay />
    <Dialog.Content>
      <Dialog.Title>Title</Dialog.Title>
      <Dialog.Description>Description</Dialog.Description>
      <Dialog.Close asChild>
        <Button>Close</Button>
      </Dialog.Close>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
```

### 4. 受控/非受控模式

所有交互组件支持两种使用方式：

```tsx
// 非受控
<Input defaultValue="Hello" />

// 受控
<Input value={value} onChange={setValue} />
```

### 5. 无障碍优先（Accessibility First）

- WCAG 2.1 AA 内建支持
- 完整的 ARIA 属性
- 键盘导航
- 焦点管理
- 屏幕阅读器兼容

---

## 目录结构

```
src/
├── atoms/              # 原子组件
│   ├── Button/         # 按钮
│   ├── Input/          # 输入框
│   ├── Badge/          # 徽章
│   └── Label/          # 标签
├── molecules/          # 分子组件
│   ├── FormField/      # 表单字段
│   └── SearchBar/      # 搜索栏
├── organisms/          # 有机体组件
│   ├── Dialog/         # 对话框
│   └── Toggle/         # 开关
├── hooks/              # 无头 Hooks
│   ├── useControllableState.ts
│   ├── useToggle.ts
│   ├── useDisclosure.ts
│   ├── useFocusTrap.ts
│   └── useMediaQuery.ts
├── tokens/             # 设计令牌
│   ├── colors.ts       # 颜色系统
│   ├── spacing.ts      # 间距系统
│   ├── typography.ts   # 排版系统
│   ├── shadows.ts      # 阴影系统
│   ├── animations.ts   # 动画系统
│   └── tokens.css      # CSS 变量
├── utils/              # 工具函数
│   ├── cn.ts           # 类名合并
│   └── mergeRefs.ts    # Ref 合并
└── types/              # 类型定义
    └── common.ts       # 通用类型
```

---

## 组件列表

### Atoms（原子组件）

| 组件 | 描述 | 特性 |
|------|------|------|
| `Button` | 按钮 | 6 种变体、5 种尺寸、图标支持、加载状态、asChild 模式 |
| `Input` | 输入框 | 4 种变体、3 种尺寸、图标/插槽、清除按钮、错误状态 |
| `Badge` | 徽章 | 7 种颜色、4 种变体、可关闭、圆点模式 |
| `Label` | 标签 | 自动关联、必填标记、错误状态 |

### Molecules（分子组件）

| 组件 | 描述 | 特性 |
|------|------|------|
| `FormField` | 表单字段 | Label + Input + HelperText + Error 组合 |
| `SearchBar` | 搜索栏 | 搜索图标、清除按钮、快捷键（Cmd+K）、防抖 |

### Organisms（有机体组件）

| 组件 | 描述 | 特性 |
|------|------|------|
| `Dialog` | 对话框 | 复合组件模式、焦点陷阱、动画、Portal |
| `Toggle` | 开关 | 复合组件模式、多种尺寸、自定义颜色 |

---

## Hooks（无头逻辑）

| Hook | 描述 | 用途 |
|------|------|------|
| `useControllableState` | 受控/非受控状态 | 统一的状态管理基础 |
| `useToggle` | 切换逻辑 | 开关、复选框 |
| `useDisclosure` | 展开/关闭逻辑 | 对话框、抽屉、折叠面板 |
| `useFocusTrap` | 焦点陷阱 | 模态框、弹出层 |
| `useMediaQuery` | 媒体查询 | 响应式设计 |
| `useBreakpoints` | 多断点匹配 | 断点感知组件 |
| `useCurrentBreakpoint` | 当前断点 | 断点特定逻辑 |

---

## 设计令牌

### 颜色系统

使用 oklch 色彩空间，感知均匀：

```typescript
import { baseColors, lightColors, darkColors } from 'phoenix-ui';

// 基础色板
baseColors.blue;      // oklch(65% 0.2 265)
baseColors.red;       // oklch(65% 0.2 20)

// 语义颜色
lightColors.text.primary;           // oklch(20% 0.005 286)
lightColors.interactive.primary;    // oklch(55% 0.2 265)
```

### CSS 变量

```css
/* 使用 CSS 变量 */
.my-component {
  background: var(--phoenix-bg-base);
  color: var(--phoenix-text-primary);
  border: 1px solid var(--phoenix-border-default);
  border-radius: var(--phoenix-radius-md);
  box-shadow: var(--phoenix-shadow-sm);
}
```

### 间距系统

基于 4px 网格：

```typescript
import { spacing } from 'phoenix-ui';

spacing[4];  // '1rem' (16px)
spacing[8];  // '2rem' (32px)
```

### 排版系统

```typescript
import { textStyles } from 'phoenix-ui';

// 预定义的文本样式
textStyles['heading-1'];
textStyles['body'];
textStyles['code'];
```

---

## 使用示例

### 基础用法

```tsx
import { Button, Input, Badge } from 'phoenix-ui';

function App() {
  return (
    <div>
      <Button variant="primary" size="md">
        Click me
      </Button>

      <Input placeholder="Enter text..." clearable />

      <Badge colorScheme="success">Active</Badge>
    </div>
  );
}
```

### 表单示例

```tsx
import { FormField, Button, Toggle } from 'phoenix-ui';

function SignupForm() {
  const [agreed, setAgreed] = useState(false);

  return (
    <form>
      <FormField
        label="Email"
        required
        error="Invalid email"
        inputProps={{ type: 'email' }}
      />

      <Toggle.Root checked={agreed} onChange={setAgreed}>
        <Toggle.Switch />
        <Toggle.Label>I agree to the terms</Toggle.Label>
      </Toggle.Root>

      <Button type="submit">Sign Up</Button>
    </form>
  );
}
```

### 自定义组件（使用 Hooks）

```tsx
import { useToggle, useDisclosure, cn } from 'phoenix-ui';

function CustomSwitch() {
  const { checked, getSwitchProps } = useToggle();

  return (
    <button
      {...getSwitchProps()}
      className={cn(
        'relative w-12 h-6 rounded-full transition-colors',
        checked ? 'bg-blue-500' : 'bg-gray-300'
      )}
    >
      <div
        className={cn(
          'absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform',
          checked && 'translate-x-6'
        )}
      />
    </button>
  );
}

function CustomModal() {
  const { isOpen, getTriggerProps, getContentProps, getOverlayProps } = useDisclosure();

  return (
    <>
      <button {...getTriggerProps()}>Open Modal</button>
      {isOpen && (
        <>
          <div {...getOverlayProps()} className="fixed inset-0 bg-black/50" />
          <div {...getContentProps()} className="fixed ...">
            Custom modal content
          </div>
        </>
      )}
    </>
  );
}
```

---

## 响应式设计

```tsx
import { useMediaQuery, useBreakpoints, useCurrentBreakpoint } from 'phoenix-ui';

function ResponsiveComponent() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const breakpoints = useBreakpoints();
  const current = useCurrentBreakpoint();

  return (
    <div>
      {isMobile ? <MobileLayout /> : <DesktopLayout />}
      <p>Current breakpoint: {current}</p>
    </div>
  );
}
```

---

## 暗色模式

组件库自动支持暗色模式：

```tsx
// 通过 data 属性切换
<html data-theme="dark">
// 或
<html class="dark">

// 通过 CSS 媒体查询自动检测
@media (prefers-color-scheme: dark) { ... }
```

---

## 减少动画

自动检测用户偏好：

```tsx
import { useMediaQuery } from 'phoenix-ui';

function AnimatedComponent() {
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');

  return (
    <div className={prefersReducedMotion ? 'no-animation' : 'animate-fade-in'}>
      Content
    </div>
  );
}
```

---

## 设计原则

1. **单一职责** — 每个组件只做一件事
2. **可组合性** — 通过组合而非继承扩展
3. **无样式逻辑** — 行为与样式完全分离
4. **无障碍优先** — WCAG 2.1 AA 内建支持
5. **类型安全** — TypeScript 严格类型

---

## 参考资源

- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [React Aria](https://react-aria.adobe.com/)
- [Brad Frost - Atomic Design](https://atomicdesign.bradfrost.com/)
- [Headless UI](https://headlessui.com/)
- [TanStack](https://tanstack.com/)

---

## 设计规范

详细的设计规范请参阅 [docs/DESIGN-SPEC.md](./docs/DESIGN-SPEC.md)
