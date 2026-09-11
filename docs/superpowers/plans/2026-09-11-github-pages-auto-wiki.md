# GitHub Pages Auto Wiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Quartz wiki automatically on GitHub Pages with generated static search indexes and an optional Cloudflare Worker-backed DeepSeek answer stream.

**Architecture:** GitHub Actions owns crawling, retention, index generation, Quartz builds, content commits, and Pages deployment. The browser loads a light static index for suggestions and fallback search; a Cloudflare Worker fetches the full static index and streams DeepSeek answers without exposing the API key.

**Tech Stack:** Node.js 22, TypeScript/Preact/Quartz 4.5.2, Python 3 stdlib, GitHub Actions/Pages, Cloudflare Workers ES modules, Node test runner.

**Spec:** `docs/superpowers/specs/2026-09-11-github-pages-auto-wiki-design.md`

## Global Constraints

- GitHub Pages must remain a static deployment; Express and SQLite are compatibility-only.
- Node.js must be version 22 or newer and npm 10.9.2 or newer.
- `DEEPSEEK_API_KEY` must never enter source, generated JSON, logs, or browser JavaScript.
- `AI_SEARCH_ENDPOINT` is a complete endpoint URL and must never receive a second `/api/search` suffix.
- Worker failure must fall back to static search instead of breaking the page.
- Do not replace the existing Quartz visual theme or discard pre-existing uncommitted changes.

---

### Task 1: Generate portable static indexes

**Files:**

- Modify: `scripts/build-wiki-index.py`
- Create: `tests/test_build_wiki_index.py`

**Interfaces:**

- Produces: `collect_entries(vault_dir) -> list[dict]`, `write_json_indexes(entries, full_path, light_path) -> None`, CLI flags `--json-output`, `--light-output`, and `--no-sqlite`.
- Entry fields: `id`, `name`, `type`, `category`, `tags`, `summary`, `content`, `last_updated`, `content_length`, `reference_count`, `links`, `page_path`.

- [ ] **Step 1: Write failing Python tests**

```python
def test_collect_entries_preserves_links_and_page_path(tmp_path):
    write_note(tmp_path, "wiki/entities/Alpha.md", "---\nname: Alpha\n---\nLinks [[Beta]].")
    entries = indexer.collect_entries(str(tmp_path))
    assert entries[0]["links"] == ["Beta"]
    assert entries[0]["page_path"] is None

def test_write_json_indexes_uses_atomic_replace(tmp_path):
    full = tmp_path / "public/wiki-index.json"
    light = tmp_path / "public/wiki-index-light.json"
    indexer.write_json_indexes([sample_entry()], str(full), str(light))
    assert json.loads(full.read_text("utf-8"))[0]["content"] == "body"
    assert "content" not in json.loads(light.read_text("utf-8"))[0]
    assert not list(full.parent.glob("*.tmp"))
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_build_wiki_index -v`
Expected: FAIL because `collect_entries` and `write_json_indexes` do not exist.

- [ ] **Step 3: Implement collection and JSON outputs**

```python
def atomic_write_json(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
    os.replace(temp_path, path)

def write_json_indexes(entries, full_path, light_path):
    atomic_write_json(full_path, entries)
    light_fields = ("id", "name", "type", "category", "tags", "summary",
                    "last_updated", "reference_count", "links", "page_path")
    atomic_write_json(light_path, [{key: row.get(key) for key in light_fields} for row in entries])
```

Refactor daily and wiki parsing to populate the shared entry dictionaries before optionally writing SQLite.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_build_wiki_index -v`
Expected: all static index tests pass.

- [ ] **Step 5: Commit task changes**

```bash
git add scripts/build-wiki-index.py tests/test_build_wiki_index.py
git commit -m "feat: generate static wiki search indexes"
```

### Task 2: Make the browser search endpoint-safe and resilient

**Files:**

- Create: `quartz/components/scripts/search-ai.core.js`
- Create: `quartz/components/scripts/search-ai.core.test.ts`
- Modify: `quartz/components/SearchAI.tsx`
- Modify: `quartz/components/scripts/search-ai.inline.js`
- Modify: `quartz.layout.ts`

**Interfaces:**

- Produces: `normalizeEndpoint(value)`, `scoreLocalEntries(query, entries, limit)`, `resolveIndexUrl(relativeRoot, filename)`, and `escapeHtml(value)`.
- `SearchAIOptions`: `{ endpoint: string }`.
- DOM data: `data-endpoint`, `data-index-light`, and `data-index-full`.

- [ ] **Step 1: Write failing browser-core tests**

```typescript
test("keeps a complete worker endpoint unchanged", () => {
  assert.equal(
    normalizeEndpoint("https://worker.example/api/search"),
    "https://worker.example/api/search",
  )
})

test("static search finds summary and escapes rendered data", () => {
  const rows = scoreLocalEntries(
    "量子模型",
    [{ name: "安全标题", summary: "量子模型进展", tags: [] }],
    5,
  )
  assert.equal(rows.length, 1)
  assert.equal(escapeHtml('<img onerror="x">'), "&lt;img onerror=&quot;x&quot;&gt;")
})
```

- [ ] **Step 2: Run tests and verify RED**

Run: `npx tsx --test quartz/components/scripts/search-ai.core.test.ts`
Expected: FAIL because the core module does not exist.

- [ ] **Step 3: Implement core functions and integrate UI**

```javascript
export function normalizeEndpoint(value) {
  return String(value || "")
    .trim()
    .replace(/\/+$/, "")
}

export function scoreLocalEntries(query, entries, limit = 10) {
  const terms = tokenize(query)
  return entries
    .map((entry) => ({ ...entry, score: scoreEntry(entry, terms) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
}
```

Render relative index paths with Quartz `pathToRoot(fileData.slug)` and call `fetch(endpoint)` directly. On missing endpoint or request failure, render local results and an explicit “AI 服务不可用，已显示本地结果” status. Escape suggestions and history before assigning `innerHTML`.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `npx tsx --test quartz/components/scripts/search-ai.core.test.ts`
Expected: all browser-core tests pass.

- [ ] **Step 5: Commit task changes**

```bash
git add quartz.layout.ts quartz/components/SearchAI.tsx quartz/components/scripts/search-ai.inline.js quartz/components/scripts/search-ai.core.js quartz/components/scripts/search-ai.core.test.ts
git commit -m "fix: make AI search Pages-safe with static fallback"
```

### Task 3: Implement the Cloudflare Worker search API

**Files:**

- Create: `worker/package.json`
- Create: `worker/wrangler.jsonc`
- Create: `worker/src/search.js`
- Create: `worker/src/prompt.js`
- Create: `worker/src/index.js`
- Create: `worker/test/search.test.js`
- Create: `worker/test/worker.test.js`
- Modify: `.gitignore`

**Interfaces:**

- Consumes: `env.DEEPSEEK_API_KEY`, `env.SITE_ORIGIN`, `env.INDEX_URL`.
- Produces: `searchEntries(entries, query, options)`, `buildPrompt(query, results)`, and default module Worker `{ fetch(request, env, ctx) }`.

- [ ] **Step 1: Write failing Worker tests**

```javascript
test("body-only matches survive scoring", () => {
  const rows = searchEntries([{ id: "1", name: "论文", content: "量子模型", tags: [] }], "量子模型")
  assert.equal(rows[0].id, "1")
})

test("rejects an unapproved browser origin", async () => {
  const response = await worker.fetch(requestFrom("https://evil.example"), env(), {})
  assert.equal(response.status, 403)
})
```

- [ ] **Step 2: Run tests and verify RED**

Run: `npm --prefix worker test`
Expected: FAIL because Worker modules do not exist.

- [ ] **Step 3: Implement Worker modules**

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    if (url.pathname === "/api/health" && request.method === "GET") {
      return json({ ok: true, mode: "static-index + deepseek" }, 200, cors(request, env))
    }
    if (url.pathname !== "/api/search") return json({ error: "not_found" }, 404)
    return handleSearch(request, env)
  },
}
```

Validate origin, content length, JSON type, and query length. Cache `INDEX_URL` responses briefly through the Cache API, send `sources` as the first SSE event, then transform DeepSeek SSE chunks into the existing `sources/chunk/done/error` protocol.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `npm --prefix worker test`
Expected: all Worker tests pass without network access.

- [ ] **Step 5: Commit task changes**

```bash
git add worker .gitignore
git commit -m "feat: add Cloudflare Worker AI search API"
```

### Task 4: Automate content updates and GitHub Pages deployment

**Files:**

- Create: `.github/workflows/deploy-pages.yml`
- Create: `tests/test_pages_workflow.mjs`
- Modify: `package.json`
- Modify: `.env.example`

**Interfaces:**

- Workflow inputs: repository variables `SITE_DOMAIN`, `AI_SEARCH_ENDPOINT`; secret `DEEPSEEK_API_KEY` for crawler summaries.
- Workflow outputs: deployed Pages URL and committed generated files under `content/`.

- [ ] **Step 1: Write a failing workflow structure test**

```javascript
test("Pages workflow schedules, builds, persists content, and deploys", () => {
  const workflow = yaml.load(readFileSync(".github/workflows/deploy-pages.yml", "utf8"))
  assert.ok(workflow.on.schedule)
  assert.match(JSON.stringify(workflow), /actions\/deploy-pages@v4/)
  assert.match(JSON.stringify(workflow), /wiki-index-light\.json/)
  assert.match(JSON.stringify(workflow), /git push/)
})
```

- [ ] **Step 2: Run test and verify RED**

Run: `node --test tests/test_pages_workflow.mjs`
Expected: FAIL because the workflow file does not exist.

- [ ] **Step 3: Implement the Pages workflow**

```yaml
on:
  push:
    branches: [master, main]
  schedule:
    - cron: "15 18 * * *"
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write
```

Use `actions/checkout@v6`, `actions/setup-node@v5`, `actions/setup-python@v6`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, and `actions/deploy-pages@v4`. Run each crawler without stopping sibling crawlers, run weekly report only on Sunday, clean old content, commit `content/`, build Quartz, generate both JSON indexes into `public/`, create `public/.nojekyll`, and upload the artifact.

- [ ] **Step 4: Run test and verify GREEN**

Run: `node --test tests/test_pages_workflow.mjs`
Expected: workflow assertions pass.

- [ ] **Step 5: Commit task changes**

```bash
git add .github/workflows/deploy-pages.yml tests/test_pages_workflow.mjs package.json .env.example
git commit -m "feat: automate GitHub Pages publishing"
```

### Task 5: Document deployment and run full verification

**Files:**

- Create: `README.md`
- Modify: `docs/superpowers/plans/2026-09-11-github-pages-auto-wiki.md`

**Interfaces:**

- Documents exact GitHub Pages settings, repository variables/secrets, Worker secret setup, local build, and failure fallback.

- [ ] **Step 1: Write the deployment guide**

Document selecting “GitHub Actions” under Pages settings, setting `AI_SEARCH_ENDPOINT`, configuring `SITE_ORIGIN` and `INDEX_URL`, running `npx wrangler secret put DEEPSEEK_API_KEY`, deploying with `npm --prefix worker run deploy`, and running all local tests.

- [ ] **Step 2: Run all project tests**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`
Expected: all Python tests pass.

Run: `npm test`
Expected: all Quartz/TypeScript tests pass.

Run: `npm --prefix worker test`
Expected: all Worker tests pass.

- [ ] **Step 3: Run static checks and a production build**

Run: `npx tsc --noEmit --incremental false`
Expected: exit 0.

Run: `npx prettier . --check`
Expected: exit 0.

Run: `node quartz/bootstrap-cli.mjs build -o public`
Expected: Quartz build exits 0.

Run: `python scripts/build-wiki-index.py content --no-sqlite --json-output public/wiki-index.json --light-output public/wiki-index-light.json`
Expected: both indexes are generated and the command exits 0.

- [ ] **Step 4: Verify deployment artifacts**

```powershell
@("public/index.html", "public/static/contentIndex.json", "public/wiki-index.json", "public/wiki-index-light.json", "public/.nojekyll") |
  ForEach-Object { if (-not (Test-Path $_)) { throw "Missing artifact: $_" } }
```

Expected: no missing artifact error.

- [ ] **Step 5: Commit documentation and plan completion**

```bash
git add README.md docs/superpowers/plans/2026-09-11-github-pages-auto-wiki.md
git commit -m "docs: explain automated wiki deployment"
```
