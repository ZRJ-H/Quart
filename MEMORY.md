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

### [2026-05-24] 方案 B：vault 结构优化 + ignorePatterns
- 完成:
  - `quartz.config.ts` ignorePatterns 新增 `.claude/`、`raw/`、`MEMORY*`、`GitHub项目档案/**`
  - 移除冗余的逐条 prompt 文件模式（已由 `templates/` 覆盖）

### [2026-05-24] Worker 搜索优化 + 自动部署
- 完成:
  - Worker 自动部署接入 deploy.yaml（CF_API_TOKEN secret）
  - 搜索 prompt 注入当前日期 + 每条结果标注 last_updated（方案 A）
  - 搜索结果按 last_updated 降序排列（方案 B）
  - 时间查询预处理：「今日/今天」直接按日期过滤，不依赖关键词匹配

### [2026-05-24] AGENTS.md 完善 + 项目自检
- 完成:
  - AGENTS.md 补充 Strategies + Skills 章节
  - 约束 #1 修正：Content API → Git Data API / Web editor
  - 约束 #3 Worker 大小更新（496KB → 706KB）
  - 约束 #6 Worker 自动化已实现 → 合并入 #1
  - 自检修复：.gitignore 缺失条目、清理 8 组 " 2" 重复目录
  - `.DS_Store`、`node_modules/`、`public/`、`quartz/.quartz-cache/` 加入 gitignore

## Progress
- 构建部署: GH Actions 每日自动 + 手动触发 — OK
- AI 搜索: Worker 运行中 (DeepSeek API) — OK
- KaTeX 溢出: v7 最终修复 — OK
- 编码问题: 已加固 — OK
- 内容过滤: 7天自动清理 — OK
- Worker 自动化: deploy.yaml + CF_API_TOKEN — ✅
