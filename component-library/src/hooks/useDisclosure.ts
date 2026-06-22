/**
 * PHOENIX AIOS — useDisclosure Hook
 *
 * 无头 Disclosure/Dialog 逻辑
 * 管理打开/关闭状态、动画、焦点、Escape 键
 *
 * @example
 * const { isOpen, open, close, toggle, getTriggerProps, getContentProps } = useDisclosure();
 */

import { useCallback, useEffect, useRef } from 'react';
import { useControllableBoolean } from './useControllableState';

export interface UseDisclosureOptions {
  /** 受控打开状态 */
  isOpen?: boolean;
  /** 默认打开状态（非受控） */
  defaultOpen?: boolean;
  /** 状态变化回调 */
  onOpenChange?: (isOpen: boolean) => void;
  /** 打开后的回调 */
  onOpen?: () => void;
  /** 关闭后的回调 */
  onClose?: () => void;
  /** 是否点击外部关闭 */
  closeOnOutsideClick?: boolean;
  /** 是否按 Escape 关闭 */
  closeOnEscape?: boolean;
  /** 关闭前的拦截器（返回 false 阻止关闭） */
  onBeforeClose?: () => boolean | void;
  /** 初始焦点元素 */
  initialFocusRef?: React.RefObject<HTMLElement>;
  /** 关闭后焦点恢复到的元素 */
  finalFocusRef?: React.RefObject<HTMLElement>;
}

export interface UseDisclosureReturn {
  /** 当前打开状态 */
  isOpen: boolean;
  /** 打开 */
  open: () => void;
  /** 关闭 */
  close: () => void;
  /** 切换 */
  toggle: () => void;
  /** 获取触发器元素的 props */
  getTriggerProps: () => Record<string, unknown>;
  /** 获取内容区域的 props */
  getContentProps: () => Record<string, unknown>;
  /** 获取关闭按钮的 props */
  getCloseProps: () => Record<string, unknown>;
  /** 获取遮罩层的 props */
  getOverlayProps: () => Record<string, unknown>;
}

/**
 * Disclosure 逻辑 Hook
 *
 * 提供：
 * - 受控/非受控状态管理
 * - 打开/关闭动画状态
 * - 焦点管理（初始焦点、焦点恢复）
 * - 键盘交互（Escape 关闭）
 * - 点击外部关闭
 * - ARIA 属性（dialog role, aria-modal）
 */
export function useDisclosure(options: UseDisclosureOptions = {}): UseDisclosureReturn {
  const {
    closeOnOutsideClick = true,
    closeOnEscape = true,
    onOpen,
    onClose,
    onBeforeClose,
    initialFocusRef,
    finalFocusRef,
  } = options;

  const [isOpen, setIsOpen] = useControllableBoolean({
    prop: options.isOpen,
    defaultProp: options.defaultOpen,
    onChange: options.onOpenChange,
  });

  const previousFocusRef = useRef<HTMLElement | null>(null);
  const contentRef = useRef<HTMLElement>(null);

  const open = useCallback(() => {
    setIsOpen(true);
    onOpen?.();
  }, [setIsOpen, onOpen]);

  const close = useCallback(() => {
    if (onBeforeClose?.() === false) return;
    setIsOpen(false);
    onClose?.();
  }, [setIsOpen, onClose, onBeforeClose]);

  const toggle = useCallback(() => {
    if (isOpen) {
      close();
    } else {
      open();
    }
  }, [isOpen, open, close]);

  // 焦点管理
  useEffect(() => {
    if (isOpen) {
      // 保存当前焦点
      previousFocusRef.current = document.activeElement as HTMLElement;

      // 设置初始焦点
      const timer = setTimeout(() => {
        if (initialFocusRef?.current) {
          initialFocusRef.current.focus();
        } else if (contentRef.current) {
          const firstFocusable = contentRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          firstFocusable?.focus();
        }
      }, 0);

      return () => clearTimeout(timer);
    } else {
      // 恢复焦点
      const element = finalFocusRef?.current || previousFocusRef.current;
      element?.focus();
    }
  }, [isOpen, initialFocusRef, finalFocusRef]);

  // Escape 键关闭
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        close();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeOnEscape, close]);

  // 点击外部关闭
  useEffect(() => {
    if (!isOpen || !closeOnOutsideClick) return;

    const handleOutsideClick = (event: MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(event.target as Node)) {
        close();
      }
    };

    // 延迟添加，避免立即触发
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleOutsideClick);
    }, 0);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isOpen, closeOnOutsideClick, close]);

  // 锁定滚动
  useEffect(() => {
    if (!isOpen) return;

    const originalStyle = window.getComputedStyle(document.body).overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalStyle;
    };
  }, [isOpen]);

  const getTriggerProps = useCallback(
    () => ({
      'aria-expanded': isOpen,
      'aria-haspopup': 'dialog' as const,
      onClick: toggle,
      'data-state': isOpen ? 'open' : 'closed',
    }),
    [isOpen, toggle]
  );

  const getContentProps = useCallback(
    () => ({
      role: 'dialog',
      'aria-modal': true,
      ref: contentRef,
      'data-state': isOpen ? 'open' : 'closed',
      tabIndex: -1,
    }),
    [isOpen]
  );

  const getCloseProps = useCallback(
    () => ({
      'aria-label': 'Close',
      onClick: close,
    }),
    [close]
  );

  const getOverlayProps = useCallback(
    () => ({
      'aria-hidden': true,
      onClick: closeOnOutsideClick ? close : undefined,
      'data-state': isOpen ? 'open' : 'closed',
    }),
    [isOpen, closeOnOutsideClick, close]
  );

  return {
    isOpen,
    open,
    close,
    toggle,
    getTriggerProps,
    getContentProps,
    getCloseProps,
    getOverlayProps,
  };
}
