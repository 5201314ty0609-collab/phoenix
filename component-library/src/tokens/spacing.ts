/**
 * PHOENIX AIOS — 间距令牌
 *
 * 基于 4px 网格系统
 */

export const spacing = {
  /** 0px */
  0: '0',
  /** 1px */
  px: '1px',
  /** 2px */
  0.5: '0.125rem',
  /** 4px */
  1: '0.25rem',
  /** 6px */
  1.5: '0.375rem',
  /** 8px */
  2: '0.5rem',
  /** 10px */
  2.5: '0.625rem',
  /** 12px */
  3: '0.75rem',
  /** 14px */
  3.5: '0.875rem',
  /** 16px */
  4: '1rem',
  /** 20px */
  5: '1.25rem',
  /** 24px */
  6: '1.5rem',
  /** 28px */
  7: '1.75rem',
  /** 32px */
  8: '2rem',
  /** 36px */
  9: '2.25rem',
  /** 40px */
  10: '2.5rem',
  /** 44px */
  11: '2.75rem',
  /** 48px */
  12: '3rem',
  /** 56px */
  14: '3.5rem',
  /** 64px */
  16: '4rem',
  /** 80px */
  20: '5rem',
  /** 96px */
  24: '6rem',
  /** 112px */
  28: '7rem',
  /** 128px */
  32: '8rem',
  /** 144px */
  36: '9rem',
  /** 160px */
  40: '10rem',
  /** 176px */
  44: '11rem',
  /** 192px */
  48: '12rem',
  /** 208px */
  52: '13rem',
  /** 224px */
  56: '14rem',
  /** 240px */
  60: '15rem',
  /** 256px */
  64: '16rem',
  /** 288px */
  72: '18rem',
  /** 320px */
  80: '20rem',
  /** 384px */
  96: '24rem',
} as const;

/** 语义化间距 */
export const semanticSpacing = {
  /** 紧凑内边距 */
  'padding-compact': spacing[2],
  /** 默认内边距 */
  'padding-default': spacing[4],
  /** 宽松内边距 */
  'padding-relaxed': spacing[6],
  /** 章节间距 */
  'section': spacing[16],
  /** 组件间距 */
  'component': spacing[4],
  /** 元素间距 */
  'element': spacing[2],
  /** 紧密间距 */
  'tight': spacing[1],
} as const;

/** 组件尺寸 */
export const componentSizes = {
  /** 最小触摸目标 44x44 */
  'touch-min': '2.75rem',
  xs: '1.5rem',
  sm: '2rem',
  md: '2.5rem',
  lg: '3rem',
  xl: '3.5rem',
} as const;
