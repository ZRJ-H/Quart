# 公共仓库安全加固实施计划

> **面向智能体执行者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans，逐项任务实施本计划。各步骤使用复选框（`- [ ]`）语法进行跟踪。

**目标：** 在保留公开 Quartz 站点的同时，消除已确认的 Worker 滥用、存储型 XSS、CI 供应链、依赖项和可观测性缺口；对生产环境中的 Cloudflare 和 GitHub 变更要求明确批准。

**架构：** 在每个 AI 搜索请求前设置一条统一的失败关闭安全管线，使用 Cloudflare Rate Limiting 控制短时间窗口内的滥用，并使用串行化 Durable Object 强制执行 UTC 每日请求上限；所有响应出口共享 CORS 和安全响应头。在内容生产端以及浏览器/构建消费端，都将生成内容视为不可信内容；随后独立加固工作流、依赖项和脱敏日志记录。

**技术栈：** Cloudflare Workers、Durable Objects、Rate Limiting 绑定、JavaScript/TypeScript、通过 `tsx --test` 使用的 Node 测试运行器、Python `unittest`、Quartz/unified/rehype、GitHub Actions、npm audit。

**规格：** `docs/superpowers/specs/2026-09-14-public-repository-security-hardening-design.md`

## 全局约束

- CORS Origin 使用精确比较；拒绝通配符、子字符串、后缀、格式错误的 Origin 和 `null` Origin。
- 缺失或无效的安全关键配置必须失败关闭。
- Cloudflare Rate Limiting 处理短时间窗口内的滥用；Durable Object 以原子方式强制执行 UTC 每日 AI 请求上限。
- 不得在静态 Quartz 包中放置客户端密钥，也不得将 CORS 描述为身份认证。
- 不可信的搜索、AI、外部、存储及生成值绝不能进入可执行 HTML 上下文。
- 移除 `/api/debug` 和由请求控制的调试输出。
- 第三方 Actions 使用经过验证的完整 40 字符提交 SHA；绝不猜测 SHA 值。
- 禁止使用 `npm audit fix --force`。
- 日志绝不能包含原始 IP 地址、令牌、请求头、查询/请求正文文本、提示词、上下文、提供商响应正文、密钥或堆栈跟踪。
- 必须先以只读方式检查 Cloudflare 部署/资源/告警和 GitHub 规则集，只有在用户明确批准后才能更改。
- 只有在聚焦测试、完整仓库测试/检查套件、依赖审计以及 `AGENTS.md` 要求的部署验证全部通过后，才能宣称完成。

---

## 文件映射

- `worker/security-boundary.js`：精确 Origin 策略、有界 JSON 读取、输入验证、响应头以及经过脱敏的安全事件日志记录。
- `worker/daily-ai-budget.js`：Durable Object 和纯 UTC 每日预算状态转换。
- `worker/index.js`：有序请求管线、速率限制和预算调用、有界检索/上游调用，不含调试路由。
- `worker/wrangler.toml`：非密钥限制项、Rate Limiting 绑定、Durable Object 绑定及迁移。
- `quartz/components/scripts/search-ai.inline.js`：DOM 安全渲染和安全链接构造。
- `scripts/daily_digest/render.py`：Markdown 上下文文本编码和安全外部 URL 处理。
- `quartz/processors/parse.ts` 和 `quartz/plugins/transformers/ofm.ts`：净化每条原始 HTML 处理路径。
- `quartz/components/Head.tsx`：仅包含经验证与生成站点兼容、可由浏览器强制执行的静态站点 meta 策略。
- `.github/workflows/deploy.yaml` 和 `.github/workflows/collect-github-trending.yaml`：不可变 Action 固定引用。
- `package.json` 和 `package-lock.json`：净化器及漏洞修复版本。
- `tests/worker-security.test.mjs`：CORS、限制项、调试移除、速率限制顺序、响应头和脱敏。
- `tests/worker-budget.test.mjs`：原子化每日预算行为。
- `tests/search-ai-xss.test.mjs`：存储数据的 DOM 回归覆盖。
- `tests/python/test_daily_rendering_security.py`：生成 Markdown 注入回归覆盖。
- `tests/quartz-html-sanitization.test.mjs`：parse/OFM 和构建后 HTML 的净化覆盖。
- `tests/actions-pinned.test.mjs`：不可变工作流引用策略。
- `docs/security/operations.md`：外部状态清单、预发布验证、告警、回滚和规则集操作手册。

## 任务 1：记录可复现的安全基线

**文件：**

- 创建：`tests/worker-security.test.mjs`
- 修改：不修改任何生产文件

**接口：**

- 消耗：`worker/index.js` 当前的默认 Worker 导出以及模拟的 Worker 绑定。
- 产出：供任务 2–6 复用的 `dispatch(request, env)` 测试工具，以及针对每个已确认 Worker 问题的明确失败用例。

- [ ] **步骤 1：记录当前工作树的干净/脏状态和基线结果**

在不更改依赖项的情况下运行：

```powershell
git status --short --branch
npm test
npm run check
npm audit --omit=dev --json
npm audit --json
npm explain js-yaml sharp ws minimatch wrangler
```

将审计输出保存在受跟踪源码之外或任务记录中。预期：测试/检查建立起始状态；审计要么复现已知的高危问题，要么提供新的准确依赖链。

- [ ] **步骤 2：编写 Worker 测试工具和失败的特征测试**

测试模块必须构造 Request，调用 Worker 导出的 `fetch`，并为 `WIKI_DATA`、`VECTORIZE`、`AI_RATE_LIMITER`、`AI_DAILY_BUDGET` 和提供商 `fetch` 提供 spy。添加以下命名测试：

```js
test("rejects an unlisted origin without ACAO", async () => {})
test("does not expose the debug route", async () => {})
test("debug in a search body cannot change the response", async () => {})
test("rejects an oversized streaming body before storage or provider work", async () => {})
test("rate denial happens before daily budget and provider work", async () => {})
test("daily budget denial happens before retrieval and provider work", async () => {})
```

每个测试都必须同时断言 HTTP 结果，以及所有不应触达的下游 spy 均为零次调用。

- [ ] **步骤 3：运行特征测试并验证预期失败**

运行：

```powershell
npm test -- tests/worker-security.test.mjs
```

预期：失败可证明通配符 CORS、公开调试行为、无界输入和缺失滥用控制。测试工具自身错误不算有效失败。

- [ ] **步骤 4：提交仅含测试的基线**

```powershell
git add tests/worker-security.test.mjs
git commit -m "test: reproduce worker security gaps"
```

## 任务 2：移除生产调试入口

**文件：**

- 修改：`worker/index.js`
- 测试：`tests/worker-security.test.mjs`

**接口：**

- 消耗：现有 Worker 路由器和搜索请求正文解析。
- 产出：不存在 `/api/debug` 路由，且响应行为不受 `debug` 请求正文属性控制。

- [ ] **步骤 1：收紧失败测试**

断言 `GET /api/debug` 返回 `404`，响应正文不包含任何环境或绑定名称，并且 `{ query: "safe", debug: true }` 要么因输入无效而被拒绝，要么其行为与 `{ query: "safe" }` 完全一致且不含提示词/上下文字段。

- [ ] **步骤 2：运行两个调试测试并验证失败**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "debug"
```

预期：针对当前实现，至少有一个调试暴露测试失败。

- [ ] **步骤 3：删除两条调试路径**

移除 `/api/debug` 路由分支、由请求正文控制的调试响应字段，以及仅可从这些路径访问的所有辅助函数。未知路由返回最小化的 `404`；内部错误仅返回请求 ID 和通用消息。

- [ ] **步骤 4：验证调试入口已移除**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "debug"
rg "/api/debug|body\.debug" worker tests
```

预期：测试通过，源码搜索在生产代码中无匹配项。

- [ ] **步骤 5：提交**

```powershell
git add worker/index.js tests/worker-security.test.mjs
git commit -m "fix: remove worker debug surfaces"
```

## 任务 3：集中实施精确 CORS、有界输入和 API 安全响应头

**文件：**

- 创建：`worker/security.js`
- 修改：`worker/index.js`
- 修改：`worker/wrangler.toml`
- 测试：`tests/worker-security.test.mjs`

**接口：**

- 消耗：`env.ALLOWED_ORIGINS`、`env.MAX_REQUEST_BYTES`、`env.MAX_QUERY_CHARS`、`env.MAX_QUERY_BYTES` 和 `env.UPSTREAM_TIMEOUT_MS`。
- 产出：
  - `parsePositiveInt(value, name): number`
  - `resolveCors(request, env): { allowed: boolean, headers: Headers }`
  - `readJsonWithLimit(request, maxBytes): Promise<unknown>`
  - `validateSearchBody(value, limits): { query: string }`
  - `applyApiSecurityHeaders(headers): Headers`
  - `jsonResponse(body, status, request, env): Response`

- [ ] **步骤 1：添加失败的精确 Origin 测试**

使用包含 `https://notes.example.com` 的允许列表，并断言：

- 精确匹配的 Origin 会被回显，并带有 `Vary: Origin`。
- `https://notes.example.com.evil.test`、`https://sub.notes.example.com`、`http://notes.example.com`、`null`、格式错误值和未列入允许列表的 Origin 返回不带 ACAO 的 `403`。
- 获准的 OPTIONS 请求仅声明 `POST`、`Content-Type` 和必需的应用请求头。
- 普通响应、错误响应和流式响应使用相同的 CORS 计算逻辑。

- [ ] **步骤 2：添加失败的输入边界测试**

覆盖非 POST（`405`）、错误内容类型（`415`）、声明长度和分块传输均超过字节限制的正文（`413`）、格式错误的 JSON（`400`）、非对象 JSON（`400`）、空白查询（`400`）、字符数过多（`400`）和 UTF-8 字节数过多（`400`）。断言 KV、Vectorize、预算或提供商均未被调用。

- [ ] **步骤 3：添加失败的 API 响应头测试**

每个 API 响应（包括 SSE）都必须包含：

```text
Content-Security-Policy: default-src 'none'; base-uri 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store
```

- [ ] **步骤 4：运行聚焦测试并验证失败**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "origin|preflight|body|query|header|streaming"
```

- [ ] **步骤 5：实现安全辅助函数**

`readJsonWithLimit` 必须获取流读取器，累计实际的 `Uint8Array.byteLength`，在溢出时取消读取，仅在限制范围内进行一次解码，然后调用 `JSON.parse`。不得在执行限制检查之前使用 `request.json()`。`resolveCors` 将 `ALLOWED_ORIGINS` 解析为完整的 URL Origin，并且仅进行相等性比较。允许列表/限制项缺失或无效时抛出配置错误，由路由器将其转换为不带 ACAO 的 `503`。

- [ ] **步骤 6：让每个响应出口都经过辅助函数**

读取请求正文前先进行 CORS 检查。对预检、验证错误、提供商错误、成功 JSON 和流式响应应用相同的响应头。确保没有 Origin 的调用方仍须经过所有非 CORS 控制，且不会因此获得特权。

- [ ] **步骤 7：在 Wrangler 配置中添加保守的非密钥默认值**

为请求字节数、查询字符数/字节数、结果数量、上下文字节数、输出令牌数和上游超时添加明确的正值。不得在 `[vars]` 中放置凭据。

- [ ] **步骤 8：运行测试和检查**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **步骤 9：提交**

```powershell
git add worker/security.js worker/index.js worker/wrangler.toml tests/worker-security.test.mjs
git commit -m "fix: enforce worker request boundaries"
```

## 任务 4：添加 Cloudflare 短时间窗口速率限制

**文件：**

- 修改：`worker/index.js`
- 修改：`worker/wrangler.toml`
- 测试：`tests/worker-security.test.mjs`

**接口：**

- 消耗：`env.AI_RATE_LIMITER.limit({ key }): Promise<{ success: boolean }>` 以及仅用作限制键的 Cloudflare 所提供客户端地址。
- 产出：`enforceRateLimit(request, env): Promise<void>`，抛出类型化拒绝并转换为 `429`，或将绑定故障转换为 `503`。

- [ ] **步骤 1：添加失败的调用顺序和响应测试**

断言获准请求在验证后、每日预算、存储、Vectorize 或 DeepSeek 之前调用限制器。`{ success: false }` 结果返回 `429`，并带有有界的 `Retry-After`。缺失或抛出异常的绑定返回 `503`；绝不绕过限制。

- [ ] **步骤 2：验证失败**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "rate"
```

- [ ] **步骤 3：配置并调用绑定**

添加一个 `AI_RATE_LIMITER` `[[ratelimits]]` 绑定，其命名空间 ID、计数和周期必须明确且受到已部署 Cloudflare 账户支持。使用 `CF-Connecting-IP` 作为匿名滥用限制键，但不得记录它。如果将来存在 Access subject，优先使用该 subject。限制器调用必须始终位于所有会产生成本的工作之前。

- [ ] **步骤 4：验证速率限制行为和所有 Worker 测试**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **步骤 5：提交**

```powershell
git add worker/index.js worker/wrangler.toml tests/worker-security.test.mjs
git commit -m "fix: rate limit ai search requests"
```

## 任务 5：强制执行原子化 UTC 每日 AI 请求预算

**文件：**

- 创建：`worker/daily-ai-budget.js`
- 创建：`tests/worker-daily-budget.test.mjs`
- 修改：`worker/index.js`
- 修改：`worker/wrangler.toml`
- 测试：`tests/worker-security.test.mjs`

**接口：**

- 消耗：`env.AI_DAILY_BUDGET`、`env.DAILY_AI_REQUEST_LIMIT` 和 `env.AI_DAILY_BUDGET.idFromName("global")`。
- 产出：
  - `transitionDailyBudget(state, nowDay, limit): { state: { day: string, used: number }, allowed: boolean, remaining: number }`
  - 导出的 `class DailyAiBudget`，其中 `fetch(request): Promise<Response>` 接受 `POST /reserve`。
  - Worker 管线中的 `reserveDailyAiRequest(env): Promise<{ remaining: number }>`。

- [ ] **步骤 1：编写纯状态转换测试**

测试首次使用、精确的最后一次获准预留、达到限制后的拒绝、UTC 日期切换、损坏的存储状态和无效的非正数限制。只有获准时转换才递增计数。

- [ ] **步骤 2：编写并发 Durable Object 契约测试**

针对一个伪造的串行化存储实例，发起数量超过限制的预留 Promise。断言恰好有 `limit` 个响应获准，其余全部被拒绝。被拒绝的请求不得递增 `used`。

- [ ] **步骤 3：运行并验证失败**

```powershell
npm test -- tests/worker-daily-budget.test.mjs
```

- [ ] **步骤 4：实现 Durable Object**

使用 UTC `YYYY-MM-DD` 日期值，并通过一个存储事务或 Durable Object 的串行事件语义完成读取/检查/递增。仅返回 `allowed`、`remaining` 和下次重置元数据。不接受调用方提供的大于一的增量。

- [ ] **步骤 5：添加 Worker 集成测试**

断言预留发生在速率限制器之后、首个会产生提供商成本的操作之前。拒绝返回 `429`，并带有根据重置时间计算的 `Retry-After`；绑定缺失、格式错误或抛出异常时返回 `503`。验证失败和速率限制拒绝不预留预算。含义不明确的提供商故障不退还预留。

- [ ] **步骤 6：接入绑定和迁移**

从 Worker 模块导出 `DailyAiBudget`。添加 `AI_DAILY_BUDGET` Durable Object 绑定、一个标签唯一的 SQLite 类迁移，以及正值 `DAILY_AI_REQUEST_LIMIT` 变量。不得复用已部署的迁移标签。

- [ ] **步骤 7：限制每个已接受请求的最大成本**

调用提供商前，限制搜索结果数量、累计 UTF-8 上下文字节数和 DeepSeek 输出令牌数。在 `UPSTREAM_TIMEOUT_MS` 时中止上游请求。添加测试，证明在构造请求前已发生截断，且超时返回通用响应。

- [ ] **步骤 8：运行聚焦测试和完整 Worker 测试**

```powershell
npm test -- tests/worker-daily-budget.test.mjs tests/worker-security.test.mjs
npm run check
```

- [ ] **步骤 9：提交**

```powershell
git add worker/daily-ai-budget.js worker/index.js worker/wrangler.toml tests/worker-daily-budget.test.mjs tests/worker-security.test.mjs
git commit -m "fix: enforce daily ai request budget"
```

## 任务 6：确保搜索和 AI 渲染的 DOM 安全

**文件：**

- 修改：`quartz/components/scripts/search-ai.inline.js`
- 创建：`tests/search-ai-xss.test.mjs`

**接口：**

- 消耗：API 搜索结果、AI 回答文本、localStorage 历史记录和结果 URL。
- 产出：
  - `appendTextElement(parent, tagName, text, className): HTMLElement`
  - `toSafeResultUrl(value, siteBase): URL | null`
  - 不解析不可信 HTML、而是构造节点的渲染器函数。

- [ ] **步骤 1：创建恶意 DOM 固定测试数据**

使用以下内容测试建议、历史记录、回答和模态框流程：

```js
const attacks = [
  "<script>globalThis.pwned = true</script>",
  '<img src=x onerror="globalThis.pwned = true">',
  '"><svg/onload=globalThis.pwned=true>',
  "javascript:alert(1)",
]
```

测试工具挂载最小必需 DOM，模拟 fetch/localStorage，渲染每个值，并断言它仅以文本出现，不会从攻击载荷创建 `script`、`img` 或 `svg` 元素，不会安装事件属性，也不会创建危险链接。

- [ ] **步骤 2：运行测试并验证失败**

```powershell
npm test -- tests/search-ai-xss.test.mjs
```

- [ ] **步骤 3：以 DOM 构造替换动态 HTML 解析**

使用 `textContent`、`createTextNode`、`createElement`、`classList` 和明确的安全属性。将 AI 回答渲染为纯文本，并通过 CSS 保留空白。使用 `new URL` 解析 URL；只允许预期的站点 Origin 和明确获准的 `http:`/`https:` 目标。将 localStorage 内容视为不可信内容。

- [ ] **步骤 4：证明每个搜索界面都安全**

```powershell
npm test -- tests/search-ai-xss.test.mjs
rg "innerHTML|insertAdjacentHTML|outerHTML" quartz/components/scripts/search-ai.inline.js
```

预期：测试通过。任何剩余匹配项都必须是仅含字面量的模板，并且有测试证明任何不可信插值都无法到达该模板；否则应将其移除。

- [ ] **步骤 5：运行仓库前端测试和检查**

```powershell
npm test
npm run check
```

- [ ] **步骤 6：提交**

```powershell
git add quartz/components/scripts/search-ai.inline.js tests/search-ai-xss.test.mjs
git commit -m "fix: render ai search content safely"
```

## 任务 7：编码生成的 Markdown 并净化原始 HTML 路径

**文件：**

- 修改：`scripts/daily_digest/render.py`
- 修改：`tests/python/test_daily_rendering.py`
- 修改：`quartz/processors/parse.ts`
- 修改：`quartz/plugins/transformers/ofm.ts`
- 修改：`quartz.config.ts`
- 修改：`package.json`
- 修改：`package-lock.json`
- 创建：`tests/quartz-html-sanitization.test.mjs`

**接口：**

- 消耗：不可信的 AI/外部标题、摘要、描述、作者、仓库名称和 URL 字段。
- 产出：
  - Python `escape_markdown_text(value: object) -> str`
  - Python `safe_external_url(value: object) -> str | None`
  - 在每次执行 `rehypeRaw` 后应用的一份共享 rehype 净化模式。

- [ ] **步骤 1：添加失败的 Python 渲染器测试**

让脚本标签、事件属性、Markdown 链接注入、闭合分隔符、控制字符和 `javascript:`/危险 `data:` URL 经过每个外部字段。断言生成的 Markdown 包含惰性文本、拒绝不安全 URL，并保留有效的 `https:` URL。

- [ ] **步骤 2：验证 Python 测试失败**

```powershell
python -m unittest tests.python.test_daily_rendering -v
```

- [ ] **步骤 3：实现与上下文相匹配的生产端编码**

`escape_markdown_text` 将值标准化为文本，并转义 Markdown 结构标点和原始 HTML 分隔符。`safe_external_url` 独立解析 URL，仅接受配置的 `http:`/`https:` 目标。绝不对文本和 URL 使用同一个通用转义函数。

- [ ] **步骤 4：添加失败的 Quartz 净化器测试**

为 `parse.ts` 和 `ofm.ts` 两条路径创建固定测试数据。断言移除 `script`、事件属性、`javascript:` 链接、可执行 SVG/MathML 和不安全嵌入内容，同时保留站点所记录的代码块、表格、图片、标题和 OFM 构造。

- [ ] **步骤 5：验证净化器测试失败**

```powershell
npm test -- tests/quartz-html-sanitization.test.mjs
```

- [ ] **步骤 6：添加并配置 `rehype-sanitize`**

安装当前兼容的 `rehype-sanitize` 版本，不进行无关升级。定义一份明确的模式，并在 `parse.ts` 和 `ofm.ts` 的每条 `rehypeRaw` 路径之后立即应用。只允许必需的标签/属性，以及 `http`、`https` 和有意支持的安全协议。事件属性、脚本、可执行嵌入命名空间和危险协议仍须禁止。

- [ ] **步骤 7：运行渲染器、净化器和完整构建验证**

```powershell
python -m unittest tests.python.test_daily_rendering -v
npm test -- tests/quartz-html-sanitization.test.mjs
npx quartz build
npm test
npm run check
```

检查恶意固定测试数据构建出的 HTML，并确认其包含惰性文本，但不含可执行节点或不安全 URL。

- [ ] **步骤 8：提交**

```powershell
git add scripts/daily_digest/render.py tests/python/test_daily_rendering.py quartz/processors/parse.ts quartz/plugins/transformers/ofm.ts quartz.config.ts package.json package-lock.json tests/quartz-html-sanitization.test.mjs
git commit -m "fix: sanitize generated quartz content"
```

## 任务 8：添加可行的静态站点 CSP 和安全策略

**文件：**

- 修改：`quartz/components/Head.tsx`
- 测试：`tests/quartz-html-sanitization.test.mjs`
- 创建：`docs/security/operations.md`

**接口：**

- 消耗：生成站点实际使用的脚本、样式、图片、字体、框架、表单和 Worker 连接来源。
- 产出：与经验证构建兼容、尽早出现的 CSP meta 策略和 referrer meta 策略；用于服务层仅 HTTP 响应头的操作手册。

- [ ] **步骤 1：添加生成页面策略测试**

构建一个代表性页面，并断言策略 meta 元素位于可执行内容之前。测试还须清点所有内联脚本/样式和外部来源，确保会静默阻止站点功能的策略无法通过测试。

- [ ] **步骤 2：验证插入策略前测试会失败**

```powershell
npm test -- tests/quartz-html-sanitization.test.mjs --test-name-pattern "content security policy"
```

- [ ] **步骤 3：添加与构建兼容的最严格 meta 策略**

从针对 `default-src`、`script-src`、`style-src`、`img-src`、`font-src`、`connect-src`、`object-src 'none'`、`base-uri 'self'` 和 `form-action` 的明确指令开始。只包含清单中发现的 Origin。对于构建过程可以保持同步的稳定内联资源，使用哈希。绝不添加 `unsafe-eval`。如果当前 Quartz 内联代码导致暂时无法避免 `unsafe-inline`，则将其限定在受影响的指令中，记录每个出现位置及其移除路径，并且不得声称该策略会阻止内联 XSS。

添加 `<meta name="referrer" content="strict-origin-when-cross-origin">`。不得在 meta CSP 中放置 `frame-ancestors`，因为浏览器会忽略它。

- [ ] **步骤 4：记录只能在服务层设置的响应头**

在 `docs/security/operations.md` 中说明 GitHub Pages 不会执行仓库中的 `_headers` 文件。要求生产代理/托管层设置 `X-Content-Type-Options`、`Permissions-Policy`、`frame-ancestors`，并且仅在完成 HTTPS/子域审查后设置 HSTS。包含基于 curl 的预发布检查及预期的精确值。

- [ ] **步骤 5：验证完整的生成站点**

```powershell
npx quartz build
npm test -- tests/quartz-html-sanitization.test.mjs
npm run check
```

在浏览器工具中启用 CSP 违规报告并加载类生产构建，在接受策略之前解决每一项非预期违规。

- [ ] **步骤 6：提交**

```powershell
git add quartz/components/Head.tsx tests/quartz-html-sanitization.test.mjs docs/security/operations.md
git commit -m "fix: add compatible site security policy"
```

## 任务 9：添加结构化且脱敏安全的安全事件

**文件：**

- 修改：`worker/security.js`
- 修改：`worker/index.js`
- 修改：`tests/worker-security.test.mjs`
- 修改：`docs/security/operations.md`

**接口：**

- 消耗：终态请求决策、请求 ID、路由、状态、时长、原因代码和粗粒度预算百分比。
- 产出：`logSecurityEvent(consoleLike, event): void`，每个终态决策恰好发出一个有界 JSON 对象。

- [ ] **步骤 1：添加失败的事件模式和脱敏测试**

覆盖 `origin_denied`、`invalid_input`、`body_too_large`、`rate_denied`、`daily_budget_denied`、`upstream_timeout`、`upstream_failure` 和 `closed_failure`。向每个请求头/请求正文/提供商字段注入哨兵密钥，并断言序列化日志不包含其中任何值、不包含原始客户端 IP，也不包含堆栈跟踪。

- [ ] **步骤 2：验证失败**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "log|redact|event"
```

- [ ] **步骤 3：实现固定事件模式**

只允许：

```js
{
  event: "worker_security_decision",
  requestId,
  route,
  decision,
  reasonCode,
  status,
  durationMs,
  budgetBand,
}
```

根据获准的原始值构造此对象，不得净化任意对象后直接使用。限制字符串长度和数值范围。生成或复用非密钥请求 ID。在最终响应边界发出一行日志。

- [ ] **步骤 4：记录告警输入，但不更改 Cloudflare**

添加针对 401/403、413、429、预算 80%/95%、5xx 和上游故障的精确原因代码、建议时间窗口和阈值。记录留存和回滚问题。将可观测性、Logpush、仪表板和告警创建标记为需批准的外部操作。

- [ ] **步骤 5：验证**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **步骤 6：提交**

```powershell
git add worker/security.js worker/index.js tests/worker-security.test.mjs docs/security/operations.md
git commit -m "feat: add redacted worker security events"
```

## 任务 10：将每个第三方 GitHub Action 固定到经过验证的 SHA

**文件：**

- 创建：`tests/actions-pinned.test.mjs`
- 修改：`.github/workflows/deploy.yaml`
- 修改：`.github/workflows/collect-github-trending.yaml`
- 仅在已存在时可选修改：`.github/dependabot.yml`

**接口：**

- 消耗：`.github/workflows` 下的每个 `uses:` 条目。
- 产出：仓库不变量——远程 Action 引用必须匹配 `owner/repository@` 后紧跟恰好 40 个十六进制字符；本地 `./` Action 不受此规则约束。

- [ ] **步骤 1：编写失败的策略测试**

解析 `.yml` 和 `.yaml`。报告工作流路径和可变的 `uses:` 字符串。测试必须对已确认的可变标签失败，对本地 Action 和由单独摘要策略管理的 Docker 镜像引用通过。

- [ ] **步骤 2：验证当前工作流会失败**

```powershell
npm test -- tests/actions-pinned.test.mjs
```

- [ ] **步骤 3：从官方仓库解析 SHA**

对于 `actions/checkout@v6`、`actions/setup-node@v7`、`actions/setup-python@v7`、`actions/configure-pages@v5`、`actions/upload-pages-artifact@v4` 和 `actions/deploy-pages@v4`，获取官方 tag/ref，并将附注标签解引用到提交。与官方仓库中的提交交叉核对。不得使用搜索引擎摘要，也不得编造值。

- [ ] **步骤 4：替换标签并保留便于审查的注释**

将每个引用写为 `owner/repository@<verified commit>`，后跟便于阅读的版本注释，并要求 `@` 后的部分匹配 `^[0-9a-f]{40}$`。复制经独立验证的提交本身；不得在工作流中使用示例性或伪造的 SHA 文本。

- [ ] **步骤 5：仅在 Dependabot 已存在时配置自动固定引用更新**

保留现有生态系统，并按照仓库已有计划在 `/` 添加 `github-actions` 生态系统。如果不存在 Dependabot，将其记录为单独的后续事项，而不要扩大此安全补丁的范围。

- [ ] **步骤 6：运行工作流测试和完整检查**

```powershell
npm test -- tests/actions-pinned.test.mjs tests/deploy-workflow.test.mjs tests/daily-workflow.test.mjs tests/daily-watchdog.test.mjs
npm run check
```

- [ ] **步骤 7：提交**

```powershell
git add .github/workflows/deploy.yaml .github/workflows/collect-github-trending.yaml tests/actions-pinned.test.mjs
git commit -m "ci: pin actions to immutable commits"
```

## 任务 11：修复存在漏洞的 npm 依赖链

**文件：**

- 修改：`package.json`
- 修改：`package-lock.json`
- 仅在确有必要设立例外时修改：`docs/security/operations.md`

**接口：**

- 消耗：最新的 `npm audit --json`、`npm audit --omit=dev --json` 和 `npm explain` 依赖图。
- 产出：生产依赖中高危/严重问题为零；完整依赖中高危/严重问题也为零，或者存在明确的、有负责人且会过期的仅开发环境例外。

- [ ] **步骤 1：复现并分类当前每一项问题**

```powershell
npm audit --omit=dev --json
npm audit --json
npm explain js-yaml
npm explain sharp
npm explain ws
npm explain minimatch
npm explain wrangler
```

对每个公告记录：属于生产/开发依赖、直接/传递依赖、在构建/部署/运行时是否可达、最近的直接依赖，以及最低修复版本。

- [ ] **步骤 2：每次升级一组直接依赖**

选择能移除存在漏洞传递版本的最小 semver 兼容直接升级。每组升级后检查 `git diff -- package.json package-lock.json`，并拒绝无关的锁文件变动。不得运行 `npm audit fix --force`。

- [ ] **步骤 3：验证每项依赖相关行为**

更改 `sharp` 后，构建包含图片的内容。更改 Quartz/Markdown 依赖后，运行净化器和渲染器固定测试数据。更改 `wrangler` 后，运行 Worker 测试和不会部署的配置干跑验证。更改 glob/YAML/WebSocket 依赖链后，运行工作流/配置解析和完整测试套件。

```powershell
npx quartz build
npm test
npm run check
```

- [ ] **步骤 4：强制执行审计验收门槛**

```powershell
npm audit --omit=dev --audit-level=high
npm audit --audit-level=high
```

预期：生产审计以零退出，且没有高危/严重问题。完整审计也以零退出；如果仍存在上游无法修复且仅限开发环境的问题，停止并交由用户审查，同时添加具体例外，其中包含公告 ID、依赖路径、可达性、补偿控制、负责人，以及不超过 90 天的到期日期。

- [ ] **步骤 5：提交**

```powershell
git add package.json package-lock.json docs/security/operations.md
git commit -m "build: remediate high severity dependencies"
```

## 任务 12：最终仓库验证

**文件：**

- 仅当验证失败揭示范围内缺陷时，修改已列出的文件。

**接口：**

- 消耗：任务 1–11 的所有交付物。
- 产出：一份证据记录，证明在执行任何外部变更前，每项仓库验收标准均已通过。

- [ ] **步骤 1：运行所有聚焦安全测试**

```powershell
npm test -- tests/worker-security.test.mjs tests/worker-daily-budget.test.mjs tests/search-ai-xss.test.mjs tests/quartz-html-sanitization.test.mjs tests/actions-pinned.test.mjs
python -m unittest tests.python.test_daily_rendering -v
```

- [ ] **步骤 2：运行完整构建、测试、检查和审计**

```powershell
npx quartz build
npm test
npm run check
npm audit --omit=dev --audit-level=high
npm audit --audit-level=high
git diff --check
```

- [ ] **步骤 3：检查差异的范围和密钥**

```powershell
git status --short
git diff --stat
git diff --check
rg "DEEPSEEK_API_KEY|Authorization:|Bearer |api/debug|body\.debug" worker quartz scripts .github docs tests
```

预期：只更改了预期文件，不含密钥值，并且 debug 匹配项只存在于反向测试或文档中。

- [ ] **步骤 4：对照设计验收标准审查**

将规格中的每项标准映射到一个通过的测试或已记录的外部门槛。不得仅凭仓库证据就将外部规则集、部署或告警标准标记为完成。

- [ ] **步骤 5：提交最终的仅测试修正（如有）**

```powershell
git add worker quartz scripts tests .github package.json package-lock.json docs/security/operations.md
git commit -m "test: verify repository security hardening"
```

## 任务 13：只读外部清点和需批准的上线

**文件：**

- 修改：`docs/security/operations.md`，仅用于记录已确认的名称、ID、当前设置和获准的回滚步骤，不包含密钥。

**接口：**

- 消耗：Cloudflare 账户/Worker 配置、GitHub 规则集/分支保护、当前成功检查名称以及预发布 URL。
- 产出：经过审查的外部变更集；实际变更仍是需要单独批准的操作。

- [ ] **步骤 1：以只读方式检查 Cloudflare 状态**

读取当前 Worker 版本、路由、绑定、按名称列出的变量、Durable Object 迁移、速率限制可用性、可观测性、Logpush、告警和回滚目标。绝不输出密钥值。将已部署的绑定名称与 `worker/wrangler.toml` 进行比较。

- [ ] **步骤 2：以只读方式检查 GitHub 状态**

读取当前规则集、分支保护、仓库默认分支、绕过角色，以及近期 `main` 运行中准确的成功作业/检查名称。保存一份脱敏快照，并识别所有会写入 `main` 的自动化。

- [ ] **步骤 3：展示拟议的外部差异并请求批准**

分别为以下事项请求批准：

- 创建 Rate Limiting 绑定和 Durable Object 命名空间/迁移。
- 设置允许 Origin 和限制项变量/密钥。
- 部署预发布环境，然后部署生产环境。
- 启用可观测性/Logpush 和告警。
- 更改 `main` 规则集。

包含准确的回滚版本，并解释错误的必需检查名称可能会锁死合并。

- [ ] **步骤 4：获批后，预发布并验证 Cloudflare 变更**

验证允许/拒绝的 Origin、预检、超大分块请求正文、速率限制拒绝、并发每日限制拒绝、使用测试命名空间的 UTC 日期切换行为、提供商超时、流式响应头、结构化/脱敏日志、CSP 和正常搜索体验。在升级到生产环境前，遵循 `AGENTS.md` 的部署验证要求。

- [ ] **步骤 5：另行获批后配置告警**

为 Origin/身份认证拒绝激增、413、429、预算 80%/95%、5xx 和提供商故障创建阈值。在预发布环境中安全触发每一种情况，确认传递、留存和去重，然后启用生产路由。

- [ ] **步骤 6：另行获批后保护 `main`**

要求使用拉取请求、至少一次批准、过期批准撤销、所有对话均已解决，并且仅要求已在 `main` 上证明成功的准确检查；禁用强制推送和分支删除；保留经过审查的机器人/管理员绕过。立即验证一个测试拉取请求能够满足所有必需检查。

- [ ] **步骤 7：记录外部验证，不含密钥**

使用资源名称、规则标识符、已部署版本、验证时间戳、告警名称和回滚命令更新 `docs/security/operations.md`。不得存储账户令牌、密钥值、原始日志或个人数据。

---

## 完成门槛

只有任务 12 通过后，仓库实施才算完成。只有任务 13 已完成经过批准和验证的预发布/生产上线、告警已实际触发测试，并通过真实拉取请求验证了 GitHub 规则集后，生产加固才算完成。如果未获得外部授权，则应将仓库工作报告为已完成，将相应生产控制报告为待完成；不得暗示这些控制已经生效。
