# Public Repository Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the confirmed Worker abuse, stored-XSS, CI supply-chain, dependency, and observability gaps while preserving the public Quartz site and requiring explicit approval for production Cloudflare and GitHub mutations.

**Architecture:** Put one fail-closed security pipeline in front of every AI search request, use Cloudflare Rate Limiting for short-window abuse and a serialized Durable Object for the UTC daily request ceiling, and make all response exits share CORS and security headers. Treat generated content as untrusted at both producer and browser/build consumers, then independently harden workflows, dependencies, and redacted logging.

**Tech Stack:** Cloudflare Workers, Durable Objects, Rate Limiting binding, JavaScript/TypeScript, Node test runner through `tsx --test`, Python `unittest`, Quartz/unified/rehype, GitHub Actions, npm audit.

**Spec:** `docs/superpowers/specs/2026-09-14-public-repository-security-hardening-design.md`

## Global Constraints

- CORS origin comparison is exact; wildcard, substring, suffix, malformed, and `null` origins are rejected.
- Security-critical configuration fails closed when missing or invalid.
- Cloudflare Rate Limiting handles short-window abuse; a Durable Object atomically enforces the UTC daily AI request limit.
- No client secret is placed in the static Quartz bundle, and CORS is never described as authentication.
- Untrusted search, AI, external, stored, and generated values never enter an executable HTML context.
- `/api/debug` and request-controlled debug output are removed.
- Third-party Actions use verified full 40-character commit SHAs; SHA values are never guessed.
- `npm audit fix --force` is prohibited.
- Logs never contain raw IP addresses, tokens, headers, query/body text, prompts, context, provider bodies, secrets, or stack traces.
- Cloudflare deployment/resources/alerts and GitHub Rulesets are inspected read-only first and changed only after explicit user approval.
- Only claim completion after focused tests, the complete repository test/check suite, dependency audits, and the deployment verification required by `AGENTS.md` have passed.

---

## File Map

- `worker/security-boundary.js`: exact Origin policy, bounded JSON reading, input validation, response headers, and redacted security-event logging.
- `worker/daily-ai-budget.js`: Durable Object and pure UTC daily-budget state transition.
- `worker/index.js`: ordered request pipeline, rate-limit and budget calls, bounded retrieval/upstream call, no debug route.
- `worker/wrangler.toml`: non-secret limits, Rate Limiting binding, Durable Object binding, and migration.
- `quartz/components/scripts/search-ai.inline.js`: DOM-safe rendering and safe link construction.
- `scripts/daily_digest/render.py`: Markdown-context text encoding and safe external URL handling.
- `quartz/processors/parse.ts` and `quartz/plugins/transformers/ofm.ts`: sanitize each raw-HTML processing path.
- `quartz/components/Head.tsx`: only browser-enforceable static-site meta policies proven compatible with the generated site.
- `.github/workflows/deploy.yaml` and `.github/workflows/collect-github-trending.yaml`: immutable action pins.
- `package.json` and `package-lock.json`: sanitizer and vulnerability-remediation versions.
- `tests/worker-security.test.mjs`: CORS, limits, debug removal, rate-limit ordering, headers, and redaction.
- `tests/worker-budget.test.mjs`: atomic daily-budget behavior.
- `tests/search-ai-xss.test.mjs`: stored-data DOM regression coverage.
- `tests/python/test_daily_rendering_security.py`: generated Markdown injection regression coverage.
- `tests/quartz-html-sanitization.test.mjs`: parse/OFM and built-HTML sanitization coverage.
- `tests/actions-pinned.test.mjs`: immutable workflow reference policy.
- `docs/security/operations.md`: external-state inventory, staging verification, alert, rollback, and Ruleset runbook.

## Task 1: Capture the Reproducible Security Baseline

**Files:**

- Create: `tests/worker-security.test.mjs`
- Modify: none of the production files

**Interfaces:**

- Consumes: the current default Worker export from `worker/index.js` and mock Worker bindings.
- Produces: `dispatch(request, env)` test harness reused by Tasks 2–6 and explicit failing cases for each confirmed Worker finding.

- [ ] **Step 1: Record the current clean/dirty state and baseline results**

Run without altering dependencies:

```powershell
git status --short --branch
npm test
npm run check
npm audit --omit=dev --json
npm audit --json
npm explain js-yaml sharp ws minimatch wrangler
```

Save audit output outside tracked source or in the task transcript. Expected: tests/check establish the starting state; audits either reproduce the known high findings or provide the new exact dependency chains.

- [ ] **Step 2: Write the Worker test harness and failing characterization tests**

The test module must construct a Request, call the Worker's exported `fetch`, and provide spies for `WIKI_DATA`, `VECTORIZE`, `AI_RATE_LIMITER`, `AI_DAILY_BUDGET`, and provider `fetch`. Add named tests for:

```js
test("rejects an unlisted origin without ACAO", async () => {})
test("does not expose the debug route", async () => {})
test("debug in a search body cannot change the response", async () => {})
test("rejects an oversized streaming body before storage or provider work", async () => {})
test("rate denial happens before daily budget and provider work", async () => {})
test("daily budget denial happens before retrieval and provider work", async () => {})
```

Each test must assert both the HTTP result and zero calls to every downstream spy that should not be reached.

- [ ] **Step 3: Run the characterization tests and verify the expected failures**

Run:

```powershell
npm test -- tests/worker-security.test.mjs
```

Expected: failures demonstrate wildcard CORS, public debug behavior, unbounded input, and missing abuse controls. Harness errors do not count as valid failures.

- [ ] **Step 4: Commit the test-only baseline**

```powershell
git add tests/worker-security.test.mjs
git commit -m "test: reproduce worker security gaps"
```

## Task 2: Remove Production Debug Surfaces

**Files:**

- Modify: `worker/index.js`
- Test: `tests/worker-security.test.mjs`

**Interfaces:**

- Consumes: existing Worker router and search body parsing.
- Produces: no `/api/debug` route and no response behavior controlled by a `debug` body property.

- [ ] **Step 1: Tighten the failing tests**

Assert that `GET /api/debug` returns `404`, the body contains no environment or binding names, and `{ query: "safe", debug: true }` is rejected as invalid input or behaves exactly like `{ query: "safe" }` without prompt/context fields.

- [ ] **Step 2: Run the two debug tests and verify failure**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "debug"
```

Expected: at least one debug exposure test fails against the current implementation.

- [ ] **Step 3: Delete both debug paths**

Remove the `/api/debug` router branch, body-controlled debug response fields, and any helper reachable only from those paths. Unknown routes return a minimal `404`; internal errors return a request ID and generic message only.

- [ ] **Step 4: Verify debug removal**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "debug"
rg "/api/debug|body\.debug" worker tests
```

Expected: tests pass and the source search has no production matches.

- [ ] **Step 5: Commit**

```powershell
git add worker/index.js tests/worker-security.test.mjs
git commit -m "fix: remove worker debug surfaces"
```

## Task 3: Centralize Exact CORS, Bounded Input, and API Security Headers

**Files:**

- Create: `worker/security.js`
- Modify: `worker/index.js`
- Modify: `worker/wrangler.toml`
- Test: `tests/worker-security.test.mjs`

**Interfaces:**

- Consumes: `env.ALLOWED_ORIGINS`, `env.MAX_REQUEST_BYTES`, `env.MAX_QUERY_CHARS`, `env.MAX_QUERY_BYTES`, and `env.UPSTREAM_TIMEOUT_MS`.
- Produces:
  - `parsePositiveInt(value, name): number`
  - `resolveCors(request, env): { allowed: boolean, headers: Headers }`
  - `readJsonWithLimit(request, maxBytes): Promise<unknown>`
  - `validateSearchBody(value, limits): { query: string }`
  - `applyApiSecurityHeaders(headers): Headers`
  - `jsonResponse(body, status, request, env): Response`

- [ ] **Step 1: Add failing exact-Origin tests**

Use an allowlist containing `https://notes.example.com` and assert:

- That exact origin is echoed with `Vary: Origin`.
- `https://notes.example.com.evil.test`, `https://sub.notes.example.com`, `http://notes.example.com`, `null`, malformed values, and unlisted origins return `403` without ACAO.
- An allowed OPTIONS request advertises only `POST`, `Content-Type`, and required application headers.
- Ordinary, error, and streaming responses use the same CORS computation.

- [ ] **Step 2: Add failing input-boundary tests**

Cover non-POST (`405`), wrong content type (`415`), declared and chunked bodies over the byte limit (`413`), malformed JSON (`400`), non-object JSON (`400`), empty/whitespace query (`400`), too many characters (`400`), and too many UTF-8 bytes (`400`). Assert no KV, Vectorize, budget, or provider call.

- [ ] **Step 3: Add failing API-header tests**

Every API response, including SSE, must contain:

```text
Content-Security-Policy: default-src 'none'; base-uri 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store
```

- [ ] **Step 4: Run focused tests and verify failure**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "origin|preflight|body|query|header|streaming"
```

- [ ] **Step 5: Implement the security helpers**

`readJsonWithLimit` must acquire the stream reader, total actual `Uint8Array.byteLength`, cancel on overflow, decode once within the limit, then call `JSON.parse`. Do not use `request.json()` before the limit. `resolveCors` parses `ALLOWED_ORIGINS` into complete URL origins and compares equality only. Missing or invalid allowlist/limits throw a configuration error that the router converts to `503` without ACAO.

- [ ] **Step 6: Route every response exit through the helpers**

Call the CORS check before reading the body. Apply the same headers to preflight, validation errors, provider errors, successful JSON, and streaming responses. Ensure a caller without an Origin still traverses all non-CORS controls and does not become privileged.

- [ ] **Step 7: Add conservative non-secret defaults to Wrangler configuration**

Add explicit positive values for request bytes, query characters/bytes, result count, context bytes, output tokens, and upstream timeout. Do not put credentials in `[vars]`.

- [ ] **Step 8: Run tests and checks**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **Step 9: Commit**

```powershell
git add worker/security.js worker/index.js worker/wrangler.toml tests/worker-security.test.mjs
git commit -m "fix: enforce worker request boundaries"
```

## Task 4: Add Cloudflare Short-Window Rate Limiting

**Files:**

- Modify: `worker/index.js`
- Modify: `worker/wrangler.toml`
- Test: `tests/worker-security.test.mjs`

**Interfaces:**

- Consumes: `env.AI_RATE_LIMITER.limit({ key }): Promise<{ success: boolean }>` and a Cloudflare-provided client address used only as the limiter key.
- Produces: `enforceRateLimit(request, env): Promise<void>`, throwing a typed denial converted to `429` or a binding failure converted to `503`.

- [ ] **Step 1: Add failing ordering and response tests**

Assert an allowed request calls the limiter after validation but before the daily budget, storage, Vectorize, or DeepSeek. A `{ success: false }` result returns `429` with bounded `Retry-After`. A missing or throwing binding returns `503`; it never bypasses the limit.

- [ ] **Step 2: Verify failure**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "rate"
```

- [ ] **Step 3: Configure and call the binding**

Add an `AI_RATE_LIMITER` `[[ratelimits]]` binding with an explicit namespace ID, count, and period supported by the deployed Cloudflare account. Use `CF-Connecting-IP` as the anonymous abuse key without logging it. If a future Access subject exists, prefer that subject. Keep the limiter call ahead of all cost-bearing work.

- [ ] **Step 4: Verify rate behavior and all Worker tests**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **Step 5: Commit**

```powershell
git add worker/index.js worker/wrangler.toml tests/worker-security.test.mjs
git commit -m "fix: rate limit ai search requests"
```

## Task 5: Enforce an Atomic UTC Daily AI Request Budget

**Files:**

- Create: `worker/daily-ai-budget.js`
- Create: `tests/worker-daily-budget.test.mjs`
- Modify: `worker/index.js`
- Modify: `worker/wrangler.toml`
- Test: `tests/worker-security.test.mjs`

**Interfaces:**

- Consumes: `env.AI_DAILY_BUDGET`, `env.DAILY_AI_REQUEST_LIMIT`, and `env.AI_DAILY_BUDGET.idFromName("global")`.
- Produces:
  - `transitionDailyBudget(state, nowDay, limit): { state: { day: string, used: number }, allowed: boolean, remaining: number }`
  - exported `class DailyAiBudget` with `fetch(request): Promise<Response>` accepting `POST /reserve`.
  - `reserveDailyAiRequest(env): Promise<{ remaining: number }>` in the Worker pipeline.

- [ ] **Step 1: Write pure state-transition tests**

Test first use, exact final allowed reservation, denial after the limit, UTC day rollover, corrupt stored state, and invalid non-positive limits. The transition increments only when allowed.

- [ ] **Step 2: Write concurrent Durable Object contract tests**

Launch more reserve promises than the limit against one fake serialized storage instance. Assert exactly `limit` responses are allowed and all others are denied. Denied requests must not increment `used`.

- [ ] **Step 3: Run and verify failure**

```powershell
npm test -- tests/worker-daily-budget.test.mjs
```

- [ ] **Step 4: Implement the Durable Object**

Use a UTC `YYYY-MM-DD` day value and one storage transaction or the Durable Object's serialized event semantics for read/check/increment. Return only `allowed`, `remaining`, and next-reset metadata. Do not accept a caller-supplied increment greater than one.

- [ ] **Step 5: Add Worker integration tests**

Assert reservation happens after the rate limiter and immediately before the first provider-cost-bearing operation. A denial returns `429` with reset-derived `Retry-After`; a missing, malformed, or throwing binding returns `503`. Validation and rate denials do not reserve budget. An ambiguous provider failure does not refund the reservation.

- [ ] **Step 6: Wire the binding and migration**

Export `DailyAiBudget` from the Worker module. Add the `AI_DAILY_BUDGET` Durable Object binding, one uniquely tagged SQLite-class migration, and a positive `DAILY_AI_REQUEST_LIMIT` variable. Do not reuse a migration tag already deployed.

- [ ] **Step 7: Bound each accepted request's maximum cost**

Before the provider call, cap search result count, accumulated UTF-8 context bytes, and DeepSeek output tokens. Abort the upstream request at `UPSTREAM_TIMEOUT_MS`. Add tests showing truncation happens before request construction and timeout returns a generic response.

- [ ] **Step 8: Run focused and complete Worker tests**

```powershell
npm test -- tests/worker-daily-budget.test.mjs tests/worker-security.test.mjs
npm run check
```

- [ ] **Step 9: Commit**

```powershell
git add worker/daily-ai-budget.js worker/index.js worker/wrangler.toml tests/worker-daily-budget.test.mjs tests/worker-security.test.mjs
git commit -m "fix: enforce daily ai request budget"
```

## Task 6: Make Search and AI Rendering DOM-Safe

**Files:**

- Modify: `quartz/components/scripts/search-ai.inline.js`
- Create: `tests/search-ai-xss.test.mjs`

**Interfaces:**

- Consumes: API search results, AI answer text, localStorage history, and result URLs.
- Produces:
  - `appendTextElement(parent, tagName, text, className): HTMLElement`
  - `toSafeResultUrl(value, siteBase): URL | null`
  - renderer functions that construct nodes without parsing untrusted HTML.

- [ ] **Step 1: Create malicious DOM fixtures**

Exercise suggestion, history, answer, and modal flows with:

```js
const attacks = [
  "<script>globalThis.pwned = true</script>",
  '<img src=x onerror="globalThis.pwned = true">',
  '"><svg/onload=globalThis.pwned=true>',
  "javascript:alert(1)",
]
```

The harness mounts the minimum required DOM, mocks fetch/localStorage, renders each value, and asserts it appears only as text, creates no `script`, `img`, or `svg` element from the payload, installs no event attribute, and creates no dangerous link.

- [ ] **Step 2: Run tests and verify failure**

```powershell
npm test -- tests/search-ai-xss.test.mjs
```

- [ ] **Step 3: Replace dynamic HTML parsing with DOM construction**

Use `textContent`, `createTextNode`, `createElement`, `classList`, and explicit safe attributes. Render AI answers as plain text with whitespace preserved by CSS. Parse URLs with `new URL`; allow only the expected site origin and explicitly approved `http:`/`https:` destinations. Treat localStorage content as untrusted.

- [ ] **Step 4: Prove every search surface is safe**

```powershell
npm test -- tests/search-ai-xss.test.mjs
rg "innerHTML|insertAdjacentHTML|outerHTML" quartz/components/scripts/search-ai.inline.js
```

Expected: tests pass. Any remaining match is a literal-only template with a test proving that no untrusted interpolation reaches it; otherwise remove it.

- [ ] **Step 5: Run the repository frontend tests and checks**

```powershell
npm test
npm run check
```

- [ ] **Step 6: Commit**

```powershell
git add quartz/components/scripts/search-ai.inline.js tests/search-ai-xss.test.mjs
git commit -m "fix: render ai search content safely"
```

## Task 7: Encode Generated Markdown and Sanitize Raw HTML Paths

**Files:**

- Modify: `scripts/daily_digest/render.py`
- Modify: `tests/python/test_daily_rendering.py`
- Modify: `quartz/processors/parse.ts`
- Modify: `quartz/plugins/transformers/ofm.ts`
- Modify: `quartz.config.ts`
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `tests/quartz-html-sanitization.test.mjs`

**Interfaces:**

- Consumes: untrusted AI/external title, summary, description, author, repository name, and URL fields.
- Produces:
  - Python `escape_markdown_text(value: object) -> str`
  - Python `safe_external_url(value: object) -> str | None`
  - one shared rehype sanitize schema applied after every `rehypeRaw` execution.

- [ ] **Step 1: Add failing Python renderer tests**

Feed script tags, event attributes, Markdown link injection, closing delimiters, control characters, and `javascript:`/dangerous `data:` URLs through every external field. Assert generated Markdown contains inert text, rejects the unsafe URL, and retains a valid `https:` URL.

- [ ] **Step 2: Verify Python failures**

```powershell
python -m unittest tests.python.test_daily_rendering -v
```

- [ ] **Step 3: Implement context-specific producer encoding**

`escape_markdown_text` normalizes to text and escapes Markdown structural punctuation and raw HTML delimiters. `safe_external_url` parses URLs independently and accepts only configured `http:`/`https:` destinations. Never use one generic escape function for both text and URLs.

- [ ] **Step 4: Add failing Quartz sanitizer tests**

Create fixtures for both `parse.ts` and `ofm.ts` paths. Assert removal of `script`, event attributes, `javascript:` links, executable SVG/MathML, and unsafe embedded content while retaining the site's documented code blocks, tables, images, headings, and OFM constructs.

- [ ] **Step 5: Verify sanitizer failures**

```powershell
npm test -- tests/quartz-html-sanitization.test.mjs
```

- [ ] **Step 6: Add and configure `rehype-sanitize`**

Install a current compatible `rehype-sanitize` version without unrelated upgrades. Define one explicit schema and apply it immediately after every `rehypeRaw` path in `parse.ts` and `ofm.ts`. Permit only required tags/attributes and `http`, `https`, and intentionally supported safe protocols. Event attributes, scripts, executable embedded namespaces, and dangerous protocols remain denied.

- [ ] **Step 7: Run renderer, sanitizer, and full-build verification**

```powershell
python -m unittest tests.python.test_daily_rendering -v
npm test -- tests/quartz-html-sanitization.test.mjs
npx quartz build
npm test
npm run check
```

Inspect the malicious fixture's built HTML and confirm it contains inert text but no executable node or unsafe URL.

- [ ] **Step 8: Commit**

```powershell
git add scripts/daily_digest/render.py tests/python/test_daily_rendering.py quartz/processors/parse.ts quartz/plugins/transformers/ofm.ts quartz.config.ts package.json package-lock.json tests/quartz-html-sanitization.test.mjs
git commit -m "fix: sanitize generated quartz content"
```

## Task 8: Add the Feasible Static-Site CSP and Security Policy

**Files:**

- Modify: `quartz/components/Head.tsx`
- Test: `tests/quartz-html-sanitization.test.mjs`
- Create: `docs/security/operations.md`

**Interfaces:**

- Consumes: the generated site's actual script, style, image, font, frame, form, and Worker connection sources.
- Produces: an early CSP meta policy and referrer meta policy compatible with the verified build; a runbook for HTTP-only headers at the serving layer.

- [ ] **Step 1: Add a generated-page policy test**

Build a representative page and assert the policy meta element precedes executable content. The test also inventories every inline script/style and external source so a policy that silently blocks the site cannot pass.

- [ ] **Step 2: Verify the test fails before policy insertion**

```powershell
npm test -- tests/quartz-html-sanitization.test.mjs --test-name-pattern "content security policy"
```

- [ ] **Step 3: Add the narrowest build-compatible meta policy**

Start from explicit directives for `default-src`, `script-src`, `style-src`, `img-src`, `font-src`, `connect-src`, `object-src 'none'`, `base-uri 'self'`, and `form-action`. Include only origins found in the inventory. Use hashes for stable inline assets where the build can keep them synchronized. Never add `unsafe-eval`. If current Quartz inline code makes `unsafe-inline` temporarily unavoidable, constrain it to the affected directive, document each occurrence and its removal path, and do not claim the policy blocks inline XSS.

Add `<meta name="referrer" content="strict-origin-when-cross-origin">`. Do not place `frame-ancestors` in meta CSP because browsers ignore it there.

- [ ] **Step 4: Document serving-layer-only headers**

In `docs/security/operations.md`, state that GitHub Pages does not enforce repository `_headers` files. Require the production proxy/host to set `X-Content-Type-Options`, `Permissions-Policy`, `frame-ancestors`, and HSTS only after HTTPS/subdomain review. Include curl-based staging checks and expected exact values.

- [ ] **Step 5: Verify the complete generated site**

```powershell
npx quartz build
npm test -- tests/quartz-html-sanitization.test.mjs
npm run check
```

Load the production-like build with CSP violation reporting in browser tooling and resolve every unexpected violation before accepting the policy.

- [ ] **Step 6: Commit**

```powershell
git add quartz/components/Head.tsx tests/quartz-html-sanitization.test.mjs docs/security/operations.md
git commit -m "fix: add compatible site security policy"
```

## Task 9: Add Structured, Redaction-Safe Security Events

**Files:**

- Modify: `worker/security.js`
- Modify: `worker/index.js`
- Modify: `tests/worker-security.test.mjs`
- Modify: `docs/security/operations.md`

**Interfaces:**

- Consumes: terminal request decision, request ID, route, status, duration, reason code, and coarse budget percentage.
- Produces: `logSecurityEvent(consoleLike, event): void`, emitting exactly one bounded JSON object per terminal decision.

- [ ] **Step 1: Add failing event-schema and redaction tests**

Cover `origin_denied`, `invalid_input`, `body_too_large`, `rate_denied`, `daily_budget_denied`, `upstream_timeout`, `upstream_failure`, and `closed_failure`. Inject sentinel secrets into every header/body/provider field and assert serialized logs contain none of them, no raw client IP, and no stack trace.

- [ ] **Step 2: Verify failures**

```powershell
npm test -- tests/worker-security.test.mjs --test-name-pattern "log|redact|event"
```

- [ ] **Step 3: Implement a fixed event schema**

Allow only:

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

Construct this object from approved primitives rather than sanitizing an arbitrary object. Clamp strings and numeric ranges. Generate or reuse a non-secret request ID. Emit one line at the final response boundary.

- [ ] **Step 4: Document alert inputs without changing Cloudflare**

Add the exact reason codes, recommended windows, and thresholds for 401/403, 413, 429, budget 80%/95%, 5xx, and upstream failures. Document retention and rollback questions. Mark Observability, Logpush, dashboards, and alert creation as approval-gated external operations.

- [ ] **Step 5: Verify**

```powershell
npm test -- tests/worker-security.test.mjs
npm run check
```

- [ ] **Step 6: Commit**

```powershell
git add worker/security.js worker/index.js tests/worker-security.test.mjs docs/security/operations.md
git commit -m "feat: add redacted worker security events"
```

## Task 10: Pin Every Third-Party GitHub Action to a Verified SHA

**Files:**

- Create: `tests/actions-pinned.test.mjs`
- Modify: `.github/workflows/deploy.yaml`
- Modify: `.github/workflows/collect-github-trending.yaml`
- Optionally modify only if already present: `.github/dependabot.yml`

**Interfaces:**

- Consumes: every `uses:` entry under `.github/workflows`.
- Produces: a repository invariant that remote action refs match `owner/repository@` followed by exactly 40 hexadecimal characters; local `./` actions are exempt.

- [ ] **Step 1: Write the failing policy test**

Parse both `.yml` and `.yaml`. Report the workflow path and mutable `uses:` string. The test must fail for the confirmed mutable tags and pass for local actions and Docker image references governed by a separate digest policy.

- [ ] **Step 2: Verify the current workflows fail**

```powershell
npm test -- tests/actions-pinned.test.mjs
```

- [ ] **Step 3: Resolve SHAs from official repositories**

For `actions/checkout@v6`, `actions/setup-node@v7`, `actions/setup-python@v7`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, and `actions/deploy-pages@v4`, retrieve the official tag/ref and dereference annotated tags to the commit. Cross-check the commit on the official repository. Do not use a search-engine snippet and do not invent a value.

- [ ] **Step 4: Replace tags and preserve reviewable comments**

Write each reference as `owner/repository@<verified commit>` followed by its
human-readable release comment, and require the portion after `@` to match
`^[0-9a-f]{40}$`. Copy the independently verified commit itself; do not use
illustrative or fabricated SHA text in the workflow.

- [ ] **Step 5: Configure automated pin updates only if Dependabot already exists**

Preserve existing ecosystems and add the `github-actions` ecosystem at `/` with the repository's established schedule. If Dependabot is absent, record this as a separate follow-up rather than broadening this security patch.

- [ ] **Step 6: Run workflow and complete tests**

```powershell
npm test -- tests/actions-pinned.test.mjs tests/deploy-workflow.test.mjs tests/daily-workflow.test.mjs tests/daily-watchdog.test.mjs
npm run check
```

- [ ] **Step 7: Commit**

```powershell
git add .github/workflows/deploy.yaml .github/workflows/collect-github-trending.yaml tests/actions-pinned.test.mjs
git commit -m "ci: pin actions to immutable commits"
```

## Task 11: Remediate Vulnerable npm Dependency Chains

**Files:**

- Modify: `package.json`
- Modify: `package-lock.json`
- Modify: `docs/security/operations.md` only if an exception is necessary

**Interfaces:**

- Consumes: fresh `npm audit --json`, `npm audit --omit=dev --json`, and `npm explain` graphs.
- Produces: zero production high/critical findings and either zero full high/critical findings or an explicit, owner-bound, expiring development-only exception.

- [ ] **Step 1: Reproduce and classify every current finding**

```powershell
npm audit --omit=dev --json
npm audit --json
npm explain js-yaml
npm explain sharp
npm explain ws
npm explain minimatch
npm explain wrangler
```

For each advisory, record whether it is production/development, direct/transitive, reachable in build/deploy/runtime, the nearest direct dependency, and the minimum fixed version.

- [ ] **Step 2: Upgrade one direct dependency group at a time**

Choose the smallest semver-compatible direct upgrade that removes the vulnerable transitive version. After each group, inspect `git diff -- package.json package-lock.json` and reject unrelated lockfile churn. Do not run `npm audit fix --force`.

- [ ] **Step 3: Verify each dependency-specific behavior**

After `sharp` changes, build image-bearing content. After Quartz/Markdown dependencies change, run sanitizer and renderer fixtures. After `wrangler` changes, run Worker tests and a configuration dry validation that does not deploy. After glob/YAML/WebSocket chains change, run workflow/config parsing and the complete test suite.

```powershell
npx quartz build
npm test
npm run check
```

- [ ] **Step 4: Enforce the audit acceptance gate**

```powershell
npm audit --omit=dev --audit-level=high
npm audit --audit-level=high
```

Expected: production exits zero with no high/critical. Full audit also exits zero; if an upstream-unfixable development-only finding remains, stop for user review and add a specific exception containing advisory ID, dependency path, reachability, compensating control, owner, and expiry date no more than 90 days away.

- [ ] **Step 5: Commit**

```powershell
git add package.json package-lock.json docs/security/operations.md
git commit -m "build: remediate high severity dependencies"
```

## Task 12: Final Repository Verification

**Files:**

- Modify only files already listed if a verification failure reveals an in-scope defect.

**Interfaces:**

- Consumes: all deliverables from Tasks 1–11.
- Produces: one evidence record showing every repository acceptance criterion passed before any external mutation.

- [ ] **Step 1: Run all focused security tests**

```powershell
npm test -- tests/worker-security.test.mjs tests/worker-daily-budget.test.mjs tests/search-ai-xss.test.mjs tests/quartz-html-sanitization.test.mjs tests/actions-pinned.test.mjs
python -m unittest tests.python.test_daily_rendering -v
```

- [ ] **Step 2: Run full build, tests, checks, and audits**

```powershell
npx quartz build
npm test
npm run check
npm audit --omit=dev --audit-level=high
npm audit --audit-level=high
git diff --check
```

- [ ] **Step 3: Inspect the diff for scope and secrets**

```powershell
git status --short
git diff --stat
git diff --check
rg "DEEPSEEK_API_KEY|Authorization:|Bearer |api/debug|body\.debug" worker quartz scripts .github docs tests
```

Expected: only intended files changed, no secret value is present, and debug matches exist only in negative tests or documentation.

- [ ] **Step 4: Review against the design acceptance criteria**

Map each criterion in the spec to a passing test or documented external gate. Do not mark external Ruleset, deployment, or alert criteria complete from repository evidence alone.

- [ ] **Step 5: Commit final test-only corrections if any**

```powershell
git add worker quartz scripts tests .github package.json package-lock.json docs/security/operations.md
git commit -m "test: verify repository security hardening"
```

## Task 13: Read-Only External Inventory and Approval-Gated Rollout

**Files:**

- Modify: `docs/security/operations.md` only to record confirmed names, IDs, current settings, and approved rollback steps without secrets.

**Interfaces:**

- Consumes: Cloudflare account/Worker configuration, GitHub Rulesets/branch protection, current successful check names, and staging URL.
- Produces: a reviewed external change set; actual mutations remain separate approval-gated operations.

- [ ] **Step 1: Inspect Cloudflare state without mutation**

Read current Worker version, route, bindings, variables by name, Durable Object migrations, rate-limit availability, observability, Logpush, alerting, and rollback target. Never print secret values. Compare the deployed binding names with `worker/wrangler.toml`.

- [ ] **Step 2: Inspect GitHub state without mutation**

Read current Rulesets, branch protection, repository default branch, bypass actors, and exact successful job/check names from recent `main` runs. Save a redacted snapshot and identify any automation that writes to `main`.

- [ ] **Step 3: Present the proposed external diff and request approval**

Separate approvals for:

- Creating the Rate Limiting binding and Durable Object namespace/migration.
- Setting allowed-origin and limit variables/secrets.
- Deploying staging, then production.
- Enabling Observability/Logpush and alerts.
- Changing the `main` Ruleset.

Include exact rollback versions and explain that a wrong required-check name can lock merges.

- [ ] **Step 4: After approval, stage and verify Cloudflare changes**

Verify allowed/disallowed Origin, preflight, oversized chunked body, rate denial, concurrent daily-limit denial, UTC rollover behavior with a test namespace, provider timeout, stream headers, structured/redacted logs, CSP, and the normal search experience. Follow `AGENTS.md` deployment verification before production promotion.

- [ ] **Step 5: After separate approval, configure alerts**

Create thresholds for origin/auth denial spikes, 413, 429, budget 80%/95%, 5xx, and provider failure. Trigger each safely in staging, confirm delivery, retention, and deduplication, then enable production routing.

- [ ] **Step 6: After separate approval, protect `main`**

Require pull requests, at least one approval, stale-approval dismissal, resolved conversations, and only exact checks already proven successful on `main`; disable force pushes and branch deletion; preserve reviewed bot/admin bypass. Immediately verify a test pull request can satisfy all required checks.

- [ ] **Step 7: Record external verification without secrets**

Update `docs/security/operations.md` with resource names, rule identifiers, deployed version, verification timestamp, alert names, and rollback commands. Do not store account tokens, secret values, raw logs, or personal data.

---

## Completion Gate

Repository implementation is complete only after Task 12 passes. Production hardening is complete only after Task 13 has an approved and verified staging/production rollout, alerts have been exercised, and the GitHub Ruleset has been verified with a real pull request. If external authorization is withheld, report the repository work as complete and the corresponding production controls as pending; do not imply they are active.
