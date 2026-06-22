/**
 * PHOENIX AIOS — Dialog 组件
 *
 * 有机体组件：对话框/模态框
 *
 * 使用复合组件模式，提供完整的无障碍支持
 *
 * @example
 * <Dialog.Root>
 *   <Dialog.Trigger asChild>
 *     <Button>打开对话框</Button>
 *   </Dialog.Trigger>
 *   <Dialog.Portal>
 *     <Dialog.Overlay />
 *     <Dialog.Content>
 *       <Dialog.Title>标题</Dialog.Title>
 *       <Dialog.Description>描述</Dialog.Description>
 *       <Dialog.Close asChild>
 *         <Button>关闭</Button>
 *       </Dialog.Close>
 *     </Dialog.Content>
 *   </Dialog.Portal>
 * </Dialog.Root>
 */

import React, {
  createContext,
  useContext,
  forwardRef,
  useCallback,
  useEffect,
  useRef,
  useMemo,
} from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/cn';
import { mergeRefs } from '../../utils/mergeRefs';
import { useDisclosure } from '../../hooks/useDisclosure';
import { useFocusTrap } from '../../hooks/useFocusTrap';
import type { BaseProps, AsChildProps, ChildrenProps, OpenableProps } from '../../types/common';

// ============================================================
// Context
// ============================================================

interface DialogContextValue {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  triggerRef: React.RefObject<HTMLElement>;
  contentRef: React.RefObject<HTMLElement>;
}

const DialogContext = createContext<DialogContextValue | null>(null);

function useDialogContext() {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error('Dialog compound components must be used within Dialog.Root');
  }
  return context;
}

// ============================================================
// Root
// ============================================================

export interface DialogRootProps extends BaseProps, ChildrenProps, OpenableProps {
  /** 是否点击外部关闭 */
  closeOnOutsideClick?: boolean;
  /** 是否按 Escape 关闭 */
  closeOnEscape?: boolean;
}

function DialogRoot(props: DialogRootProps) {
  const {
    children,
    isOpen: controlledIsOpen,
    onOpenChange,
    defaultOpen = false,
    closeOnOutsideClick = true,
    closeOnEscape = true,
    className,
    ...rest
  } = props;

  const triggerRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLElement>(null);

  const { isOpen, open, close, toggle } = useDisclosure({
    isOpen: controlledIsOpen,
    onOpenChange,
    defaultOpen,
    closeOnOutsideClick,
    closeOnEscape,
    finalFocusRef: triggerRef,
  });

  const contextValue = useMemo(
    () => ({
      isOpen,
      open,
      close,
      toggle,
      triggerRef,
      contentRef,
    }),
    [isOpen, open, close, toggle]
  );

  return (
    <DialogContext.Provider value={contextValue}>
      {children}
    </DialogContext.Provider>
  );
}

DialogRoot.displayName = 'Dialog.Root';

// ============================================================
// Trigger
// ============================================================

export interface DialogTriggerProps extends BaseProps, AsChildProps, ChildrenProps {
  onClick?: (event: React.MouseEvent) => void;
}

const DialogTrigger = forwardRef<HTMLElement, DialogTriggerProps>(
  (props, ref) => {
    const { children, asChild, onClick, className, ...rest } = props;
    const { open, triggerRef, isOpen } = useDialogContext();

    const handleClick = useCallback(
      (event: React.MouseEvent) => {
        open();
        onClick?.(event);
      },
      [open, onClick]
    );

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        ...rest,
        ref: mergeRefs(ref, triggerRef as any),
        onClick: handleClick,
        'aria-haspopup': 'dialog',
        'aria-expanded': isOpen,
        'data-state': isOpen ? 'open' : 'closed',
      });
    }

    return (
      <button
        ref={mergeRefs(ref, triggerRef as any)}
        type="button"
        onClick={handleClick}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        data-state={isOpen ? 'open' : 'closed'}
        className={className}
        {...rest}
      >
        {children}
      </button>
    );
  }
);

DialogTrigger.displayName = 'Dialog.Trigger';

// ============================================================
// Portal
// ============================================================

export interface DialogPortalProps extends ChildrenProps {
  /** Portal 容器 */
  container?: HTMLElement;
}

function DialogPortal(props: DialogPortalProps) {
  const { children, container } = props;
  const { isOpen } = useDialogContext();

  if (!isOpen) return null;

  const portalContainer = container || document.body;
  return createPortal(children, portalContainer);
}

DialogPortal.displayName = 'Dialog.Portal';

// ============================================================
// Overlay
// ============================================================

export interface DialogOverlayProps extends BaseProps {
  onClick?: (event: React.MouseEvent) => void;
}

const DialogOverlay = forwardRef<HTMLDivElement, DialogOverlayProps>(
  (props, ref) => {
    const { className, onClick, ...rest } = props;
    const { isOpen, close } = useDialogContext();

    const handleClick = useCallback(
      (event: React.MouseEvent) => {
        close();
        onClick?.(event);
      },
      [close, onClick]
    );

    if (!isOpen) return null;

    return (
      <div
        ref={ref}
        className={cn(
          'fixed inset-0 z-50',
          'bg-black/50 backdrop-blur-sm',
          'data-[state=open]:animate-in data-[state=open]:fade-in',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out',
          className
        )}
        data-state={isOpen ? 'open' : 'closed'}
        aria-hidden="true"
        onClick={handleClick}
        {...rest}
      />
    );
  }
);

DialogOverlay.displayName = 'Dialog.Overlay';

// ============================================================
// Content
// ============================================================

export interface DialogContentProps extends BaseProps, ChildrenProps {
  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;
  /** 关闭按钮图标 */
  closeIcon?: React.ReactNode;
}

const DialogContent = forwardRef<HTMLDivElement, DialogContentProps>(
  (props, ref) => {
    const {
      children,
      className,
      showCloseButton = true,
      closeIcon,
      ...rest
    } = props;

    const { isOpen, close, contentRef } = useDialogContext();
    const focusTrapRef = useFocusTrap({ enabled: isOpen });

    if (!isOpen) return null;

    return (
      <div
        ref={mergeRefs(ref, contentRef as any, focusTrapRef)}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description"
        className={cn(
          // 定位
          'fixed left-1/2 top-1/2 z-50',
          '-translate-x-1/2 -translate-y-1/2',
          // 样式
          'w-full max-w-lg',
          'bg-bg-base rounded-lg shadow-xl',
          'border border-border-default',
          // 动画
          'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]',
          // 自定义类名
          className
        )}
        data-state={isOpen ? 'open' : 'closed'}
        tabIndex={-1}
        {...rest}
      >
        {children}

        {/* 关闭按钮 */}
        {showCloseButton && (
          <button
            type="button"
            onClick={close}
            className={cn(
              'absolute right-4 top-4',
              'p-1 rounded-md',
              'text-text-tertiary hover:text-text-secondary',
              'hover:bg-gray-100 transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-border-focus'
            )}
            aria-label="Close dialog"
          >
            {closeIcon || (
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
            )}
          </button>
        )}
      </div>
    );
  }
);

DialogContent.displayName = 'Dialog.Content';

// ============================================================
// Title
// ============================================================

export interface DialogTitleProps extends BaseProps, ChildrenProps {}

const DialogTitle = forwardRef<HTMLHeadingElement, DialogTitleProps>(
  (props, ref) => {
    const { children, className, ...rest } = props;

    return (
      <h2
        ref={ref}
        id="dialog-title"
        className={cn(
          'text-lg font-semibold text-text-primary',
          'pr-8', // 为关闭按钮留空间
          className
        )}
        {...rest}
      >
        {children}
      </h2>
    );
  }
);

DialogTitle.displayName = 'Dialog.Title';

// ============================================================
// Description
// ============================================================

export interface DialogDescriptionProps extends BaseProps, ChildrenProps {}

const DialogDescription = forwardRef<HTMLParagraphElement, DialogDescriptionProps>(
  (props, ref) => {
    const { children, className, ...rest } = props;

    return (
      <p
        ref={ref}
        id="dialog-description"
        className={cn(
          'mt-2 text-sm text-text-secondary',
          className
        )}
        {...rest}
      >
        {children}
      </p>
    );
  }
);

DialogDescription.displayName = 'Dialog.Description';

// ============================================================
// Close
// ============================================================

export interface DialogCloseProps extends BaseProps, AsChildProps, ChildrenProps {
  onClick?: (event: React.MouseEvent) => void;
}

const DialogClose = forwardRef<HTMLElement, DialogCloseProps>(
  (props, ref) => {
    const { children, asChild, onClick, className, ...rest } = props;
    const { close } = useDialogContext();

    const handleClick = useCallback(
      (event: React.MouseEvent) => {
        close();
        onClick?.(event);
      },
      [close, onClick]
    );

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        ...rest,
        ref,
        onClick: handleClick,
      });
    }

    return (
      <button
        ref={ref as any}
        type="button"
        onClick={handleClick}
        className={className}
        {...rest}
      >
        {children}
      </button>
    );
  }
);

DialogClose.displayName = 'Dialog.Close';

// ============================================================
// 复合组件导出
// ============================================================

export const Dialog = {
  Root: DialogRoot,
  Trigger: DialogTrigger,
  Portal: DialogPortal,
  Overlay: DialogOverlay,
  Content: DialogContent,
  Title: DialogTitle,
  Description: DialogDescription,
  Close: DialogClose,
};

export type {
  DialogRootProps,
  DialogTriggerProps,
  DialogPortalProps,
  DialogOverlayProps,
  DialogContentProps,
  DialogTitleProps,
  DialogDescriptionProps,
  DialogCloseProps,
};
