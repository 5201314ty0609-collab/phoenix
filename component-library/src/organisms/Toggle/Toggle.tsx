/**
 * PHOENIX AIOS — Toggle 组件
 *
 * 有机体组件：开关
 *
 * 使用无头 Hook 模式，提供完整无障碍支持
 *
 * @example
 * // 基础用法
 * <Toggle checked={value} onChange={setValue} />
 *
 * // 带标签
 * <Toggle.Root checked={value} onChange={setValue}>
 *   <Toggle.Label>启用通知</Toggle.Label>
 *   <Toggle.Switch />
 * </Toggle.Root>
 *
 * // 无头模式
 * const { checked, getSwitchProps } = useToggle({ onChange: handler });
 * <button {...getSwitchProps()}>...</button>
 */

import React, { forwardRef, createContext, useContext, useMemo } from 'react';
import { cn } from '../../utils/cn';
import { useToggle } from '../../hooks/useToggle';
import type { BaseProps, ChildrenProps } from '../../types/common';

// ============================================================
// Context
// ============================================================

interface ToggleContextValue {
  checked: boolean;
  disabled: boolean;
  getSwitchProps: () => Record<string, unknown>;
  getLabelProps: () => Record<string, unknown>;
}

const ToggleContext = createContext<ToggleContextValue | null>(null);

function useToggleContext() {
  const context = useContext(ToggleContext);
  if (!context) {
    throw new Error('Toggle compound components must be used within Toggle.Root');
  }
  return context;
}

// ============================================================
// Root
// ============================================================

export interface ToggleRootProps extends BaseProps, ChildrenProps {
  /** 受控状态 */
  checked?: boolean;
  /** 默认状态（非受控） */
  defaultChecked?: boolean;
  /** 状态变化回调 */
  onChange?: (checked: boolean) => void;
  /** 是否禁用 */
  disabled?: boolean;
}

function ToggleRoot(props: ToggleRootProps) {
  const {
    children,
    checked: controlledChecked,
    defaultChecked = false,
    onChange,
    disabled = false,
    className,
    ...rest
  } = props;

  const { checked, getSwitchProps, getLabelProps } = useToggle({
    checked: controlledChecked,
    defaultChecked,
    onChange,
    disabled,
  });

  const contextValue = useMemo(
    () => ({
      checked,
      disabled,
      getSwitchProps,
      getLabelProps,
    }),
    [checked, disabled, getSwitchProps, getLabelProps]
  );

  return (
    <ToggleContext.Provider value={contextValue}>
      <div
        className={cn(
          'inline-flex items-center gap-2',
          disabled && 'opacity-60 cursor-not-allowed',
          className
        )}
        data-state={checked ? 'checked' : 'unchecked'}
        data-disabled={disabled || undefined}
        {...rest}
      >
        {children}
      </div>
    </ToggleContext.Provider>
  );
}

ToggleRoot.displayName = 'Toggle.Root';

// ============================================================
// Switch
// ============================================================

export interface ToggleSwitchProps extends BaseProps {
  /** 开关尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 轨道颜色（开启状态） */
  activeColor?: string;
}

const ToggleSwitch = forwardRef<HTMLButtonElement, ToggleSwitchProps>(
  (props, ref) => {
    const { size = 'md', activeColor, className, ...rest } = props;
    const { checked, disabled, getSwitchProps } = useToggleContext();

    const switchProps = getSwitchProps();

    const sizeStyles = {
      sm: {
        track: 'h-5 w-9',
        thumb: 'h-4 w-4',
        translate: 'translate-x-4',
      },
      md: {
        track: 'h-6 w-11',
        thumb: 'h-5 w-5',
        translate: 'translate-x-5',
      },
      lg: {
        track: 'h-7 w-14',
        thumb: 'h-6 w-6',
        translate: 'translate-x-7',
      },
    }[size];

    return (
      <button
        ref={ref}
        {...switchProps}
        className={cn(
          // 基础样式
          'relative inline-flex items-center',
          'rounded-full transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-border-focus focus:ring-offset-2',
          // 尺寸
          sizeStyles.track,
          // 颜色
          checked
            ? activeColor || 'bg-interactive-primary'
            : 'bg-gray-200',
          // 禁用
          disabled && 'cursor-not-allowed',
          className
        )}
        {...rest}
      >
        <span
          className={cn(
            'inline-block rounded-full bg-white shadow-sm',
            'transition-transform duration-200',
            'pointer-events-none',
            sizeStyles.thumb,
            checked ? sizeStyles.translate : 'translate-x-0.5'
          )}
          aria-hidden="true"
        />
      </button>
    );
  }
);

ToggleSwitch.displayName = 'Toggle.Switch';

// ============================================================
// Label
// ============================================================

export interface ToggleLabelProps extends BaseProps, ChildrenProps {
  /** 标签位置 */
  position?: 'start' | 'end';
}

const ToggleLabel = forwardRef<HTMLLabelElement, ToggleLabelProps>(
  (props, ref) => {
    const { children, position = 'end', className, ...rest } = props;
    const { checked, disabled, getLabelProps } = useToggleContext();

    const labelProps = getLabelProps();

    return (
      <label
        ref={ref}
        {...labelProps}
        className={cn(
          'text-sm font-medium text-text-primary select-none',
          disabled && 'cursor-not-allowed',
          position === 'start' && 'order-first',
          className
        )}
        {...rest}
      >
        {children}
      </label>
    );
  }
);

ToggleLabel.displayName = 'Toggle.Label';

// ============================================================
// 复合组件导出
// ============================================================

export const Toggle = {
  Root: ToggleRoot,
  Switch: ToggleSwitch,
  Label: ToggleLabel,
};

export type {
  ToggleRootProps,
  ToggleSwitchProps,
  ToggleLabelProps,
};
