/**
 * PHOENIX AIOS — Ref 合并工具
 *
 * 合并多个 ref（callback ref 和 ref object）
 * 用于组件需要同时暴露 ref 给外部和内部使用
 */

import type { Ref, RefCallback } from 'react';

type PossibleRef<T> = Ref<T> | undefined | null;

/**
 * 合并多个 ref
 *
 * @example
 * const MyComponent = forwardRef((props, ref) => {
 *   const internalRef = useRef(null);
 *   const mergedRef = useMergedRefs(internalRef, ref);
 *
 *   return <div ref={mergedRef}>...</div>;
 * });
 */
export function mergeRefs<T>(...refs: PossibleRef<T>[]): RefCallback<T> {
  return (value) => {
    for (const ref of refs) {
      if (typeof ref === 'function') {
        ref(value);
      } else if (ref != null) {
        (ref as React.MutableRefObject<T | null>).current = value;
      }
    }
  };
}

/**
 * React Hook 版本的 ref 合并
 * 自动处理更新
 */
export function useMergedRefs<T>(...refs: PossibleRef<T>[]): RefCallback<T> {
  // 使用 useCallback 确保引用稳定
  return mergeRefs(...refs);
}

/**
 * 检查 ref 是否已设置
 */
export function isRefSet<T>(ref: Ref<T>): boolean {
  if (typeof ref === 'function') return false;
  return ref?.current != null;
}

/**
 * 安全地获取 ref 的值
 */
export function getRefValue<T>(ref: Ref<T> | undefined | null): T | null {
  if (!ref) return null;
  if (typeof ref === 'function') return null;
  return ref.current ?? null;
}
