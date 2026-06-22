/**
 * PHOENIX AIOS — 颜色令牌
 *
 * 使用 oklch 色彩空间，感知均匀
 * Catppuccin Mocha 启发的配色方案
 */

// ============================================================
// 基础色板
// ============================================================

export const baseColors = {
  // 灰度
  white: 'oklch(100% 0 0)',
  black: 'oklch(0% 0 0)',

  gray: {
    50: 'oklch(98% 0.001 286)',
    100: 'oklch(96% 0.001 286)',
    200: 'oklch(92% 0.002 286)',
    300: 'oklch(87% 0.003 286)',
    400: 'oklch(71% 0.005 286)',
    500: 'oklch(55% 0.005 286)',
    600: 'oklch(45% 0.005 286)',
    700: 'oklch(37% 0.005 286)',
    800: 'oklch(27% 0.005 286)',
    900: 'oklch(20% 0.005 286)',
    950: 'oklch(14% 0.005 286)',
  },

  // Catppuccin Mocha 启发的色彩
  rosewater: 'oklch(90% 0.05 30)',
  flamingo: 'oklch(85% 0.08 20)',
  pink: 'oklch(80% 0.12 340)',
  mauve: 'oklch(70% 0.15 300)',
  red: 'oklch(65% 0.2 20)',
  maroon: 'oklch(60% 0.15 10)',
  peach: 'oklch(75% 0.15 50)',
  yellow: 'oklch(80% 0.15 85)',
  green: 'oklch(70% 0.18 150)',
  teal: 'oklch(70% 0.12 180)',
  sky: 'oklch(75% 0.12 230)',
  sapphire: 'oklch(70% 0.15 250)',
  blue: 'oklch(65% 0.2 265)',
  lavender: 'oklch(80% 0.1 280)',
} as const;

// ============================================================
// 语义颜色（亮色模式）
// ============================================================

export const lightColors = {
  // 基础表面
  bg: {
    base: 'oklch(100% 0 0)',
    mantle: 'oklch(98% 0.001 286)',
    crust: 'oklch(96% 0.001 286)',
    elevated: 'oklch(100% 0 0)',
    overlay: 'oklch(0% 0 0 / 0.5)',
  },

  // 文本
  text: {
    primary: 'oklch(20% 0.005 286)',
    secondary: 'oklch(45% 0.005 286)',
    tertiary: 'oklch(55% 0.005 286)',
    disabled: 'oklch(71% 0.005 286)',
    inverse: 'oklch(100% 0 0)',
    link: 'oklch(55% 0.15 265)',
    'link-hover': 'oklch(45% 0.18 265)',
  },

  // 交互状态
  interactive: {
    primary: 'oklch(55% 0.2 265)',
    'primary-hover': 'oklch(50% 0.22 265)',
    'primary-active': 'oklch(45% 0.2 265)',
    secondary: 'oklch(92% 0.002 286)',
    'secondary-hover': 'oklch(87% 0.003 286)',
    'secondary-active': 'oklch(82% 0.004 286)',
    ghost: 'transparent',
    'ghost-hover': 'oklch(96% 0.001 286)',
    'ghost-active': 'oklch(92% 0.002 286)',
    danger: 'oklch(60% 0.2 20)',
    'danger-hover': 'oklch(55% 0.22 20)',
    'danger-active': 'oklch(50% 0.2 20)',
  },

  // 边框
  border: {
    default: 'oklch(90% 0.002 286)',
    hover: 'oklch(80% 0.003 286)',
    focus: 'oklch(55% 0.2 265)',
    danger: 'oklch(60% 0.2 20)',
    success: 'oklch(65% 0.18 150)',
  },

  // 状态颜色
  status: {
    success: 'oklch(65% 0.18 150)',
    'success-bg': 'oklch(95% 0.05 150)',
    warning: 'oklch(75% 0.15 85)',
    'warning-bg': 'oklch(95% 0.05 85)',
    danger: 'oklch(60% 0.2 20)',
    'danger-bg': 'oklch(95% 0.05 20)',
    info: 'oklch(70% 0.12 230)',
    'info-bg': 'oklch(95% 0.05 230)',
  },
} as const;

// ============================================================
// 语义颜色（暗色模式）
// ============================================================

export const darkColors = {
  // 基础表面
  bg: {
    base: 'oklch(18% 0.005 286)',
    mantle: 'oklch(16% 0.005 286)',
    crust: 'oklch(14% 0.005 286)',
    elevated: 'oklch(22% 0.005 286)',
    overlay: 'oklch(0% 0 0 / 0.7)',
  },

  // 文本
  text: {
    primary: 'oklch(90% 0.002 286)',
    secondary: 'oklch(71% 0.005 286)',
    tertiary: 'oklch(55% 0.005 286)',
    disabled: 'oklch(45% 0.005 286)',
    inverse: 'oklch(20% 0.005 286)',
    link: 'oklch(75% 0.12 265)',
    'link-hover': 'oklch(80% 0.1 265)',
  },

  // 交互状态
  interactive: {
    primary: 'oklch(70% 0.15 265)',
    'primary-hover': 'oklch(75% 0.12 265)',
    'primary-active': 'oklch(65% 0.18 265)',
    secondary: 'oklch(27% 0.005 286)',
    'secondary-hover': 'oklch(32% 0.005 286)',
    'secondary-active': 'oklch(37% 0.005 286)',
    ghost: 'transparent',
    'ghost-hover': 'oklch(27% 0.005 286)',
    'ghost-active': 'oklch(32% 0.005 286)',
    danger: 'oklch(70% 0.15 20)',
    'danger-hover': 'oklch(75% 0.12 20)',
    'danger-active': 'oklch(65% 0.18 20)',
  },

  // 边框
  border: {
    default: 'oklch(27% 0.005 286)',
    hover: 'oklch(37% 0.005 286)',
    focus: 'oklch(70% 0.15 265)',
    danger: 'oklch(70% 0.15 20)',
    success: 'oklch(70% 0.18 150)',
  },

  // 状态颜色
  status: {
    success: 'oklch(70% 0.18 150)',
    'success-bg': 'oklch(25% 0.05 150)',
    warning: 'oklch(80% 0.12 85)',
    'warning-bg': 'oklch(25% 0.05 85)',
    danger: 'oklch(70% 0.15 20)',
    'danger-bg': 'oklch(25% 0.05 20)',
    info: 'oklch(75% 0.1 230)',
    'info-bg': 'oklch(25% 0.05 230)',
  },
} as const;
