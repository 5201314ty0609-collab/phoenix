/**
 * PHOENIX AIOS — FormField 组件
 *
 * 分子组件：表单字段
 *
 * 组合了 Label + Input + HelperText + ErrorMessage
 *
 * 特性：
 * - 自动关联标签和输入框
 * - 帮助文本
 * - 错误信息
 * - 必填标记
 * - 字符计数
 */

import React, { forwardRef, useMemo, useId } from 'react';
import { cn } from '../../utils/cn';
import { Label } from '../../atoms/Label/Label';
import { Input } from '../../atoms/Input/Input';
import type { InputProps } from '../../atoms/Input/Input';
import type { BaseProps } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export interface FormFieldProps extends BaseProps {
  /** 字段标签 */
  label?: string;
  /** 帮助文本 */
  helperText?: string;
  /** 错误信息 */
  error?: string;
  /** 是否必填 */
  required?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否只读 */
  readOnly?: boolean;
  /** 标签位置 */
  labelPlacement?: 'top' | 'left' | 'inside';
  /** 标签宽度（labelPlacement='left' 时生效） */
  labelWidth?: string;
  /** 显示字符计数 */
  showCharCount?: boolean;
  /** 最大字符数 */
  maxLength?: number;
  /** 当前字符数 */
  charCount?: number;
  /** 输入框 Props */
  inputProps?: Partial<InputProps>;
  /** 子元素（自定义输入控件） */
  children?: React.ReactNode;
}

// ============================================================
// FormField 组件
// ============================================================

export const FormField = forwardRef<HTMLDivElement, FormFieldProps>(
  (props, ref) => {
    const {
      label,
      helperText,
      error,
      required = false,
      disabled = false,
      readOnly = false,
      labelPlacement = 'top',
      labelWidth = '120px',
      showCharCount = false,
      maxLength,
      charCount,
      inputProps = {},
      children,
      className,
      id: propId,
      ...rest
    } = props;

    const generatedId = useId();
    const fieldId = propId || generatedId;
    const labelId = `${fieldId}-label`;
    const helperId = `${fieldId}-helper`;
    const errorId = `${fieldId}-error`;

    const isInvalid = !!error;

    // 构建 aria-describedby
    const ariaDescribedBy = useMemo(() => {
      const ids: string[] = [];
      if (helperText) ids.push(helperId);
      if (error) ids.push(errorId);
      return ids.length > 0 ? ids.join(' ') : undefined;
    }, [helperText, error, helperId, errorId]);

    // 字符计数
    const currentCharCount = charCount ?? (inputProps.value?.toString().length || 0);
    const isOverLimit = maxLength !== undefined && currentCharCount > maxLength;

    // 标签样式
    const labelClasses = cn(
      labelPlacement === 'left' && 'flex-shrink-0',
      labelPlacement === 'inside' && 'absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-tertiary'
    );

    // 标签元素
    const labelElement = label && (
      <Label
        id={labelId}
        htmlFor={fieldId}
        required={required}
        isInvalid={isInvalid}
        disabled={disabled}
        className={labelClasses}
        style={labelPlacement === 'left' ? { width: labelWidth } : undefined}
      >
        {label}
      </Label>
    );

    // 输入控件
    const inputElement = children || (
      <Input
        id={fieldId}
        disabled={disabled}
        readOnly={readOnly}
        isInvalid={isInvalid}
        aria-labelledby={label ? labelId : undefined}
        aria-describedby={ariaDescribedBy}
        fullWidth
        {...inputProps}
      />
    );

    // 底部信息（帮助文本、错误信息、字符计数）
    const bottomContent = (helperText || error || showCharCount) && (
      <div className="flex items-center justify-between gap-2 mt-1.5">
        {/* 帮助文本或错误信息 */}
        <div className="flex-1 min-w-0">
          {error ? (
            <p
              id={errorId}
              className="text-xs text-status-danger"
              role="alert"
            >
              {error}
            </p>
          ) : helperText ? (
            <p
              id={helperId}
              className="text-xs text-text-tertiary"
            >
              {helperText}
            </p>
          ) : null}
        </div>

        {/* 字符计数 */}
        {showCharCount && maxLength !== undefined && (
          <span
            className={cn(
              'text-xs tabular-nums flex-shrink-0',
              isOverLimit ? 'text-status-danger' : 'text-text-tertiary'
            )}
          >
            {currentCharCount}/{maxLength}
          </span>
        )}
      </div>
    );

    // 水平布局
    if (labelPlacement === 'left') {
      return (
        <div
          ref={ref}
          className={cn(
            'flex items-start gap-3',
            className
          )}
          {...rest}
        >
          {labelElement}
          <div className="flex-1 min-w-0">
            {inputElement}
            {bottomContent}
          </div>
        </div>
      );
    }

    // 垂直布局（默认）
    return (
      <div
        ref={ref}
        className={cn(
          'flex flex-col gap-1.5',
          labelPlacement === 'inside' && 'relative',
          className
        )}
        {...rest}
      >
        {labelPlacement !== 'inside' && labelElement}
        <div className="relative">
          {labelPlacement === 'inside' && labelElement}
          {inputElement}
        </div>
        {bottomContent}
      </div>
    );
  }
);

FormField.displayName = 'FormField';
