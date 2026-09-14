import test from "node:test"
import assert from "node:assert/strict"

import { runDailyWatchdog, shanghaiDate } from "../worker/daily-watchdog.js"

const NOW = new Date("2026-09-14T16:30:00.000Z")
const env = {
  GITHUB_TOKEN: "test-token",
  GITHUB_OWNER: "ZRJ-H",
  GITHUB_REPO: "Quart",
  GITHUB_BRANCH: "main",
  GITHUB_WORKFLOW: "collect-github-trending.yaml",
  SITE_BASE_URL: "https://example.pages.dev",
}

function response(status, body = "") {
  return new Response(body, { status })
}

function pageFetch(statuses, githubResponse = response(200, JSON.stringify({ workflow_runs: [] }))) {
  const calls = []
  const fetch = async (input, init = {}) => {
    const url = String(input)
    calls.push({ url, init })
    if (url.includes("pages.dev")) {
      const section = new URL(url).pathname.split("/").filter(Boolean)[0]
      return response(statuses[section] ?? 200)
    }
    return githubResponse
  }
  return { fetch, calls }
}

test("maps a UTC instant to the Shanghai calendar date", () => {
  assert.equal(shanghaiDate(NOW), "2026-09-15")
})

test("returns healthy and does not call GitHub when all four pages exist", async () => {
  const transport = pageFetch({})

  const result = await runDailyWatchdog(env, { fetch: transport.fetch, now: NOW })

  assert.deepEqual(result, { status: "healthy", date: "2026-09-15", missing: [] })
  assert.equal(transport.calls.filter(({ url }) => url.includes("api.github.com")).length, 0)
})

test("returns collection-active when a page is missing and a run is queued", async () => {
  const transport = pageFetch(
    { "ai-news": 404 },
    response(200, JSON.stringify({ workflow_runs: [{ status: "queued" }] })),
  )

  const result = await runDailyWatchdog(env, { fetch: transport.fetch, now: NOW })

  assert.equal(result.status, "collection-active")
  assert.deepEqual(result.missing, ["ai-news"])
  assert.equal(transport.calls.filter(({ init }) => init.method === "POST").length, 0)
})

test("dispatches the workflow once on main when a page is missing and no run is active", async () => {
  const transport = pageFetch(
    { "hn-daily": 404 },
    response(200, JSON.stringify({ workflow_runs: [] })),
  )
  const dispatchResponse = response(204)
  const originalFetch = transport.fetch
  transport.fetch = async (input, init = {}) => {
    if (String(input).endsWith("/dispatches")) return dispatchResponse
    return originalFetch(input, init)
  }

  const result = await runDailyWatchdog(env, { fetch: transport.fetch, now: NOW })
  const dispatch = transport.calls.find(({ url }) => url.endsWith("/dispatches"))

  assert.equal(result.status, "dispatched")
  assert.deepEqual(result.missing, ["hn-daily"])
  assert.deepEqual(JSON.parse(dispatch.init.body), { ref: "main" })
  assert.equal(dispatch.init.headers.Authorization, "Bearer test-token")
})

test("fails closed when a page check returns a server error", async () => {
  const transport = pageFetch({ "daily-news": 500 })

  await assert.rejects(
    runDailyWatchdog(env, { fetch: transport.fetch, now: NOW }),
    /page check failed.*500/,
  )
  assert.equal(transport.calls.some(({ url }) => url.endsWith("/dispatches")), false)
})

test("rejects a workflow dispatch response other than 204", async () => {
  const transport = pageFetch(
    { "arxiv-daily": 404 },
    response(200, JSON.stringify({ workflow_runs: [] })),
  )
  const originalFetch = transport.fetch
  transport.fetch = async (input, init = {}) => {
    if (String(input).endsWith("/dispatches")) return response(202)
    return originalFetch(input, init)
  }

  await assert.rejects(
    runDailyWatchdog(env, { fetch: transport.fetch, now: NOW }),
    /workflow dispatch failed.*202/,
  )
})
