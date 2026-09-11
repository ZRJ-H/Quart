# GitHub Pages 自动知识库设计

## 目标

把现有 Quartz 知识库改造成由 GitHub Actions 自动采集、生成索引、构建并发布到 GitHub Pages 的网站，同时保留 Cloudflare Worker 提供的 DeepSeek 流式问答。网站在 Worker 未配置或不可用时必须自动退化为静态搜索，不能阻断普通浏览。

## 部署架构

GitHub Actions 是唯一的自动化调度入口。工作流在推送、手动触发和每日定时触发时安装 Node.js 22 与 Python，运行五类日报爬虫，在每周日生成周报，按 30 天策略清理日报，生成静态搜索索引，构建 Quartz，再通过 GitHub 官方 Pages actions 发布 `public/`。

GitHub Pages 只承载静态文件，包括 Quartz 页面、`wiki-index.json` 完整索引和 `wiki-index-light.json` 轻量索引。页面使用轻量索引完成搜索建议和 Worker 故障时的本地搜索。Cloudflare Worker 从 Pages 获取完整索引，完成检索和结果筛选，再把检索上下文发送给 DeepSeek，以 SSE 返回来源与回答。

现有 Express、SQLite、Docker 文件保留，作为本地或自托管兼容路径，但 GitHub Pages 发布不依赖它们。

## 配置边界

- `SITE_DOMAIN`：Quartz 的规范站点地址，由 GitHub Actions 根据仓库所有者和仓库名自动推导，也允许自定义域名覆盖。
- `AI_SEARCH_ENDPOINT`：构建时注入前端的完整搜索端点，例如 `https://wiki-search.example.workers.dev/api/search`。为空时启用纯静态模式。
- `DEEPSEEK_API_KEY`：只保存在 Cloudflare Worker secret 和可选的 GitHub Actions secret 中，不进入页面、索引或仓库。
- `SITE_ORIGIN`：Worker 允许访问的 GitHub Pages 或自定义域名来源。
- `INDEX_URL`：Worker 获取 `wiki-index.json` 的绝对 HTTPS 地址。

## 静态索引

扩展现有 Python 索引构建器，使一次解析同时产生 SQLite（兼容本地服务）、完整 JSON 和轻量 JSON。完整索引包含受限长度的正文，用于 Worker 检索；轻量索引仅包含名称、分类、标签、摘要、更新时间、引用数和可访问页面路径。

索引中保留结构化 wikilink 列表，避免现有流程在清理正文后丢失关联信息。构建应使用临时文件后原子替换，避免生成半成品。

## 搜索界面

前端组件接收完整的 `AI_SEARCH_ENDPOINT`，不再自行重复拼接 `/api/search`。索引 URL由 Quartz 当前页面相对站点根生成，兼容用户主页仓库、自定义域名和 `/repository` 子路径。

搜索流程：先加载轻量索引；提交查询时优先请求 Worker；未配置端点、网络失败、超时或 Worker 返回错误时，立即用本地索引按标题、标签、分类和摘要评分，并显示可点击来源卡片。所有进入 `innerHTML` 的标题、摘要、分类和历史查询必须转义。

## Worker API

Worker 使用 ES module `fetch` handler，仅支持 `POST /api/search`、`GET /api/health` 和 CORS 预检。它验证请求来源、正文大小、查询长度和 JSON 结构，从 Pages 拉取并短时缓存完整索引，返回来源事件后代理 DeepSeek 的流式响应。

检索评分必须允许正文命中，不能沿用会丢弃低 BM25 数值的固定 8 分阈值。相关页面直接使用索引中的 `links` 字段扩展。Worker 不暴露索引重载接口，也不向客户端返回上游错误正文或密钥。

## 自动更新与发布

工作流使用 `concurrency` 防止并发发布。定时任务按 UTC 配置为北京时间凌晨执行。生成的 Markdown 变化由机器人提交回当前默认分支，以便后续周报和历史页面基于持续数据；机器人提交不会通过默认 `GITHUB_TOKEN` 递归触发新工作流。随后使用 `configure-pages`、`upload-pages-artifact` 和 `deploy-pages` 发布当前构建。

单个爬虫失败不阻止其他数据源和现有内容发布，但索引构建、Quartz 构建或 Pages 上传失败必须使工作流失败。日志不得输出密钥。

## 测试与验收

- Python 单元测试验证 Markdown 切分、wikilink 保留、完整/轻量索引字段和原子输出。
- Node 单元测试验证 Worker 路由、CORS、输入校验、正文搜索、关联扩展和 DeepSeek SSE 转发。
- Quartz 测试验证端点不重复拼接、子路径索引 URL和静态回退评分。
- 运行现有 TypeScript、Prettier 和 Quartz 测试。
- 用临时内容目录完成一次不访问外网的索引构建，并完成 Quartz 生产构建。
- 验证输出包含 `index.html`、`static/contentIndex.json`、`wiki-index.json`、`wiki-index-light.json` 和 `.nojekyll`。

## 非目标

- 不在 GitHub Pages 中运行 Express、SQLite 或任何服务器进程。
- 不把 DeepSeek 密钥放入浏览器。
- 不引入 D1、KV、Vectorize 或额外数据库。
- 不重写 Quartz 框架或现有视觉主题。
