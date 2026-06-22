/**
 * PHOENIX AIOS — useFocusTrap Hook
 *
 * 焦点陷阱：将焦点限制在指定容器内
 * 用于 Modal、Dialog、Popover 等弹出层
 *
 * @example
 * const trapRef = useFocusTrap(isOpen);
 * <div ref={trapRef}>...</div>
 */

import { useEffect, useRef, useCallback } from 'react';

const FOCUSABLE_SELECTORS = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable]',
  'audio[controls]',
  'video[controls]',
  'details > summary',
].join(', ');

export interface UseFocusTrapOptions {
  /** 是否激活焦点陷阱 */
  enabled?: boolean;
  /** 初始焦点元素的选择器或 ref */
  initialFocus?: string | React.RefObject<HTMLElement>;
  /** 恢复焦点的元素 */
  restoreFocus?: boolean;
  /** 是否允许 Tab 循环 */
  loop?: boolean;
}

/**
 * 获取容器内所有可聚焦元素
 */
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const elements = Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS)
  );

  return elements.filter((el) => {
    // 过滤不可见元素
    if (el.offsetParent === null) return false;
    if (el.getAttribute('aria-hidden') === 'true') return false;
    return true;
  });
}

/**
 * 焦点陷阱 Hook
 */
export function useFocusTrap<T extends HTMLElement = HTMLElement>(
  options: UseFocusTrapOptions = {}
): React.RefObject<T> {
  const {
    enabled = true,
    initialFocus,
    restoreFocus = true,
    loop = true,
  } = options;

  const containerRef = useRef<T>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // 设置初始焦点
  const setInitialFocus = useCallback(() => {
    if (!containerRef.current) return;

    let target: HTMLElement | null = null;

    if (initialFocus) {
      if (typeof initialFocus === 'string') {
        target = containerRef.current.querySelector(initialFocus);
      } else {
        target = initialFocus.current;
      }
    }

    // 默认聚焦第一个可聚焦元素
    if (!target) {
      const focusable = getFocusableElements(containerRef.current);
      target = focusable[0] || containerRef.current;
    }

    target?.focus();
  }, [initialFocus]);

  // 处理 Tab 键循环
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key !== 'Tab' || !containerRef.current) return;

      const focusable = getFocusableElements(containerRef.current);
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }

      const firstFocusable = focusable[0];
      const lastFocusable = focusable[focusable.length - 1];

      if (event.shiftKey) {
        // Shift+Tab: 从第一个跳到最后一个
        if (document.activeElement === firstFocusable) {
          event.preventDefault();
          if (loop) {
            lastFocusable.focus();
          }
        }
      } else {
        // Tab: 从最后一个跳到第一个
        if (document.activeElement === lastFocusable) {
          event.preventDefault();
          if (loop) {
            firstFocusable.focus();
          }
        }
      }
    },
    [loop]
  );

  // 监听焦点逃逸
  const handleFocusIn = useCallback(
    (event: FocusEvent) => {
      if (!containerRef.current) return;

      // 如果焦点移到容器外，拉回来
      if (!containerRef.current.contains(event.target as Node)) {
        const focusable = getFocusableElements(containerRef.current);
        if (focusable.length > 0) {
          focusable[0].focus();
        }
      }
    },
    []
  );

  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    // 保存当前焦点
    previousFocusRef.current = document.activeElement as HTMLElement;

    // 设置初始焦点
    setInitialFocus();

    // 绑定事件
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('focusin', handleFocusIn);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('focusin', handleFocusIn);

      // 恢复焦点
      if (restoreFocus) {
        previousFocusRef.current?.focus();
      }
    };
  }, [enabled, setInitialFocus, handleKeyDown, handleFocusIn, restoreFocus]);

  return containerRef;
}
