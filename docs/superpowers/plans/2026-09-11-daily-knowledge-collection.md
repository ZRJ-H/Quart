# Daily Knowledge Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate factual, detailed Chinese daily digests for five knowledge sections, publish them automatically every day, and keep the weekly entry current.

**Architecture:** A Python standard-library package collects normalized `Article` records from RSS/Atom, arXiv, and Hacker News, then an evidence-bound summarizer returns structured Chinese fields or falls back to deterministic source text. One GitHub Actions workflow creates a single atomic content commit; the existing Pages workflow deploys only successful collection runs.

**Tech Stack:** Python 3.13 standard library, Node.js 22 for the existing GitHub Trending generator, GitHub Actions, Quartz 4, `node:test`, Python `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-11-daily-knowledge-collection-design.md`

## Global Constraints

- Run every day at 08:30 Asia/Shanghai (`30 0 * * *`) and allow manual execution.
- Use the Shanghai calendar date for filenames; prefer same-day items and fall back no farther than 48 hours.
- Produce 8 AI technology items, 8 current-affairs items, 5 arXiv papers, 8 Hacker News items, and keep the existing 25-project GitHub Trending limit.
- Require at least 3 AI technology items, 3 current-affairs items, 3 papers, and 5 Hacker News items before replacing files.
- Never invent facts; model output may only transform supplied evidence, and deterministic rendering must work without a model key.
- Network calls use a named User-Agent, 20-second timeout, two retries, and HTTP(S)-only URLs.
- Re-running identical inputs for a date must not change the generated files.
- Do not add paid APIs or Python package dependencies.

---

### Task 1: Normalize syndication data and enforce the 48-hour window

**Files:**

- Create: `scripts/daily_digest/__init__.py`
- Create: `scripts/daily_digest/models.py`
- Create: `scripts/daily_digest/feeds.py`
- Create: `tests/python/test_daily_feeds.py`

**Interfaces:**

- Produces: `Article(id, title, url, source, published_at, summary, score=0, comments=0, discussion_url="", extra={})`.
- Produces: `parse_feed(xml_text: str, source: str) -> list[Article]`.
- Produces: `select_recent(articles: list[Article], now: datetime, limit: int, window_hours: int = 48) -> list[Article]`.
- Produces: `deduplicate(articles: list[Article]) -> list[Article]`.

- [ ] **Step 1: Write failing feed and time-window tests**

```python
def test_parse_feed_normalizes_rss_and_atom():
    articles = parse_feed(RSS_AND_ATOM_FIXTURES, "Fixture Source")
    assert articles[0].title == "Model release"
    assert articles[0].url == "https://example.com/model"
    assert articles[0].published_at.isoformat() == "2026-09-11T00:15:00+00:00"
    assert articles[0].summary == "Measured result, not HTML."

def test_select_recent_uses_48_hour_fallback_and_deduplicates():
    selected = select_recent(ARTICLES_WITH_DUPLICATES, SHANGHAI_NOON, limit=3)
    assert [article.id for article in selected] == ["today", "yesterday"]
```

- [ ] **Step 2: Run `python -m unittest tests.python.test_daily_feeds -v` and verify failures are missing imports/interfaces**
- [ ] **Step 3: Implement the immutable data model, RSS/Atom namespace parsing, HTML cleanup, date parsing, normalized URL/title deduplication, and recent selection**
- [ ] **Step 4: Re-run the feed tests and verify all pass**
- [ ] **Step 5: Commit with `git commit -m "feat: normalize daily feed articles"`**

### Task 2: Add reliable source collectors

**Files:**

- Create: `scripts/daily_digest/http.py`
- Create: `scripts/daily_digest/sources.py`
- Create: `scripts/daily_digest/collectors.py`
- Create: `tests/python/test_daily_collectors.py`

**Interfaces:**

- Consumes: `Article`, `parse_feed`, `deduplicate`, and `select_recent` from Task 1.
- Produces: `fetch_text(url: str, *, timeout: int = 20, retries: int = 2) -> str`.
- Produces: `fetch_json(url: str, *, timeout: int = 20, retries: int = 2) -> object`.
- Produces: `collect_feed_category(sources: tuple[FeedSource, ...], now: datetime, limit: int) -> list[Article]`.
- Produces: `collect_arxiv(now: datetime, limit: int = 5) -> list[Article]`.
- Produces: `collect_hacker_news(now: datetime, limit: int = 8) -> list[Article]`.

The AI source constants are:

```python
AI_SOURCES = (
    FeedSource("OpenAI", "https://openai.com/news/rss.xml"),
    FeedSource("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    FeedSource("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    FeedSource("Microsoft Research", "https://www.microsoft.com/en-us/research/feed/"),
    FeedSource("Google Research", "https://research.google/blog/rss/"),
)
```

The current-affairs source constants are:

```python
NEWS_SOURCES = (
    FeedSource("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    FeedSource("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    FeedSource("NPR World", "https://feeds.npr.org/1004/rss.xml"),
)
```

- [ ] **Step 1: Write failing tests with complete recorded API/feed payloads and injected transport functions**

```python
def test_hacker_news_collects_ranked_stories_and_discussion_evidence():
    items = collect_hacker_news(NOW, limit=2, fetch_json=fake_hn_transport)
    assert [(item.score, item.comments) for item in items] == [(420, 88), (200, 30)]
    assert items[0].discussion_url == "https://news.ycombinator.com/item?id=101"
    assert items[0].extra["top_comments"] == ["First discussion point"]

def test_arxiv_combines_categories_and_removes_duplicate_papers():
    papers = collect_arxiv(NOW, limit=5, fetch_text=fake_arxiv_transport)
    assert [paper.id for paper in papers] == ["2609.00001", "2609.00002"]
```

- [ ] **Step 2: Run the collector tests and verify they fail because collectors do not exist**
- [ ] **Step 3: Implement retrying HTTP helpers, source configuration, multi-feed collection, the arXiv query `cat:cs.AI OR cat:cs.LG OR cat:cs.CL`, HN top-story/item/comment retrieval, sorting, and minimum-count exceptions**
- [ ] **Step 4: Re-run collector tests and verify all pass**
- [ ] **Step 5: Commit with `git commit -m "feat: collect daily public sources"`**

### Task 3: Generate evidence-bound detailed Chinese summaries

**Files:**

- Create: `scripts/daily_digest/summarize.py`
- Create: `scripts/daily_digest/render.py`
- Create: `tests/python/test_daily_rendering.py`

**Interfaces:**

- Consumes: normalized `Article` lists.
- Produces: `summarize(category: str, articles: list[Article], api_key: str | None, go_key: str | None) -> DigestSummary`.
- Produces: `render_digest(category: str, run_date: date, articles: list[Article], summary: DigestSummary) -> str`.
- `DigestSummary` contains ordered item fields and exactly three `{fact, inference}` trend records.

- [ ] **Step 1: Write failing rendering and validation tests**

```python
def test_layered_digest_keeps_sources_and_category_fields():
    markdown = render_digest("AI论文日报", RUN_DATE, PAPERS, VALID_SUMMARY)
    assert "## 深度解读" in markdown
    assert "**研究问题**" in markdown
    assert "**实验结果**" in markdown
    assert "**局限**" in markdown
    assert "https://arxiv.org/abs/2609.00001" in markdown
    assert markdown.count("**事实依据**") == 3
    assert markdown.count("**编辑判断**") == 3

def test_invalid_model_output_falls_back_to_source_evidence():
    result = summarize("AI科技动态", ARTICLES, api_key="key", go_key=None, request=fake_invalid_response)
    assert result.mode == "deterministic"
    assert ARTICLES[0].summary in render_digest("AI科技动态", RUN_DATE, ARTICLES, result)
```

- [ ] **Step 2: Run rendering tests and verify the new interfaces are absent**
- [ ] **Step 3: Implement deterministic per-category fields, model JSON prompting, DeepSeek/GO endpoint fallback, strict index/count validation, 250–400 Chinese-character top-three detail, 80–150 character remaining summaries, and fact/inference trend labels**
- [ ] **Step 4: Re-run rendering tests and verify all pass**
- [ ] **Step 5: Commit with `git commit -m "feat: render evidence-bound daily digests"`**

### Task 4: Orchestrate atomic daily files and weekly synthesis

**Files:**

- Create: `scripts/collect-daily-content.py`
- Create: `scripts/generate-weekly-report.py`
- Create: `tests/python/test_daily_pipeline.py`
- Modify: `content/index.md`

**Interfaces:**

- Consumes: Task 2 collectors and Task 3 summary/renderer.
- Produces CLI: `python scripts/collect-daily-content.py --content-root content --date YYYY-MM-DD --raw-dir PATH`.
- Produces CLI: `python scripts/generate-weekly-report.py --content-root content --date YYYY-MM-DD`.
- Writes through a temporary sibling followed by `os.replace`; no target changes occur until every category validates.

- [ ] **Step 1: Write failing integration tests for idempotency, atomic failure, expected paths, and weekly links**

```python
def test_pipeline_writes_four_valid_today_files_atomically():
    run_pipeline(ROOT, RUN_DATE, collectors=FIXTURE_COLLECTORS, summarizer=fallback_summarizer)
    assert generated_paths(ROOT) == {
        "AI科技动态/2026-09-11.md",
        "时政要闻/2026-09-11.md",
        "AI论文日报/2026-09-11.md",
        "Hacker News/2026-09-11.md",
    }

def test_failed_category_leaves_existing_files_unchanged():
    before = snapshot(ROOT)
    with self.assertRaises(CollectionError):
        run_pipeline(ROOT, RUN_DATE, collectors=ONE_EMPTY_COLLECTOR)
    assert snapshot(ROOT) == before
```

- [ ] **Step 2: Run pipeline tests and verify they fail on missing orchestration**
- [ ] **Step 3: Implement argument parsing, Shanghai dates, raw JSON diagnostics, all-category validation, atomic replacement, deterministic ordering, and weekly aggregation from repository Markdown**
- [ ] **Step 4: Replace the hard-coded `[[周报/2026-W25|...]]` homepage link with `[[周报|浏览全部]]`**
- [ ] **Step 5: Re-run all Python tests twice and verify the second run produces identical snapshots**
- [ ] **Step 6: Commit with `git commit -m "feat: orchestrate daily and weekly knowledge notes"`**

### Task 5: Consolidate collection automation and deployment triggering

**Files:**

- Modify: `.github/workflows/collect-github-trending.yaml`
- Modify: `.github/workflows/deploy.yaml`
- Modify: `tests/deploy-workflow.test.mjs`
- Create: `tests/daily-workflow.test.mjs`

**Interfaces:**

- Consumes the CLIs from Task 4 and existing `scripts/github_trending.py` / `scripts/generate-github-trending.js`.
- Produces workflow display name `Collect Daily Knowledge`.
- Produces a single staged `content/` commit per successful run.
- Produces successful `workflow_run` input for `Deploy Quartz to GitHub Pages`.

- [ ] **Step 1: Write failing Node workflow tests**

```javascript
test("daily collection runs on schedule, manual dispatch, and collector changes", () => {
  assert.equal(workflow.name, "Collect Daily Knowledge")
  assert.deepEqual(workflow.on.schedule, [{ cron: "30 0 * * *" }])
  assert.ok(workflow.on.workflow_dispatch)
  assert.deepEqual(workflow.on.push.branches, ["main"])
})

test("Pages deployment waits for the consolidated collector", () => {
  assert.deepEqual(deploy.on.workflow_run.workflows, ["Collect Daily Knowledge"])
})
```

- [ ] **Step 2: Run the two workflow test files and verify failures name the old workflow and missing collector steps**
- [ ] **Step 3: Rename and expand the collection workflow, add Python tests before network collection, pass existing model secrets, run all collectors and weekly generation, and retain one guarded commit/push step**
- [ ] **Step 4: Update `deploy.yaml` to listen to `Collect Daily Knowledge`**
- [ ] **Step 5: Run Node workflow tests and the full `npm test` suite**
- [ ] **Step 6: Commit with `git commit -m "ci: automate daily knowledge collection"`**

### Task 6: Record operations and perform local production verification

**Files:**

- Modify: `MEMORY.md`

**Interfaces:**

- Consumes all prior tasks.
- Produces an operations record with the schedule, sources, failure policy, summary format, and recovery commands.

- [ ] **Step 1: Append Decision Log and Session Log entries to `MEMORY.md`, update the site URL to `https://zrj-h.github.io/Quart/`, and remove the obsolete Pages-enable pending note**
- [ ] **Step 2: Run `python -m unittest discover -s tests/python -p "test_*.py" -v`**
- [ ] **Step 3: Run `npm test` and `npx tsc --noEmit --incremental false`**
- [ ] **Step 4: Run the collector against live sources with `--date 2026-09-11`, without model keys, and verify all four new Markdown files meet count/link requirements**
- [ ] **Step 5: Run `npx quartz build --directory content`, copy the generated search index into `public/`, create `public/.nojekyll`, and verify all six section routes are emitted**
- [ ] **Step 6: Run Prettier only on changed files and `git diff --check`**
- [ ] **Step 7: Commit with `git commit -m "docs: record daily collection operations"`**

### Task 7: Push, observe automatic collection, and verify production

**Files:**

- Generated by Actions: `content/AI科技动态/2026-09-11.md`
- Generated by Actions: `content/时政要闻/2026-09-11.md`
- Generated by Actions: `content/AI论文日报/2026-09-11.md`
- Generated by Actions: `content/Hacker News/2026-09-11.md`
- Generated by Actions: `content/GitHub Trending/2026-09-11.md`
- Generated by Actions: `content/周报/2026-W37.md`

**Interfaces:**

- Consumes the public GitHub repository, configured model secrets, and Pages environment.
- Produces a successful collection commit followed by a successful Pages deployment.

- [ ] **Step 1: Fetch `origin/main`, verify a fast-forward push, and push the implementation commits**
- [ ] **Step 2: Observe the push-triggered `Collect Daily Knowledge` run through the public Actions API until completion**
- [ ] **Step 3: If collection fails, inspect the exact failing job/step, reproduce locally, add a failing regression test, and fix before pushing again**
- [ ] **Step 4: Verify the Actions-created content commit contains all expected 2026-09-11 files and that `Deploy Quartz to GitHub Pages` succeeds for it**
- [ ] **Step 5: Verify HTTP 200 and non-empty entries for `/AI科技动态`, `/时政要闻`, `/GitHub-Trending`, `/AI论文日报`, `/Hacker-News`, `/周报`, plus the four daily detail URLs**
- [ ] **Step 6: Verify `static/contentIndex.json` and `wiki-index-light.json` return HTTP 200 and include the new daily pages**
- [ ] **Step 7: Run final local tests, type checking, `git diff --check`, and remote SHA verification before reporting completion**
