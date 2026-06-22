# 输入框组件 (Input)

> 组件类型: 表单元素
> 最后更新: 2026-06-19

---

## 概述

输入框是用户向系统提供信息的主要方式。PHOENIX 输入系统注重清晰的标签、及时的反馈和无障碍体验。

---

## 变体 (Variants)

### 1. 类型 (Type)

| 变体 | 用途 | 特殊行为 |
|------|------|----------|
| **Text** | 单行文本 | 标准输入 |
| **Password** | 密码输入 | 显示/隐藏切换 |
| **Email** | 邮箱输入 | 自动验证格式 |
| **Number** | 数字输入 | 增减按钮 |
| **Search** | 搜索框 | 清除按钮 |
| **Textarea** | 多行文本 | 可调整高度 |

### 2. 尺寸 (Size)

| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| **Small** | 32px | 8px 12px | 14px |
| **Medium** | 40px | 12px 16px | 14px |
| **Large** | 48px | 16px 20px | 16px |

### 3. 状态 (State)

| 状态 | 视觉特征 |
|------|----------|
| **Default** | 边框: --border-default |
| **Hover** | 边框: --border-hover |
| **Focus** | 边框: --border-focus, 焦点环 |
| **Filled** | 显示清除按钮 |
| **Error** | 边框: --color-error, 错误信息 |
| **Disabled** | 背景变暗，禁止光标 |
| **Readonly** | 背景变暗，允许选择 |

---

## 设计规范

### 基础样式

```
背景: --bg-input
边框: 1px solid --border-default
圆角: --radius-md
文字: --text-primary
占位符: --text-tertiary
```

### 焦点状态

```css
.input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--color-accent-500 / 20%);
  outline: none;
}
```

### 错误状态

```css
.input--error {
  border-color: var(--color-error);
}

.input--error:focus {
  box-shadow: 0 0 0 3px var(--color-error / 20%);
}
```

---

## 标签 (Label)

### 规范

- 标签必须始终可见（不使用浮动标签）
- 标签在输入框上方
- 必填字段用红色星号标记
- 标签文字简洁明确

```html
<div class="form-field">
  <label class="form-label" for="email">
    邮箱地址 <span class="required">*</span>
  </label>
  <input class="input" type="email" id="email" required />
</div>
```

### 标签样式

```css
.form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.form-label .required {
  color: var(--color-error);
  margin-left: var(--space-1);
}
```

---

## 帮助文本

### 帮助文本 (Help Text)

```html
<div class="form-field">
  <label class="form-label" for="password">密码</label>
  <input class="input" type="password" id="password" />
  <p class="form-help">至少 8 个字符，包含大小写字母和数字</p>
</div>
```

### 错误文本 (Error Text)

```html
<div class="form-field form-field--error">
  <label class="form-label" for="email">邮箱</label>
  <input class="input input--error" type="email" id="email" />
  <p class="form-error">请输入有效的邮箱地址</p>
</div>
```

### 样式

```css
.form-help {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}

.form-error {
  font-size: var(--text-xs);
  color: var(--color-error);
  margin-top: var(--space-1);
}
```

---

## 输入框组合

### 带图标

```html
<div class="input-group">
  <span class="input-icon">
    <svg><!-- search icon --></svg>
  </span>
  <input class="input input--with-icon" type="search" placeholder="搜索..." />
</div>
```

### 带按钮

```html
<div class="input-group">
  <input class="input" type="email" placeholder="输入邮箱" />
  <button class="button button--primary">订阅</button>
</div>
```

---

## Textarea

### 规范

- 最小高度: 120px
- 可调整高度: `resize: vertical`
- 字符计数器（可选）

```html
<div class="form-field">
  <label class="form-label" for="bio">简介</label>
  <textarea
    class="input textarea"
    id="bio"
    rows="4"
    maxlength="200"
  ></textarea>
  <div class="form-footer">
    <span class="form-help">简要介绍自己</span>
    <span class="char-count">0/200</span>
  </div>
</div>
```

---

## 无障碍

1. **标签关联**: 每个输入框必须有 `<label>` 或 `aria-label`
2. **错误提示**: 使用 `aria-describedby` 关联错误信息
3. **必填标记**: 使用 `required` 属性和 `aria-required="true"`
4. **禁用状态**: 使用 `disabled` 属性
5. **焦点顺序**: 保持自然的 Tab 顺序

```html
<div class="form-field form-field--error">
  <label class="form-label" for="email">
    邮箱 <span class="required">*</span>
  </label>
  <input
    class="input input--error"
    type="email"
    id="email"
    required
    aria-required="true"
    aria-describedby="email-error"
  />
  <p class="form-error" id="email-error" role="alert">
    请输入有效的邮箱地址
  </p>
</div>
```

---

## Figma 组件结构

```
Input/
├── Text/
│   ├── Small/
│   │   ├── Default
│   │   ├── Hover
│   │   ├── Focus
│   │   ├── Filled
│   │   ├── Error
│   │   └── Disabled
│   ├── Medium/
│   └── Large/
├── Password/
├── Email/
├── Number/
├── Search/
└── Textarea/
```

---

## 最佳实践

1. **明确的标签**: 避免使用占位符作为标签
2. **即时验证**: 在失焦时验证，而非输入时
3. **清晰的错误信息**: 说明问题和解决方法
4. **合适的输入类型**: 使用 `type="email"` 等语义化类型
5. **自动完成**: 为常见字段启用 `autocomplete`
