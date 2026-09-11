import assert from "node:assert/strict"
import test from "node:test"

import {
  escapeHtml,
  normalizeEndpoint,
  resolveIndexUrl,
  scoreLocalEntries,
} from "./search-ai.core.js"

test("keeps a complete Worker endpoint without adding another API path", () => {
  assert.equal(
    normalizeEndpoint("https://worker.example/api/search/"),
    "https://worker.example/api/search",
  )
  assert.equal(normalizeEndpoint(""), "")
})

test("resolves static indexes from the Quartz page root", () => {
  assert.equal(resolveIndexUrl(".", "wiki-index-light.json"), "./wiki-index-light.json")
  assert.equal(resolveIndexUrl("../..", "wiki-index.json"), "../../wiki-index.json")
})

test("static search finds summary, tags, and title with deterministic ranking", () => {
  const entries = [
    {
      id: "summary",
      name: "研究进展",
      summary: "量子模型取得突破",
      category: "arxiv-daily",
      tags: [],
    },
    {
      id: "title",
      name: "量子模型",
      summary: "今日论文",
      category: "arxiv-daily",
      tags: ["AI"],
    },
    {
      id: "miss",
      name: "财经新闻",
      summary: "市场信息",
      category: "daily-news",
      tags: [],
    },
  ]

  const rows = scoreLocalEntries("量子模型", entries, 5)

  assert.deepEqual(
    rows.map((entry) => entry.id),
    ["title", "summary"],
  )
})

test("escapes untrusted titles and history before innerHTML rendering", () => {
  assert.equal(
    escapeHtml('<img src=x onerror="alert(1)">'),
    "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;",
  )
})
