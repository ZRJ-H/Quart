import assert from "node:assert/strict"
import test from "node:test"

import "./cloudflare-runtime-register.mjs"

const worker = (await import("../worker/index.js")).default

const env = {
  GITHUB_TOKEN: "test-token",
  GITHUB_OWNER: "ZRJ-H",
  GITHUB_REPO: "Quart",
  GITHUB_BRANCH: "main",
  GITHUB_WORKFLOW: "collect-github-trending.yaml",
  SITE_BASE_URL: "https://zrj-h.github.io/Quart",
}

test("scheduled watchdog tracks a missing daily page dispatch", async () => {
  const originalFetch = globalThis.fetch
  const calls = []
  globalThis.fetch = async (input, init = {}) => {
    const url = String(input)
    calls.push({ url, init })
    if (url.includes("zrj-h.github.io")) {
      return new Response(null, {
        status: url.includes("AI%E7%A7%91%E6%8A%80%E5%8A%A8%E6%80%81") ? 404 : 200,
      })
    }
    if (url.endsWith("/runs?branch=main&per_page=10")) return Response.json({ workflow_runs: [] })
    if (url.endsWith("/dispatches")) return new Response(null, { status: 204 })
    throw new Error(`unexpected request: ${url}`)
  }

  const tracked = []
  try {
    worker.scheduled({}, env, {
      waitUntil(promise) {
        tracked.push(promise)
      },
    })
    assert.equal(tracked.length, 1)
    const result = await tracked[0]
    assert.equal(result.status, "dispatched")
    assert.deepEqual(result.missing, ["AI科技动态"])
    assert.equal(calls.filter(({ url }) => url.endsWith("/dispatches")).length, 1)
  } finally {
    globalThis.fetch = originalFetch
  }
})
