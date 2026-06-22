/**
 * PHOENIX AIOS Component Library
 *
 * 基于原子设计方法论的 React 组件库
 *
 * 架构特点：
 * - 原子设计：Atoms → Molecules → Organisms → Templates → Pages
 * - 无头组件：Hooks 提供行为逻辑，组件提供默认 UI
 * - 复合组件：通过 Context 实现隐式状态共享
 * - 受控/非受控：统一的状态管理模式
 * - 无障碍优先：WCAG 2.1 AA 内建支持
 */

// ============================================================
// 组件导出
// ============================================================

// Atoms（原子组件）
export { Button, Input, Badge, Label } from './atoms';
export type {
  ButtonProps, ButtonVariant, ButtonSize,
  InputProps, InputVariant, InputSize,
  BadgeProps, BadgeVariant, BadgeSize,
  LabelProps,
} from './atoms';

// Molecules（分子组件）
export { FormField, SearchBar } from './molecules';
export type { FormFieldProps, SearchBarProps } from './molecules';

// Organisms（有机体组件）
export { Dialog, Toggle } from './organisms';
export type {
  DialogRootProps, DialogTriggerProps, DialogPortalProps,
  DialogOverlayProps, DialogContentProps, DialogTitleProps,
  DialogDescriptionProps, DialogCloseProps,
  ToggleRootProps, ToggleSwitchProps, ToggleLabelProps,
} from './organisms';

// ============================================================
// Hooks 导出
// ============================================================

export {
  useControllableState,
  useControllableBoolean,
  useToggle,
  useDisclosure,
  useFocusTrap,
  useMediaQuery,
  useBreakpoints,
  useCurrentBreakpoint,
  BREAKPOINTS,
} from './hooks';
export type {
  UseControllableStateProps,
  UseToggleOptions,
  UseToggleReturn,
  UseDisclosureOptions,
  UseDisclosureReturn,
  UseFocusTrapOptions,
  Breakpoint,
} from './hooks';

// ============================================================
// 设计令牌导出
// ============================================================

export {
  baseColors,
  lightColors,
  darkColors,
  spacing,
  semanticSpacing,
  componentSizes,
  fontFamily,
  fontSize,
  fontWeight,
  lineHeight,
  letterSpacing,
  responsiveFontSize,
  textStyles,
  shadows,
  darkShadows,
  duration,
  easing,
  keyframes,
  animationPresets,
  reducedMotion,
} from './tokens';

// ============================================================
// 工具函数导出
// ============================================================

export { cn, cx } from './utils/cn';
export { mergeRefs, useMergedRefs } from './utils/mergeRefs';

// ============================================================
// 类型导出
// ============================================================

export type {
  Size,
  Variant,
  ColorScheme,
  BaseProps,
  ChildrenProps,
  AriaProps,
  DisableableProps,
  LoadableProps,
  ControllableProps,
  ControllableBooleanProps,
  AsChildProps,
  RenderProps,
  SlotProps,
  Placement,
  Alignment,
  Side,
  Option,
  Options,
  FormFieldProps as FormFieldType,
  OpenableProps,
  ExpandableProps,
} from './types/common';
