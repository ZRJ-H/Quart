import assert from "node:assert/strict"
import test from "node:test"

import { createWorker } from "../src/index.js"

const SITE_ORIGIN = "https://fdogelover.github.io"
const INDEX_URL = SITE_ORIGIN + "/Quart/wiki-index.json"

function environment() {
  return {
    SITE_ORIGIN,
    INDEX_URL,
    DEEPSEEK_API_KEY: "test-key",
  }
}

function searchRequest(origin = SITE_ORIGIN) {
  return new Request("https://wiki-search.example/api/search", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      origin,
    },
    body: JSON.stringify({ query: "量子模型" }),
  })
}

test("rejects an unapproved browser origin before external fetches", async () => {
  let fetchCalls = 0
  const worker = createWorker({
    fetchImpl: async () => {
      fetchCalls += 1
      throw new Error("must not fetch")
    },
  })

  const response = await worker.fetch(searchRequest("https://evil.example"), environment(), {})

  assert.equal(response.status, 403)
  assert.equal(fetchCalls, 0)
})

test("streams sources and transformed DeepSeek chunks", async () => {
  const entries = [
    {
      id: "paper",
      name: "量子模型论文",
      category: "arxiv-daily",
      summary: "量子模型取得进展",
      content: "量子模型正文",
      tags: ["AI"],
      links: [],
      page_path: "AI论文日报/2026-09-11",
      last_updated: "2026-09-11",
    },
  ]
  const deepSeekBody = [
    'data: {"choices":[{"delta":{"content":"答案"}}]}',
    "",
    "data: [DONE]",
    "",
  ].join("\n")

  const worker = createWorker({
    fetchImpl: async (url) => {
      if (String(url) === INDEX_URL) {
        const body = JSON.stringify(entries)
        return new Response(body, {
          headers: {
            "content-type": "application/json",
            "content-length": String(new TextEncoder().encode(body).byteLength),
          },
        })
      }
      return new Response(deepSeekBody, {
        headers: { "content-type": "text/event-stream" },
      })
    },
  })

  const response = await worker.fetch(searchRequest(), environment(), {})
  const body = await response.text()

  assert.equal(response.status, 200)
  assert.equal(response.headers.get("access-control-allow-origin"), SITE_ORIGIN)
  assert.match(body, /"type":"sources"/)
  assert.match(body, /"page_path":"AI论文日报\/2026-09-11"/)
  assert.match(body, /"type":"chunk","text":"答案"/)
  assert.match(body, /"type":"done"/)
})
