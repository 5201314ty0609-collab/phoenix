import type { Config } from 'tailwindcss';

/**
 * PHOENIX AIOS Tailwind CSS v4 配置
 *
 * 设计理念：
 * - 深蓝 + 橙色：信任 + 活力
 * - 暗色优先，支持亮色
 * - 4px 基准网格
 * - WCAG AA 对比度
 */
const config: Config = {
  content: [
    './src/**/*.{ts,tsx,js,jsx}',
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './phoenix/**/*.{html,ts,tsx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    /* ═══════════════════════════════════════════════
       断点系统 (Breakpoints)
       Mobile-first，覆盖主流设备
       ═══════════════════════════════════════════════ */
    screens: {
      xs: '320px',     // 小手机
      sm: '375px',     // iPhone SE
      md: '768px',     // iPad
      lg: '1024px',    // iPad Pro / 小桌面
      xl: '1280px',    // 桌面
      '2xl': '1440px', // 大桌面
      '3xl': '1920px', // 全高清
      // 条件断点
      portrait: { raw: '(orientation: portrait)' },
      landscape: { raw: '(orientation: landscape)' },
      'touch': { raw: '(pointer: coarse)' },
      'mouse': { raw: '(pointer: fine)' },
      'reduced-motion': { raw: '(prefers-reduced-motion: reduce)' },
    },

    /* ═══════════════════════════════════════════════
       色彩系统 (Colors)
       基于 color-system.css 令牌
       ═══════════════════════════════════════════════ */
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: '#ffffff',
      black: '#000000',

      // 主色：深蓝 (Trust + Professional)
      primary: {
        50:  'hsl(220, 30%, 95%)',
        100: 'hsl(220, 30%, 90%)',
        200: 'hsl(220, 35%, 85%)',
        300: 'hsl(220, 40%, 75%)',
        400: 'hsl(220, 45%, 65%)',
        500: 'hsl(220, 50%, 50%)',
        600: 'hsl(220, 60%, 35%)',
        700: 'hsl(220, 70%, 25%)',
        800: 'hsl(220, 80%, 15%)',
        900: 'hsl(220, 100%, 8%)',
        950: 'hsl(220, 100%, 4%)',
      },

      // 辅助色：橙色 (Energy + Innovation)
      accent: {
        50:  'hsl(25, 75%, 95%)',
        100: 'hsl(25, 75%, 90%)',
        200: 'hsl(25, 80%, 85%)',
        300: 'hsl(25, 85%, 75%)',
        400: 'hsl(25, 90%, 65%)',
        500: 'hsl(25, 95%, 55%)',
        600: 'hsl(25, 85%, 45%)',
        700: 'hsl(25, 90%, 35%)',
        800: 'hsl(25, 95%, 25%)',
        900: 'hsl(25, 100%, 15%)',
      },

      // 中性色：灰阶
      neutral: {
        50:  'hsl(220, 1%, 95%)',
        100: 'hsl(220, 2%, 90%)',
        200: 'hsl(220, 2%, 80%)',
        300: 'hsl(220, 3%, 70%)',
        400: 'hsl(220, 3%, 60%)',
        500: 'hsl(220, 4%, 50%)',
        600: 'hsl(220, 5%, 40%)',
        700: 'hsl(220, 6%, 30%)',
        800: 'hsl(220, 8%, 20%)',
        900: 'hsl(220, 10%, 10%)',
        950: 'hsl(220, 12%, 5%)',
      },

      // 语义色
      success: {
        50:  'hsl(150, 50%, 90%)',
        100: 'hsl(150, 50%, 85%)',
        300: 'hsl(150, 60%, 60%)',
        500: 'hsl(150, 70%, 40%)',
        700: 'hsl(150, 80%, 25%)',
        900: 'hsl(150, 100%, 10%)',
      },
      warning: {
        50:  'hsl(40, 85%, 90%)',
        100: 'hsl(40, 85%, 85%)',
        300: 'hsl(40, 90%, 70%)',
        500: 'hsl(40, 95%, 50%)',
        700: 'hsl(40, 95%, 30%)',
        900: 'hsl(40, 100%, 15%)',
      },
      error: {
        50:  'hsl(0, 75%, 90%)',
        100: 'hsl(0, 75%, 85%)',
        300: 'hsl(0, 80%, 70%)',
        500: 'hsl(0, 85%, 50%)',
        700: 'hsl(0, 85%, 30%)',
        900: 'hsl(0, 100%, 15%)',
      },
      info: {
        50:  'hsl(210, 75%, 90%)',
        100: 'hsl(210, 75%, 85%)',
        300: 'hsl(210, 80%, 70%)',
        500: 'hsl(210, 85%, 50%)',
        700: 'hsl(210, 85%, 30%)',
        900: 'hsl(210, 100%, 15%)',
      },

      // 语义表面色 (通过 CSS 变量动态切换)
      surface: {
        DEFAULT: 'var(--surface)',
        alt: 'var(--surface-alt)',
        hover: 'var(--surface-hover)',
        active: 'var(--surface-active)',
      },
      bg: {
        DEFAULT: 'var(--bg)',
        subtle: 'var(--bg-subtle)',
      },
      border: {
        DEFAULT: 'var(--border)',
        subtle: 'var(--border-subtle)',
        strong: 'var(--border-strong)',
      },
      text: {
        DEFAULT: 'var(--text)',
        secondary: 'var(--text-secondary)',
        dim: 'var(--text-dim)',
        muted: 'var(--text-muted)',
        inverse: 'var(--text-inverse)',
      },
    },

    /* ═══════════════════════════════════════════════
       字体系统 (Font Family)
       ═══════════════════════════════════════════════ */
    fontFamily: {
      sans: [
        'PingFang SC',
        'Noto Sans SC',
        'SF Pro',
        'system-ui',
        '-apple-system',
        'sans-serif',
      ],
      mono: [
        'JetBrains Mono',
        'SF Mono',
        'Cascadia Code',
        'Fira Code',
        'monospace',
      ],
      display: [
        'SF Pro Display',
        'PingFang SC',
        'sans-serif',
      ],
    },

    /* ═══════════════════════════════════════════════
       字号系统 (Font Size)
       基于 Major Third (1.25) 比例
       ═══════════════════════════════════════════════ */
    fontSize: {
      xs:    ['0.75rem',  { lineHeight: '1rem' }],       // 12px
      sm:    ['0.875rem', { lineHeight: '1.25rem' }],     // 14px
      base:  ['1rem',     { lineHeight: '1.5rem' }],      // 16px
      lg:    ['1.125rem', { lineHeight: '1.75rem' }],     // 18px
      xl:    ['1.25rem',  { lineHeight: '1.75rem' }],     // 20px
      '2xl': ['1.5rem',   { lineHeight: '2rem' }],        // 24px
      '3xl': ['1.875rem', { lineHeight: '2.25rem' }],     // 30px
      '4xl': ['2.25rem',  { lineHeight: '2.5rem' }],      // 36px
      '5xl': ['3rem',     { lineHeight: '1' }],            // 48px
      '6xl': ['3.75rem',  { lineHeight: '1' }],            // 60px
      '7xl': ['4.5rem',   { lineHeight: '1' }],            // 72px
      // 响应式字号
      hero:    ['clamp(2.5rem, 1rem + 5vw, 5rem)',    { lineHeight: '1.1' }],
      h1:      ['clamp(2rem, 1rem + 3vw, 3.5rem)',    { lineHeight: '1.15' }],
      h2:      ['clamp(1.5rem, 1rem + 2vw, 2.5rem)',  { lineHeight: '1.2' }],
      h3:      ['clamp(1.25rem, 1rem + 1vw, 1.75rem)', { lineHeight: '1.3' }],
      body:    ['clamp(0.875rem, 0.8rem + 0.5vw, 1.125rem)', { lineHeight: '1.75' }],
      display: ['clamp(3rem, 1rem + 6vw, 6rem)',      { lineHeight: '1' }],
    },

    /* ═══════════════════════════════════════════════
       间距系统 (Spacing)
       基于 4px 网格，与 spacing-system.css 对齐
       ═══════════════════════════════════════════════ */
    spacing: {
      px: '1px',
      0:  '0',
      0.5: '0.125rem',  // 2px
      1:  '0.25rem',    // 4px
      1.5: '0.375rem',  // 6px
      2:  '0.5rem',     // 8px
      2.5: '0.625rem',  // 10px
      3:  '0.75rem',    // 12px
      3.5: '0.875rem',  // 14px
      4:  '1rem',       // 16px
      5:  '1.25rem',    // 20px
      6:  '1.5rem',     // 24px
      7:  '1.75rem',    // 28px
      8:  '2rem',       // 32px
      9:  '2.25rem',    // 36px
      10: '2.5rem',     // 40px
      11: '2.75rem',    // 44px (触摸目标最小尺寸)
      12: '3rem',       // 48px
      14: '3.5rem',     // 56px
      16: '4rem',       // 64px
      20: '5rem',       // 80px
      24: '6rem',       // 96px
      28: '7rem',       // 112px
      32: '8rem',       // 128px
      36: '9rem',       // 144px
      40: '10rem',      // 160px
      44: '11rem',      // 176px
      48: '12rem',      // 192px
      52: '13rem',      // 208px
      56: '14rem',      // 224px
      60: '15rem',      // 240px
      64: '16rem',      // 256px
      72: '18rem',      // 288px
      80: '20rem',      // 320px
      96: '24rem',      // 384px
      // 语义间距
      section: 'clamp(2rem, 1rem + 3vw, 6rem)',
      card: 'clamp(1rem, 0.5rem + 2vw, 2rem)',
      'button-x': 'clamp(0.75rem, 0.5rem + 1vw, 1.5rem)',
      'button-y': 'clamp(0.5rem, 0.25rem + 0.5vw, 0.75rem)',
      grid: 'clamp(1rem, 0.5rem + 1.5vw, 1.5rem)',
    },

    /* ═══════════════════════════════════════════════
       圆角 (Border Radius)
       ═══════════════════════════════════════════════ */
    borderRadius: {
      none: '0',
      xs:   '0.125rem',   // 2px
      sm:   '0.25rem',    // 4px
      DEFAULT: '0.375rem', // 6px
      md:   '0.5rem',     // 8px
      lg:   '0.75rem',    // 12px
      xl:   '1rem',       // 16px
      '2xl': '1.5rem',    // 24px
      '3xl': '2rem',      // 32px
      full: '9999px',
    },

    /* ═══════════════════════════════════════════════
       阴影 (Box Shadow)
       ═══════════════════════════════════════════════ */
    boxShadow: {
      none: 'none',
      xs:   '0 1px 2px rgba(0, 0, 0, 0.2)',
      sm:   '0 2px 4px rgba(0, 0, 0, 0.25)',
      DEFAULT: '0 4px 8px rgba(0, 0, 0, 0.3)',
      md:   '0 4px 8px rgba(0, 0, 0, 0.3)',
      lg:   '0 8px 16px rgba(0, 0, 0, 0.35)',
      xl:   '0 16px 32px rgba(0, 0, 0, 0.4)',
      '2xl': '0 24px 48px rgba(0, 0, 0, 0.45)',
      inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)',
      // 发光效果
      'glow-accent':  '0 0 20px rgba(244, 158, 66, 0.3), 0 0 40px rgba(244, 158, 66, 0.1)',
      'glow-primary': '0 0 20px rgba(59, 130, 246, 0.3), 0 0 40px rgba(59, 130, 246, 0.1)',
      'glow-success': '0 0 20px rgba(76, 175, 80, 0.3), 0 0 40px rgba(76, 175, 80, 0.1)',
      'glow-error':   '0 0 20px rgba(224, 85, 85, 0.3), 0 0 40px rgba(224, 85, 85, 0.1)',
    },

    /* ═══════════════════════════════════════════════
       动画 (Animation)
       ═══════════════════════════════════════════════ */
    transitionDuration: {
      DEFAULT: '300ms',
      75:  '75ms',
      100: '100ms',
      150: '150ms',
      200: '200ms',
      300: '300ms',
      500: '500ms',
      700: '700ms',
      1000: '1000ms',
    },
    transitionTimingFunction: {
      DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
      linear:  'linear',
      in:      'cubic-bezier(0.4, 0, 1, 1)',
      out:     'cubic-bezier(0, 0, 0.2, 1)',
      'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce:  'cubic-bezier(0.34, 1.56, 0.64, 1)',
      spring:  'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
    animation: {
      none: 'none',
      spin: 'spin 1s linear infinite',
      ping: 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
      pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      bounce: 'bounce 1s infinite',
      'fade-in':       'fadeIn 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      'fade-in-up':    'fadeInUp 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      'fade-in-down':  'fadeInDown 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      'slide-in-left': 'slideInLeft 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      'slide-in-right': 'slideInRight 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      'scale-in':      'scaleIn 300ms cubic-bezier(0, 0, 0.2, 1) forwards',
      shimmer: 'shimmer 1.5s infinite',
      glow:    'glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      float:   'float 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    },
    keyframes: {
      fadeIn: {
        from: { opacity: '0' },
        to: { opacity: '1' },
      },
      fadeInUp: {
        from: { opacity: '0', transform: 'translateY(12px)' },
        to: { opacity: '1', transform: 'translateY(0)' },
      },
      fadeInDown: {
        from: { opacity: '0', transform: 'translateY(-12px)' },
        to: { opacity: '1', transform: 'translateY(0)' },
      },
      slideInLeft: {
        from: { opacity: '0', transform: 'translateX(-20px)' },
        to: { opacity: '1', transform: 'translateX(0)' },
      },
      slideInRight: {
        from: { opacity: '0', transform: 'translateX(20px)' },
        to: { opacity: '1', transform: 'translateX(0)' },
      },
      scaleIn: {
        from: { opacity: '0', transform: 'scale(0.95)' },
        to: { opacity: '1', transform: 'scale(1)' },
      },
      shimmer: {
        '0%': { backgroundPosition: '-200% 0' },
        '100%': { backgroundPosition: '200% 0' },
      },
      glow: {
        '0%, 100%': { boxShadow: 'var(--glow-accent)' },
        '50%': { boxShadow: '0 0 30px rgba(244, 158, 66, 0.5), 0 0 60px rgba(244, 158, 66, 0.2)' },
      },
      float: {
        '0%, 100%': { transform: 'translateY(0)' },
        '50%': { transform: 'translateY(-6px)' },
      },
    },

    /* ═══════════════════════════════════════════════
       扩展 (Extend)
       ═══════════════════════════════════════════════ */
    extend: {
      // Z-Index 层级
      zIndex: {
        base:     '0',
        dropdown: '100',
        sticky:   '200',
        overlay:  '300',
        modal:    '400',
        popover:  '500',
        tooltip:  '600',
        toast:    '700',
      },
      // 容器宽度
      maxWidth: {
        xs:   '20rem',    // 320px
        sm:   '24rem',    // 384px
        md:   '28rem',    // 448px
        lg:   '32rem',    // 512px
        xl:   '36rem',    // 576px
        '2xl': '42rem',   // 672px
        '3xl': '48rem',   // 768px
        '4xl': '56rem',   // 896px
        '5xl': '64rem',   // 1024px
        '6xl': '72rem',   // 1152px
        '7xl': '80rem',   // 1280px
      },
      // 排版节奏
      lineHeight: {
        chinese: '1.75',
        'chinese-loose': '2',
        'chinese-tight': '1.5',
      },
      // 字间距
      letterSpacing: {
        tighter: '-0.05em',
        tight:   '-0.025em',
        normal:  '0',
        wide:    '0.025em',
        wider:   '0.05em',
        widest:  '0.1em',
      },
    },
  },

  /* ═══════════════════════════════════════════════
     插件 (Plugins)
     ═══════════════════════════════════════════════ */
  plugins: [
    // 自定义组件类
    function({ addComponents }: any) {
      addComponents({
        '.btn': {
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          padding: 'clamp(0.5rem, 0.25rem + 0.5vw, 0.75rem) clamp(0.75rem, 0.5rem + 1vw, 1.5rem)',
          borderRadius: '0.5rem',
          fontWeight: '600',
          fontSize: '0.875rem',
          lineHeight: '1',
          letterSpacing: '0.025em',
          textTransform: 'uppercase' as const,
          cursor: 'pointer',
          userSelect: 'none' as const,
          transition: 'all 150ms cubic-bezier(0, 0, 0.2, 1)',
          '&:active': { transform: 'scale(0.98)' },
          '&:focus-visible': {
            outline: '2px solid rgba(59, 130, 246, 0.3)',
            outlineOffset: '2px',
          },
        },
        '.btn-primary': {
          background: 'hsl(220, 50%, 50%)',
          color: '#ffffff',
          '&:hover': { background: 'hsl(220, 45%, 65%)' },
        },
        '.btn-accent': {
          background: 'hsl(25, 95%, 55%)',
          color: '#ffffff',
          '&:hover': { background: 'hsl(25, 90%, 65%)' },
        },
        '.btn-ghost': {
          background: 'transparent',
          color: 'var(--text-secondary)',
          '&:hover': { background: 'var(--interactive-hover)' },
        },
        '.btn-outline': {
          background: 'transparent',
          color: 'var(--text)',
          border: '1px solid var(--border)',
          '&:hover': { borderColor: 'var(--border-strong)' },
        },
        '.btn-sm': {
          padding: '0.25rem 0.75rem',
          fontSize: '0.75rem',
        },
        '.btn-lg': {
          padding: '0.75rem 2rem',
          fontSize: '1rem',
        },
        // 卡片
        '.card': {
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '0.75rem',
          padding: 'clamp(1rem, 0.5rem + 1.5vw, 2rem)',
          transition: 'all 300ms cubic-bezier(0, 0, 0.2, 1)',
          '&:hover': {
            borderColor: 'var(--border-strong)',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
            transform: 'translateY(-2px)',
          },
        },
        '.card-flat': {
          background: 'var(--surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '0.75rem',
          padding: 'clamp(1rem, 0.5rem + 1.5vw, 2rem)',
        },
        // 徽章
        '.badge': {
          display: 'inline-flex',
          alignItems: 'center',
          padding: '0.125rem 0.5rem',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: '600',
          lineHeight: '1',
          letterSpacing: '0.05em',
          textTransform: 'uppercase' as const,
        },
        '.badge-success': {
          background: 'hsl(150, 50%, 90%)',
          color: 'hsl(150, 80%, 25%)',
        },
        '.badge-warning': {
          background: 'hsl(40, 85%, 90%)',
          color: 'hsl(40, 95%, 30%)',
        },
        '.badge-error': {
          background: 'hsl(0, 75%, 90%)',
          color: 'hsl(0, 85%, 30%)',
        },
        '.badge-info': {
          background: 'hsl(210, 75%, 90%)',
          color: 'hsl(210, 85%, 30%)',
        },
        '.badge-primary': {
          background: 'hsl(220, 30%, 90%)',
          color: 'hsl(220, 60%, 35%)',
        },
        // 骨架屏
        '.skeleton': {
          background: 'linear-gradient(90deg, var(--surface) 25%, var(--surface-alt) 50%, var(--surface) 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 1.5s infinite',
          borderRadius: '0.375rem',
        },
        // 分割线
        '.divider': {
          height: '1px',
          background: 'var(--border)',
          margin: '1rem 0',
        },
        // 表单输入
        '.input': {
          width: '100%',
          padding: '0.5rem 0.75rem',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '0.5rem',
          color: 'var(--text)',
          fontFamily: 'inherit',
          fontSize: '0.875rem',
          transition: 'all 150ms cubic-bezier(0, 0, 0.2, 1)',
          '&::placeholder': { color: 'var(--text-muted)' },
          '&:focus': {
            outline: 'none',
            borderColor: 'hsl(220, 50%, 50%)',
            boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.3)',
          },
        },
      });
    },
    // 自定义工具类
    function({ addUtilities }: any) {
      addUtilities({
        // 玻璃效果
        '.glass': {
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(12px) saturate(150%)',
          WebkitBackdropFilter: 'blur(12px) saturate(150%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
        '.glass-heavy': {
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.15)',
        },
        // 文本渐变
        '.text-gradient-primary': {
          background: 'linear-gradient(135deg, hsl(220, 60%, 35%), hsl(220, 45%, 65%))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        },
        '.text-gradient-accent': {
          background: 'linear-gradient(135deg, hsl(25, 95%, 55%), hsl(25, 85%, 75%))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        },
        // 隐藏滚动条但保留滚动
        '.scrollbar-hide': {
          scrollbarWidth: 'none' as any,
          '&::-webkit-scrollbar': { display: 'none' },
        },
        // 平滑滚动
        '.scroll-smooth': {
          scrollBehavior: 'smooth',
        },
        // 安全区域内边距
        '.safe-top':    { paddingTop: 'env(safe-area-inset-top)' },
        '.safe-bottom': { paddingBottom: 'env(safe-area-inset-bottom)' },
        '.safe-left':   { paddingLeft: 'env(safe-area-inset-left)' },
        '.safe-right':  { paddingRight: 'env(safe-area-inset-right)' },
        // 触摸目标
        '.touch-target': {
          minWidth: '44px',
          minHeight: '44px',
        },
      });
    },
  ],
};

export default config;
