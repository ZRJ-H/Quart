# MEMORY.md - Quartz 网站活跃记忆

## 项目状态

- 当前阶段: 生产运行
- 活跃分支: main
- 网站 URL: https://zrj-h.github.io/Quart/
- Worker URL: https://doge-wiki-search.zstufjj2004.workers.dev
- 构建状态: 正常（每日内容采集成功后自动部署 GitHub Pages）

## Decision Log

### 2026-09-11: 每日知识采集与分层摘要

- **问题**: AI 科技、时政、AI 论文和 Hacker News 长期无新数据，7 天内容过滤后栏目入口直接 404。
- **方案**: 统一 Python 采集管道，每日 08:30（Asia/Shanghai）抓取公开源；同日不足时最多回退 48 小时，任一栏目未达最低数量则整批不写入。
- **数量**: AI 科技 8、时政 8、AI 论文 5、Hacker News 8；GitHub Trending 延续 25 条。
- **摘要规范**: 每栏前 3 条 250–400 字，其余 80–150 字；输出 3 条趋势判断并明确区分事实与推断；论文补充问题、方法、结果、局限、工程价值，HN 补充讨论焦点。
- **证据约束**: 模型只可基于采集到的标题、正文摘要、作者、指标和评论生成；如配置 DeepSeek/GO 则生成中文结构化摘要，否则使用满足同等阅读预算的 `evidence-only` 摘要；随后由 08:45 的 Codex 定时任务做中文精修。
- **容错**: RSS 源并发抓取且单源失败不影响栏目；arXiv API 失败时并发回退到 cs.AI、cs.LG、cs.CL 官方 RSS；HN 仅为最终入选项目抓评论。
- **部署**: `Collect Daily Knowledge` 一次提交所有当天内容，成功完成后由 `workflow_run` 触发 GitHub Pages 部署。

### 2026-06-16: 搜索质量优化 + 部署管道修复

- **背景**: 线上搜索对中文连写词/时间词大面积 0 召回；排查发现部署管道根本没更新搜索 worker
- **搜索优化**:
  - 中文分词 `tokenize()`: 英文/数字段整体 + 中文段 bigram 滑窗，修复「AI项目」「claude动态」连写 0 召回
  - 时间意图: 今日/最新/最近/本周 → 最近度加权（非严格等于），修复「今日」0 召回
  - `buildPrompt` 改用 KV 完整正文（~800字）替代恒为 undefined 的 30 字 summary
  - 内嵌同义词词典 `worker/synonyms.json`（AI/人工智能、Claude/Anthropic 等），KV 可叠加
  - `reference_count` 按反向链接统计（build-wiki-index 两遍扫描），激活质量排序
  - category 缺失回退到 type；源卡片摘要改用 KV 正文片段（120字）
  - 前端: 空结果显示热门主题建议 + 补全分类图标
- **部署管道 4 个隐藏 bug（关键，易复踩）**:
  1. 根目录 `wrangler.jsonc`(jackyzha0-quartz，Quartz 模板残留)被 git 跟踪后，CI 的 `wrangler deploy` 一直部署它而非 worker/wrangler.toml 的 doge-wiki-search → **删除根 wrangler.jsonc**
  2. `upload-to-kv.py` 缺 `--remote`，wrangler 4.x 默认写 CI 本地模拟 KV → 加 `--remote`
  3. KV 免费版每日写入额度(code 10048)失败 + `set -e` 会阻断后续 worker 部署 → upload-to-kv 把额度类错误降级为警告
  4. 前端建议 fetch `/worker/wiki-index-light.json` 在 /Quart/ 基路径下 404 → 改为站点根候选路径
- **约束**: deploy.yaml 是 workflow 文件，OAuth/gh token 无 workflow scope 无法 push；上述修复均走非 workflow 文件
- **影响范围**: worker/index.js, worker/synonyms.json, scripts/build-wiki-index.py, scripts/upload-to-kv.py, quartz/components/scripts/search-ai.inline.js, 删除根 wrangler.jsonc

### 2026-06-06: 前端设计升级（Editorial/Magazine 风格）

- **问题**: 默认 Quartz 样式较保守，缺乏视觉特色
- **方案**: 采用 Editorial/Magazine（杂志风）设计风格，渐进式增强
- **设计规范**:
  - 配色：蓝灰色系 + 金色点缀 (#c9a84c)
  - 排版：Noto Serif SC（标题）+ Inter（正文）
  - 动效：微妙悬停 + 滚动淡入 + 平滑过渡
  - 质感：阴影 + 圆角 + 呼吸感间距
- **改动范围**:
  - `quartz.config.ts`: 字体配置（Google Fonts）
  - `quartz/styles/custom.scss`: CSS 变量主题系统、排版、组件样式、动效
- **实施方式**: Subagent-Driven Development（8 个任务，每个任务含规范审查 + 代码质量审查）
- **验证**: 构建成功，CSS 变量正确使用，字体加载正常

### 2026-06-03: Worker KV 存储架构升级

- **问题**: Worker 内嵌索引已达 706KB（接近 1MB 限制），无法继续扩展
- **方案**: 将完整数据存储到 Cloudflare KV，Worker 仅保留轻量索引（名称+摘要+标签）
- **架构变更**:
  - 轻量索引 (`wiki-index-light.json`): ~200KB，内嵌在 Worker 中用于关键词匹配
  - 完整数据 (`wiki-data-full.json`): 存储在 KV 中，搜索时按需读取
  - 关联页面查找: 从搜索结果中提取 `[[链接]]`，自动扩展上下文
- **影响范围**: worker/index.js, worker/wrangler.toml, scripts/deploy-worker.sh, scripts/upload-to-kv.py

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

### [2026-06-06] 前端设计升级（Editorial/Magazine 风格）

- 完成:
  - 配置字体系统（Google Fonts: Noto Serif SC + Inter）
  - 定义 CSS 变量主题系统（颜色、阴影、过渡、间距）
  - 增强排版样式（标题、段落、链接、引用块、列表、分隔线）
  - 增强代码块和表格样式
  - 增强组件样式（卡片、标签、搜索框、Explorer）
  - 添加动效系统（淡入动画、悬停效果、滚动触发）
  - 添加滚动动画脚本和移动端优化
  - 最终验证和清理
- 文件变更:
  - `quartz.config.ts`: 字体配置
  - `quartz/styles/custom.scss`: 所有自定义样式
  - `design-preview.html`: 设计预览文件
  - `docs/superpowers/specs/2026-06-06-frontend-design-upgrade.md`: 设计规范
  - `docs/superpowers/plans/2026-06-06-frontend-design-upgrade.md`: 实施计划
- 提交记录:
  - `config: switch to Google Fonts (Noto Serif SC + Inter)`
  - `style: add CSS variables theme system`
  - `style: enhance typography with serif headers and improved spacing`
  - `style: enhance code blocks and tables`
  - `style: enhance component styles (cards, search, explorer)`
  - `style: add animation system and micro-interactions`
  - `style: add scroll animations and mobile optimizations`
  - `feat: complete frontend design upgrade (Editorial/Magazine style)`

### [2026-06-03] Worker KV 存储架构升级

- 完成:
  - 实现轻量索引 + KV 存储架构
  - 添加关联页面查找功能（从 `[[链接]]` 提取关联页面）
  - 添加 KV 调试端点 (`/api/debug`)
  - 更新 `.gitignore` 忽略生成的数据文件
  - 部署脚本集成 KV 上传步骤

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
- KV 存储架构: 轻量索引 + KV 完整数据 — ✅
- 前端设计升级: Editorial/Magazine 风格 — ✅

### [2026-06-13] 基础设施清理

- **背景**: 项目重构 Phase 3，清理残留测试目录和旧数据文件
- 删除 `quartz-test/` 目录（31MB 测试构建残留）
- 删除 `worker/kv-bulk-upload.json`（1.1MB 旧 KV 批量上传文件）
- 新建 `refactor/infra-cleanup` 分支
- 关联仓库: Obsidian `refactor/project-restructure`（Phase 1-4 重构）

### [2026-09-11] GitHub Pages 自动部署链路修复

- **问题**: 内容采集工作流通过默认 `GITHUB_TOKEN` 推送提交，这类提交不会再次触发 `push` 部署工作流，Pages 因而没有随每日内容更新。
- **方案**: `deploy.yaml` 监听 `Collect GitHub Trending` 的成功 `workflow_run`，并补齐 `configure-pages`、`.nojekyll` 与当前 Pages action 版本。
- **验证**: 工作流回归测试 2/2 通过；本地生成 4539 条轻量索引并完成 Quartz 生产构建，Pages 四项必需产物齐全。
- **验证**: 仓库已公开并启用 GitHub Pages；Actions 运行 #34577937532 成功，线上地址为 https://zrj-h.github.io/Quart/。
### [2026-09-11] 每日知识自动采集与摘要重构

- 完成四类缺失数据的真实来源采集、48 小时回退、数量门槛和原子写入。
- 完成分层详细摘要、论文专用字段、HN 讨论焦点、事实/判断分离和模型输出校验。
- GitHub Models 推理端点已返回 410，未采用会计入个人 Copilot 席位的 CLI；无模型降级版加入长度预算与长文本截断，并由 Codex 定时任务负责中文精修。
- 每日工作流合并采集、测试、周报与一次性提交，时间为北京时间 08:30。
- 首页周报入口改为稳定目录页，避免继续指向过期周次。
- arXiv 增加 API→官方 RSS 容错；RSS 与 HN 抓取并发化以限制运行时间。
