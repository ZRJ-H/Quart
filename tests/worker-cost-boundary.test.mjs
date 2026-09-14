import assert from "node:assert/strict"
import test from "node:test"

import "./cloudflare-runtime-register.mjs"

const workerModule = await import("../worker/index.js")
const worker = workerModule.default

const SITE_ORIGIN = "https://zrj-h.github.io"

function searchRequest(body) {
  return new Request("https://worker.example/api/search", {
    method: "POST",
    headers: {
      Origin: SITE_ORIGIN,
      "Content-Type": "application/json",
      "CF-Connecting-IP": "203.0.113.10",
    },
    body: JSON.stringify(body),
  })
}

test("an empty selected result set never reserves paid AI budget", async () => {
  let budgetRead = false
  const response = await worker.fetch(searchRequest({ query: "AI" }), {
    ALLOWED_ORIGINS: SITE_ORIGIN,
    DEEPSEEK_API_KEY: "test-secret",
    WIKI_DATA: { get: async () => null },
    SEARCH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    VECTORIZE: {
      query: async () => ({
        matches: [
          {
            id: "vector-only",
            score: 0.99,
            metadata: { name: "Vector only", category: "future-category" },
          },
        ],
      }),
    },
    AI_BUDGET: {
      getByName() {
        budgetRead = true
        throw new Error("budget must not be touched")
      },
    },
  })

  assert.equal(response.status, 200)
  assert.deepEqual(await response.json(), {
    answer: "知识库中未找到相关内容。",
    sources: [],
  })
  assert.equal(budgetRead, false)
})

test("streaming provider failures expose only a generic public error", async () => {
  assert.equal(typeof workerModule.streamDeepSeek, "function")

  const originalFetch = globalThis.fetch
  const chunks = []
  let closed = false
  globalThis.fetch = async () => {
    throw new Error("socket failed with api-key=super-secret")
  }
  try {
    await workerModule.streamDeepSeek(
      "prompt",
      "super-secret",
      {
        async write(chunk) {
          chunks.push(chunk)
        },
        async close() {
          closed = true
        },
      },
      new TextEncoder(),
    )
  } finally {
    globalThis.fetch = originalFetch
  }

  const payload = Buffer.concat(chunks.map((chunk) => Buffer.from(chunk))).toString("utf8")
  assert.match(payload, /provider temporarily unavailable/)
  assert.doesNotMatch(payload, /super-secret|socket failed/)
  assert.equal(closed, true)
})

test("the paid-provider prompt has a hard UTF-8 byte ceiling", () => {
  assert.equal(typeof workerModule.buildPrompt, "function")
  const prompt = workerModule.buildPrompt(
    "解释安全边界",
    [{ id: "large", name: "Large", category: "security", tags: [], last_updated: "2026-09-14" }],
    { large: { content: "界".repeat(100_000), tags: [] } },
    "overview",
  )

  assert.ok(new TextEncoder().encode(prompt).byteLength <= 65_536)
  assert.match(prompt, /解释安全边界/)
})

test("the paid-provider request has bounded output and aborts on timeout", async () => {
  const originalFetch = globalThis.fetch
  const chunks = []
  let requestBody
  let sawSignal = false
  globalThis.fetch = async (_url, options) => {
    requestBody = JSON.parse(options.body)
    sawSignal = options.signal instanceof AbortSignal
    return new Response("data: [DONE]\n\n", {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    })
  }
  try {
    await workerModule.streamDeepSeek(
      "prompt",
      "secret",
      {
        async write(chunk) {
          chunks.push(chunk)
        },
        async close() {},
      },
      new TextEncoder(),
      { timeoutMs: 1_000 },
    )
  } finally {
    globalThis.fetch = originalFetch
  }
  assert.ok(requestBody.max_tokens <= 2_000)
  assert.equal(sawSignal, true)

  let aborted = false
  globalThis.fetch = async (_url, options) =>
    new Promise((_resolve, reject) => {
      options.signal.addEventListener(
        "abort",
        () => {
          aborted = true
          reject(new Error("timed out with internal detail"))
        },
        { once: true },
      )
    })
  try {
    await workerModule.streamDeepSeek(
      "prompt",
      "secret",
      {
        async write(chunk) {
          chunks.push(chunk)
        },
        async close() {},
      },
      new TextEncoder(),
      { timeoutMs: 5 },
    )
  } finally {
    globalThis.fetch = originalFetch
  }
  assert.equal(aborted, true)
  const payload = Buffer.concat(chunks.map((chunk) => Buffer.from(chunk))).toString("utf8")
  assert.doesNotMatch(payload, /internal detail/)
})
