# 前端设计升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Quartz 网站从默认样式升级为 Editorial/Magazine（杂志风）设计风格

**Architecture:** 通过覆盖 `custom.scss` 添加 CSS 变量主题系统、排版增强、组件样式、动效系统；修改 `quartz.config.ts` 配置字体和主题

**Tech Stack:** SCSS, CSS Variables, Google Fonts (Noto Serif SC + Inter), Intersection Observer API

---

## 文件结构

| 文件 | 职责 | 改动类型 |
|------|------|---------|
| `quartz/styles/custom.scss` | 所有自定义样式覆盖 | 主要修改 |
| `quartz.config.ts` | 字体、主题配置 | 配置修改 |

---

## Task 1: 配置字体系统

**Files:**
- Modify: `quartz.config.ts:22-30`

- [ ] **Step 1: 读取当前配置**

```bash
cat quartz.config.ts | head -30
```

- [ ] **Step 2: 修改字体配置**

将 `quartz.config.ts` 中的字体配置：

```typescript
theme: {
  fontOrigin: "systemFonts",
  cdnCaching: false,
  typography: {
    header: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
    body: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
    code: "SF Mono, Menlo, Consolas, monospace",
  },
```

修改为：

```typescript
theme: {
  fontOrigin: "googleFonts",
  cdnCaching: true,
  typography: {
    header: "Noto Serif SC, serif",
    body: "Inter, system-ui, -apple-system, sans-serif",
    code: "SF Mono, Menlo, Consolas, monospace",
  },
```

- [ ] **Step 3: 验证配置**

```bash
grep -A 8 "typography:" quartz.config.ts
```

Expected: 看到新的字体配置

- [ ] **Step 4: Commit**

```bash
git add quartz.config.ts
git commit -m "config: switch to Google Fonts (Noto Serif SC + Inter)"
```

---

## Task 2: 定义 CSS 变量主题系统

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 读取当前 custom.scss**

```bash
cat quartz/styles/custom.scss
```

- [ ] **Step 2: 添加 CSS 变量主题系统**

在 `quartz/styles/custom.scss` 文件顶部添加：

```scss
/* ============================================
   CSS 变量主题系统
   ============================================ */
:root {
  /* 主色调 - 蓝灰色系 */
  --primary: #284b63;
  --primary-light: #3a6a8a;
  --primary-dark: #1a3446;
  
  /* 金色点缀 */
  --accent: #c9a84c;
  --accent-light: #d4b86a;
  --accent-dark: #b0903a;
  
  /* 中性色 */
  --bg: #faf8f8;
  --bg-secondary: #f5f3f3;
  --text: #2b2b2b;
  --text-secondary: #4e4e4e;
  --text-muted: #8a8a8a;
  --border: #e5e5e5;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  
  /* 过渡 */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 400ms ease;
  
  /* 间距 */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
}
```

- [ ] **Step 3: 验证语法**

```bash
npx quartz build --directory vault-content 2>&1 | head -20
```

Expected: 构建成功，无 SCSS 语法错误

- [ ] **Step 4: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: add CSS variables theme system"
```

---

## Task 3: 增强排版样式

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 添加排版增强样式**

在 `quartz/styles/custom.scss` 的 CSS 变量之后添加：

```scss
/* ============================================
   排版增强
   ============================================ */

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {
  letter-spacing: 0.02em;
  line-height: 1.3;
  margin-top: var(--space-xl);
  margin-bottom: var(--space-md);
}

h1 {
  font-size: 2.5rem;
  margin-top: 0;
}

h2 {
  font-size: 1.8rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: var(--space-sm);
}

h3 {
  font-size: 1.4rem;
}

/* 段落 */
p {
  line-height: 1.7;
  margin-bottom: var(--space-md);
  color: var(--text-secondary);
}

/* 链接 */
a {
  color: var(--primary);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color var(--transition-fast);
}

a:hover {
  border-bottom-color: var(--accent);
}

/* 引用块 */
blockquote {
  border-left: 4px solid var(--accent);
  padding: var(--space-md) var(--space-lg);
  margin: var(--space-lg) 0;
  background: var(--bg-secondary);
  border-radius: 0 4px 4px 0;
}

blockquote p {
  margin-bottom: 0;
  color: var(--text);
  font-style: italic;
}

/* 列表 */
ul, ol {
  padding-left: var(--space-lg);
  margin-bottom: var(--space-md);
}

li {
  margin-bottom: var(--space-xs);
  line-height: 1.7;
}

/* 分隔线 */
hr {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  border: none;
  margin: var(--space-xl) 0;
}
```

- [ ] **Step 2: 验证构建**

```bash
npx quartz build --directory vault-content 2>&1 | tail -5
```

Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: enhance typography with serif headers and improved spacing"
```

---

## Task 4: 增强代码块和表格样式

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 添加代码块样式**

在 `quartz/styles/custom.scss` 中添加：

```scss
/* ============================================
   代码块样式
   ============================================ */

/* 代码块 */
pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: var(--space-lg);
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: var(--space-md) 0;
  box-shadow: var(--shadow-sm);
}

pre code {
  background: transparent;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
  color: inherit;
}

/* 行内代码 */
code {
  font-family: var(--code-font);
  background: var(--bg-secondary);
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
  color: var(--primary-dark);
}

/* ============================================
   表格样式
   ============================================ */

table {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-md) 0;
  box-shadow: var(--shadow-sm);
  border-radius: 8px;
  overflow: hidden;
}

th, td {
  padding: var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--border);
}

th {
  font-weight: 600;
  color: var(--primary);
  background: var(--bg-secondary);
}

tbody tr:hover {
  background: var(--bg-secondary);
}

tbody tr:last-child td {
  border-bottom: none;
}
```

- [ ] **Step 2: 验证构建**

```bash
npx quartz build --directory vault-content 2>&1 | tail -5
```

Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: enhance code blocks and tables"
```

---

## Task 5: 增强组件样式

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 添加卡片组件样式**

在 `quartz/styles/custom.scss` 中添加：

```scss
/* ============================================
   卡片组件样式
   ============================================ */

/* 通用卡片 */
.card, .backlinks-card, .recent-notes-card {
  background: white;
  border-radius: 8px;
  padding: var(--space-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  transition: all var(--transition-normal);
}

.card:hover, .backlinks-card:hover, .recent-notes-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
  border-color: var(--accent);
}

/* 标签 */
.tag {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-right: var(--space-xs);
  transition: background var(--transition-fast);
}

.tag:hover {
  background: var(--accent);
  color: white;
}

/* ============================================
   搜索框样式
   ============================================ */

.search-input, #search-input {
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  transition: all var(--transition-fast);
  width: 100%;
}

.search-input:focus, #search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.2);
}

/* ============================================
   导航和 Explorer 样式
   ============================================ */

/* Explorer 树状线条 */
.explorer-node {
  border-left: 1px solid var(--border);
  padding-left: var(--space-md);
  margin-left: var(--space-sm);
}

.explorer-node:hover {
  border-left-color: var(--accent);
}

/* 悬停状态 */
.explorer-item:hover, .nav-link:hover {
  color: var(--accent);
  background: var(--bg-secondary);
  border-radius: 4px;
}
```

- [ ] **Step 2: 验证构建**

```bash
npx quartz build --directory vault-content 2>&1 | tail -5
```

Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: enhance component styles (cards, search, explorer)"
```

---

## Task 6: 添加动效系统

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 添加动效样式**

在 `quartz/styles/custom.scss` 中添加：

```scss
/* ============================================
   动效系统
   ============================================ */

/* 淡入动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 应用动画 */
.article-card, .backlinks-card, .recent-notes-card {
  animation: fadeIn var(--transition-slow) ease-out forwards;
}

/* 延迟动画 */
.delay-1 { animation-delay: 100ms; }
.delay-2 { animation-delay: 200ms; }
.delay-3 { animation-delay: 300ms; }

/* 滚动触发动画（配合 Intersection Observer） */
.animate-on-scroll {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

.animate-on-scroll.visible {
  opacity: 1;
  transform: translateY(0);
}

/* 按钮悬停效果 */
.btn, button {
  transition: all var(--transition-fast);
}

.btn:hover, button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* 链接悬停效果 */
a {
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

/* 图片悬停效果 */
img {
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
  border-radius: 8px;
}

img:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-lg);
}

/* 选中文本高亮 */
::selection {
  background: rgba(201, 168, 76, 0.3);
  color: var(--text);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--gray);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--primary);
}
```

- [ ] **Step 2: 验证构建**

```bash
npx quartz build --directory vault-content 2>&1 | tail -5
```

Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: add animation system and micro-interactions"
```

---

## Task 7: 添加滚动动画脚本

**Files:**
- Modify: `quartz/styles/custom.scss`

- [ ] **Step 1: 添加滚动动画初始化脚本**

在 `quartz/styles/custom.scss` 末尾添加：

```scss
/* ============================================
   滚动动画初始化（需配合 JS）
   ============================================ */

/* 为 Quartz 组件添加动画类 */
.page-header, .article-title {
  animation: fadeIn var(--transition-slow) ease-out forwards;
}

.content-meta, .tag-list {
  animation: fadeIn var(--transition-slow) ease-out forwards;
  animation-delay: 100ms;
}

.toc, .backlinks {
  animation: fadeIn var(--transition-slow) ease-out forwards;
  animation-delay: 200ms;
}

/* 移动端优化 */
@media (max-width: 768px) {
  :root {
    --space-xl: 1.5rem;
    --space-2xl: 2rem;
  }
  
  h1 { font-size: 2rem; }
  h2 { font-size: 1.5rem; }
  h3 { font-size: 1.2rem; }
}
```

- [ ] **Step 2: 验证最终构建**

```bash
npx quartz build --directory vault-content 2>&1 | tail -10
```

Expected: 构建成功，无错误

- [ ] **Step 3: 本地预览测试**

```bash
npx quartz build --serve --directory vault-content &
sleep 5
echo "预览地址: http://localhost:8080"
```

- [ ] **Step 4: Commit**

```bash
git add quartz/styles/custom.scss
git commit -m "style: add scroll animations and mobile optimizations"
```

---

## Task 8: 最终验证和清理

**Files:**
- None (verification only)

- [ ] **Step 1: 完整构建测试**

```bash
npm ci && npx quartz build --directory vault-content
```

Expected: 构建成功，无错误

- [ ] **Step 2: 检查生成的 CSS**

```bash
grep -r "var(--accent)" public/ | head -5
```

Expected: 看到 CSS 变量被正确使用

- [ ] **Step 3: 检查字体加载**

```bash
grep -r "Noto Serif SC" public/ | head -3
```

Expected: 看到字体配置

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete frontend design upgrade (Editorial/Magazine style)"
```

---

## 验证清单

- [ ] 构建成功：`npm ci && npx quartz build --directory vault-content`
- [ ] 字体加载：Noto Serif SC + Inter 正确加载
- [ ] 配色正确：金色点缀 (#c9a84c) 出现在标签、链接悬停等位置
- [ ] 动效正常：卡片悬停有阴影和上移效果
- [ ] 移动端兼容：响应式布局正常
- [ ] 功能完整：搜索、Explorer、Graph 等组件正常工作

---

## 风险和回退

| 风险 | 影响 | 回退方案 |
|------|------|---------|
| 字体加载慢 | 首屏性能 | 改回 `fontOrigin: "systemFonts"` |
| CSS 变量不兼容 | 旧浏览器 | 提供静态回退值 |
| 样式冲突 | 组件异常 | 删除 `custom.scss` 中的对应样式 |
