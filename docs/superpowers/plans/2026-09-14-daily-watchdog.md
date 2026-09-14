# Daily Knowledge Cloudflare Watchdog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent Cloudflare cron watchdog that retries the existing daily GitHub Actions workflow when the current Shanghai-date pages are missing.

**Architecture:** A focused module inside the existing Cloudflare search Worker checks four public GitHub Pages URLs at 11:00 and 14:00 Asia/Shanghai. If any page is missing, it first checks for a queued or running collection job, then dispatches `collect-github-trending.yaml` with a repository-scoped secret; the existing GitHub workflow remains responsible for collection and deployment.

**Tech Stack:** Cloudflare Workers, JavaScript ES modules, Wrangler 4, Node.js test runner, GitHub REST API and Actions.

**Spec:** `docs/superpowers/specs/2026-09-14-daily-watchdog-design.md`

## Global Constraints

- Preserve the current GitHub repository, collection workflow, Quartz build, GitHub Pages hosting and search Worker endpoints.
- Run checks at UTC 03:00 and 06:00, corresponding to Asia/Shanghai 11:00 and 14:00.
- Dispatch only when at least one of four current-date pages is missing and no collection run is queued or in progress.
- Never store or log the GitHub token in source, Wrangler configuration, generated files or workflow output.
- Treat 404 as a missing page; fail closed on other page-check or GitHub API errors.
- Keep the watchdog deterministic and idempotent; no KV, D1, Queue or Workflow dependency.

---

### Task 1: Implement and test watchdog decision logic

**Files:**

- Create: `worker/daily-watchdog.js`
- Create: `tests/daily-watchdog.test.mjs`

**Interfaces:**

- Produces: `shanghaiDate(now: Date) -> string` in `YYYY-MM-DD` format.
- Produces: `runDailyWatchdog(env, options?) -> Promise<{ status: string, date: string, missing: string[] }>`.
- Consumes: `env.GITHUB_TOKEN`, `env.GITHUB_OWNER`, `env.GITHUB_REPO`, `env.GITHUB_BRANCH`, `env.GITHUB_WORKFLOW`, `env.SITE_BASE_URL`.
- `options.fetch` injects the transport and `options.now` injects the clock for deterministic tests.

- [ ] **Step 1: Write failing tests for the observable decisions**

  Add literal fixtures that verify: a UTC 16:30 instant maps to the next Shanghai date; four HTTP 200 pages return `healthy` without a GitHub call; one 404 page with an active run returns `collection-active`; one 404 page with no active run sends exactly one `POST` with `{ "ref": "main" }`; a page 500 and a dispatch response other than 204 reject.

- [ ] **Step 2: Run `node --test tests/daily-watchdog.test.mjs`**

  Expected: fail because `worker/daily-watchdog.js` does not exist.

- [ ] **Step 3: Implement the minimal module**

  Use four fixed section slugs, `Intl.DateTimeFormat` with `Asia/Shanghai`, parallel page checks, the public workflow-runs endpoint, and an authenticated dispatch request. Await every request and log no token values.

- [ ] **Step 4: Re-run `node --test tests/daily-watchdog.test.mjs`**

  Expected: all watchdog behavior tests pass.

- [ ] **Step 5: Commit**

  Run `git add worker/daily-watchdog.js tests/daily-watchdog.test.mjs && git commit -m "feat: add daily publication watchdog"`.

### Task 2: Connect Cron and secret deployment

**Files:**

- Modify: `worker/index.js`
- Modify: `worker/wrangler.toml`
- Modify: `.github/workflows/deploy.yaml`
- Modify: `tests/deploy-workflow.test.mjs`
- Create: `tests/watchdog-worker.test.mjs`

**Interfaces:**

- Existing Worker default export adds `scheduled(controller, env, ctx)` and calls `ctx.waitUntil(runDailyWatchdog(env))`.
- Wrangler config adds `crons = ["0 3 * * *", "0 6 * * *"]` and non-secret GitHub/site variables.
- Deploy workflow maps repository secret `WATCHDOG_GITHUB_TOKEN` to a temporary file, runs `wrangler secret bulk`, deletes the file, then deploys the existing Worker with `CF_API_TOKEN`.

- [ ] **Step 1: Write failing integration/config tests**

  Import the real Worker and assert its scheduled handler registers one tracked promise whose result follows the injected page/GitHub responses. Parse `worker/wrangler.toml` and assert both cron triggers and all non-secret variables. Parse `.github/workflows/deploy.yaml` and assert the Cloudflare step receives `WATCHDOG_GITHUB_TOKEN`, syncs `GITHUB_TOKEN`, and still skips cleanly when `CF_API_TOKEN` is absent.

- [ ] **Step 2: Run `node --test tests/watchdog-worker.test.mjs tests/deploy-workflow.test.mjs`**

  Expected: fail because the scheduled handler, triggers and secret sync do not exist.

- [ ] **Step 3: Implement integration and configuration**

  Add only the watchdog import/handler to the existing Worker. Add `[triggers]` and `[vars]` to TOML. In the deploy step, create a mode-restricted temporary JSON secret file through Python, call `wrangler secret bulk`, and remove it in a shell trap; if `WATCHDOG_GITHUB_TOKEN` is empty, emit a warning but do not block Pages deployment.

- [ ] **Step 4: Run focused tests and Wrangler validation**

  Run `node --test tests/watchdog-worker.test.mjs tests/deploy-workflow.test.mjs`, `npx wrangler types --config worker/wrangler.toml`, and `npx wrangler deploy --dry-run --config worker/wrangler.toml --outdir .wrangler/watchdog-dry-run`.

- [ ] **Step 5: Run full regressions**

  Run `python -m unittest discover -s tests/python -p "test_*.py" -v`, `npm test`, `npx tsc --noEmit --incremental false`, and `git diff --check`.

- [ ] **Step 6: Commit**

  Run `git add worker/index.js worker/daily-watchdog.js worker/wrangler.toml .github/workflows/deploy.yaml tests && git commit -m "ci: add Cloudflare backup scheduler"`.

### Task 3: Document, deploy and verify production

**Files:**

- Modify: `MEMORY.md`
- Generated locally but ignored: `.wrangler/watchdog-dry-run/**`

**Interfaces:**

- Production health remains `GET https://doge-wiki-search.zstufjj2004.workers.dev/api/health`.
- Cloudflare structured logs expose `healthy`, `collection-active`, `dispatched` or a sanitized error.
- GitHub deployment uses the already-configured `CF_API_TOKEN` and newly configured `WATCHDOG_GITHUB_TOKEN` repository secret.

- [ ] **Step 1: Update operations memory**

  Record both cron times, secret names, the four-page decision rule, failure policy and manual recovery URL without including credential values.

- [ ] **Step 2: Run final local verification**

  Re-run the focused watchdog tests, full Python and Node tests, Wrangler dry-run, TypeScript check and `git diff --check`.

- [ ] **Step 3: Commit and push**

  Commit documentation with `git commit -m "docs: record daily watchdog operations"`, push the branch to `main`, and preserve unrelated user changes.

- [ ] **Step 4: Observe deployment**

  Wait for `Deploy Quartz to GitHub Pages`; verify the Cloudflare sync step, Pages deployment and resulting main SHA all succeed. If the repository secret is absent, stop and report the exact setup requirement rather than claiming the watchdog is active.

- [ ] **Step 5: Verify live behavior boundaries**

  Confirm the existing Worker health and search endpoints still respond, confirm the deployed Worker version contains both cron triggers through Wrangler/API evidence, and verify the current daily pages remain available. Do not deliberately dispatch collection while all pages exist.
