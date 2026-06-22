// PHOENIX AIOS Tailwind CSS 配置
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      // 颜色系统
      colors: {
        primary: {
          50: 'hsl(220, 100%, 97%)',
          100: 'hsl(220, 100%, 93%)',
          200: 'hsl(220, 100%, 85%)',
          300: 'hsl(220, 100%, 75%)',
          400: 'hsl(220, 100%, 65%)',
          500: 'hsl(220, 100%, 50%)',
          600: 'hsl(220, 100%, 40%)',
          700: 'hsl(220, 100%, 30%)',
          800: 'hsl(220, 100%, 20%)',
          900: 'hsl(220, 100%, 10%)',
        },
        accent: {
          50: 'hsl(180, 100%, 97%)',
          100: 'hsl(180, 100%, 93%)',
          200: 'hsl(180, 100%, 85%)',
          300: 'hsl(180, 100%, 75%)',
          400: 'hsl(180, 100%, 65%)',
          500: 'hsl(180, 100%, 50%)',
          600: 'hsl(180, 100%, 40%)',
          700: 'hsl(180, 100%, 30%)',
          800: 'hsl(180, 100%, 20%)',
          900: 'hsl(180, 100%, 10%)',
        },
        surface: {
          DEFAULT: 'hsl(220, 15%, 8%)',
          alt: 'hsl(220, 15%, 12%)',
          raised: 'hsl(220, 15%, 16%)',
        },
        border: {
          DEFAULT: 'hsl(220, 15%, 20%)',
          strong: 'hsl(220, 15%, 30%)',
        },
      },
      // 字体
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'monospace'],
        display: ['Geist', 'system-ui', 'sans-serif'],
      },
      // 字号
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        '7xl': ['4.5rem', { lineHeight: '1' }],
      },
      // 间距
      spacing: {
        '0.5': '0.125rem',
        '1.5': '0.375rem',
        '2.5': '0.625rem',
        '3.5': '0.875rem',
        '4.5': '1.125rem',
        '5.5': '1.375rem',
        '6.5': '1.625rem',
        '7.5': '1.875rem',
        '8.5': '2.125rem',
        '9.5': '2.375rem',
        '10.5': '2.625rem',
        '11.5': '2.875rem',
        '12.5': '3.125rem',
        '13': '3.25rem',
        '15': '3.75rem',
        '17': '4.25rem',
        '18': '4.5rem',
        '19': '4.75rem',
        '21': '5.25rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
        '34': '8.5rem',
        '38': '9.5rem',
        '42': '10.5rem',
        '46': '11.5rem',
        '50': '12.5rem',
        '54': '13.5rem',
        '58': '14.5rem',
        '62': '15.5rem',
        '66': '16.5rem',
        '70': '17.5rem',
        '74': '18.5rem',
        '78': '19.5rem',
        '82': '20.5rem',
        '86': '21.5rem',
        '90': '22.5rem',
        '94': '23.5rem',
        '98': '24.5rem',
      },
      // 圆角
      borderRadius: {
        'sm': '0.25rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        'full': '9999px',
      },
      // 阴影
      boxShadow: {
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'sm': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        'glow': '0 0 20px rgb(64 110 255 / 0.3)',
        'glow-accent': '0 0 20px rgb(34 211 238 / 0.3)',
      },
      // 动画
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-out': 'fadeOut 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin': 'spin 1s linear infinite',
        'bounce': 'bounce 1s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulse: {
          '50%': { opacity: '0.5' },
        },
        spin: {
          'to': { transform: 'rotate(360deg)' },
        },
        bounce: {
          '0%, 100%': {
            transform: 'translateY(-25%)',
            animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
          },
          '50%': {
            transform: 'none',
            animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
          },
        },
      },
    },
  },
  plugins: [
    // 自定义插件：添加基础样式
    function({ addBase }) {
      addBase({
        'html': {
          fontSize: '16px',
          '-webkit-font-smoothing': 'antialiased',
          '-moz-osx-font-smoothing': 'grayscale',
        },
        'body': {
          fontFamily: 'Geist, Inter, system-ui, sans-serif',
          backgroundColor: 'hsl(220, 15%, 8%)',
          color: 'hsl(220, 10%, 90%)',
        },
      })
    },
  ],
}
