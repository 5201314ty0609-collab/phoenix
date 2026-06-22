/**
 * PHOENIX AIOS 主题管理器
 * 支持暗色/亮色/自动主题切换
 * 包含过渡动画、系统偏好检测、本地存储
 */

class ThemeManager {
  constructor(options = {}) {
    this.storageKey = options.storageKey || 'phoenix-theme';
    this.defaultTheme = options.defaultTheme || 'dark';
    this.transitionDuration = options.transitionDuration || 300;
    this.onThemeChange = options.onThemeChange || null;

    this.themes = ['dark', 'light', 'auto'];
    this.currentTheme = null;
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    this.init();
  }

  /**
   * 初始化主题管理器
   */
  init() {
    // 从本地存储读取主题偏好
    const savedTheme = localStorage.getItem(this.storageKey);

    // 使用保存的主题或默认主题
    this.currentTheme = savedTheme || this.defaultTheme;

    // 应用主题
    this.applyTheme(this.currentTheme, false);

    // 监听系统主题变化
    this.mediaQuery.addEventListener('change', (e) => {
      if (this.currentTheme === 'auto') {
        this.applyTheme('auto', false);
      }
    });

    // 监听存储变化（跨标签页同步）
    window.addEventListener('storage', (e) => {
      if (e.key === this.storageKey && e.newValue) {
        this.currentTheme = e.newValue;
        this.applyTheme(this.currentTheme, false);
      }
    });
  }

  /**
   * 应用主题
   * @param {string} theme - 主题名称 (dark/light/auto)
   * @param {boolean} animate - 是否启用过渡动画
   */
  applyTheme(theme, animate = true) {
    if (!this.themes.includes(theme)) {
      console.warn(`Unknown theme: ${theme}`);
      return;
    }

    const root = document.documentElement;

    // 添加过渡动画类
    if (animate) {
      root.classList.add('theme-transition');
      setTimeout(() => {
        root.classList.remove('theme-transition');
      }, this.transitionDuration);
    }

    // 移除旧主题属性
    root.removeAttribute('data-theme');

    // 应用新主题
    if (theme === 'auto') {
      // 跟随系统偏好
      const systemTheme = this.mediaQuery.matches ? 'dark' : 'light';
      root.setAttribute('data-theme', systemTheme);
    } else {
      root.setAttribute('data-theme', theme);
    }

    // 更新 meta theme-color
    this.updateMetaThemeColor(theme);

    // 保存到本地存储
    localStorage.setItem(this.storageKey, theme);
    this.currentTheme = theme;

    // 触发回调
    if (this.onThemeChange) {
      this.onThemeChange(theme, this.getEffectiveTheme());
    }

    // 触发自定义事件
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: {
        theme,
        effectiveTheme: this.getEffectiveTheme()
      }
    }));
  }

  /**
   * 获取当前生效的实际主题
   * @returns {string} 'dark' 或 'light'
   */
  getEffectiveTheme() {
    if (this.currentTheme === 'auto') {
      return this.mediaQuery.matches ? 'dark' : 'light';
    }
    return this.currentTheme;
  }

  /**
   * 切换到下一个主题
   */
 toggleTheme() {
    const currentIndex = this.themes.indexOf(this.currentTheme);
    const nextIndex = (currentIndex + 1) % this.themes.length;
    this.applyTheme(this.themes[nextIndex]);
  }

  /**
   * 切换暗色/亮色主题
   */
  toggleDarkLight() {
    const effectiveTheme = this.getEffectiveTheme();
    this.applyTheme(effectiveTheme === 'dark' ? 'light' : 'dark');
  }

  /**
   * 更新 meta theme-color
   * @param {string} theme - 主题名称
   */
  updateMetaThemeColor(theme) {
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'theme-color';
      document.head.appendChild(meta);
    }

    // 根据主题设置颜色
    const colors = {
      dark: '#0f172a',  // oklch(14% 0.02 250)
      light: '#ffffff', // oklch(100% 0 0)
      auto: this.mediaQuery.matches ? '#0f172a' : '#ffffff'
    };

    meta.content = colors[theme] || colors.dark;
  }

  /**
   * 获取当前主题
   * @returns {string}
   */
  getTheme() {
    return this.currentTheme;
  }

  /**
   * 设置高对比度模式
   * @param {boolean} enabled
   */
  setHighContrast(enabled) {
    document.documentElement.setAttribute('data-contrast', enabled ? 'high' : 'normal');
    localStorage.setItem('phoenix-contrast', enabled ? 'high' : 'normal');
  }

  /**
   * 设置减少动画模式
   * @param {boolean} enabled
   */
  setReduceMotion(enabled) {
    document.documentElement.setAttribute('data-reduce-motion', enabled ? 'true' : 'false');
    localStorage.setItem('phoenix-reduce-motion', enabled ? 'true' : 'false');
  }

  /**
   * 获取系统偏好
   * @returns {object}
   */
  getSystemPreferences() {
    return {
      prefersDark: this.mediaQuery.matches,
      prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      prefersHighContrast: window.matchMedia('(prefers-contrast: high)').matches
    };
  }
}

/**
 * 主题切换按钮组件
 */
class ThemeToggle {
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    this.themeManager = options.themeManager || new ThemeManager();
    this.style = options.style || 'icon'; // icon, button, dropdown
    this.size = options.size || 'md'; // sm, md, lg

    this.render();
    this.bindEvents();
  }

  /**
   * 渲染切换按钮
   */
  render() {
    if (!this.container) return;

    const theme = this.themeManager.getTheme();
    const effectiveTheme = this.themeManager.getEffectiveTheme();

    if (this.style === 'icon') {
      this.renderIcon(theme, effectiveTheme);
    } else if (this.style === 'button') {
      this.renderButton(theme);
    } else if (this.style === 'dropdown') {
      this.renderDropdown(theme);
    }
  }

  /**
   * 渲染图标样式
   */
  renderIcon(theme, effectiveTheme) {
    const sizeMap = { sm: 16, md: 20, lg: 24 };
    const size = sizeMap[this.size] || 20;

    const icons = {
      dark: `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>`,
      light: `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>`,
      auto: `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>`
    };

    this.container.innerHTML = `
      <button class="theme-toggle theme-toggle--icon theme-toggle--${this.size}"
              aria-label="当前主题: ${theme}，点击切换"
              title="切换主题 (当前: ${theme})">
        <span class="theme-toggle__icon theme-toggle__icon--${effectiveTheme}">
          ${icons[theme] || icons.auto}
        </span>
      </button>
    `;
  }

  /**
   * 渲染按钮样式
   */
  renderButton(theme) {
    const labels = {
      dark: '暗色',
      light: '亮色',
      auto: '自动'
    };

    this.container.innerHTML = `
      <button class="theme-toggle theme-toggle--button theme-toggle--${this.size}"
              aria-label="当前主题: ${theme}，点击切换">
        <span class="theme-toggle__label">${labels[theme]}</span>
      </button>
    `;
  }

  /**
   * 渲染下拉菜单样式
   */
  renderDropdown(theme) {
    const labels = {
      dark: '暗色主题',
      light: '亮色主题',
      auto: '跟随系统'
    };

    this.container.innerHTML = `
      <div class="theme-toggle theme-toggle--dropdown">
        <button class="theme-toggle__trigger theme-toggle--${this.size}"
                aria-label="选择主题"
                aria-expanded="false"
                aria-haspopup="true">
          <span class="theme-toggle__label">${labels[theme]}</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <div class="theme-toggle__menu" role="menu" hidden>
          ${Object.entries(labels).map(([key, label]) => `
            <button class="theme-toggle__option ${key === theme ? 'theme-toggle__option--active' : ''}"
                    role="menuitem"
                    data-theme="${key}"
                    aria-current="${key === theme ? 'true' : 'false'}">
              ${label}
            </button>
          `).join('')}
        </div>
      </div>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;

    // 图标/按钮点击
    this.container.addEventListener('click', (e) => {
      const trigger = e.target.closest('.theme-toggle--icon, .theme-toggle--button, .theme-toggle__trigger');
      if (trigger) {
        if (this.style === 'dropdown') {
          this.toggleDropdown();
        } else {
          this.themeManager.toggleDarkLight();
          this.render();
        }
      }

      // 下拉选项点击
      const option = e.target.closest('.theme-toggle__option');
      if (option) {
        const theme = option.dataset.theme;
        this.themeManager.applyTheme(theme);
        this.render();
        this.closeDropdown();
      }
    });

    // 键盘导航
    this.container.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeDropdown();
      }
    });

    // 点击外部关闭下拉菜单
    document.addEventListener('click', (e) => {
      if (!this.container.contains(e.target)) {
        this.closeDropdown();
      }
    });

    // 监听主题变化
    window.addEventListener('themechange', () => {
      this.render();
    });
  }

  /**
   * 切换下拉菜单
   */
  toggleDropdown() {
    const menu = this.container.querySelector('.theme-toggle__menu');
    const trigger = this.container.querySelector('.theme-toggle__trigger');
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
      this.closeDropdown();
    } else {
      menu.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      // 聚焦第一个选项
      const firstOption = menu.querySelector('.theme-toggle__option');
      if (firstOption) firstOption.focus();
    }
  }

  /**
   * 关闭下拉菜单
   */
  closeDropdown() {
    const menu = this.container.querySelector('.theme-toggle__menu');
    const trigger = this.container.querySelector('.theme-toggle__trigger');
    if (menu && trigger) {
      menu.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
    }
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ThemeManager, ThemeToggle };
}

// 自动初始化
if (typeof window !== 'undefined') {
  window.ThemeManager = ThemeManager;
  window.ThemeToggle = ThemeToggle;

  // DOM 加载完成后自动初始化
  document.addEventListener('DOMContentLoaded', () => {
    // 查找所有主题切换容器并初始化
    document.querySelectorAll('[data-theme-toggle]').forEach(container => {
      const style = container.dataset.themeToggle || 'icon';
      const size = container.dataset.themeSize || 'md';
      new ThemeToggle(container, { style, size });
    });
  });
}
