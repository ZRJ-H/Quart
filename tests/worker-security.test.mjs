import assert from "node:assert/strict"
import test from "node:test"

import "./cloudflare-runtime-register.mjs"

const worker = (await import("../worker/index.js")).default

const SITE_ORIGIN = "https://zrj-h.github.io"

function testEnv(overrides = {}) {
  return {
    SITE_BASE_URL: `${SITE_ORIGIN}/Quart`,
    WIKI_DATA: { get: async () => null },
    SEARCH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    ...overrides,
  }
}

function searchRequest(body, headers = {}) {
  return new Request("https://worker.example/api/search", {
    method: "POST",
    headers: {
      Origin: SITE_ORIGIN,
      "Content-Type": "application/json",
      "CF-Connecting-IP": "203.0.113.9",
      ...headers,
    },
    body: typeof body === "string" ? body : JSON.stringify(body),
  })
}

test("CORS rejects an untrusted origin and only reflects the configured site origin", async () => {
  const denied = await worker.fetch(
    new Request("https://worker.example/api/health", {
      headers: { Origin: "https://evil.example" },
    }),
    testEnv(),
  )
  assert.equal(denied.status, 403)
  assert.equal(denied.headers.get("access-control-allow-origin"), null)

  const allowed = await worker.fetch(
    new Request("https://worker.example/api/health", {
      headers: { Origin: SITE_ORIGIN },
    }),
    testEnv(),
  )
  assert.equal(allowed.status, 200)
  assert.equal(allowed.headers.get("access-control-allow-origin"), SITE_ORIGIN)
  assert.equal(allowed.headers.get("vary"), "Origin")
  assert.equal(allowed.headers.get("x-content-type-options"), "nosniff")
  assert.equal(allowed.headers.get("referrer-policy"), "no-referrer")
  assert.match(allowed.headers.get("permissions-policy") || "", /camera=\(\)/)
  assert.equal(allowed.headers.get("cache-control"), "no-store")
  assert.match(
    allowed.headers.get("content-security-policy") || "",
    /default-src 'none'.*frame-ancestors 'none'/,
  )
})

test("OPTIONS validates both the origin and the route", async () => {
  const deniedOrigin = await worker.fetch(
    new Request("https://worker.example/api/search", {
      method: "OPTIONS",
      headers: { Origin: "https://evil.example" },
    }),
    testEnv(),
  )
  assert.equal(deniedOrigin.status, 403)

  const unknownRoute = await worker.fetch(
    new Request("https://worker.example/not-an-api", {
      method: "OPTIONS",
      headers: { Origin: SITE_ORIGIN },
    }),
    testEnv(),
  )
  assert.equal(unknownRoute.status, 404)

  const allowed = await worker.fetch(
    new Request("https://worker.example/api/search", {
      method: "OPTIONS",
      headers: {
        Origin: SITE_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
      },
    }),
    testEnv(),
  )
  assert.equal(allowed.status, 204)
  assert.equal(allowed.headers.get("access-control-allow-origin"), SITE_ORIGIN)
  assert.equal(allowed.headers.get("vary"), "Origin")
})

test("production debug routes and request flags are unavailable", async () => {
  const route = await worker.fetch(
    new Request("https://worker.example/api/debug?key=private/key", {
      headers: { Origin: SITE_ORIGIN },
    }),
    testEnv(),
  )
  assert.equal(route.status, 404)

  const flag = await worker.fetch(searchRequest({ query: "AI", debug: true }), testEnv())
  assert.equal(flag.status, 400)
  assert.deepEqual(await flag.json(), { error: "invalid request" })
})

test("search requires JSON and rejects malformed or oversized payloads with safe errors", async () => {
  const wrongType = await worker.fetch(
    searchRequest("query=AI", { "Content-Type": "text/plain" }),
    testEnv(),
  )
  assert.equal(wrongType.status, 415)
  assert.deepEqual(await wrongType.json(), { error: "application/json required" })

  const malformed = await worker.fetch(searchRequest("{"), testEnv())
  assert.equal(malformed.status, 400)
  assert.deepEqual(await malformed.json(), { error: "invalid JSON" })

  const oversized = await worker.fetch(searchRequest({ query: "x".repeat(9000) }), testEnv())
  assert.equal(oversized.status, 413)
  assert.deepEqual(await oversized.json(), { error: "request too large" })
})

test("search validates query, filters, and sort while clamping limit before Vectorize", async () => {
  const invalidQuery = await worker.fetch(searchRequest({ query: { nested: true } }), testEnv())
  assert.equal(invalidQuery.status, 400)

  const invalidFilters = await worker.fetch(
    searchRequest({ query: "AI", filters: { tags: "companies", time: "forever" } }),
    testEnv(),
  )
  assert.equal(invalidFilters.status, 400)

  const invalidSort = await worker.fetch(
    searchRequest({ query: "AI", sort: "drop-table" }),
    testEnv(),
  )
  assert.equal(invalidSort.status, 400)

  let observedTopK = null
  const response = await worker.fetch(
    searchRequest({ query: "AI", limit: 999 }),
    testEnv({
      VECTORIZE: {
        async query(_query, options) {
          observedTopK = options.topK
          return { matches: [] }
        },
      },
    }),
  )
  assert.equal(response.status, 200)
  assert.equal(observedTopK, 30)

  const futureCategory = await worker.fetch(
    searchRequest({ query: "AI", filters: { tags: ["future-category"], time: "all" } }),
    testEnv(),
  )
  assert.equal(futureCategory.status, 200)
})

test("search rate limiting is route-scoped and fails closed when unavailable", async () => {
  const limited = await worker.fetch(
    searchRequest({ query: "AI" }),
    testEnv({
      SEARCH_RATE_LIMITER: {
        async limit({ key }) {
          return { success: key !== "203.0.113.9:/api/search" }
        },
      },
    }),
  )
  assert.equal(limited.status, 429)
  assert.equal(limited.headers.get("retry-after"), "60")
  assert.deepEqual(await limited.json(), { error: "rate limit exceeded" })

  const unavailable = await worker.fetch(
    searchRequest({ query: "AI" }),
    testEnv({ SEARCH_RATE_LIMITER: undefined }),
  )
  assert.equal(unavailable.status, 503)
  assert.deepEqual(await unavailable.json(), { error: "service unavailable" })
})
