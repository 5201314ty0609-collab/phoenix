/**
 * PHOENIX AIOS — useToggle Hook
 *
 * 无头 Toggle 组件逻辑
 * 提供切换行为、ARIA 属性、键盘交互
 *
 * @example
 * const { checked, toggle, getInputProps } = useToggle({
 *   checked: props.checked,
 *   onChange: props.onChange,
 * });
 */

import { useCallback, useMemo } from 'react';
import { useControllableBoolean } from './useControllableState';

export interface UseToggleOptions {
  /** 受控状态 */
  checked?: boolean;
  /** 默认状态（非受控） */
  defaultChecked?: boolean;
  /** 状态变化回调 */
  onChange?: (checked: boolean) => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 字段名称 */
  name?: string;
  /** 是否必填 */
  required?: boolean;
}

export interface UseToggleReturn {
  /** 当前状态 */
  checked: boolean;
  /** 切换状态 */
  toggle: () => void;
  /** 设置状态 */
  setChecked: (value: boolean) => void;
  /** 获取 input 元素的 props */
  getInputProps: () => Record<string, unknown>;
  /** 获取 switch 元素的 props */
  getSwitchProps: () => Record<string, unknown>;
  /** 获取 label 元素的 props */
  getLabelProps: () => Record<string, unknown>;
}

/**
 * Toggle 逻辑 Hook
 *
 * 提供：
 * - 受控/非受控状态管理
 * - ARIA switch 角色和属性
 * - 键盘交互（Space/Enter 切换）
 * - 禁用状态处理
 */
export function useToggle(options: UseToggleOptions = {}): UseToggleReturn {
  const {
    disabled = false,
    name,
    required = false,
  } = options;

  const [checked, setChecked] = useControllableBoolean({
    prop: options.checked,
    defaultProp: options.defaultChecked,
    onChange: options.onChange,
  });

  const toggle = useCallback(() => {
    if (!disabled) {
      setChecked((prev) => !prev);
    }
  }, [disabled, setChecked]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (disabled) return;
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault();
        toggle();
      }
    },
    [disabled, toggle]
  );

  const handleClick = useCallback(
    (event: React.MouseEvent) => {
      if (disabled) {
        event.preventDefault();
        return;
      }
      toggle();
    },
    [disabled, toggle]
  );

  const getInputProps = useMemo(
    () => () => ({
      type: 'checkbox' as const,
      name,
      checked,
      disabled,
      required,
      onChange: handleClick,
      'aria-checked': checked,
      'aria-required': required || undefined,
      'aria-disabled': disabled || undefined,
      style: {
        position: 'absolute' as const,
        width: '1px',
        height: '1px',
        padding: 0,
        margin: '-1px',
        overflow: 'hidden' as const,
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap' as const,
        border: 0,
      },
    }),
    [name, checked, disabled, required, handleClick]
  );

  const getSwitchProps = useMemo(
    () => () => ({
      role: 'switch' as const,
      'aria-checked': checked,
      'aria-disabled': disabled || undefined,
      tabIndex: disabled ? -1 : 0,
      onKeyDown: handleKeyDown,
      onClick: handleClick,
      'data-state': checked ? 'checked' : 'unchecked',
      'data-disabled': disabled ? '' : undefined,
    }),
    [checked, disabled, handleKeyDown, handleClick]
  );

  const getLabelProps = useMemo(
    () => () => ({
      'data-state': checked ? 'checked' : 'unchecked',
      'data-disabled': disabled ? '' : undefined,
    }),
    [checked, disabled]
  );

  return {
    checked,
    toggle,
    setChecked,
    getInputProps,
    getSwitchProps,
    getLabelProps,
  };
}
