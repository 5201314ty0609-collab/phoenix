/**
 * PHOENIX AIOS — Label 组件
 *
 * 原子组件：表单标签
 *
 * 特性：
 * - 自动关联表单控件
 * - 必填标记
 * - 错误状态
 * - 帮助文本
 */

import React, { forwardRef, useMemo } from 'react';
import { cn } from '../../utils/cn';
import type { BaseProps, DisableableProps } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export interface LabelProps
  extends BaseProps,
    DisableableProps,
    Omit<React.LabelHTMLAttributes<HTMLLabelElement>, 'htmlFor'> {
  /** 关联的表单控件 ID */
  htmlFor?: string;
  /** 是否必填 */
  required?: boolean;
  /** 必填标记位置 */
  requiredIndicator?: React.ReactNode;
  /** 错误状态 */
  isInvalid?: boolean;
  /** 标签尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 子元素 */
  children?: React.ReactNode;
}

// ============================================================
// Label 组件
// ============================================================

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  (props, ref) => {
    const {
      htmlFor,
      required = false,
      requiredIndicator,
      isInvalid = false,
      disabled = false,
      size = 'md',
      className,
      children,
      ...rest
    } = props;

    const labelClasses = useMemo(
      () =>
        cn(
          // 基础样式
          'inline-flex items-center gap-1',
          'font-medium text-text-primary',
          'select-none',
          // 尺寸样式
          size === 'sm' && 'text-sm',
          size === 'md' && 'text-sm',
          size === 'lg' && 'text-base',
          // 错误状态
          isInvalid && 'text-status-danger',
          // 禁用状态
          disabled && 'opacity-60 cursor-not-allowed',
          // 自定义类名
          className
        ),
      [size, isInvalid, disabled, className]
    );

    const defaultRequiredIndicator = (
      <span
        className="text-status-danger ml-0.5"
        aria-hidden="true"
      >
        *
      </span>
    );

    return (
      <label
        ref={ref}
        htmlFor={htmlFor}
        className={labelClasses}
        data-invalid={isInvalid || undefined}
        data-disabled={disabled || undefined}
        {...rest}
      >
        {children}
        {required && (requiredIndicator || defaultRequiredIndicator)}
      </label>
    );
  }
);

Label.displayName = 'Label';
