/**
 * PHOENIX AIOS — className 合并工具
 *
 * 使用 clsx + tailwind-merge 实现智能类名合并
 * 解决 Tailwind CSS 类名冲突问题
 */

// 简化版 clsx 实现
type ClassValue = string | number | boolean | undefined | null | ClassValue[] | Record<string, boolean | undefined | null>;

function clsx(...inputs: ClassValue[]): string {
  const classes: string[] = [];

  for (const input of inputs) {
    if (!input) continue;

    if (typeof input === 'string' || typeof input === 'number') {
      classes.push(String(input));
    } else if (Array.isArray(input)) {
      const inner = clsx(...input);
      if (inner) classes.push(inner);
    } else if (typeof input === 'object') {
      for (const [key, value] of Object.entries(input)) {
        if (value) classes.push(key);
      }
    }
  }

  return classes.join(' ');
}

// Tailwind 类名冲突解决
// 简化版：处理常见的 Tailwind 冲突模式
const CONFLICT_GROUPS: Record<string, string[]> = {
  // 间距冲突
  padding: ['p-', 'px-', 'py-', 'pt-', 'pr-', 'pb-', 'pl-', 'ps-', 'pe-'],
  margin: ['m-', 'mx-', 'my-', 'mt-', 'mr-', 'mb-', 'ml-', 'ms-', 'me-'],

  // 尺寸冲突
  width: ['w-'],
  height: ['h-'],
  minWidth: ['min-w-'],
  minHeight: ['min-h-'],
  maxWidth: ['max-w-'],
  maxHeight: ['max-h-'],

  // 背景色冲突
  bg: ['bg-'],

  // 文字颜色冲突
  text: ['text-'],
  textDecoration: ['underline', 'overline', 'line-through', 'no-underline'],

  // 字体大小和行高
  fontSize: ['text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl', 'text-4xl', 'text-5xl', 'text-6xl', 'text-7xl', 'text-8xl', 'text-9xl'],
  lineHeight: ['leading-'],

  // 边框冲突
  border: ['border', 'border-0', 'border-2', 'border-4', 'border-8'],
  borderColor: ['border-'],
  borderRadius: ['rounded-', 'rounded'],

  // 显示模式
  display: ['block', 'inline-block', 'inline', 'flex', 'inline-flex', 'grid', 'inline-grid', 'hidden', 'table', 'inline-table'],

  // 定位
  position: ['static', 'fixed', 'absolute', 'relative', 'sticky'],

  // Flexbox
  flexDirection: ['flex-row', 'flex-col', 'flex-row-reverse', 'flex-col-reverse'],
  flexWrap: ['flex-wrap', 'flex-nowrap', 'flex-wrap-reverse'],
  justifyContent: ['justify-'],
  alignItems: ['items-'],
  alignSelf: ['self-'],

  // Grid
  gridTemplateColumns: ['grid-cols-'],
  gridTemplateRows: ['grid-rows-'],

  // Overflow
  overflow: ['overflow-', 'overflow-x-', 'overflow-y-'],

  // Opacity
  opacity: ['opacity-'],

  // Shadow
  shadow: ['shadow-', 'shadow'],

  // Ring
  ring: ['ring-', 'ring'],

  // Z-index
  zIndex: ['z-'],
};

/**
 * 提取类名的冲突组
 */
function getClassGroup(className: string): string | null {
  // 完全匹配（如 'block', 'flex', 'hidden'）
  for (const [group, patterns] of Object.entries(CONFLICT_GROUPS)) {
    if (patterns.includes(className)) {
      return group;
    }
  }

  // 前缀匹配（如 'bg-red-500' 匹配 'bg-'）
  for (const [group, patterns] of Object.entries(CONFLICT_GROUPS)) {
    for (const pattern of patterns) {
      if (pattern.endsWith('-') && className.startsWith(pattern)) {
        return group;
      }
    }
  }

  return null;
}

/**
 * 智能合并 Tailwind 类名
 *
 * @example
 * cn('px-4 py-2', 'px-8') // => 'py-2 px-8' (px-4 被 px-8 覆盖)
 * cn('text-red-500', 'text-blue-500') // => 'text-blue-500'
 * cn('bg-white dark:bg-gray-900', 'bg-gray-100') // => 'dark:bg-gray-900 bg-gray-100'
 */
export function cn(...inputs: ClassValue[]): string {
  const classes = clsx(...inputs).split(/\s+/).filter(Boolean);
  const result: string[] = [];
  const seen = new Map<string, number>();

  for (const className of classes) {
    // 处理 dark: 等变体前缀
    const variants: string[] = [];
    let base = className;

    // 提取变体前缀（支持 dark:, hover:, focus: 等）
    const variantMatch = base.match(/^((?:dark|hover|focus|active|disabled|group-hover|peer-focus|first|last|odd|even|sm|md|lg|xl|2xl):)+/);
    if (variantMatch) {
      variants.push(variantMatch[0]);
      base = base.slice(variantMatch[0].length);
    }

    // 获取冲突组
    const group = getClassGroup(base);
    const key = group ? `${variants.join('')}${group}` : className;

    if (group) {
      const existingIndex = seen.get(key);
      if (existingIndex !== undefined) {
        // 替换同一组的旧类名
        result[existingIndex] = className;
        continue;
      }
      seen.set(key, result.length);
    }

    result.push(className);
  }

  return result.join(' ');
}

/**
 * 条件类名
 *
 * @example
 * cx('base-class', {
 *   'active-class': isActive,
 *   'disabled-class': isDisabled,
 * })
 */
export function cx(
  base: string,
  conditions: Record<string, boolean | undefined | null>
): string {
  return cn(base, conditions);
}
