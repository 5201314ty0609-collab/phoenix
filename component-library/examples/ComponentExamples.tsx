/**
 * PHOENIX AIOS Component Library — 使用示例
 *
 * 展示组件库的核心模式和最佳实践
 */

import React, { useState } from 'react';
import {
  // 组件
  Button,
  Input,
  Badge,
  Label,
  FormField,
  SearchBar,
  Dialog,
  Toggle,

  // Hooks
  useToggle,
  useDisclosure,
  useMediaQuery,
  useBreakpoints,

  // 工具
  cn,
} from '../src';

// ============================================================
// 1. Button 示例
// ============================================================

export function ButtonExamples() {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsLoading(false);
  };

  return (
    <section>
      <h2>Button</h2>

      {/* 变体 */}
      <div className="flex gap-2">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="danger">Danger</Button>
        <Button variant="link">Link</Button>
      </div>

      {/* 尺寸 */}
      <div className="flex gap-2 items-center">
        <Button size="xs">Extra Small</Button>
        <Button size="sm">Small</Button>
        <Button size="md">Medium</Button>
        <Button size="lg">Large</Button>
        <Button size="xl">Extra Large</Button>
      </div>

      {/* 图标 */}
      <div className="flex gap-2">
        <Button
          leftIcon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 12.5a5.5 5.5 0 110-11 5.5 5.5 0 010 11zM7.25 4v4.5l3.75 2.25-.75 1.23L6.25 9.75V4h1z" />
            </svg>
          }
        >
          With Icon
        </Button>
        <Button iconOnly aria-label="Settings">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 4.754a3.246 3.246 0 100 6.492 3.246 3.246 0 000-6.492zM5.754 8a2.246 2.246 0 114.492 0 2.246 2.246 0 01-4.492 0z" />
            <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 01-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 01-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 01.52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 011.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 011.255-.52l.292.16c1.64.892 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 01.52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 01-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 01-1.255-.52l-.094-.319z" />
          </svg>
        </Button>
      </div>

      {/* 加载状态 */}
      <div className="flex gap-2">
        <Button isLoading loadingText="保存中...">
          保存
        </Button>
        <Button isLoading variant="secondary">
          提交
        </Button>
        <Button onClick={handleClick} isLoading={isLoading}>
          异步操作
        </Button>
      </div>

      {/* 禁用状态 */}
      <div className="flex gap-2">
        <Button disabled>Disabled</Button>
        <Button disabled variant="outline">
          Disabled Outline
        </Button>
      </div>

      {/* asChild 模式 */}
      <div className="flex gap-2">
        <Button asChild>
          <a href="/dashboard">Go to Dashboard</a>
        </Button>
      </div>
    </section>
  );
}

// ============================================================
// 2. Input 示例
// ============================================================

export function InputExamples() {
  const [value, setValue] = useState('');

  return (
    <section>
      <h2>Input</h2>

      {/* 变体 */}
      <div className="space-y-4">
        <Input variant="outline" placeholder="Outline variant" />
        <Input variant="filled" placeholder="Filled variant" />
        <Input variant="flushed" placeholder="Flushed variant" />
        <Input variant="unstyled" placeholder="Unstyled variant" />
      </div>

      {/* 图标 */}
      <div className="space-y-4">
        <Input
          leftIcon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M11.742 10.344a6.5 6.5 0 10-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 001.415-1.414l-3.85-3.85a1.007 1.007 0 00-.115-.1zM12 6.5a5.5 5.5 0 11-11 0 5.5 5.5 0 0111 0z" />
            </svg>
          }
          placeholder="Search..."
        />
        <Input
          rightIcon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 12.5a5.5 5.5 0 110-11 5.5 5.5 0 010 11zM7.25 4v4.5l3.75 2.25-.75 1.23L6.25 9.75V4h1z" />
            </svg>
          }
          placeholder="Time..."
        />
      </div>

      {/* 附加元素 */}
      <div className="space-y-4">
        <Input leftAddon="https://" placeholder="example.com" />
        <Input rightAddon=".com" placeholder="domain" />
      </div>

      {/* 清除按钮 */}
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        clearable
        onClear={() => setValue('')}
        placeholder="Clearable input"
      />

      {/* 错误状态 */}
      <Input isInvalid placeholder="Invalid input" />

      {/* 禁用 */}
      <Input disabled placeholder="Disabled input" />
    </section>
  );
}

// ============================================================
// 3. Badge 示例
// ============================================================

export function BadgeExamples() {
  return (
    <section>
      <h2>Badge</h2>

      {/* 颜色方案 */}
      <div className="flex gap-2">
        <Badge colorScheme="neutral">Neutral</Badge>
        <Badge colorScheme="primary">Primary</Badge>
        <Badge colorScheme="success">Success</Badge>
        <Badge colorScheme="warning">Warning</Badge>
        <Badge colorScheme="danger">Danger</Badge>
        <Badge colorScheme="info">Info</Badge>
      </div>

      {/* 变体 */}
      <div className="flex gap-2">
        <Badge variant="solid">Solid</Badge>
        <Badge variant="outline">Outline</Badge>
        <Badge variant="soft">Soft</Badge>
        <Badge variant="dot" colorScheme="success" />
      </div>

      {/* 尺寸 */}
      <div className="flex gap-2 items-center">
        <Badge size="sm">Small</Badge>
        <Badge size="md">Medium</Badge>
        <Badge size="lg">Large</Badge>
      </div>

      {/* 可关闭 */}
      <div className="flex gap-2">
        <Badge closable onClose={() => alert('Closed!')}>
          Closable
        </Badge>
        <Badge colorScheme="primary" closable>
          Primary Closable
        </Badge>
      </div>

      {/* 圆形 */}
      <div className="flex gap-2">
        <Badge rounded>Rounded</Badge>
        <Badge rounded colorScheme="success">
          Success Rounded
        </Badge>
      </div>
    </section>
  );
}

// ============================================================
// 4. FormField 示例
// ============================================================

export function FormFieldExamples() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (e.target.value && !e.target.value.includes('@')) {
      setError('请输入有效的邮箱地址');
    } else {
      setError('');
    }
  };

  return (
    <section>
      <h2>FormField</h2>

      {/* 基础用法 */}
      <FormField
        label="用户名"
        helperText="请输入您的用户名"
        inputProps={{
          placeholder: 'Enter username',
        }}
      />

      {/* 必填字段 */}
      <FormField
        label="邮箱"
        required
        error={error}
        inputProps={{
          type: 'email',
          value: email,
          onChange: handleEmailChange,
          placeholder: 'your@email.com',
        }}
      />

      {/* 水平布局 */}
      <FormField
        label="标签"
        labelPlacement="left"
        inputProps={{
          defaultValue: 'some-value',
        }}
      />

      {/* 字符计数 */}
      <FormField
        label="简介"
        showCharCount
        maxLength={100}
        inputProps={{
          placeholder: 'Tell us about yourself...',
        }}
      />

      {/* 禁用状态 */}
      <FormField
        label="Disabled Field"
        disabled
        helperText="This field is disabled"
        inputProps={{
          defaultValue: 'Disabled value',
        }}
      />

      {/* 自定义输入控件 */}
      <FormField label="自定义控件">
        <select className="w-full h-10 px-4 border rounded-md">
          <option>选项 1</option>
          <option>选项 2</option>
          <option>选项 3</option>
        </select>
      </FormField>
    </section>
  );
}

// ============================================================
// 5. SearchBar 示例
// ============================================================

export function SearchBarExamples() {
  const [query, setQuery] = useState('');

  return (
    <section>
      <h2>SearchBar</h2>

      {/* 基础用法 */}
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={(q) => alert(`Searching: ${q}`)}
      />

      {/* 带快捷键 */}
      <SearchBar
        placeholder="Search with shortcut..."
        showShortcut
        shortcutKey="k"
      />

      {/* 不同尺寸 */}
      <div className="space-y-4">
        <SearchBar size="sm" placeholder="Small search" />
        <SearchBar size="md" placeholder="Medium search" />
        <SearchBar size="lg" placeholder="Large search" />
      </div>
    </section>
  );
}

// ============================================================
// 6. Dialog 示例
// ============================================================

export function DialogExamples() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section>
      <h2>Dialog</h2>

      {/* 复合组件模式 */}
      <Dialog.Root>
        <Dialog.Trigger asChild>
          <Button>打开对话框</Button>
        </Dialog.Trigger>
        <Dialog.Portal>
          <Dialog.Overlay />
          <Dialog.Content>
            <Dialog.Title>确认操作</Dialog.Title>
            <Dialog.Description>
              您确定要执行此操作吗？此操作不可撤销。
            </Dialog.Description>
            <div className="mt-4 flex justify-end gap-2">
              <Dialog.Close asChild>
                <Button variant="ghost">取消</Button>
              </Dialog.Close>
              <Dialog.Close asChild>
                <Button variant="danger">确认删除</Button>
              </Dialog.Close>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* 受控模式 */}
      <Button onClick={() => setIsOpen(true)}>受控对话框</Button>
      <Dialog.Root isOpen={isOpen} onOpenChange={setIsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay />
          <Dialog.Content>
            <Dialog.Title>受控模式</Dialog.Title>
            <Dialog.Description>
              这个对话框通过外部状态控制。
            </Dialog.Description>
            <Dialog.Close asChild>
              <Button className="mt-4">关闭</Button>
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </section>
  );
}

// ============================================================
// 7. Toggle 示例
// ============================================================

export function ToggleExamples() {
  const [notifications, setNotifications] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [autoSave, setAutoSave] = useState(true);

  return (
    <section>
      <h2>Toggle</h2>

      {/* 基础用法 */}
      <Toggle.Root checked={notifications} onChange={setNotifications}>
        <Toggle.Switch />
        <Toggle.Label>启用通知</Toggle.Label>
      </Toggle.Root>

      {/* 标签在前 */}
      <Toggle.Root checked={darkMode} onChange={setDarkMode}>
        <Toggle.Label position="start">深色模式</Toggle.Label>
        <Toggle.Switch />
      </Toggle.Root>

      {/* 不同尺寸 */}
      <div className="space-y-2">
        <Toggle.Root>
          <Toggle.Switch size="sm" />
          <Toggle.Label>Small</Toggle.Label>
        </Toggle.Root>
        <Toggle.Root>
          <Toggle.Switch size="md" />
          <Toggle.Label>Medium</Toggle.Label>
        </Toggle.Root>
        <Toggle.Root>
          <Toggle.Switch size="lg" />
          <Toggle.Label>Large</Toggle.Label>
        </Toggle.Root>
      </div>

      {/* 自定义颜色 */}
      <Toggle.Root checked={autoSave} onChange={setAutoSave}>
        <Toggle.Switch activeColor="bg-green-500" />
        <Toggle.Label>自动保存</Toggle.Label>
      </Toggle.Root>

      {/* 禁用状态 */}
      <Toggle.Root disabled>
        <Toggle.Switch />
        <Toggle.Label>禁用的开关</Toggle.Label>
      </Toggle.Root>
    </section>
  );
}

// ============================================================
// 8. 无头 Hook 示例
// ============================================================

export function HeadlessHookExamples() {
  // 使用 useToggle 无头 Hook
  const { checked, getSwitchProps, getInputProps } = useToggle({
    onChange: (value) => console.log('Toggle changed:', value),
  });

  // 使用 useDisclosure 无头 Hook
  const { isOpen, getTriggerProps, getContentProps, getOverlayProps } = useDisclosure();

  // 使用 useMediaQuery
  const isMobile = useMediaQuery('(max-width: 768px)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');

  return (
    <section>
      <h2>Headless Hooks</h2>

      {/* 自定义 Toggle */}
      <div>
        <h3>Custom Toggle (useToggle)</h3>
        <label className="flex items-center gap-2 cursor-pointer">
          <input {...getInputProps()} />
          <div
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
          </div>
          <span>{checked ? 'ON' : 'OFF'}</span>
        </label>
      </div>

      {/* 自定义 Disclosure */}
      <div>
        <h3>Custom Disclosure (useDisclosure)</h3>
        <button
          {...getTriggerProps()}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          {isOpen ? 'Close' : 'Open'}
        </button>

        {isOpen && (
          <>
            <div
              {...getOverlayProps()}
              className="fixed inset-0 bg-black/50"
            />
            <div
              {...getContentProps()}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-xl"
            >
              <p>Custom content rendered with headless hooks!</p>
            </div>
          </>
        )}
      </div>

      {/* 响应式信息 */}
      <div>
        <h3>Responsive Info (useMediaQuery)</h3>
        <p>Is mobile: {isMobile ? 'Yes' : 'No'}</p>
        <p>Prefers reduced motion: {prefersReducedMotion ? 'Yes' : 'No'}</p>
      </div>
    </section>
  );
}

// ============================================================
// 9. 完整表单示例
// ============================================================

export function CompleteFormExample() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    bio: '',
    notifications: false,
    theme: 'light',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!formData.name) {
      newErrors.name = 'Name is required';
    }
    if (!formData.email.includes('@')) {
      newErrors.email = 'Invalid email';
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      alert('Form submitted!');
    }
  };

  return (
    <section>
      <h2>Complete Form Example</h2>

      <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
        <FormField
          label="Name"
          required
          error={errors.name}
          inputProps={{
            value: formData.name,
            onChange: (e) => setFormData({ ...formData, name: e.target.value }),
            placeholder: 'John Doe',
          }}
        />

        <FormField
          label="Email"
          required
          error={errors.email}
          inputProps={{
            type: 'email',
            value: formData.email,
            onChange: (e) => setFormData({ ...formData, email: e.target.value }),
            placeholder: 'john@example.com',
          }}
        />

        <FormField
          label="Bio"
          showCharCount
          maxLength={200}
          helperText="Tell us about yourself"
          inputProps={{
            value: formData.bio,
            onChange: (e) => setFormData({ ...formData, bio: e.target.value }),
            placeholder: 'I am a developer...',
          }}
        />

        <Toggle.Root
          checked={formData.notifications}
          onChange={(checked) =>
            setFormData({ ...formData, notifications: checked })
          }
        >
          <Toggle.Switch />
          <Toggle.Label>Enable notifications</Toggle.Label>
        </Toggle.Root>

        <div className="flex gap-2">
          <Button type="submit">Submit</Button>
          <Button type="button" variant="ghost" onClick={() => setFormData({
            name: '',
            email: '',
            bio: '',
            notifications: false,
            theme: 'light',
          })}>
            Reset
          </Button>
        </div>
      </form>
    </section>
  );
}

// ============================================================
// 导出所有示例
// ============================================================

export function AllExamples() {
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">PHOENIX AIOS Component Library</h1>
      <ButtonExamples />
      <InputExamples />
      <BadgeExamples />
      <FormFieldExamples />
      <SearchBarExamples />
      <DialogExamples />
      <ToggleExamples />
      <HeadlessHookExamples />
      <CompleteFormExample />
    </div>
  );
}
