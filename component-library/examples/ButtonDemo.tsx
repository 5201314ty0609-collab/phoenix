/**
 * PHOENIX AIOS Button 组件演示
 * 展示优化后的效果
 */

'use client';

import React, { useState } from 'react';
import { Button, type ButtonProps } from '../src/atoms/Button/Button';
import '../src/tokens/theme-variables.css';

export function ButtonDemo() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [isLoading, setIsLoading] = useState(false);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleClick = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      color: 'var(--foreground)',
      padding: '2rem',
      fontFamily: 'var(--font-sans)',
    }}>
      {/* 头部 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '3rem',
      }}>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 700,
          background: 'linear-gradient(135deg, var(--accent), var(--primary))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          PHOENIX Button 组件
        </h1>
        <Button variant="outline" onClick={toggleTheme}>
          {theme === 'dark' ? '☀️ 亮色' : '🌙 暗色'}
        </Button>
      </div>

      {/* 变体展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          变体 (Variants)
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="link">Link</Button>
        </div>
      </section>

      {/* 尺寸展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          尺寸 (Sizes)
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <Button size="xs">Extra Small</Button>
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
          <Button size="xl">Extra Large</Button>
        </div>
      </section>

      {/* 状态展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          状态 (States)
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <Button>Default</Button>
          <Button disabled>Disabled</Button>
          <Button isLoading={isLoading} onClick={handleClick}>
            {isLoading ? '加载中...' : '点击加载'}
          </Button>
          <Button isLoading loadingText="提交中...">Submit</Button>
        </div>
      </section>

      {/* 图标展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          图标 (Icons)
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <Button leftIcon="←">返回</Button>
          <Button rightIcon="→">下一步</Button>
          <Button leftIcon="✓" rightIcon="→">确认</Button>
          <Button iconOnly>🔥</Button>
          <Button iconOnly variant="outline">⚡</Button>
        </div>
      </section>

      {/* 全宽展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          全宽 (Full Width)
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
          <Button fullWidth>全宽按钮</Button>
          <Button fullWidth variant="outline">全宽轮廓按钮</Button>
          <Button fullWidth variant="ghost">全宽幽灵按钮</button>
        </div>
      </section>

      {/* 组合展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          组合示例
        </h2>
        <div style={{
          display: 'flex',
          gap: '1rem',
          padding: '1.5rem',
          background: 'var(--surface)',
          borderRadius: '0.75rem',
          border: '1px solid var(--border)',
        }}>
          <Button variant="primary" size="lg" leftIcon="🚀">
            开始使用
          </Button>
          <Button variant="outline" size="lg">
            了解更多
          </Button>
        </div>
      </section>

      {/* 主题变量展示 */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          主题变量
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
          gap: '1rem',
        }}>
          {[
            { name: 'Primary', color: 'var(--primary)' },
            { name: 'Secondary', color: 'var(--secondary)' },
            { name: 'Accent', color: 'var(--accent)' },
            { name: 'Success', color: 'var(--success)' },
            { name: 'Warning', color: 'var(--warning)' },
            { name: 'Destructive', color: 'var(--destructive)' },
            { name: 'Info', color: 'var(--info)' },
          ].map((item) => (
            <div
              key={item.name}
              style={{
                padding: '1rem',
                background: `hsl(${item.color})`,
                borderRadius: '0.5rem',
                textAlign: 'center',
                color: 'white',
                fontWeight: 600,
                fontSize: '0.875rem',
              }}
            >
              {item.name}
            </div>
          ))}
        </div>
      </section>

      {/* 动画效果展示 */}
      <section>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          动画效果
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <Button variant="primary">悬停效果</Button>
          <Button variant="primary">点击缩放</Button>
          <Button variant="primary" isLoading>加载动画</Button>
        </div>
        <p style={{
          marginTop: '1rem',
          fontSize: '0.875rem',
          color: 'var(--foreground-muted)',
        }}>
          • 悬停：颜色渐变 + 轻微上移
          • 点击：缩放 0.98
          • 加载：旋转动画
        </p>
      </section>
    </div>
  );
}

export default ButtonDemo;
