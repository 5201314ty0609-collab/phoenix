/**
 * PHOENIX AIOS — Badge 组件
 *
 * 原子组件：徽章/标签
 *
 * 特性：
 * - 多种颜色方案
 * - 多种变体
 * - 可关闭
 * - 图标支持
 * - 圆点模式
 */

import React, { forwardRef, useMemo, useCallback } from 'react';
import { cn } from '../../utils/cn';
import type { BaseProps, ColorScheme } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export type BadgeVariant = 'solid' | 'outline' | 'soft' | 'dot';
export type BadgeSize = 'sm' | 'md' | 'lg';

export interface BadgeProps extends BaseProps {
  /** 颜色方案 */
  colorScheme?: ColorScheme;
  /** 徽章变体 */
  variant?: BadgeVariant;
  /** 徽章尺寸 */
  size?: BadgeSize;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 是否可关闭 */
  closable?: boolean;
  /** 关闭回调 */
  onClose?: () => void;
  /** 圆角胶囊形状 */
  rounded?: boolean;
  /** 子元素 */
  children?: React.ReactNode;
}

// ============================================================
// 样式映射
// ============================================================

const colorSchemeStyles: Record<ColorScheme, { solid: string; outline: string; soft: string; dot: string }> = {
  neutral: {
    solid: 'bg-gray-600 text-white',
    outline: 'border-gray-300 text-gray-700',
    soft: 'bg-gray-100 text-gray-700',
    dot: 'bg-gray-500',
  },
  primary: {
    solid: 'bg-interactive-primary text-white',
    outline: 'border-interactive-primary text-interactive-primary',
    soft: 'bg-blue-50 text-blue-700',
    dot: 'bg-interactive-primary',
  },
  secondary: {
    solid: 'bg-gray-500 text-white',
    outline: 'border-gray-400 text-gray-600',
    soft: 'bg-gray-100 text-gray-600',
    dot: 'bg-gray-500',
  },
  success: {
    solid: 'bg-status-success text-white',
    outline: 'border-status-success text-status-success',
    soft: 'bg-status-success-bg text-green-700',
    dot: 'bg-status-success',
  },
  warning: {
    solid: 'bg-status-warning text-black',
    outline: 'border-status-warning text-yellow-700',
    soft: 'bg-status-warning-bg text-yellow-700',
    dot: 'bg-status-warning',
  },
  danger: {
    solid: 'bg-status-danger text-white',
    outline: 'border-status-danger text-status-danger',
    soft: 'bg-status-danger-bg text-red-700',
    dot: 'bg-status-danger',
  },
  info: {
    solid: 'bg-status-info text-white',
    outline: 'border-status-info text-status-info',
    soft: 'bg-status-info-bg text-blue-700',
    dot: 'bg-status-info',
  },
};

const sizeStyles: Record<BadgeSize, { base: string; dot: string }> = {
  sm: {
    base: 'h-5 px-1.5 text-xs gap-1',
    dot: 'h-1.5 w-1.5',
  },
  md: {
    base: 'h-6 px-2 text-xs gap-1.5',
    dot: 'h-2 w-2',
  },
  lg: {
    base: 'h-7 px-2.5 text-sm gap-2',
    dot: 'h-2.5 w-2.5',
  },
};

// ============================================================
// Badge 组件
// ============================================================

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (props, ref) => {
    const {
      colorScheme = 'neutral',
      variant = 'soft',
      size = 'md',
      leftIcon,
      rightIcon,
      closable = false,
      onClose,
      rounded = false,
      className,
      children,
      ...rest
    } = props;

    const handleClose = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        onClose?.();
      },
      [onClose]
    );

    const badgeClasses = useMemo(() => {
      if (variant === 'dot') {
        return cn(
          'inline-block rounded-full',
          sizeStyles[size].dot,
          colorSchemeStyles[colorScheme].dot,
          className
        );
      }

      return cn(
        // 基础样式
        'inline-flex items-center justify-center',
        'font-medium whitespace-nowrap',
        'transition-colors duration-150',
        // 尺寸样式
        sizeStyles[size].base,
        // 圆角
        rounded ? 'rounded-full' : 'rounded-md',
        // 变体和颜色
        variant === 'solid' && colorSchemeStyles[colorScheme].solid,
        variant === 'outline' && [
          'border',
          colorSchemeStyles[colorScheme].outline,
        ],
        variant === 'soft' && colorSchemeStyles[colorScheme].soft,
        // 自定义类名
        className
      );
    }, [colorScheme, variant, size, rounded, className]);

    // 圆点模式
    if (variant === 'dot') {
      return (
        <span
          ref={ref}
          className={badgeClasses}
          role="status"
          aria-label={`${colorScheme} status`}
          {...rest}
        />
      );
    }

    return (
      <span
        ref={ref}
        className={badgeClasses}
        role="status"
        data-color-scheme={colorScheme}
        data-variant={variant}
        data-size={size}
        {...rest}
      >
        {/* 左侧图标 */}
        {leftIcon && (
          <span className="inline-flex shrink-0">{leftIcon}</span>
        )}

        {/* 内容 */}
        {children}

        {/* 右侧图标 */}
        {rightIcon && (
          <span className="inline-flex shrink-0">{rightIcon}</span>
        )}

        {/* 关闭按钮 */}
        {closable && (
          <button
            type="button"
            onClick={handleClose}
            className={cn(
              'inline-flex items-center justify-center',
              'rounded-full hover:bg-black/10 transition-colors',
              size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'
            )}
            aria-label="Remove badge"
            tabIndex={-1}
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 10 10"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M2 2l6 6M8 2l-6 6" />
            </svg>
          </button>
        )}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
