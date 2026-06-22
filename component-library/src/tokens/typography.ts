/**
 * PHOENIX AIOS — 排版令牌
 *
 * 精心设计的排版系统
 */

// ============================================================
// 字体族
// ============================================================

export const fontFamily = {
  /** 主要字体（无衬线） */
  sans: [
    'Geist',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    '"Noto Sans"',
    'sans-serif',
    '"Apple Color Emoji"',
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
    '"Noto Color Emoji"',
  ].join(', '),

  /** 等宽字体 */
  mono: [
    'Geist Mono',
    'ui-monospace',
    'SFMono-Regular',
    '"SF Mono"',
    'Menlo',
    'Consolas',
    '"Liberation Mono"',
    'monospace',
  ].join(', '),

  /** 衬线字体（用于标题） */
  serif: [
    'Georgia',
    'Cambria',
    '"Times New Roman"',
    'Times',
    'serif',
  ].join(', '),
} as const;

// ============================================================
// 字体大小
// ============================================================

export const fontSize = {
  /** 12px */
  xs: ['0.75rem', { lineHeight: '1rem' }],
  /** 14px */
  sm: ['0.875rem', { lineHeight: '1.25rem' }],
  /** 16px */
  base: ['1rem', { lineHeight: '1.5rem' }],
  /** 18px */
  lg: ['1.125rem', { lineHeight: '1.75rem' }],
  /** 20px */
  xl: ['1.25rem', { lineHeight: '1.75rem' }],
  /** 24px */
  '2xl': ['1.5rem', { lineHeight: '2rem' }],
  /** 30px */
  '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
  /** 36px */
  '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
  /** 48px */
  '5xl': ['3rem', { lineHeight: '1' }],
  /** 60px */
  '6xl': ['3.75rem', { lineHeight: '1' }],
  /** 72px */
  '7xl': ['4.5rem', { lineHeight: '1' }],
  /** 96px */
  '8xl': ['6rem', { lineHeight: '1' }],
  /** 128px */
  '9xl': ['8rem', { lineHeight: '1' }],
} as const;

// ============================================================
// 字体粗细
// ============================================================

export const fontWeight = {
  thin: '100',
  extralight: '200',
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
  black: '900',
} as const;

// ============================================================
// 行高
// ============================================================

export const lineHeight = {
  none: '1',
  tight: '1.25',
  snug: '1.375',
  normal: '1.5',
  relaxed: '1.625',
  loose: '2',
} as const;

// ============================================================
// 字间距
// ============================================================

export const letterSpacing = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
} as const;

// ============================================================
// 响应式字体大小（clamp）
// ============================================================

export const responsiveFontSize = {
  /** 正文 */
  body: 'clamp(1rem, 0.92rem + 0.4vw, 1.125rem)',
  /** 小标题 */
  heading: 'clamp(1.5rem, 1rem + 1.5vw, 2.5rem)',
  /** 大标题 */
  display: 'clamp(2.5rem, 1rem + 4vw, 5rem)',
  /** 超大标题 */
  hero: 'clamp(3rem, 1rem + 7vw, 8rem)',
} as const;

// ============================================================
// 文本样式（组合令牌）
// ============================================================

export const textStyles = {
  /** 标题 1 */
  'heading-1': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize['5xl'],
    fontWeight: fontWeight.bold,
    letterSpacing: letterSpacing.tight,
    lineHeight: lineHeight.tight,
  },
  /** 标题 2 */
  'heading-2': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize['4xl'],
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.tight,
    lineHeight: lineHeight.tight,
  },
  /** 标题 3 */
  'heading-3': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize['3xl'],
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.snug,
  },
  /** 标题 4 */
  'heading-4': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize['2xl'],
    fontWeight: fontWeight.semibold,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.snug,
  },
  /** 正文大 */
  'body-lg': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.relaxed,
  },
  /** 正文 */
  'body': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.base,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.normal,
  },
  /** 正文小 */
  'body-sm': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.normal,
  },
  /** 代码 */
  'code': {
    fontFamily: fontFamily.mono,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.normal,
  },
  /** 标签 */
  'label': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
    letterSpacing: letterSpacing.wide,
    lineHeight: lineHeight.normal,
  },
  /** 说明文字 */
  'caption': {
    fontFamily: fontFamily.sans,
    fontSize: fontSize.xs,
    fontWeight: fontWeight.normal,
    letterSpacing: letterSpacing.normal,
    lineHeight: lineHeight.normal,
  },
} as const;
