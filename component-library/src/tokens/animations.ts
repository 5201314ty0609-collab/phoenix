/**
 * PHOENIX AIOS — 动画令牌
 *
 * 动画持续时间、缓动函数、预设动画
 */

// ============================================================
// 持续时间
// ============================================================

export const duration = {
  /** 75ms - 即时反馈 */
  instant: '75ms',
  /** 150ms - 微交互 */
  fast: '150ms',
  /** 200ms - 快速过渡 */
  faster: '200ms',
  /** 300ms - 标准过渡 */
  normal: '300ms',
  /** 400ms - 慢速过渡 */
  slower: '400ms',
  /** 500ms - 复杂动画 */
  slow: '500ms',
  /** 700ms - 大型动画 */
  slower: '700ms',
  /** 1000ms - 超慢动画 */
  slowest: '1000ms',
} as const;

// ============================================================
// 缓动函数
// ============================================================

export const easing = {
  /** 线性 */
  linear: 'linear',
  /** 标准进入 */
  'ease-in': 'cubic-bezier(0.4, 0, 1, 1)',
  /** 标准退出 */
  'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
  /** 标准过渡 */
  'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
  /** 快速进入（强调） */
  'ease-in-expo': 'cubic-bezier(0.95, 0.05, 0.795, 0.035)',
  /** 快速退出（强调） */
  'ease-out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
  /** 弹性效果 */
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  /** 回弹效果 */
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  /** 平滑进入 */
  smooth: 'cubic-bezier(0.16, 1, 0.3, 1)',
} as const;

// ============================================================
// 预设关键帧
// ============================================================

export const keyframes = {
  /** 淡入 */
  fadeIn: {
    from: { opacity: '0' },
    to: { opacity: '1' },
  },
  /** 淡出 */
  fadeOut: {
    from: { opacity: '1' },
    to: { opacity: '0' },
  },
  /** 从下方滑入 */
  slideUp: {
    from: { transform: 'translateY(10px)', opacity: '0' },
    to: { transform: 'translateY(0)', opacity: '1' },
  },
  /** 从上方滑入 */
  slideDown: {
    from: { transform: 'translateY(-10px)', opacity: '0' },
    to: { transform: 'translateY(0)', opacity: '1' },
  },
  /** 从左侧滑入 */
  slideLeft: {
    from: { transform: 'translateX(10px)', opacity: '0' },
    to: { transform: 'translateX(0)', opacity: '1' },
  },
  /** 从右侧滑入 */
  slideRight: {
    from: { transform: 'translateX(-10px)', opacity: '0' },
    to: { transform: 'translateX(0)', opacity: '1' },
  },
  /** 缩放进入 */
  scaleIn: {
    from: { transform: 'scale(0.95)', opacity: '0' },
    to: { transform: 'scale(1)', opacity: '1' },
  },
  /** 缩放退出 */
  scaleOut: {
    from: { transform: 'scale(1)', opacity: '1' },
    to: { transform: 'scale(0.95)', opacity: '0' },
  },
  /** 旋转 */
  spin: {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(360deg)' },
  },
  /** 脉冲 */
  pulse: {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.5' },
  },
  /** 弹跳 */
  bounce: {
    '0%, 100%': { transform: 'translateY(-25%)', animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)' },
    '50%': { transform: 'translateY(0)', animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)' },
  },
  /** 摇晃 */
  shake: {
    '0%, 100%': { transform: 'translateX(0)' },
    '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
    '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
  },
} as const;

// ============================================================
// 动画预设（组合令牌）
// ============================================================

export const animationPresets = {
  /** 淡入 */
  'fade-in': {
    animation: `fadeIn ${duration.normal} ${easing['ease-out']} forwards`,
  },
  /** 淡出 */
  'fade-out': {
    animation: `fadeOut ${duration.fast} ${easing['ease-in']} forwards`,
  },
  /** 从下方进入 */
  'enter-up': {
    animation: `slideUp ${duration.normal} ${easing.smooth} forwards`,
  },
  /** 从上方进入 */
  'enter-down': {
    animation: `slideDown ${duration.normal} ${easing.smooth} forwards`,
  },
  /** 缩放进入 */
  'enter-scale': {
    animation: `scaleIn ${duration.normal} ${easing.spring} forwards`,
  },
  /** 旋转加载 */
  'spin': {
    animation: `spin ${duration.slow} ${easing.linear} infinite`,
  },
  /** 脉冲加载 */
  'pulse': {
    animation: `pulse ${duration.slower} ${easing['ease-in-out']} infinite`,
  },
  /** 错误摇晃 */
  'error-shake': {
    animation: `shake ${duration.normal} ${easing.smooth}`,
  },
} as const;

// ============================================================
// 减少动画偏好
// ============================================================

export const reducedMotion = {
  /** 替代动画（仅淡入淡出） */
  'fade-in': {
    animation: `fadeIn ${duration.instant} ${easing.linear} forwards`,
  },
  'fade-out': {
    animation: `fadeOut ${duration.instant} ${easing.linear} forwards`,
  },
  /** 禁用动画 */
  none: {
    animation: 'none',
  },
} as const;
