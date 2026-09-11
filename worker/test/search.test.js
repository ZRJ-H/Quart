import assert from "node:assert/strict"
import test from "node:test"

import { searchEntries } from "../src/search.js"

test("body-only matches survive search scoring", () => {
  const results = searchEntries(
    [
      {
        id: "body",
        name: "研究记录",
        summary: "",
        content: "这一条正文讨论量子模型的最新进展",
        tags: [],
        links: [],
      },
    ],
    "量子模型",
  )

  assert.equal(results.length, 1)
  assert.equal(results[0].id, "body")
  assert.ok(results[0].score > 0)
})

test("title matches rank ahead of summary matches", () => {
  const results = searchEntries(
    [
      { id: "summary", name: "研究", summary: "量子模型", content: "", tags: [], links: [] },
      { id: "title", name: "量子模型", summary: "", content: "", tags: [], links: [] },
    ],
    "量子模型",
  )

  assert.deepEqual(
    results.map((entry) => entry.id),
    ["title", "summary"],
  )
})

test("linked entries are included once as related results", () => {
  const results = searchEntries(
    [
      {
        id: "alpha",
        name: "Alpha",
        summary: "目标主题",
        content: "",
        tags: [],
        links: ["Beta", "Beta"],
      },
      {
        id: "beta",
        name: "Beta",
        summary: "关联背景",
        content: "",
        tags: [],
        links: [],
      },
    ],
    "目标主题",
  )

  assert.deepEqual(
    results.map((entry) => entry.id),
    ["alpha", "beta"],
  )
  assert.equal(results[1].is_related, true)
})
