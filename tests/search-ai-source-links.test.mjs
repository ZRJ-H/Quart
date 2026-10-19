import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import vm from "node:vm"

const sourceUrl = new URL("../quartz/components/scripts/search-ai.inline.js", import.meta.url)
const source = await readFile(sourceUrl, "utf8")
const start = source.indexOf("  function escapeHtml(text) {")
const end = source.indexOf("  function renderEmptyState() {", start)
assert.ok(start >= 0 && end > start, "production source-card renderer must be present")

// Execute the real renderer without initializing the UI or making network requests.
const now = Date.parse("2026-10-19T12:00:00Z")
const renderSourceCards = vm.runInNewContext(source.slice(start, end) + "\nrenderSourceCards", {
  CAT_LABELS: {},
  Date: class extends Date {
    static now() {
      return now
    }
  },
  window: { location: { origin: "https://zrj-h.github.io", pathname: "/Quart/search" } },
})

function card(overrides = {}) {
  return {
    name: "Daily source",
    category: "daily",
    last_updated: "2026-10-19",
    ...overrides,
  }
}

function assertLink(item, path) {
  const html = renderSourceCards([card(item)])
  assert.equal(html.match(/href="([^"]*)"/)?.[1], "https://zrj-h.github.io/Quart/" + path)
  assert.doesNotMatch(html, /source-card--archived/)
  return html
}

for (const [name, item, expected] of [
  [
    "Hacker News daily IDs",
    { id: "daily/Hacker News/2026-10-19#story-1" },
    "Hacker-News/2026-10-19",
  ],
  [
    "GitHub Trending daily IDs",
    { id: "daily/GitHub Trending/2026-10-19#repository-1" },
    "GitHub-Trending/2026-10-19",
  ],
  ["Chinese daily IDs", { id: "daily/新闻/2026-10-19#条目" }, "%E6%96%B0%E9%97%BB/2026-10-19"],
  [
    "Hacker News source_file paths",
    { source_file: "Hacker News/2026-10-19" },
    "Hacker-News/2026-10-19",
  ],
  [
    "GitHub Trending source_file paths",
    { source_file: "GitHub Trending/2026-10-19" },
    "GitHub-Trending/2026-10-19",
  ],
  [
    "Chinese source_file paths",
    { source_file: "新闻/2026-10-19" },
    "%E6%96%B0%E9%97%BB/2026-10-19",
  ],
  [
    "whitespace in every daily ID path segment",
    { id: "daily/Daily  News/技术\t日报/a b#story" },
    "Daily--News/%E6%8A%80%E6%9C%AF-%E6%97%A5%E6%8A%A5/a-b",
  ],
  [
    "whitespace in every source_file path segment",
    { source_file: "Daily  News/技术\t日报/a b" },
    "Daily--News/%E6%8A%80%E6%9C%AF-%E6%97%A5%E6%8A%A5/a-b",
  ],
]) {
  test(`source cards use Quartz slugs for ${name}`, () => {
    assertLink(item, expected)
  })
}

test("daily sources older than seven days stay archived without a link", () => {
  const html = renderSourceCards([
    card({ id: "daily/Hacker News/2026-10-12#story", last_updated: "2026-10-12T11:59:59Z" }),
  ])
  assert.doesNotMatch(html, /href=/)
  assert.match(html, /source-card--archived/)
  assert.match(html, /已归档/)
})

test("daily sources exactly seven days old keep their link", () => {
  assertLink(
    { id: "daily/Hacker News/2026-10-12#story", last_updated: "2026-10-12T12:00:00Z" },
    "Hacker-News/2026-10-12",
  )
})

test("daily sources without a date retain the existing link behavior", () => {
  assertLink(
    { id: "daily/Hacker News/2026-10-19#story", last_updated: "" },
    "Hacker-News/2026-10-19",
  )
})

test("source_file retains precedence over daily ID and age fallback", () => {
  assertLink(
    {
      source_file: "GitHub Trending/2026-10-19",
      id: "daily/Hacker News/2026-10-01#story",
      last_updated: "2026-10-01",
    },
    "GitHub-Trending/2026-10-19",
  )
})

test("wiki entries without a source page stay archived", () => {
  const html = renderSourceCards([card({ id: "entities/example" })])
  assert.doesNotMatch(html, /href=/)
  assert.match(html, /source-card--archived/)
})

test("source-card text and href attributes remain HTML-escaped", () => {
  const html = assertLink(
    {
      source_file: 'Hacker News/it\'s "quoted" <page>',
      name: '<img src=x onerror="alert(1)">',
      summary: "摘要：<script>alert('1')</script> & text",
      category: '<svg onload="alert(1)">',
      last_updated: '<img src=x onerror="alert(2)">',
    },
    "Hacker-News/it&#039;s-%22quoted%22-%3Cpage%3E",
  )
  assert.doesNotMatch(html, /<img|<script|<svg/)
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/)
  assert.match(html, /&lt;script&gt;alert\(&#039;1&#039;\)&lt;\/script&gt; &amp; text/)
  assert.match(html, /&lt;svg onload=&quot;alert\(1\)&quot;&gt;/)
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(2\)&quot;&gt;/)
})

test("empty source lists render no cards", () => {
  for (const items of [undefined, null, []]) assert.equal(renderSourceCards(items), "")
})
