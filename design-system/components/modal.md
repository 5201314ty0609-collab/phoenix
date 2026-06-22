# 弹窗组件 (Modal)

> 组件类型: 浮层元素
> 最后更新: 2026-06-19

---

## 概述

弹窗用于需要用户专注处理的任务，如确认操作、填写表单或展示详细信息。

---

## 变体 (Variants)

### 1. 类型 (Type)

| 变体 | 用途 | 特点 |
|------|------|------|
| **Dialog** | 通用对话框 | 标准弹窗 |
| **Alert** | 警示信息 | 简单确认 |
| **Drawer** | 侧边抽屉 | 从侧面滑入 |
| **Sheet** | 底部表单 | 从底部滑入（移动端） |

### 2. 尺寸 (Size)

| 尺寸 | 宽度 | 适用场景 |
|------|------|----------|
| **Small** | 400px | 确认对话框 |
| **Medium** | 560px | 表单、详情 |
| **Large** | 720px | 复杂内容 |
| **Full** | 90vw | 全屏预览 |

---

## 设计规范

### 基础弹窗

```
背景: --bg-card
边框: 1px solid --border-default
圆角: --radius-xl
阴影: --shadow-xl
最大宽度: 根据尺寸
最大高度: 85vh
```

### 遮罩层

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0% 0 0 / 60%);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

---

## 结构

```html
<div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal modal--medium">
    <div class="modal__header">
      <h2 class="modal__title" id="modal-title">确认操作</h2>
      <button class="modal__close" aria-label="关闭">
        <svg><!-- x icon --></svg>
      </button>
    </div>

    <div class="modal__body">
      <p>确定要删除这个 Agent 吗？此操作不可撤销。</p>
    </div>

    <div class="modal__footer">
      <button class="button button--secondary">取消</button>
      <button class="button button--danger">删除</button>
    </div>
  </div>
</div>
```

---

## 样式

```css
.modal {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  animation: modalEnter var(--duration-normal) var(--ease-out);
}

.modal--small { width: 400px; }
.modal--medium { width: 560px; }
.modal--large { width: 720px; }
.modal--full { width: 90vw; height: 90vh; }

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border-default);
}

.modal__title {
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.modal__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.modal__close:hover {
  background: var(--surface-tertiary);
  color: var(--text-primary);
}

.modal__body {
  padding: var(--space-6);
  overflow-y: auto;
  flex: 1;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border-default);
}

@keyframes modalEnter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```

---

## 抽屉 (Drawer)

```css
.drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 400px;
  background: var(--bg-card);
  border-left: 1px solid var(--border-default);
  box-shadow: var(--shadow-xl);
  z-index: 1001;
  animation: drawerSlideIn var(--duration-normal) var(--ease-out);
}

@keyframes drawerSlideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
```

---

## 交互规范

### 打开动画

- **弹窗**: 缩放 + 淡入，200ms
- **抽屉**: 滑入，300ms
- **遮罩**: 淡入，200ms

### 关闭方式

1. 点击关闭按钮
2. 点击遮罩层（可选）
3. 按 Escape 键
4. 完成操作后自动关闭

### 焦点管理

- 打开时焦点移至弹窗内第一个可交互元素
- 关闭时焦点返回触发元素
- Tab 键循环限制在弹窗内

---

## 无障碍

1. 使用 `role="dialog"` 和 `aria-modal="true"`
2. 提供 `aria-labelledby` 关联标题
3. 提供 `aria-describedby` 关联描述（可选）
4. 焦点陷阱在弹窗内
5. Escape 键可关闭

---

## 特殊弹窗

### 确认对话框

```html
<div class="modal modal--small">
  <div class="modal__header">
    <h2 class="modal__title">确认删除</h2>
  </div>
  <div class="modal__body">
    <p>确定要删除这个文件吗？此操作不可撤销。</p>
  </div>
  <div class="modal__footer">
    <button class="button button--secondary">取消</button>
    <button class="button button--danger">删除</button>
  </div>
</div>
```

### 表单弹窗

```html
<div class="modal modal--medium">
  <div class="modal__header">
    <h2 class="modal__title">创建 Agent</h2>
    <button class="modal__close" aria-label="关闭">×</button>
  </div>
  <div class="modal__body">
    <form>
      <div class="form-field">
        <label class="form-label">名称</label>
        <input class="input" type="text" />
      </div>
      <div class="form-field">
        <label class="form-label">描述</label>
        <textarea class="input textarea"></textarea>
      </div>
    </form>
  </div>
  <div class="modal__footer">
    <button class="button button--secondary">取消</button>
    <button class="button button--primary">创建</button>
  </div>
</div>
```

---

## Figma 组件结构

```
Modal/
├── Dialog/
│   ├── Small
│   ├── Medium
│   └── Large
├── Alert/
│   ├── Info
│   ├── Warning
│   ├── Error
│   └── Success
├── Drawer/
│   ├── Left
│   └── Right
└── Sheet/ (Mobile)
```

---

## 最佳实践

1. **谨慎使用**: 弹窗打断用户流程，非必要不使用
2. **明确目的**: 每个弹窗只有一个主要任务
3. **易于关闭**: 提供多种关闭方式
4. **内容简洁**: 避免在弹窗中放过多内容
5. **移动适配**: 小屏幕使用全屏或底部表单
