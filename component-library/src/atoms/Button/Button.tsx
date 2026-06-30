/**
 * PHOENIX AIOS — Button 组件 (优化版)
 *
 * 原子组件：按钮
 *
 * 特性：
 * - 使用 CVA 定义样式变体
 * - 支持主题变量
 * - 动画效果
 * - 完整的 ARIA 支持
 * - asChild 模式
 */

import React, { forwardRef, useMemo } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';
import { mergeRefs } from '../../utils/mergeRefs';

// ============================================================
// 样式变体定义 (使用 CVA)
// ============================================================

const buttonVariants = cva(
  // 基础样式
  [
    'inline-flex items-center justify-center',
    'font-medium whitespace-nowrap',
    'transition-all duration-200 ease-out',
    'active:scale-[0.98]',
    'select-none',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100',
  ].join(' '),
  {
    variants: {
      variant: {
        primary: [
          'bg-[hsl(var(--primary))]',
          'text-[hsl(var(--primary-foreground))]',
          'hover:bg-[hsl(var(--primary-hover))]',
          'focus-visible:ring-[hsl(var(--primary))]',
        ].join(' '),
        secondary: [
          'bg-[hsl(var(--secondary))]',
          'text-[hsl(var(--secondary-foreground))]',
          'hover:bg-[hsl(var(--secondary-hover))]',
          'focus-visible:ring-[hsl(var(--secondary))]',
        ].join(' '),
        ghost: [
          'bg-transparent',
          'text-[hsl(var(--foreground))]',
          'hover:bg-[hsl(var(--accent))]',
          'focus-visible:ring-[hsl(var(--accent))]',
        ].join(' '),
        outline: [
          'bg-transparent',
          'text-[hsl(var(--foreground))]',
          'border border-[hsl(var(--border))]',
          'hover:bg-[hsl(var(--accent))]',
          'focus-visible:ring-[hsl(var(--accent))]',
        ].join(' '),
        danger: [
          'bg-[hsl(var(--destructive))]',
          'text-[hsl(var(--destructive-foreground))]',
          'hover:bg-[hsl(var(--destructive-hover))]',
          'focus-visible:ring-[hsl(var(--destructive))]',
        ].join(' '),
        link: [
          'bg-transparent',
          'text-[hsl(var(--primary))]',
          'underline-offset-4',
          'hover:underline',
          'focus-visible:ring-[hsl(var(--primary))]',
        ].join(' '),
      },
      size: {
        xs: 'h-6 px-2 text-xs gap-1 rounded',
        sm: 'h-8 px-3 text-sm gap-1.5 rounded-md',
        md: 'h-10 px-4 text-sm gap-2 rounded-md',
        lg: 'h-12 px-6 text-base gap-2 rounded-lg',
        xl: 'h-14 px-8 text-lg gap-3 rounded-lg',
      },
      fullWidth: {
        true: 'w-full',
        false: '',
      },
      iconOnly: {
        true: 'px-0',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      fullWidth: false,
      iconOnly: false,
    },
  }
);

// ============================================================
// 类型定义
// ============================================================

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** 加载状态 */
  isLoading?: boolean;
  /** 加载时显示的文字 */
  loadingText?: string;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** asChild 模式 */
  asChild?: boolean;
  /** 子元素 */
  children?: React.ReactNode;
}

// ============================================================
// Loading 组件
// ============================================================

interface SpinnerProps {
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
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
      fullWidth = false,
      iconOnly = false,
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
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
          buttonVariants({ variant, size, fullWidth, iconOnly }),
          className
        ),
      [variant, size, fullWidth, iconOnly, className]
    );

    const content = useMemo(() => {
      if (isLoading) {
        return (
          <>
            <Spinner size={size || 'md'} />
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

// ============================================================
// 导出
// ============================================================

export { buttonVariants };
export type { ButtonProps as ButtonPropsType };
