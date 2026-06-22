/**
 * PHOENIX AIOS — SearchBar 组件
 *
 * 分子组件：搜索栏
 *
 * 组合了 Input + 搜索图标 + 清除按钮 + 快捷键提示
 *
 * 特性：
 * - 搜索图标
 * - 清除按钮
 * - 快捷键提示（Cmd+K / Ctrl+K）
 * - 防抖搜索
 * - 受控/非受控模式
 */

import React, { forwardRef, useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { cn } from '../../utils/cn';
import { Input } from '../../atoms/Input/Input';
import type { BaseProps, DisableableProps } from '../../types/common';

// ============================================================
// Props 定义
// ============================================================

export interface SearchBarProps extends BaseProps, DisableableProps {
  /** 搜索值（受控） */
  value?: string;
  /** 默认值（非受控） */
  defaultValue?: string;
  /** 值变化回调 */
  onChange?: (value: string) => void;
  /** 搜索回调（按 Enter 触发） */
  onSearch?: (value: string) => void;
  /** 占位符 */
  placeholder?: string;
  /** 是否显示清除按钮 */
  clearable?: boolean;
  /** 是否显示快捷键提示 */
  showShortcut?: boolean;
  /** 快捷键 */
  shortcutKey?: string;
  /** 防抖时间（毫秒） */
  debounceMs?: number;
  /** 搜索图标 */
  searchIcon?: React.ReactNode;
  /** 输入框尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否自动聚焦 */
  autoFocus?: boolean;
}

// ============================================================
// 默认图标
// ============================================================

function DefaultSearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="6.5" cy="6.5" r="5.5" />
      <path d="M14 14l-3.5-3.5" />
    </svg>
  );
}

function ClearIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <path d="M3 3l8 8M11 3l-8 8" />
    </svg>
  );
}

// ============================================================
// SearchBar 组件
// ============================================================

export const SearchBar = forwardRef<HTMLInputElement, SearchBarProps>(
  (props, ref) => {
    const {
      value: controlledValue,
      defaultValue = '',
      onChange,
      onSearch,
      placeholder = '搜索...',
      clearable = true,
      showShortcut = true,
      shortcutKey = 'k',
      debounceMs = 300,
      searchIcon,
      size = 'md',
      autoFocus = false,
      disabled = false,
      className,
      ...rest
    } = props;

    const [internalValue, setInternalValue] = useState(defaultValue);
    const isControlled = controlledValue !== undefined;
    const value = isControlled ? controlledValue : internalValue;

    const debounceTimerRef = useRef<ReturnType<typeof setTimeout>>();
    const inputRef = useRef<HTMLInputElement>(null);

    // 清理定时器
    useEffect(() => {
      return () => {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
      };
    }, []);

    // 处理值变化
    const handleChange = useCallback(
      (newValue: string) => {
        if (!isControlled) {
          setInternalValue(newValue);
        }

        // 防抖搜索
        if (debounceMs > 0 && onChange) {
          if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
          }
          debounceTimerRef.current = setTimeout(() => {
            onChange(newValue);
          }, debounceMs);
        } else {
          onChange?.(newValue);
        }
      },
      [isControlled, onChange, debounceMs]
    );

    // 处理输入事件
    const handleInput = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        handleChange(e.target.value);
      },
      [handleChange]
    );

    // 处理搜索（Enter 键）
    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
          onSearch?.(value);
        }
      },
      [onSearch, value]
    );

    // 处理清除
    const handleClear = useCallback(() => {
      handleChange('');
      inputRef.current?.focus();
    }, [handleChange]);

    // 全局快捷键（Cmd+K / Ctrl+K）
    useEffect(() => {
      if (!showShortcut || !shortcutKey) return;

      const handleGlobalKeyDown = (e: KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.key === shortcutKey) {
          e.preventDefault();
          inputRef.current?.focus();
        }
      };

      document.addEventListener('keydown', handleGlobalKeyDown);
      return () => document.removeEventListener('keydown', handleGlobalKeyDown);
    }, [showShortcut, shortcutKey]);

    // 检测操作系统（用于显示正确的快捷键符号）
    const isMac = useMemo(() => {
      if (typeof navigator === 'undefined') return false;
      return navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    }, []);

    const shortcutDisplay = useMemo(() => {
      if (!showShortcut || !shortcutKey) return null;
      return isMac ? `⌘${shortcutKey.toUpperCase()}` : `Ctrl+${shortcutKey.toUpperCase()}`;
    }, [showShortcut, shortcutKey, isMac]);

    // 左侧图标
    const leftIconElement = searchIcon || <DefaultSearchIcon />;

    // 右侧元素（快捷键提示或清除按钮）
    const rightElement = (
      <div className="flex items-center gap-1">
        {/* 清除按钮 */}
        {clearable && value && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="p-0.5 rounded hover:bg-gray-200 text-text-tertiary hover:text-text-secondary transition-colors"
            aria-label="Clear search"
            tabIndex={-1}
          >
            <ClearIcon />
          </button>
        )}

        {/* 快捷键提示 */}
        {shortcutDisplay && !value && (
          <kbd
            className={cn(
              'hidden sm:inline-flex items-center',
              'px-1.5 py-0.5',
              'text-xs font-medium text-text-tertiary',
              'bg-gray-100 border border-gray-200 rounded',
              'pointer-events-none select-none'
            )}
          >
            {shortcutDisplay}
          </kbd>
        )}
      </div>
    );

    return (
      <div
        className={cn(
          'relative',
          className
        )}
        {...rest}
      >
        <Input
          ref={ref}
          type="search"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          size={size}
          autoFocus={autoFocus}
          leftIcon={leftIconElement}
          rightIcon={rightElement}
          fullWidth
          aria-label="Search"
        />
      </div>
    );
  }
);

SearchBar.displayName = 'SearchBar';
