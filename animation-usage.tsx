/**
 * PHOENIX 动画使用示例
 * 展示如何在 React/TypeScript 项目中使用动画库
 * 版本: v1.0.0
 * 更新: 2026-06-23
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useAnimation, useInView } from 'framer-motion';
import {
  fadeVariants,
  slideUpVariants,
  slideDownVariants,
  scaleVariants,
  fadeSlideUpVariants,
  staggerContainer,
  staggerItem,
  dropdownVariants,
  modalVariants,
  toastVariants,
  accordionVariants,
  buttonHover,
  buttonTap,
  cardHover,
  springs,
  durations,
  easings,
} from './framer-motion';

// ═══════════════════════════════════════════════════════
// 基础动画组件
// ═══════════════════════════════════════════════════════

/**
 * 淡入组件
 */
export const FadeIn: React.FC<{
  children: React.ReactNode;
  delay?: number;
  duration?: number;
}> = ({ children, delay = 0, duration = durations.normal }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration, delay, ease: easings.enter }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 滑入组件
 */
export const SlideUp: React.FC<{
  children: React.ReactNode;
  delay?: number;
  distance?: number;
}> = ({ children, delay = 0, distance = 20 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: distance }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: durations.normal,
        delay,
        ease: easings.enterSmooth,
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 缩放进入组件
 */
export const ScaleIn: React.FC<{
  children: React.ReactNode;
  delay?: number;
}> = ({ children, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: durations.normal,
        delay,
        ease: easings.bounce,
      }}
    >
      {children}
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════
// 序列动画组件
// ═══════════════════════════════════════════════════════

/**
 * 交错列表组件
 */
export const StaggerList: React.FC<{
  children: React.ReactNode;
  staggerDelay?: number;
}> = ({ children, staggerDelay = 0.08 }) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
            delayChildren: 0.1,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 交错列表项
 */
export const StaggerItem: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <motion.div variants={staggerItem}>
      {children}
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════
// 视口动画组件
// ═══════════════════════════════════════════════════════

/**
 * 视口进入动画
 */
export const ViewportAnimator: React.FC<{
  children: React.ReactNode;
  variants?: typeof fadeVariants;
  threshold?: number;
  once?: boolean;
}> = ({
  children,
  variants = fadeSlideUpVariants,
  threshold = 0.2,
  once = true,
}) => {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: threshold }}
      variants={variants}
    >
      {children}
    </motion.div>
  );
};

/**
 * 使用 IntersectionObserver 的视口动画
 */
export const useViewportAnimation = (threshold = 0.2) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: threshold });
  const controls = useAnimation();

  useEffect(() => {
    if (isInView) {
      controls.start('visible');
    }
  }, [isInView, controls]);

  return { ref, controls, isInView };
};

// ═══════════════════════════════════════════════════════
// 交互动画组件
// ═══════════════════════════════════════════════════════

/**
 * 动画按钮
 */
export const AnimatedButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'accent';
  disabled?: boolean;
  loading?: boolean;
}> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
}) => {
  const baseClasses = 'btn';
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    accent: 'btn-accent',
  };

  return (
    <motion.button
      className={`${baseClasses} ${variantClasses[variant]}`}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={disabled ? {} : buttonHover}
      whileTap={disabled ? {} : buttonTap}
      animate={loading ? { opacity: 0.7 } : { opacity: 1 }}
    >
      {loading ? (
        <motion.div
          className="spinner"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      ) : (
        children
      )}
    </motion.button>
  );
};

/**
 * 动画卡片
 */
export const AnimatedCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}> = ({ children, className = '', onClick }) => {
  return (
    <motion.div
      className={`card ${className}`}
      whileHover={cardHover}
      whileTap={onClick ? { scale: 0.98 } : {}}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {children}
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════
// 容器动画组件
// ═══════════════════════════════════════════════════════

/**
 * 下拉菜单
 */
export const Dropdown: React.FC<{
  isOpen: boolean;
  children: React.ReactNode;
  className?: string;
}> = ({ isOpen, children, className = '' }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className={className}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={dropdownVariants}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * 模态框
 */
export const Modal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}> = ({ isOpen, onClose, children, title }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 遮罩 */}
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1000,
            }}
          />

          {/* 内容 */}
          <motion.div
            className="modal-content"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={modalVariants}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              zIndex: 1001,
              maxWidth: '500px',
              width: '90%',
            }}
          >
            {title && (
              <h2 style={{ marginBottom: '16px' }}>{title}</h2>
            )}
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

/**
 * Toast 通知
 */
export const Toast: React.FC<{
  isVisible: boolean;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  onClose: () => void;
}> = ({ isVisible, message, type = 'info', onClose }) => {
  const typeStyles = {
    success: { background: 'var(--success-500)', color: 'white' },
    error: { background: 'var(--error-500)', color: 'white' },
    warning: { background: 'var(--warning-500)', color: 'white' },
    info: { background: 'var(--info-500)', color: 'white' },
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={toastVariants}
          style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: 1002,
            ...typeStyles[type],
          }}
          onClick={onClose}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * Accordion 折叠面板
 */
export const Accordion: React.FC<{
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}> = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="accordion">
      <motion.div
        className="accordion-header"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: '16px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'var(--gray-50)',
          borderRadius: '8px',
        }}
        whileHover={{ background: 'var(--gray-100)' }}
      >
        <span>{title}</span>
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: durations.fast }}
        >
          ▼
        </motion.span>
      </motion.div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={accordionVariants}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '16px' }}>
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ═══════════════════════════════════════════════════════
// 特效组件
// ═══════════════════════════════════════════════════════

/**
 * 脉冲效果
 */
export const Pulse: React.FC<{
  children: React.ReactNode;
  scale?: number;
  duration?: number;
}> = ({ children, scale = 1.05, duration = 2 }) => {
  return (
    <motion.div
      animate={{
        scale: [1, scale, 1],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 摇晃效果
 */
export const Shake: React.FC<{
  children: React.ReactNode;
  trigger: boolean;
}> = ({ children, trigger }) => {
  return (
    <motion.div
      animate={trigger ? { x: [0, -4, 4, -4, 4, 0] } : {}}
      transition={{ duration: 0.5 }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 浮动效果
 */
export const Float: React.FC<{
  children: React.ReactNode;
  distance?: number;
  duration?: number;
}> = ({ children, distance = 8, duration = 3 }) => {
  return (
    <motion.div
      animate={{
        y: [0, -distance, 0],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 打字机效果
 */
export const Typewriter: React.FC<{
  text: string;
  speed?: number;
  delay?: number;
}> = ({ text, speed = 50, delay = 0 }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (currentIndex < text.length) {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }
    }, currentIndex === 0 ? delay : speed);

    return () => clearTimeout(timeout);
  }, [currentIndex, text, speed, delay]);

  return (
    <span>
      {displayText}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity }}
      >
        |
      </motion.span>
    </span>
  );
};

/**
 * 数字滚动
 */
export const AnimatedNumber: React.FC<{
  value: number;
  duration?: number;
  format?: (n: number) => string;
}> = ({ value, duration = 1, format = n => Math.round(n).toString() }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const start = displayValue;
    const end = value;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / (duration * 1000), 1);

      // 缓动函数
      const eased = 1 - Math.pow(1 - progress, 3);

      setDisplayValue(start + (end - start) * eased);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value, duration]);

  return <span>{format(displayValue)}</span>;
};

// ═══════════════════════════════════════════════════════
// 页面过渡组件
// ═══════════════════════════════════════════════════════

/**
 * 页面过渡包装器
 */
export const PageTransition: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{
        duration: durations.moderate,
        ease: easings.enterSmooth,
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * 路由过渡
 */
export const RouteTransition: React.FC<{
  children: React.ReactNode;
  location: string;
}> = ({ children, location }) => {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{
          duration: durations.normal,
          ease: easings.standard,
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

// ═══════════════════════════════════════════════════════
// 使用示例
// ═══════════════════════════════════════════════════════

/**
 * 示例页面
 */
export const AnimationExample: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isToastVisible, setIsToastVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const items = ['项目 1', '项目 2', '项目 3', '项目 4', '项目 5'];

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>PHOENIX 动画示例</h1>

      {/* 基础动画 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>基础动画</h2>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <FadeIn>
            <div style={{ padding: '20px', background: 'var(--primary-100)', borderRadius: '8px' }}>
              淡入
            </div>
          </FadeIn>

          <SlideUp>
            <div style={{ padding: '20px', background: 'var(--accent-100)', borderRadius: '8px' }}>
              上滑
            </div>
          </SlideUp>

          <ScaleIn>
            <div style={{ padding: '20px', background: 'var(--success-100)', borderRadius: '8px' }}>
              缩放
            </div>
          </ScaleIn>
        </div>
      </section>

      {/* 序列动画 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>序列动画</h2>
        <StaggerList>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {items.map((item, i) => (
              <StaggerItem key={i}>
                <div style={{
                  padding: '16px 24px',
                  background: 'var(--gray-100)',
                  borderRadius: '8px',
                }}>
                  {item}
                </div>
              </StaggerItem>
            ))}
          </div>
        </StaggerList>
      </section>

      {/* 交互动画 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>交互动画</h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <AnimatedButton
            variant="primary"
            onClick={() => setIsModalOpen(true)}
          >
            打开模态框
          </AnimatedButton>

          <AnimatedButton
            variant="secondary"
            onClick={() => setIsToastVisible(true)}
          >
            显示 Toast
          </AnimatedButton>

          <AnimatedButton
            variant="accent"
            loading={isLoading}
            onClick={() => {
              setIsLoading(true);
              setTimeout(() => setIsLoading(false), 2000);
            }}
          >
            加载动画
          </AnimatedButton>
        </div>
      </section>

      {/* 卡片动画 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>卡片动画</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
          <AnimatedCard>
            <h3>卡片 1</h3>
            <p>悬停查看效果</p>
          </AnimatedCard>

          <AnimatedCard onClick={() => alert('点击了!')}>
            <h3>卡片 2</h3>
            <p>可点击卡片</p>
          </AnimatedCard>

          <AnimatedCard>
            <h3>卡片 3</h3>
            <p>悬停查看效果</p>
          </AnimatedCard>
        </div>
      </section>

      {/* 折叠面板 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>折叠面板</h2>
        <Accordion title="点击展开" defaultOpen={false}>
          <p>这是折叠面板的内容，使用动画展开和收起。</p>
        </Accordion>
      </section>

      {/* 特效 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>特效</h2>
        <div style={{ display: 'flex', gap: '40px', alignItems: 'center' }}>
          <div>
            <h3>脉冲</h3>
            <Pulse>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'var(--primary-500)',
                borderRadius: '50%',
              }} />
            </Pulse>
          </div>

          <div>
            <h3>浮动</h3>
            <Float>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'var(--accent-500)',
                borderRadius: '8px',
              }} />
            </Float>
          </div>

          <div>
            <h3>数字滚动</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              <AnimatedNumber value={1234} duration={2} />
            </div>
          </div>
        </div>
      </section>

      {/* 视口动画 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>视口动画</h2>
        <p>向下滚动查看效果</p>

        <div style={{ marginTop: '200px' }}>
          <ViewportAnimator>
            <div style={{
              padding: '40px',
              background: 'var(--gradient-primary)',
              borderRadius: '12px',
              color: 'white',
              textAlign: 'center',
            }}>
              <h3>滚动到我</h3>
              <p>使用视口触发动画</p>
            </div>
          </ViewportAnimator>
        </div>
      </section>

      {/* 模态框 */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="模态框示例"
      >
        <p>这是一个带动画的模态框。</p>
        <div style={{ marginTop: '16px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <AnimatedButton variant="secondary" onClick={() => setIsModalOpen(false)}>
            取消
          </AnimatedButton>
          <AnimatedButton variant="primary" onClick={() => setIsModalOpen(false)}>
            确认
          </AnimatedButton>
        </div>
      </Modal>

      {/* Toast */}
      <Toast
        isVisible={isToastVisible}
        message="操作成功！"
        type="success"
        onClose={() => setIsToastVisible(false)}
      />
    </div>
  );
};

export default AnimationExample;
