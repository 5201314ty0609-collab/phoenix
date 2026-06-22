/**
 * PHOENIX AIOS — Input 组件
 *
 * 原子组件：输入框
 *
 * 特性：
 * - 多种变体和尺寸
 * - 左右图标/插槽
 * - 错误状态
 * - 完整的 ARIA 支持
 * - 受控/非受控模式
 */

import React, { forwardRef, useMemo, useState, useCallback } from 'react';
import { cn } from '../../utils/cn';
import type { BaseProps, DisableableProps, ValidationState } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export type InputVariant = 'outline' | 'filled' | 'flushed' | 'unstyled';
export type InputSize = 'sm' | 'md' | 'lg';

export interface InputProps
  extends BaseProps,
    DisableableProps,
    Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'disabled'> {
  /** 输入框变体 */
  variant?: InputVariant;
  /** 输入框尺寸 */
  size?: InputSize;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 左侧附加元素 */
  leftAddon?: React.ReactNode;
  /** 右侧附加元素 */
  rightAddon?: React.ReactNode;
  /** 错误状态 */
  isInvalid?: boolean;
  /** 验证状态 */
  validationState?: ValidationState;
  /** 全宽 */
  fullWidth?: boolean;
  /** 是否可清除 */
  clearable?: boolean;
  /** 清除回调 */
  onClear?: () => void;
}

// ============================================================
// 样式映射
// ============================================================

const variantStyles: Record<InputVariant, string> = {
  outline: [
    'bg-bg-base border border-border-default',
    'hover:border-border-hover',
    'focus:border-border-focus focus:ring-2 focus:ring-border-focus/20',
    'disabled:bg-gray-50 disabled:border-gray-200',
  ].join(' '),
  filled: [
    'bg-gray-50 border border-transparent',
    'hover:bg-gray-100',
    'focus:bg-bg-base focus:border-border-focus focus:ring-2 focus:ring-border-focus/20',
    'disabled:bg-gray-100',
  ].join(' '),
  flushed: [
    'bg-transparent border-b border-border-default',
    'hover:border-border-hover',
    'focus:border-border-focus focus:ring-0',
    'rounded-none',
    'disabled:border-gray-200',
  ].join(' '),
  unstyled: [
    'bg-transparent border-none',
    'focus:ring-0',
  ].join(' '),
};

const sizeStyles: Record<InputSize, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-4 text-base',
};

// ============================================================
// Input 组件
// ============================================================

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (props, ref) => {
    const {
      variant = 'outline',
      size = 'md',
      leftIcon,
      rightIcon,
      leftAddon,
      rightAddon,
      isInvalid = false,
      validationState,
      fullWidth = true,
      clearable = false,
      onClear,
      disabled = false,
      className,
      value,
      defaultValue,
      onChange,
      type = 'text',
      id,
      name,
      placeholder,
      required,
      readOnly,
      autoComplete,
      autoFocus,
      maxLength,
      minLength,
      pattern,
      'aria-label': ariaLabel,
      'aria-describedby': ariaDescribedBy,
      ...rest
    } = props;

    const [internalValue, setInternalValue] = useState(defaultValue ?? '');
    const isControlled = value !== undefined;
    const currentValue = isControlled ? value : internalValue;
    const hasError = isInvalid || validationState === 'invalid';

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!isControlled) {
          setInternalValue(e.target.value);
        }
        onChange?.(e);
      },
      [isControlled, onChange]
    );

    const handleClear = useCallback(() => {
      if (!isControlled) {
        setInternalValue('');
      }
      onClear?.();
      // 触发 onChange 事件
      const event = {
        target: { value: '' },
        currentTarget: { value: '' },
      } as React.ChangeEvent<HTMLInputElement>;
      onChange?.(event);
    }, [isControlled, onClear, onChange]);

    const inputClasses = useMemo(
      () =>
        cn(
          // 基础样式
          'w-full text-text-primary placeholder:text-text-tertiary',
          'transition-colors duration-150',
          'focus:outline-none',
          // 变体样式
          variantStyles[variant],
          // 尺寸样式
          sizeStyles[size],
          // 错误状态
          hasError && 'border-status-danger focus:border-status-danger focus:ring-status-danger/20',
          // 禁用
          disabled && 'cursor-not-allowed opacity-60',
          // 只读
          readOnly && 'cursor-default',
          // 左侧有图标/插槽时的内边距
          leftIcon && 'pl-10',
          leftAddon && 'pl-0',
          // 右侧有图标/插槽时的内边距
          (rightIcon || clearable) && 'pr-10',
          rightAddon && 'pr-0',
          // 自定义类名
          className
        ),
      [variant, size, hasError, disabled, readOnly, leftIcon, leftAddon, rightIcon, clearable, className]
    );

    const inputElement = (
      <input
        ref={ref}
        type={type}
        id={id}
        name={name}
        value={currentValue}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        required={required}
        autoComplete={autoComplete}
        autoFocus={autoFocus}
        maxLength={maxLength}
        minLength={minLength}
        pattern={pattern}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-invalid={hasError || undefined}
        aria-required={required || undefined}
        aria-disabled={disabled || undefined}
        aria-readonly={readOnly || undefined}
        className={inputClasses}
        data-variant={variant}
        data-size={size}
        data-invalid={hasError || undefined}
        {...rest}
      />
    );

    // 简单模式（无附加元素）
    if (!leftIcon && !rightIcon && !leftAddon && !rightAddon && !clearable) {
      return inputElement;
    }

    // 复合模式（带附加元素）
    return (
      <div
        className={cn(
          'relative inline-flex items-center',
          fullWidth && 'w-full'
        )}
      >
        {/* 左侧附加元素 */}
        {leftAddon && (
          <div className="flex items-center justify-center px-3 bg-gray-50 border border-r-0 border-border-default rounded-l-md text-text-secondary text-sm h-full">
            {leftAddon}
          </div>
        )}

        {/* 左侧图标 */}
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
            {leftIcon}
          </div>
        )}

        {/* 输入框 */}
        {React.cloneElement(inputElement, {
          className: cn(
            inputElement.props.className,
            leftAddon && 'rounded-l-none',
            rightAddon && 'rounded-r-none'
          ),
        })}

        {/* 清除按钮 */}
        {clearable && currentValue && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
            aria-label="Clear input"
            tabIndex={-1}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        )}

        {/* 右侧图标 */}
        {rightIcon && !clearable && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
            {rightIcon}
          </div>
        )}

        {/* 右侧附加元素 */}
        {rightAddon && (
          <div className="flex items-center justify-center px-3 bg-gray-50 border border-l-0 border-border-default rounded-r-md text-text-secondary text-sm h-full">
            {rightAddon}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
