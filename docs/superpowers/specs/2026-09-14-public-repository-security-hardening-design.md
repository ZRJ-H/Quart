# 公共仓库安全加固设计

**日期：** 2026-09-14

**状态：** 仓库实现已完成；外部上线等待批准

## 目的

加固公共 Quartz 仓库及其 Cloudflare Worker，防范未经授权的 AI 费用支出、跨域滥用、钱包拒绝服务攻击、存储型 XSS、可变的 CI 依赖、存在漏洞的 npm 依赖以及薄弱的生产可观测性。本次工作在保留公共站点正常阅读体验的同时，确保 AI 搜索端点在每一个产生费用的边界都采用失败关闭策略。

## 已确认的问题

- `worker/index.js` 在普通响应和流式响应中都会发出 `Access-Control-Allow-Origin: *`，因此无法一致地限制浏览器来源。
- `/api/search` 没有入口身份验证或匿名证明边界，没有请求大小或查询大小上限，没有短窗口速率限制，并且在调用 DeepSeek 前没有跨实例的全局每日硬预算。
- `worker/wrangler.toml` 当前绑定了 KV 和 Vectorize，但没有速率限制或原子预算服务。
- `/api/debug` 可被公开访问，请求体也可以启用 `debug` 响应路径。
- `quartz/components/scripts/search-ai.inline.js` 将搜索、历史记录、模态框和 AI 回答数据赋值给 `innerHTML`。
- `scripts/daily_digest/render.py` 将 AI 和外部字段插入 Markdown。随后，Quartz 通过 `quartz/processors/parse.ts` 和 `quartz/plugins/transformers/ofm.ts` 中的 `allowDangerousHtml` 与 `rehypeRaw` 路径允许原始 HTML。
- GitHub 工作流使用可变的主版本标签引用第三方 Actions。
- 最近一次已知的 npm 审计报告了高严重性生产和开发漏洞，涉及包含 `js-yaml`、`sharp`、`ws`、`minimatch` 和 `wrangler` 的依赖链；升级前必须重新审计当前的确切依赖图。
- Worker 日志是临时拼凑的，没有定义可安全脱敏的事件契约或生产告警阈值。
- `main` 保护、Worker 部署、密钥、资源创建和告警规则均属于外部状态，无法仅通过提交仓库文件来强制实施。

## 安全模型

### 信任边界

以下输入即使此前已由本应用存储，也仍然是不可信的：

- HTTP 标头、来源、请求体、查询和客户端生成的令牌。
- 搜索索引和 KV 记录。
- DeepSeek 输出。
- GitHub Trending 和其他外部采集的数据。
- 生成的 Markdown 和本地浏览器历史记录。

DeepSeek API 密钥、Cloudflare 绑定状态、授权或证明令牌以及预算计数器均为服务端机密状态。任何密钥都不得嵌入 Quartz 的静态浏览器包中。

### 公共访问和身份验证

CORS 是浏览器响应策略，而不是身份验证。精确的 Origin 强制校验可减少浏览器滥用，但无法阻止脚本或直接 HTTP 客户端。因此，选定的仓库范围实现了适用于公共静态站点的以下控制措施：

- 精确的 CORS 允许列表。
- 严格的输入限制。
- 使用 Cloudflare Rate Limiting 防范短窗口滥用。
- 使用 Durable Object 实现全局、原子的每日 AI 请求预算。

如果部署需要身份识别而非匿名公共访问，必须将 Cloudflare Access 作为独立的生产决策进行选择和配置。绝不能把 bearer 密钥下发到静态前端。后续可以添加 Turnstile 作为机器人证明，但不能将其表述为用户身份验证，并且它不在本次已收敛的实现范围内。

## 架构

### Worker 请求流水线

所有 `/api/search` 请求都经过一条有序流水线：

1. 匹配路由和方法。
2. 根据精确配置的来源校验请求 Origin。
3. 强制校验内容类型，并使用按字节计数的限制读取请求体。
4. 校验解析后的 schema、查询长度、结果上限及其他数值边界。
5. 使用稳定的滥用控制键应用 Cloudflare 的 Rate Limiting 绑定。
6. 从 Durable Object 的 UTC 每日预算中原子预留一次请求。
7. 限制检索结果数量和上下文总字节数。
8. 使用固定的输出令牌上限和超时时间调用 DeepSeek。
9. 通过统一的响应标头函数返回响应。

每一次拒绝都发生在后续成本更高的阶段之前。如果速率限制或预算绑定不可用，端点将采用失败关闭策略并返回通用 `503`。预算在调用提供商前立即扣除；因校验、CORS 和速率限制被拒绝的请求不会消耗预算。对于结果不明确的提供商故障，请求预留不会退还，否则重试可能突破硬请求预算。

Durable Object 使用基于 UTC 的日期键，存储 `{ day, used }`，并在一次串行调用中完成读取、检查和递增。配置的每日上限必须是正整数。达到上限时返回 `429`，并附带截止到下一个 UTC 日期边界的 `Retry-After` 值。这是硬性请求上限，而不是对提供商计费的估算。上下文和输出令牌上限会分别限制每个已接受请求的最大成本。

### CORS 策略

允许的来源来自配置，并解析为完整的来源：scheme、host 以及显式或默认 port。比较必须精确；substring、suffix、wildcard、`null` 和格式错误的来源都会被拒绝。允许的响应会回显已经验证的 Origin，并包含 `Vary: Origin`。预检只允许必需的方法和标头。被拒绝的响应不包含 allow-origin 标头。

没有 Origin 的请求不会自动受信任。可以根据端点明确的公共策略处理这类请求，但它们不能绕过速率、输入或预算控制。

### 输入和上游限制

Worker 不会在强制执行请求体限制前调用 `request.json()`。它以流式方式读取并统计字节数，使用 `413` 拒绝过大的请求体，然后再解析 JSON。该路由只接受 `POST` 和 JSON。只有在已有文档说明时才可以忽略未知键；`debug` 必须被拒绝或移除，并且绝不能改变输出。

配置为以下项目定义保守的正数边界：

- 请求体字节数。
- 查询字符数和 UTF-8 字节数。
- 搜索结果数量。
- 检索上下文字节数。
- DeepSeek 最大输出令牌数。
- 上游超时时间。
- 速率限制周期和次数。
- 每日 AI 请求数。

安全关键值配置错误或缺失时，应以失败关闭方式处理，而不是使用无限制的默认值。

### 移除调试功能

从生产代码中移除 `/api/debug` 和由请求体控制的调试行为。未知路由返回最小化响应。绝不向调用者返回提供商响应、prompt、检索到的上下文、环境名称、绑定元数据或 stack trace。

### XSS 防护

XSS 在生产者和消费者两侧的边界同时修复。

在浏览器中，使用 `textContent`、`createTextNode`、属性设置器和 DOM 构造来插入不可信值。AI 回答最初按保留空白的纯文本呈现。链接会被解析，并限制为已批准的协议和预期目标。搜索结果、模态框内容和本地浏览器历史记录即使已存储也仍然是不可信的。任何动态不可信值都不得进入 `innerHTML`。

在 `scripts/daily_digest/render.py` 中，根据 AI 和外部值所处的 Markdown 上下文进行编码。链接目标需要单独解析并限制为安全协议。仅进行 HTML 转义不足以保护 Markdown 链接语法，因此文本和 URL 使用不同的辅助函数。

作为纵深防御，每一条执行 `rehypeRaw` 的 Quartz 路径后都紧跟使用显式 schema 的 `rehype-sanitize`。该 schema 只允许现有创作内容和 Quartz 功能所需的元素、属性和 URL 协议。测试在拒绝 script、事件处理属性、危险 URL 和可执行嵌入内容的同时，保护合法的代码块、图像、表格和 OFM 构造不发生回归。

### CSP 和响应安全标头

实现只添加与部署架构兼容的标头，并在收紧策略前验证生成的站点：

- `Content-Security-Policy`，包含明确的 `default-src`、`script-src`、`style-src`、`img-src`、`font-src`、`connect-src`、`object-src 'none'`、`base-uri 'self'` 和 `frame-ancestors 'none'` 指令。
- `X-Content-Type-Options: nosniff`。
- `Referrer-Policy: strict-origin-when-cross-origin`。
- 使用 `Permissions-Policy` 禁用未使用的能力。

由于 Quartz 当前使用内联资源，虚假宣称采用了严格 CSP 会带来危害。实现首先盘点生成的内联 script/style。随后，在托管路径支持的情况下使用 hash/nonce，否则记录临时所需的最小内联指令。不得允许 `unsafe-eval`。仅当生产 HTTPS 主机名及其所有子域均确定可安全使用 HTTPS 时才配置 HSTS；不会盲目地将其添加到本地或预览响应中。

### GitHub Actions 和依赖

每个第三方工作流 Action 都固定到经过验证的完整 40 字符 commit SHA，并保留版本注释以便维护。仓库测试会拒绝未来出现的可变引用。SHA 值在实现期间从官方 Action 仓库获取，绝不猜测。Dependabot 或同等自动化可以提出固定版本更新，但仍然必须经过常规审查。

依赖修复从全新的 `npm audit` 以及针对每条脆弱依赖链执行 `npm explain` 开始。直接依赖按每次一个可独立测试的分组进行升级。禁止使用 `npm audit fix --force`。生产环境中的 high/critical 问题必须降至零。任何暂时无法修复且仅影响开发环境的问题，都必须记录可达性评估、补偿控制、负责人和到期日期。

### 日志和告警

Worker 会为每个最终决策发出一条有大小限制的 JSON 安全事件。schema 包含事件名称、请求 ID、路由、决策、稳定的原因代码、状态、持续时间和粗粒度预算状态。它绝不包含授权标头、令牌、原始 IP 地址、请求体、查询、prompt、检索到的上下文、提供商响应体、密钥或 stack trace。

仓库代码和测试为来源拒绝、无效输入、过大请求体、短窗口速率拒绝、每日预算拒绝、上游超时或失败以及内部关闭失败定义事件。Cloudflare Observability、Logpush 目标、保留策略、dashboard 和生产告警阈值均属于外部配置。首先以只读方式检查这些配置，只有获得明确授权后才能更改。

## 外部操作和安全门

仓库测试通过后，必须执行以下顺序：

1. 读取并导出当前 Cloudflare Worker 绑定、变量、路由、迁移、可观测性配置和部署版本。
2. 读取并导出当前 GitHub 规则集或分支保护，以及已成功运行的工作流检查的确切名称。
3. 向用户展示预期 diff 和回滚步骤。
4. 获得明确批准后，创建 Rate Limiting 绑定和 Durable Object namespace/migration，设置非密钥变量或密钥，并部署到 staging。
5. 验证 staging 行为、日志、限制、每日滚动、流式响应、CSP 和站点渲染。
6. 获得明确的生产批准后，部署并启用告警。
7. 获得单独批准后，使用 GitHub 规则集保护 `main`：要求 pull request、approval、已解决的对话以及已经验证的 required checks；禁用 force push 和删除；并保留有意设置的 bot/admin bypass。

在 `main` 上成功运行当前各 job 的确切名称之前，不得启用规则集自动化，因为不存在的 required check 可能锁死仓库。仓库代码可以记录所需配置，但不能宣称 `main` 已受保护。

## 测试策略

每项变更都遵循 red-green-refactor。测试使用恶意 fixture，例如 `<script>`、事件处理属性、`javascript:` URL、格式错误的来源、后缀混淆来源、过大的流式请求体、并发预算请求和不可用的绑定。

验证采用分层方式：

- 聚焦的 Worker 安全与预算单元测试。
- Python 渲染器测试。
- 浏览器或 DOM XSS 回归测试。
- Quartz 解析或 OFM 以及完整构建 fixture。
- 工作流固定版本和现有工作流测试。
- 类型检查和格式检查。
- 生产依赖审计和完整依赖审计。
- 按照 `AGENTS.md` 的要求，在部署后进行 staging 验证。

## 验收标准

- 被拒绝的 Origin 绝不会收到 allow-origin 标头；允许的来源必须精确匹配，并且响应按 Origin 区分缓存。
- 无效或过大的输入无法访问搜索存储、Vectorize、预算对象或 DeepSeek。
- 短窗口超额请求会在每日预算和提供商调用之前被拒绝。
- 并发接受的调用不能超过配置的 UTC 每日请求预算。
- `/api/debug` 和由请求体控制的调试输出均不存在。
- 已存储的搜索、历史记录、AI 和生成的 Markdown payload 无法创建可执行 DOM 或不安全链接。
- Quartz 原始 HTML 会被清理，同时不会破坏有文档记录的合法内容。
- CSP 或安全标头存在于正确的服务层，并已针对类似生产环境的构建进行验证。
- 所有第三方 Actions 都使用经过验证的 40 字符 SHA。
- 生产 npm 审计不报告 high/critical 问题；任何允许的开发环境例外都必须明确说明并设有时限。
- 安全日志采用结构化格式，并经过脱敏测试；生产告警在获得授权进行配置后单独验证。
- 未先取得只读快照和明确批准，绝不更改 Cloudflare 和 GitHub 外部状态。
