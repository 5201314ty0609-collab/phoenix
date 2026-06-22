# PHOENIX AIOS Component Library — Design Specification

## 1. Atomic Design Methodology

### 层级定义

```
Atoms        → 最小可复用单元 (Button, Input, Badge, Icon)
Molecules    → 原子组合 (SearchBar, FormField, MenuItem)
Organisms    → 复杂 UI 区块 (Header, Sidebar, DataTable)
Templates    → 页面骨架 (DashboardLayout, AuthLayout)
Pages        → 具体页面实例
```

### 设计原则

| 原则 | 描述 |
|------|------|
| **单一职责** | 每个组件只做一件事 |
| **可组合性** | 组件通过组合而非继承扩展 |
| **无样式逻辑** | 行为与样式完全分离 |
| **无障碍优先** | WCAG 2.1 AA 内建支持 |
| **类型安全** | TypeScript 严格类型 |

---

## 2. 组件 API 设计

### 2.1 Props 设计原则

```typescript
// 好的设计：语义明确，类型严格
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: (event: React.MouseEvent) => void;
}

// 坏的设计：模糊的类型，过多的 boolean flags
interface BadButtonProps {
  type?: string;  // 太宽泛
  big?: boolean;  // 应该用 size
  small?: boolean;
  loading?: boolean;
  icon?: any;     // 不安全
}
```

### 2.2 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 组件 | PascalCase | `Button`, `FormField` |
| Props 接口 | `{Component}Props` | `ButtonProps` |
| Hooks | `use{Feature}` | `useToggle`, `useForm` |
| 工具函数 | camelCase | `cn()`, `mergeRefs()` |
| 常量 | UPPER_SNAKE | `BUTTON_VARIANTS` |
| CSS 变量 | `--{component}-{property}` | `--button-height` |

### 2.3 受控与非受控模式

```typescript
// 支持受控和非受控两种使用方式
interface ToggleProps {
  // 受控模式
  checked?: boolean;
  onChange?: (checked: boolean) => void;

  // 非受控模式
  defaultChecked?: boolean;

  // 公共 props
  disabled?: boolean;
  name?: string;
}
```

---

## 3. 组件状态管理

### 3.1 状态分类

| 状态类型 | 描述 | 示例 |
|---------|------|------|
| **UI 状态** | 视觉呈现状态 | hover, focus, active, disabled |
| **交互状态** | 用户交互状态 | expanded, selected, checked |
| **数据状态** | 业务数据状态 | loading, error, empty, success |
| **生命周期状态** | 组件生命周期 | mounted, entering, exiting |

### 3.2 状态管理模式

```typescript
// 状态机模式（推荐用于复杂组件）
type ModalState =
  | { status: 'closed' }
  | { status: 'opening'; startTime: number }
  | { status: 'open' }
  | { status: 'closing'; startTime: number };

// useReducer 模式
type Action =
  | { type: 'OPEN' }
  | { type: 'CLOSE' }
  | { type: 'TOGGLE' };

function modalReducer(state: ModalState, action: Action): ModalState {
  // 状态转换逻辑
}
```

---

## 4. 组件组合模式

### 4.1 Compound Components（复合组件）

```tsx
// 使用方式
<Select value={value} onChange={setValue}>
  <Select.Trigger>
    <Select.Value placeholder="选择选项" />
    <Select.Icon />
  </Select.Trigger>
  <Select.Portal>
    <Select.Content>
      <Select.Viewport>
        <Select.Item value="apple">
          <Select.ItemText>苹果</Select.ItemText>
          <Select.ItemIndicator>✓</Select.ItemIndicator>
        </Select.Item>
      </Select.Viewport>
    </Select.Content>
  </Select.Portal>
</Select>
```

### 4.2 Render Props 模式

```tsx
// 用于需要自定义渲染的场景
<Listbox
  options={options}
  value={value}
  onChange={setValue}
>
  {({ items, getSelectedItemProps }) => (
    <div>
      {items.map((item, index) => (
        <div key={item.value} {...getSelectedItemProps({ index })}>
          {item.label}
        </div>
      ))}
    </div>
  )}
</Listbox>
```

### 4.3 Slot 模式

```tsx
// 通过 Context 注入子组件
<AlertDialog.Root>
  <AlertDialog.Trigger asChild>
    <Button variant="danger">删除</Button>
  </AlertDialog.Trigger>
  <AlertDialog.Portal>
    <AlertDialog.Overlay />
    <AlertDialog.Content>
      <AlertDialog.Title>确认删除</AlertDialog.Title>
      <AlertDialog.Description>
        此操作不可撤销
      </AlertDialog.Description>
      <AlertDialog.Cancel asChild>
        <Button variant="ghost">取消</Button>
      </AlertDialog.Cancel>
      <AlertDialog.Action asChild>
        <Button variant="danger">确认删除</Button>
      </AlertDialog.Action>
    </AlertDialog.Content>
  </AlertDialog.Portal>
</AlertDialog.Root>
```

---

## 5. Headless 组件模式

### 5.1 Hooks-Based API（推荐）

```typescript
// 无头 Hook 提供行为逻辑，不包含 UI
function useToggle(options?: ToggleOptions) {
  const [checked, setChecked] = useControllableState({
    prop: options?.checked,
    defaultProp: options?.defaultChecked ?? false,
    onChange: options?.onChange,
  });

  const toggle = useCallback(() => {
    setChecked(prev => !prev);
  }, [setChecked]);

  const getToggleProps = useCallback(() => ({
    role: 'switch',
    'aria-checked': checked,
    onClick: toggle,
  }), [checked, toggle]);

  return { checked, toggle, getToggleProps };
}
```

### 5.2 使用方式

```tsx
// 开发者完全控制 UI
function MyToggle() {
  const { checked, toggle, getToggleProps } = useToggle({
    onChange: (value) => console.log('Toggled:', value),
  });

  return (
    <button
      {...getToggleProps()}
      className={`toggle ${checked ? 'active' : ''}`}
    >
      {checked ? 'ON' : 'OFF'}
    </button>
  );
}
```

---

## 6. 无障碍设计规范

### 6.1 ARIA 属性

| 组件 | 必需 ARIA 属性 |
|------|---------------|
| Button | `role="button"`, `aria-disabled`, `aria-pressed` |
| Dialog | `role="dialog"`, `aria-modal`, `aria-labelledby` |
| Tabs | `role="tablist"`, `role="tab"`, `role="tabpanel"` |
| Menu | `role="menu"`, `role="menuitem"`, `aria-expanded` |
| Select | `role="combobox"`, `aria-expanded`, `aria-activedescendant` |

### 6.2 键盘导航

| 按键 | 行为 |
|------|------|
| `Tab` / `Shift+Tab` | 焦点移动 |
| `Enter` / `Space` | 激活/选择 |
| `Escape` | 关闭弹出层 |
| `Arrow Keys` | 列表/菜单导航 |
| `Home` / `End` | 跳转到首/末项 |

### 6.3 焦点管理

```typescript
// 焦点陷阱（用于 Modal）
function useFocusTrap(ref: React.RefObject<HTMLElement>) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

    // 限制焦点在容器内
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          lastFocusable.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          firstFocusable.focus();
          e.preventDefault();
        }
      }
    };

    element.addEventListener('keydown', handleKeyDown);
    firstFocusable?.focus();

    return () => element.removeEventListener('keydown', handleKeyDown);
  }, [ref]);
}
```

---

## 7. 设计令牌系统

### 7.1 令牌层级

```
Global Tokens    → 通用值 (colors.blue.500)
  ↓
Alias Tokens     → 语义映射 (color.primary)
  ↓
Component Tokens → 组件专属 (button.bg.primary)
```

### 7.2 令牌定义

```css
:root {
  /* 基础颜色 */
  --phoenix-color-black: oklch(0% 0 0);
  --phoenix-color-white: oklch(100% 0 0);

  /* 语义颜色 */
  --phoenix-color-primary: oklch(55% 0.25 265);
  --phoenix-color-danger: oklch(55% 0.25 25);
  --phoenix-color-success: oklch(55% 0.25 145);

  /* 间距 */
  --phoenix-space-1: 0.25rem;
  --phoenix-space-2: 0.5rem;
  --phoenix-space-4: 1rem;
  --phoenix-space-8: 2rem;

  /* 圆角 */
  --phoenix-radius-sm: 0.25rem;
  --phoenix-radius-md: 0.5rem;
  --phoenix-radius-lg: 1rem;
  --phoenix-radius-full: 9999px;

  /* 阴影 */
  --phoenix-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --phoenix-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);

  /* 动画 */
  --phoenix-duration-fast: 150ms;
  --phoenix-duration-normal: 300ms;
  --phoenix-easing: cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 8. 文件结构

```
src/
├── atoms/              # 原子组件
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.css
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   ├── Input/
│   ├── Badge/
│   └── ...
├── molecules/          # 分子组件
│   ├── SearchBar/
│   ├── FormField/
│   └── ...
├── organisms/          # 有机体组件
│   ├── Header/
│   ├── DataTable/
│   └── ...
├── hooks/              # 无头 Hooks
│   ├── useToggle.ts
│   ├── useDisclosure.ts
│   ├── useControllableState.ts
│   └── ...
├── tokens/             # 设计令牌
│   ├── colors.ts
│   ├── spacing.ts
│   └── ...
├── utils/              # 工具函数
│   ├── cn.ts           # className 合并
│   ├── mergeRefs.ts    # ref 合并
│   └── ...
└── types/              # 类型定义
    ├── common.ts
    └── ...
```

---

## 9. 质量检查清单

### 组件发布前

- [ ] TypeScript 类型完整且导出
- [ ] 支持受控和非受控模式
- [ ] ARIA 属性正确实现
- [ ] 键盘导航正常工作
- [ ] 焦点管理正确
- [ ] 动画遵循 prefers-reduced-motion
- [ ] CSS 变量可覆盖
- [ ] 单元测试覆盖 80%+
- [ ] Storybook 文档完整
- [ ] 性能无回归

---

## 10. 参考资源

- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [React Aria](https://react-aria.adobe.com/)
- [Headless UI](https://headlessui.com/)
- [TanStack](https://tanstack.com/)
- [Brad Frost - Atomic Design](https://atomicdesign.bradfrost.com/)
