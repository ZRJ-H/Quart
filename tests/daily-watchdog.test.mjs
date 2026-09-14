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
  return new Response(status === 204 ? null : body, { status })
}

function pageFetch(
  statuses,
  githubResponse = response(200, JSON.stringify({ workflow_runs: [] })),
) {
  const calls = []
  const fetch = async (input, init = {}) => {
    const url = String(input)
    calls.push({ url, init })
    if (url.includes("pages.dev")) {
      const section = decodeURIComponent(new URL(url).pathname.split("/").filter(Boolean)[0])
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
    { AI科技动态: 404 },
    response(200, JSON.stringify({ workflow_runs: [{ status: "queued" }] })),
  )

  const result = await runDailyWatchdog(env, { fetch: transport.fetch, now: NOW })

  assert.equal(result.status, "collection-active")
  assert.deepEqual(result.missing, ["AI科技动态"])
  assert.equal(transport.calls.filter(({ init }) => init.method === "POST").length, 0)
})

test("dispatches the workflow once on main when a page is missing and no run is active", async () => {
  const transport = pageFetch(
    { "Hacker-News": 404 },
    response(200, JSON.stringify({ workflow_runs: [] })),
  )
  const dispatchResponse = response(204)
  const originalFetch = transport.fetch
  transport.fetch = async (input, init = {}) => {
    if (String(input).endsWith("/dispatches")) {
      transport.calls.push({ url: String(input), init })
      return dispatchResponse
    }
    return originalFetch(input, init)
  }

  const result = await runDailyWatchdog(env, {
    fetch: transport.fetch,
    now: NOW,
    logger: { log() {} },
  })
  const dispatches = transport.calls.filter(({ url }) => url.endsWith("/dispatches"))
  const [dispatch] = dispatches

  assert.equal(result.status, "dispatched")
  assert.deepEqual(result.missing, ["Hacker-News"])
  assert.equal(dispatches.length, 1)
  assert.equal(dispatch.init.method, "POST")
  assert.equal(
    dispatch.url,
    "https://api.github.com/repos/ZRJ-H/Quart/actions/workflows/collect-github-trending.yaml/dispatches",
  )
  assert.deepEqual(JSON.parse(dispatch.init.body), { ref: "main" })
  assert.equal(dispatch.init.headers.Authorization, "Bearer test-token")
})

test("fails closed when a page check returns a server error", async () => {
  const transport = pageFetch({ 时政要闻: 500 })

  await assert.rejects(
    runDailyWatchdog(env, { fetch: transport.fetch, now: NOW }),
    /page check failed.*500/,
  )
  assert.equal(
    transport.calls.some(({ url }) => url.endsWith("/dispatches")),
    false,
  )
})

test("rejects a workflow dispatch response other than 204", async () => {
  const transport = pageFetch(
    { AI论文日报: 404 },
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
