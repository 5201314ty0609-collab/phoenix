/**
 * PHOENIX AIOS — useControllableState Hook
 *
 * 实现受控/非受控模式的统一状态管理
 * 这是所有交互组件的基础 Hook
 *
 * 参考: Radix UI 的 useControllableState 实现
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface UseControllableStateProps<T> {
  /** 受控值 */
  prop?: T;
  /** 非受控默认值 */
  defaultProp?: T;
  /** 值变化回调 */
  onChange?: (value: T) => void;
}

type SetStateFn<T> = (prevState: T) => T;

/**
 * 统一的受控/非受控状态管理
 *
 * @example
 * // 非受控模式
 * const [value, setValue] = useControllableState({
 *   defaultProp: 'initial',
 * });
 *
 * // 受控模式
 * const [value, setValue] = useControllableState({
 *   prop: props.value,
 *   onChange: props.onChange,
 * });
 */
export function useControllableState<T>({
  prop,
  defaultProp,
  onChange,
}: UseControllableStateProps<T>): [T, (value: T | SetStateFn<T>) => void] {
  const [internalValue, setInternalValue] = useState<T | undefined>(defaultProp);
  const isControlled = prop !== undefined;
  const value = isControlled ? prop : internalValue;
  const onChangeRef = useRef(onChange);

  // 保持 onChange 引用最新
  useEffect(() => {
    onChangeRef.current = onChange;
  });

  // 开发环境警告
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      if (isControlled && defaultProp !== undefined) {
        console.warn(
          'PHOENIX: A component contains both controlled and uncontrolled ' +
          'aspects. This is not recommended.'
        );
      }
    }
  }, [isControlled, defaultProp]);

  const setValue = useCallback(
    (nextValue: T | SetStateFn<T>) => {
      const resolvedValue =
        typeof nextValue === 'function'
          ? (nextValue as SetStateFn<T>)(value as T)
          : nextValue;

      if (!isControlled) {
        setInternalValue(resolvedValue);
      }

      onChangeRef.current?.(resolvedValue);
    },
    [isControlled, value]
  );

  return [value as T, setValue];
}

/**
 * 布尔状态的简化版本
 *
 * @example
 * const [isOpen, setIsOpen] = useControllableBoolean({
 *   prop: props.isOpen,
 *   defaultProp: false,
 *   onChange: props.onOpenChange,
 * });
 */
export function useControllableBoolean({
  prop,
  defaultProp = false,
  onChange,
}: {
  prop?: boolean;
  defaultProp?: boolean;
  onChange?: (value: boolean) => void;
}): [boolean, (value: boolean | ((prev: boolean) => boolean)) => void] {
  return useControllableState({
    prop,
    defaultProp,
    onChange,
  });
}
