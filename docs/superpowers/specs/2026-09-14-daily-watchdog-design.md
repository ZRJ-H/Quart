# 每日知识库 Cloudflare 守望器设计

## 背景与目标

GitHub Actions 的 `schedule` 事件在 2026-09-12 和 2026-09-13 分别延迟约四小时，2026-09-14 到北京时间 13:14 仍未创建运行记录。现有采集、缓存、摘要和 Pages 部署只有在工作流被触发后才会执行，因此内部容错无法处理“定时事件根本没有发生”。

本改动保留 GitHub 仓库、`Collect Daily Knowledge` 工作流和 GitHub Pages，只为现有 Cloudflare 搜索 Worker 增加独立守望功能。守望器在北京时间 11:00 和 14:00 检查当天四个日报页面；页面缺失且没有采集任务正在运行时，通过 GitHub API 触发原工作流。正常情况下不写仓库、不调用模型，也不产生重复任务。

## 架构与数据流

1. Cloudflare Cron 在 UTC 03:00、06:00 触发现有 `doge-wiki-search` Worker 的 `scheduled` 处理器。
2. 守望器用 `Asia/Shanghai` 日期构造 AI 科技动态、时政要闻、AI 论文日报和 Hacker News 的当天 Pages URL。
3. 四个页面均返回成功时记录结构化 `healthy` 日志并结束。
4. 任一页面缺失时，读取 `Collect Daily Knowledge` 最近运行；若存在 `queued` 或 `in_progress` 任务则记录 `collection-active` 并结束。
5. 否则调用 GitHub `workflow_dispatch`，分支固定为 `main`，记录 `dispatched` 日志。
6. 原 GitHub Actions 工作流继续负责采集、摘要、提交和 Pages 部署，现有幂等逻辑避免同一天重复内容提交。

## 组件与文件

- 新增 `worker/daily-watchdog.js`：日期计算、页面检查、活动任务判断和补跑请求。逻辑通过依赖注入的 `fetch` 测试，不依赖真实网络。
- 修改 `worker/index.js`：保留现有搜索 `fetch` 处理器，新增 `scheduled` 处理器并等待守望任务完成。
- 修改 `worker/wrangler.toml`：增加两条 Cron Trigger。
- 修改 `.github/workflows/deploy.yaml`：使用现有 `CF_API_TOKEN` 部署 Worker；当仓库配置了 `WATCHDOG_GITHUB_TOKEN` 时，将它同步为 Worker 的 `GITHUB_TOKEN` secret。未配置时只发出警告，不阻断 Pages 部署。
- 新增 Node 测试：覆盖健康时不触发、页面缺失时触发、采集正在运行时不重复触发、上海日期边界和 GitHub 错误响应。
- 更新 `MEMORY.md`：记录守望时间、所需 secret 和恢复方式。

## 配置与安全

- Worker 非敏感配置：GitHub owner `ZRJ-H`、repo `Quart`、分支 `main`、工作流文件名和站点根 URL，写入 `wrangler.toml` 的变量。
- Worker 敏感配置：`GITHUB_TOKEN` 只通过 Wrangler secret 保存，不写入源码、配置或日志。
- GitHub 仓库需新增 Actions secret `WATCHDOG_GITHUB_TOKEN`，值为仅限 `ZRJ-H/Quart` 的 fine-grained personal access token；权限只需 Actions 读写。
- 日志不记录 Authorization header 或 token，只记录日期、缺失栏目、判断结果和 GitHub HTTP 状态。

## 错误处理

- 页面请求中的 404 视为缺失；其他网络或 5xx 错误视为检查失败，守望器抛错并由 Cloudflare 记录，不盲目触发。
- GitHub 运行列表解析失败时不补跑，避免在状态未知时制造重复任务。
- `workflow_dispatch` 非 204 时抛出包含状态码的错误，但不记录响应中的潜在敏感内容。
- 缺少 `GITHUB_TOKEN` 时明确失败，搜索 API 的正常请求不受影响。

## 验收标准

- 北京时间 11:00 和 14:00 存在 Cloudflare Cron Trigger。
- 四个当天页面存在时不调用 GitHub dispatch。
- 任一页面缺失且无活动采集时只发送一次正确的 `workflow_dispatch` 请求。
- 存在 `queued` 或 `in_progress` 采集时不重复触发。
- 所有新测试、原有 Python 测试、`npm test`、TypeScript 检查和 Wrangler dry-run 通过。
- 推送后 GitHub Pages 部署不受影响，Cloudflare Worker 部署成功并保留现有 `/api/health` 和搜索功能。

## 非目标

- 不把采集器迁移到 Cloudflare。
- 不改变 Markdown、摘要、缓存或 Quartz 构建机制。
- 不增加 KV、D1、队列或 Workflows。
- 不自动创建高权限 GitHub 凭证。
