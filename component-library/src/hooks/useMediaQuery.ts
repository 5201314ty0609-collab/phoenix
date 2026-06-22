/**
 * PHOENIX AIOS — useMediaQuery Hook
 *
 * 响应式媒体查询 Hook
 * 监听 CSS 媒体查询变化，返回匹配状态
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)');
 * const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
 * const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
 */

import { useState, useEffect, useCallback, useRef } from 'react';

/** 预定义断点 */
export const BREAKPOINTS = {
  xs: '(max-width: 479px)',
  sm: '(min-width: 480px)',
  md: '(min-width: 768px)',
  lg: '(min-width: 1024px)',
  xl: '(min-width: 1280px)',
  '2xl': '(min-width: 1536px)',
  motion: '(prefers-reduced-motion: reduce)',
  dark: '(prefers-color-scheme: dark)',
  portrait: '(orientation: portrait)',
  landscape: '(orientation: landscape)',
  touch: '(hover: none) and (pointer: coarse)',
  mouse: '(hover: hover) and (pointer: fine)',
  highContrast: '(forced-colors: active)',
} as const;

export type Breakpoint = keyof typeof BREAKPOINTS;

/**
 * 媒体查询 Hook
 *
 * @param query - CSS 媒体查询字符串或预定义断点名称
 * @returns 是否匹配
 */
export function useMediaQuery(query: string | Breakpoint): boolean {
  const mediaQuery = query in BREAKPOINTS
    ? BREAKPOINTS[query as Breakpoint]
    : query;

  const [matches, setMatches] = useState<boolean>(() => {
    // SSR 安全：服务端返回 false
    if (typeof window === 'undefined') return false;
    return window.matchMedia(mediaQuery).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mql = window.matchMedia(mediaQuery);

    // 初始值同步
    setMatches(mql.matches);

    // 监听变化
    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [mediaQuery]);

  return matches;
}

/**
 * 多断点匹配 Hook
 *
 * @example
 * const breakpoints = useBreakpoints();
 * // breakpoints: { sm: true, md: true, lg: false, xl: false }
 */
export function useBreakpoints(): Record<Breakpoint, boolean> {
  const xs = useMediaQuery('xs');
  const sm = useMediaQuery('sm');
  const md = useMediaQuery('md');
  const lg = useMediaQuery('lg');
  const xl = useMediaQuery('xl');
  const xxl = useMediaQuery('2xl');
  const motion = useMediaQuery('motion');
  const dark = useMediaQuery('dark');
  const portrait = useMediaQuery('portrait');
  const landscape = useMediaQuery('landscape');
  const touch = useMediaQuery('touch');
  const mouse = useMediaQuery('mouse');
  const highContrast = useMediaQuery('highContrast');

  return {
    xs,
    sm,
    md,
    lg,
    xl,
    '2xl': xxl,
    motion,
    dark,
    portrait,
    landscape,
    touch,
    mouse,
    highContrast,
  };
}

/**
 * 当前断点名称 Hook
 *
 * @example
 * const current = useCurrentBreakpoint(); // 'md' | 'lg' | ...
 */
export function useCurrentBreakpoint(): Breakpoint {
  const breakpoints = useBreakpoints();

  if (breakpoints['2xl']) return '2xl';
  if (breakpoints.xl) return 'xl';
  if (breakpoints.lg) return 'lg';
  if (breakpoints.md) return 'md';
  if (breakpoints.sm) return 'sm';
  return 'xs';
}
