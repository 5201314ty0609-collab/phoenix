/**
 * PHOENIX AIOS — 阴影令牌
 *
 * 多层次阴影系统
 */

export const shadows = {
  /** 无阴影 */
  none: 'none',

  /** 最小阴影 */
  xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',

  /** 小阴影 */
  sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',

  /** 中等阴影 */
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',

  /** 大阴影 */
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',

  /** 超大阴影 */
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',

  /** 2倍大阴影 */
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',

  /** 内阴影 */
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',

  /** 聚焦环 */
  ring: '0 0 0 3px rgb(59 130 246 / 0.5)',

  /** 危险聚焦环 */
  'ring-danger': '0 0 0 3px rgb(239 68 68 / 0.5)',

  /** 成功聚焦环 */
  'ring-success': '0 0 0 3px rgb(34 197 94 / 0.5)',
} as const;

/** 暗色模式阴影 */
export const darkShadows = {
  none: 'none',
  xs: '0 1px 2px 0 rgb(0 0 0 / 0.2)',
  sm: '0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.3)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.3), 0 8px 10px -6px rgb(0 0 0 / 0.3)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.5)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.2)',
} as const;
