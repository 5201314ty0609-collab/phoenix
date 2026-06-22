/**
 * PHOENIX Framer Motion 配置
 * 基于动画设计最佳实践
 * 版本: v1.0.0
 * 更新: 2026-06-23
 */

import { Variants, Transition, Variant } from 'framer-motion';

// ═══════════════════════════════════════════════════════
// 缓动预设 (Easing Presets)
// ═══════════════════════════════════════════════════════

export const easings = {
  // 标准缓动
  standard: [0.4, 0, 0.2, 1],
  standardSmooth: [0.25, 0.1, 0.25, 1],

  // 进入缓动
  enter: [0, 0, 0.2, 1],
  enterSmooth: [0.16, 1, 0.3, 1],
  enterExpo: [0.16, 1, 0.3, 1],

  // 退出缓动
  exit: [0.4, 0, 1, 1],
  exitSmooth: [0.7, 0, 0.84, 0],
  exitExpo: [0.87, 0, 0.13, 1],

  // 弹性缓动
  bounce: [0.34, 1.56, 0.64, 1],
  spring: [0.22, 1.6, 0.36, 1],
  springGentle: [0.25, 1, 0.5, 1],
  springBouncy: [0.34, 1.8, 0.64, 1],

  // 线性
  linear: [0, 0, 1, 1],

  // 衰减
  decelerate: [0, 0, 0, 1],
  accelerate: [1, 0, 1, 1],
} as const;

// ═══════════════════════════════════════════════════════
// 时长预设 (Duration Presets)
// ═══════════════════════════════════════════════════════

export const durations = {
  instant: 0.1,
  fast: 0.15,
  normal: 0.25,
  moderate: 0.35,
  slow: 0.5,
  page: 0.7,
  dramatic: 1,
} as const;

// ═══════════════════════════════════════════════════════
// 弹簧配置 (Spring Configurations)
// ═══════════════════════════════════════════════════════

export const springs = {
  // 轻柔弹簧
  gentle: {
    type: 'spring',
    stiffness: 200,
    damping: 20,
    mass: 1,
  },

  // 标准弹簧
  default: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
    mass: 1,
  },

  // 活泼弹簧
  bouncy: {
    type: 'spring',
    stiffness: 400,
    damping: 25,
    mass: 1,
  },

  // 紧凑弹簧
  stiff: {
    type: 'spring',
    stiffness: 500,
    damping: 40,
    mass: 1,
  },

  // 慢速弹簧
  slow: {
    type: 'spring',
    stiffness: 100,
    damping: 15,
    mass: 1,
  },

  // 弹跳弹簧
  bounce: {
    type: 'spring',
    stiffness: 300,
    damping: 10,
    mass: 1,
  },
} as const;

// ═══════════════════════════════════════════════════════
// 基础变体 (Base Variants)
// ═══════════════════════════════════════════════════════

/** 淡入淡出 */
export const fadeVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: durations.normal, ease: easings.enter },
  },
  exit: {
    opacity: 0,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 从下方滑入 */
export const slideUpVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 从上方滑入 */
export const slideDownVariants: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    y: 10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 从左侧滑入 */
export const slideLeftVariants: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    x: -10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 从右侧滑入 */
export const slideRightVariants: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    x: 10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 缩放进入 */
export const scaleVariants: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: durations.normal, ease: easings.bounce },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 弹性缩放 */
export const scaleSpringVariants: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springs.bouncy,
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 淡入 + 滑动 */
export const fadeSlideUpVariants: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: durations.moderate, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: durations.normal, ease: easings.exit },
  },
};

// ═══════════════════════════════════════════════════════
// 容器变体 (Container Variants)
// 用于子元素序列动画
// ═══════════════════════════════════════════════════════

/** 交错容器 */
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

/** 快速交错容器 */
export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04,
      delayChildren: 0.05,
    },
  },
};

/** 慢速交错容器 */
export const staggerContainerSlow: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.2,
    },
  },
};

/** 交错子项 */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

// ═══════════════════════════════════════════════════════
// 组件变体 (Component Variants)
// 特定 UI 组件的动画
// ═══════════════════════════════════════════════════════

/** 下拉菜单 */
export const dropdownVariants: Variants = {
  hidden: {
    opacity: 0,
    y: -8,
    scale: 0.96,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    y: -8,
    scale: 0.96,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

/** 模态框 */
export const modalVariants: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    y: 10,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: durations.moderate, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 10,
    transition: { duration: durations.normal, ease: easings.exit },
  },
};

/** 模态框遮罩 */
export const modalOverlayVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: durations.normal },
  },
  exit: {
    opacity: 0,
    transition: { duration: durations.fast },
  },
};

/** Toast 通知 */
export const toastVariants: Variants = {
  hidden: {
    opacity: 0,
    x: 100,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: { duration: durations.moderate, ease: easings.bounce },
  },
  exit: {
    opacity: 0,
    x: 100,
    scale: 0.95,
    transition: { duration: durations.normal, ease: easings.exit },
  },
};

/** Tooltip */
export const tooltipVariants: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.9,
    y: 4,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: durations.fast, ease: easings.enter },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: 4,
    transition: { duration: durations.instant, ease: easings.exit },
  },
};

/** Accordion 内容 */
export const accordionVariants: Variants = {
  collapsed: {
    height: 0,
    opacity: 0,
    transition: {
      height: { duration: durations.normal, ease: easings.standard },
      opacity: { duration: durations.fast },
    },
  },
  expanded: {
    height: 'auto',
    opacity: 1,
    transition: {
      height: { duration: durations.moderate, ease: easings.standard },
      opacity: { duration: durations.normal, delay: 0.1 },
    },
  },
};

/** 侧边栏 */
export const sidebarVariants: Variants = {
  hidden: {
    x: '-100%',
    opacity: 0,
  },
  visible: {
    x: 0,
    opacity: 1,
    transition: { duration: durations.moderate, ease: easings.enterSmooth },
  },
  exit: {
    x: '-100%',
    opacity: 0,
    transition: { duration: durations.normal, ease: easings.exitSmooth },
  },
};

/** 标签页内容 */
export const tabContentVariants: Variants = {
  hidden: {
    opacity: 0,
    x: 10,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: durations.normal, ease: easings.enterSmooth },
  },
  exit: {
    opacity: 0,
    x: -10,
    transition: { duration: durations.fast, ease: easings.exit },
  },
};

// ═══════════════════════════════════════════════════════
// 交互变体 (Interaction Variants)
// 用于悬停、点击等交互状态
// ═══════════════════════════════════════════════════════

/** 按钮悬停 */
export const buttonHover = {
  y: -2,
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
  transition: { duration: durations.fast },
};

/** 按钮点击 */
export const buttonTap = {
  y: 0,
  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  scale: 0.98,
};

/** 卡片悬停 */
export const cardHover = {
  y: -4,
  boxShadow: '0 12px 24px rgba(0, 0, 0, 0.15)',
  transition: { duration: durations.normal, ease: easings.standard },
};

/** 图标旋转 */
export const iconSpin = {
  rotate: 90,
  transition: { duration: durations.normal, ease: easings.standard },
};

/** 脉冲效果 */
export const pulse = {
  scale: [1, 1.05, 1],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

/** 摇晃效果 */
export const shake = {
  x: [0, -4, 4, -4, 4, 0],
  transition: { duration: 0.5 },
};

// ═══════════════════════════════════════════════════════
// 动画钩子 (Animation Hooks)
// 便于使用的预配置动画
// ═══════════════════════════════════════════════════════

/**
 * 创建序列动画配置
 */
export function createSequenceAnimation(
  items: number,
  staggerDelay: number = 0.08
): { container: Variants; item: Variants } {
  return {
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: staggerDelay,
          delayChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, y: 20 },
      visible: {
        opacity: 1,
        y: 0,
        transition: { duration: durations.normal, ease: easings.enterSmooth },
      },
    },
  };
}

/**
 * 创建循环动画配置
 */
export function createLoopAnimation(
  keyframes: number[],
  duration: number = 2
): { animate: object; transition: Transition } {
  return {
    animate: {
      scale: keyframes,
    },
    transition: {
      duration,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  };
}

/**
 * 创建视口动画配置
 */
export function createViewportAnimation(
  variants: Variants,
  threshold: number = 0.2
) {
  return {
    initial: 'hidden',
    whileInView: 'visible',
    viewport: { once: true, amount: threshold },
    variants,
  };
}

// ═══════════════════════════════════════════════════════
// 导出所有预设 (Export All Presets)
// ═══════════════════════════════════════════════════════

export const animationPresets = {
  // 基础
  fadeIn: fadeVariants,
  slideUp: slideUpVariants,
  slideDown: slideDownVariants,
  slideLeft: slideLeftVariants,
  slideRight: slideRightVariants,
  scale: scaleVariants,
  scaleSpring: scaleSpringVariants,
  fadeSlideUp: fadeSlideUpVariants,

  // 容器
  stagger: staggerContainer,
  staggerFast: staggerContainerFast,
  staggerSlow: staggerContainerSlow,
  staggerItem,

  // 组件
  dropdown: dropdownVariants,
  modal: modalVariants,
  modalOverlay: modalOverlayVariants,
  toast: toastVariants,
  tooltip: tooltipVariants,
  accordion: accordionVariants,
  sidebar: sidebarVariants,
  tabContent: tabContentVariants,

  // 交互
  buttonHover,
  buttonTap,
  cardHover,
  iconSpin,
  pulse,
  shake,
} as const;

export default animationPresets;
