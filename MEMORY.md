# MEMORY.md - Quartz 网站活跃记忆

## 项目状态
- 当前阶段: 生产运行
- 活跃分支: main
- 网站 URL: https://fdogelover.github.io/Quart/
- Worker URL: https://doge-wiki-search.zstufjj2004.workers.dev
- 构建状态: 正常（每日 GH Actions 自动构建）

## Decision Log

### 2026-05-24: 项目记忆框架初始化
- **问题**: 缺少跨会话的记忆持久化机制，agent 每次会话上下文丢失
- **方案**: 创建 AGENTS.md + MEMORY.md
- **影响范围**: AGENTS.md, MEMORY.md

### 2026-05-23: build-wiki-index.py 编码加固
- **问题**: `wiki/entities/msitarzewski-agency-agents.md` 含非法 UTF-8 字节，构建崩溃
- **方案**: `open(..., errors="replace")` 跳过坏字符
- **影响范围**: scripts/build-wiki-index.py

### 2026-05-22: KaTeX 溢出修复 v7 (display: contents)
- **问题**: KaTeX CDN CSS `position: relative` + `white-space: nowrap` 导致长公式水平溢出
- **方案**: `.katex .base, .katex .strut { display: contents }` — 从 box tree 溶解，消除溢出
- **放弃方案**: (v1-v6) `white-space: normal`, `overflow-x: auto`, `max-width: 100%` 等均无效
- **影响范围**: quartz/styles/custom.scss

### 2026-05-20: AI 语义搜索上线
- **问题**: 262 页 wiki 内容需要可搜索入口
- **方案**: Cloudflare Worker (关键词检索 + DeepSeek API) + 首页 SearchAI 组件
- **索引**: 内嵌在 Worker 脚本中（当前 ~496KB，~400 页余量到 1MB 限制）
- **影响范围**: worker/, quartz/components/SearchAI.tsx, quartz.layout.ts, scripts/build-wiki-index.py

### 2026-05-18: 7天内容过滤
- **问题**: 网站膨胀，需自动清理过时内容
- **方案**: postinstall hook 触发 filter-old-content.py（保留 7 天）
- **影响范围**: package.json, scripts/postinstall.sh, scripts/filter-old-content.py

## Session Log

### [2026-05-24] 项目记忆层初始化
- 完成:
  - 创建 AGENTS.md + MEMORY.md
- 待办:
  - [无]

## Progress
- 构建部署: GH Actions 每日自动 + 手动触发 — OK
- AI 搜索: Worker 运行中 (DeepSeek API) — OK
- KaTeX 溢出: v7 最终修复 — OK
- 编码问题: 已加固 — OK
- 内容过滤: 7天自动清理 — OK
- Worker 自动化: 阻塞（OAuth token 无 workflow scope）— ❌
- GH Actions schedule: 未观察到定时触发事件 — ⚠️
