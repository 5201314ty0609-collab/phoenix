/**
 * PHOENIX AIOS Component Library — Common Types
 *
 * 通用类型定义，所有组件共享
 */

import type { ReactNode, HTMLAttributes, AriaAttributes } from 'react';

// ============================================================
// 基础尺寸和变体
// ============================================================

export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export type Variant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';

export type ColorScheme =
  | 'neutral'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info';

// ============================================================
// 组件基础 Props
// ============================================================

/** 所有组件的基础 Props */
export interface BaseProps {
  /** 自定义类名 */
  className?: string;
  /** 自定义样式 */
  style?: React.CSSProperties;
  /** 测试标识符 */
  'data-testid'?: string;
}

/** 可包含子元素的 Props */
export interface ChildrenProps {
  children?: ReactNode;
}

/** 可访问性基础 Props */
export interface AriaProps extends AriaAttributes {
  /** 元素的 ARIA 标签 */
  'aria-label'?: string;
  /** 描述元素的 ID */
  'aria-describedby'?: string;
}

/** 可禁用的组件 Props */
export interface DisableableProps {
  disabled?: boolean;
}

/** 可加载的组件 Props */
export interface LoadableProps {
  isLoading?: boolean;
  loadingText?: string;
}

// ============================================================
// 受控/非受控模式
// ============================================================

/** 受控组件的通用 Props */
export interface ControllableProps<T> {
  /** 受控值 */
  value?: T;
  /** 值变化回调 */
  onChange?: (value: T) => void;
  /** 非受控默认值 */
  defaultValue?: T;
}

/** 受控布尔状态 */
export interface ControllableBooleanProps {
  checked?: boolean;
  onChange?: (checked: boolean) => void;
  defaultChecked?: boolean;
}

// ============================================================
// 渲染相关
// ============================================================

/** asChild 模式 — 将组件行为应用到子元素 */
export interface AsChildProps {
  asChild?: boolean;
}

/** Render Props 模式 */
export interface RenderProps<T> {
  children?: (props: T) => ReactNode;
}

/** Slot 模式 */
export interface SlotProps {
  slot?: string;
}

// ============================================================
// 动画相关
// ============================================================

export type AnimationState = 'entering' | 'entered' | 'exiting' | 'exited';

export interface AnimatableProps {
  /** 是否启用动画 */
  animated?: boolean;
  /** 动画持续时间 */
  animationDuration?: number;
}

// ============================================================
// 位置和对齐
// ============================================================

export type Placement =
  | 'top'
  | 'top-start'
  | 'top-end'
  | 'right'
  | 'right-start'
  | 'right-end'
  | 'bottom'
  | 'bottom-start'
  | 'bottom-end'
  | 'left'
  | 'left-start'
  | 'left-end';

export type Alignment = 'start' | 'center' | 'end';

export type Side = 'top' | 'right' | 'bottom' | 'left';

// ============================================================
// 事件处理
// ============================================================

export type EventHandler<T> = (event: T) => void;

export interface KeyboardHandlers {
  onKeyDown?: EventHandler<React.KeyboardEvent>;
  onKeyUp?: EventHandler<React.KeyboardEvent>;
}

export interface FocusHandlers {
  onFocus?: EventHandler<React.FocusEvent>;
  onBlur?: EventHandler<React.FocusEvent>;
}

// ============================================================
// 列表和选择
// ============================================================

export interface Option<T = string> {
  value: T;
  label: string;
  disabled?: boolean;
  description?: string;
  icon?: ReactNode;
}

export type Options<T = string> = Option<T>[];

export interface SelectableProps<T> {
  selected?: T;
  onSelect?: (value: T) => void;
  defaultSelected?: T;
}

// ============================================================
// 表单相关
// ============================================================

export interface FormFieldProps extends BaseProps {
  /** 字段名称 */
  name?: string;
  /** 字段标签 */
  label?: string;
  /** 帮助文本 */
  helperText?: string;
  /** 错误信息 */
  error?: string;
  /** 是否必填 */
  required?: boolean;
}

export type ValidationState = 'valid' | 'invalid' | 'pending';

// ============================================================
// 组件状态
// ============================================================

export interface OpenableProps {
  isOpen?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
  defaultOpen?: boolean;
}

export interface ExpandableProps {
  isExpanded?: boolean;
  onExpandChange?: (isExpanded: boolean) => void;
  defaultExpanded?: boolean;
}

// ============================================================
// 工具类型
// ============================================================

/** 移除某些属性 */
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

/** 合并两个类型，后者覆盖前者的同名属性 */
export type Merge<A, B> = Omit<A, keyof B> & B;

/** 使某些属性可选 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/** 提取组件 Props 类型 */
export type PropsOf<C extends keyof JSX.IntrinsicElements | React.JSXElementConstructor<any>> =
  JSX.LibraryManagedAttributes<C, React.ComponentPropsWithRef<C>>;
