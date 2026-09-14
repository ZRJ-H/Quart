# 公开仓库安全运维

最后复核：2026-09-14 (Asia/Shanghai)

## 仓库控制措施

仓库现已定义以下失败关闭控制措施：

- 浏览器来源：使用精确白名单，当前为 `https://zrj-h.github.io`；CORS 不使用通配符。
- 请求边界：仅接受 JSON，请求体上限为 8 KiB，查询上限为 500 个字符，结果上限为 15 条，并对筛选器 schema 设置边界。
- 突发流量控制：Cloudflare Rate Limiting binding `SEARCH_RATE_LIMITER`，每个 Worker 位置和客户端键每 60 秒最多 10 个请求。
- 付费 AI 硬上限：Durable Object binding `AI_BUDGET`，每个 UTC 日最多保留 100 次，migration tag 为 `v1`。
- 单请求上限：源上下文最多 48 KiB，输出 token 最多 2,000 个，provider 超时时间为 30 秒。
- 响应策略：no-store、nosniff、no-referrer、受限的 Permissions Policy、精确 CORS 和 API CSP。
- 静态站点策略：CSP meta 策略为每个必需的内联脚本设置 hash；`script-src` 不包含 `unsafe-inline` 或 `unsafe-eval`。
- 内容安全：生成的 Markdown 会按上下文编码，URL host 会被验证，原始 HTML 会在 `rehypeRaw` 之后净化，搜索 UI 中的值会被转义。
- 供应链：Actions 使用经验证的完整 commit SHA；CODEOWNERS 将安全关键路径分配给 `@ZRJ-H`。
- 依赖门禁：在 2026-09-14 更新后，生产环境和完整 npm 审计均报告零漏洞。

Cloudflare Rate Limiting 是突发流量控制，不是全局计费上限。Durable Object 是权威的每日付费 provider 上限。

## 上线前的外部状态快照

2026-09-14 的 GitHub 公共 API 快照：

- 仓库：`ZRJ-H/Quart`，公开，默认分支为 `main`。
- `main.protected`：`false`。
- 仓库规则集响应：`[]`。
- 最近检查的成功 deployment run：`34824900802`。
- 该 run 中成功的 job 名称：`build` 和 `deploy`。
- 每日采集 workflow 会将生成内容直接写入 `main`；除非先添加明确经过评审的自动化 bypass 或基于 PR 的发布流程，否则全面的“pull request required”规则会破坏该自动化。

本地 Wrangler 4.131.2 dry-run 已成功解析 `AI_BUDGET`、`WIKI_DATA`、`VECTORIZE`、`SEARCH_RATE_LIMITER`、所有非秘密限制参数以及 Durable Object migration。由于没有可用的 `CLOUDFLARE_API_TOKEN`，本工作站会话无法读取远程 Cloudflare 状态。这意味着仓库配置已就绪，但在授权部署得到验证之前，不得声称新的 Worker 控制已启用。

## 生产上线记录

完成于 2026-09-14 (Asia/Shanghai)：

- 安全发布 commit：`7f35b52ce1e83414234cff6381e4857990757d40`。
- 初始 push deployment：Actions run `34846322725`，成功；Cloudflare 同步步骤和 Pages deployment 均已运行。
- 每日采集兼容性检查：Actions run `34846322679`，成功，包括它对 `main` 的正常快进 push。
- 最终内容 commit：`7739e057bb766fe4d8fa70c4aac9d11cd6bc1e9b`。
- 最终 workflow-run deployment：Actions run `34846569585`，成功；Pages deployment `6437567214` 已发布 `https://zrj-h.github.io/Quart/`。
- 安全内容上线 Worker version：`d1917cd2-b075-4797-bc06-753a1106719b`。
- 回滚 Worker version：`9d9bb744-4878-4226-89b9-f8b3833f77f2`。
- 已启用的仓库规则集：`23305251` (`Protect main history`)，仅作用于 `refs/heads/main`，包含 `deletion` 和 `non_fast_forward` 规则。
- 生产冒烟检查已通过：无 Origin 的 health、精确允许的 Origin、被拒绝的外部 Origin、允许的 preflight、已移除的 `/api/debug`、被拒绝的 `debug` 请求字段，以及不含 `unsafe-inline` 或 `unsafe-eval` 的静态站点 CSP。

由于本工作站没有直接 Cloudflare 凭据或隔离的 staging binding，未部署独立的 staging Worker。因此，生产发布在本地测试、依赖审计、完整 Quartz 构建和 Wrangler dry-run 之后，使用了经评审的 GitHub workflow。不要仅为了证明拒绝机制就对生产环境的每日预算执行破坏性测试，也不要强制 push 以测试保护；当可以使用隔离的 staging namespace 时，应在其中验证这些控制。

## 需要审批的生产上线

生产部署前：

1. 获取 Cloudflare 只读快照：当前 deployment/version ID、binding、route、migration、observability 以及回滚目标。不要输出 secret 值。
2. 部署到 staging Worker 或使用独立限流和 Durable Object 资源的临时测试环境。
3. 验证精确允许/拒绝的 Origin、preflight、8 KiB 拒绝、10/60 突发流量拒绝、每日预算拒绝、UTC 日切换、30 秒超时、通用 provider 错误、SSE header 和结构化脱敏日志。
4. 通过现有的已评审 GitHub workflow 部署。记录新的 Worker version ID，并保留上一个 version 作为回滚目标。
5. 验证线上站点的正常搜索、无结果搜索、CSP console、移动端搜索、生成页面和 Worker health 响应。

回滚：

1. 停止后续发布。
2. 通过 Wrangler 的 rollback 命令使用已记录的上一个 Worker version。
3. 重新运行允许/拒绝 Origin 和正常搜索冒烟测试。
4. 如果静态渲染发生回归，通过正常仓库 workflow revert 发布 commit，并重新部署 Pages。

## 日志和告警

日志使用有界的 JSON 事件，并排除原始 IP 地址、查询、请求体、prompt、检索文本、authorization header、token、provider 响应体、stack trace 和 exception message。

部署后，针对以下情况创建并演练告警：

- 持续的 `origin_denied` 或无效输入激增；
- `search_rate_limited` 激增；
- 每日 AI 预算达到 80%、95% 以及耗尽；
- `deepseek_stream_failed` 和 Worker 5xx 错误；
- 缺失限流或预算 binding。

对单次拒绝保持静默，仅转发有意义的持续变化或故障。

## GitHub 规则集方案

在某个 required-check 名称已成功用于一个 pull request 之前，不要启用该名称。观察到的 `build` 和 `deploy` job 来自 push deployment；`deploy` 可能不适合用作合并要求。

安全上线：

1. 首先为 `main` 启用删除保护和非快进/force-push 保护。
2. 决定每日采集是使用经评审的 bypass，还是打开自动 pull request。
3. 在临时分支/规则集上测试所选的发布流程。
4. 然后要求 pull request、CODEOWNERS 路径的 owner 审核、解决对话、驳回过期批准，并仅要求已在 pull request 上验证的检查。
5. 立即使用真实的测试 pull request 进行验证，并记录 Ruleset ID。

## 常规验证

每次安全敏感型发布前运行：

```text
npm test
python -m unittest discover -s tests -p "test_*.py"
npm audit --omit=dev --audit-level=high --registry=https://registry.npmjs.org
npm audit --audit-level=high --registry=https://registry.npmjs.org
npx quartz build --directory content
npx wrangler deploy --dry-run --config worker/wrangler.toml
git diff --check
```
