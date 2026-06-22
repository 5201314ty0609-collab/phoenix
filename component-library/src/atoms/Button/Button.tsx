/**
 * PHOENIX AIOS — Button 组件
 *
 * 原子组件：按钮
 *
 * 特性：
 * - 多种变体和尺寸
 * - 加载状态
 * - 图标支持
 * - 完整的 ARIA 支持
 * - asChild 模式
 */

import React, { forwardRef, useCallback, useMemo } from 'react';
import { cn } from '../../utils/cn';
import { mergeRefs } from '../../utils/mergeRefs';
import type { Size, Variant, AsChildProps, DisableableProps, LoadableProps, BaseProps } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'link';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps
  extends BaseProps,
    DisableableProps,
    LoadableProps,
    AsChildProps,
    Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'disabled'> {
  /** 按钮变体 */
  variant?: ButtonVariant;
  /** 按钮尺寸 */
  size?: ButtonSize;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 是否全宽 */
  fullWidth?: boolean;
  /** 图标按钮（无内边距） */
  iconOnly?: boolean;
  /** 子元素 */
  children?: React.ReactNode;
}

// ============================================================
// 样式映射
// ============================================================

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    'bg-interactive-primary text-white',
    'hover:bg-interactive-primary-hover',
    'active:bg-interactive-primary-active',
    'disabled:bg-gray-300 disabled:text-gray-500',
    'focus-visible:ring-2 focus-visible:ring-interactive-primary focus-visible:ring-offset-2',
  ].join(' '),
  secondary: [
    'bg-interactive-secondary text-text-primary',
    'hover:bg-interactive-secondary-hover',
    'active:bg-interactive-secondary-active',
    'disabled:bg-gray-100 disabled:text-gray-400',
    'focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2',
  ].join(' '),
  ghost: [
    'bg-transparent text-text-primary',
    'hover:bg-interactive-ghost-hover',
    'active:bg-interactive-ghost-active',
    'disabled:bg-transparent disabled:text-gray-400',
    'focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2',
  ].join(' '),
  outline: [
    'bg-transparent text-text-primary',
    'border border-border-default',
    'hover:bg-interactive-ghost-hover hover:border-border-hover',
    'active:bg-interactive-ghost-active',
    'disabled:bg-transparent disabled:text-gray-400 disabled:border-gray-200',
    'focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2',
  ].join(' '),
  danger: [
    'bg-interactive-danger text-white',
    'hover:bg-interactive-danger-hover',
    'active:bg-interactive-danger-active',
    'disabled:bg-gray-300 disabled:text-gray-500',
    'focus-visible:ring-2 focus-visible:ring-interactive-danger focus-visible:ring-offset-2',
  ].join(' '),
  link: [
    'bg-transparent text-text-link underline-offset-4',
    'hover:text-text-link-hover hover:underline',
    'active:text-text-link-hover',
    'disabled:text-gray-400 disabled:no-underline',
    'focus-visible:ring-2 focus-visible:ring-interactive-primary focus-visible:ring-offset-2',
  ].join(' '),
};

const sizeStyles: Record<ButtonSize, { base: string; icon: string }> = {
  xs: {
    base: 'h-6 px-2 text-xs gap-1 rounded',
    icon: 'h-6 w-6',
  },
  sm: {
    base: 'h-8 px-3 text-sm gap-1.5 rounded-md',
    icon: 'h-8 w-8',
  },
  md: {
    base: 'h-10 px-4 text-sm gap-2 rounded-md',
    icon: 'h-10 w-10',
  },
  lg: {
    base: 'h-12 px-6 text-base gap-2 rounded-lg',
    icon: 'h-12 w-12',
  },
  xl: {
    base: 'h-14 px-8 text-lg gap-3 rounded-lg',
    icon: 'h-14 w-14',
  },
};

// ============================================================
// Loading 组件
// ============================================================

interface SpinnerProps {
  size: ButtonSize;
}

function Spinner({ size }: SpinnerProps) {
  const spinnerSize = {
    xs: 'h-3 w-3',
    sm: 'h-3.5 w-3.5',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
    xl: 'h-6 w-6',
  }[size];

  return (
    <svg
      className={cn('animate-spin', spinnerSize)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

// ============================================================
// Button 组件
// ============================================================

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (props, ref) => {
    const {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      iconOnly = false,
      disabled = false,
      className,
      children,
      asChild,
      ...rest
    } = props;

    const isDisabled = disabled || isLoading;

    const buttonClasses = useMemo(
      () =>
        cn(
          // 基础样式
          'inline-flex items-center justify-center',
          'font-medium whitespace-nowrap',
          'transition-colors duration-150',
          'select-none',
          'focus-visible:outline-none',
          // 变体样式
          variantStyles[variant],
          // 尺寸样式
          iconOnly ? sizeStyles[size].icon : sizeStyles[size].base,
          // 全宽
          fullWidth && 'w-full',
          // 禁用
          isDisabled && 'cursor-not-allowed',
          // 自定义类名
          className
        ),
      [variant, size, iconOnly, fullWidth, isDisabled, className]
    );

    const content = useMemo(() => {
      if (isLoading) {
        return (
          <>
            <Spinner size={size} />
            {loadingText || children}
          </>
        );
      }

      return (
        <>
          {leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
        </>
      );
    }, [isLoading, loadingText, children, size, leftIcon, rightIcon]);

    // asChild 模式：将 props 合并到子元素
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        ...rest,
        className: cn(buttonClasses, (children as any).props.className),
        ref: mergeRefs(ref, (children as any).ref),
        disabled: isDisabled,
        'aria-disabled': isDisabled || undefined,
        'data-loading': isLoading || undefined,
      });
    }

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={isDisabled}
        aria-disabled={isDisabled || undefined}
        aria-busy={isLoading || undefined}
        data-loading={isLoading || undefined}
        data-variant={variant}
        data-size={size}
        {...rest}
      >
        {content}
      </button>
    );
  }
);

Button.displayName = 'Button';

export type { ButtonProps as ButtonPropsType };
