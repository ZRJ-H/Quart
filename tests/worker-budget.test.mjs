import assert from "node:assert/strict"
import test from "node:test"

import "./cloudflare-runtime-register.mjs"

const { DurableObject } = await import("cloudflare:workers")
const workerModule = await import("../worker/index.js")

const SITE_ORIGIN = "https://zrj-h.github.io"
const FIXED_NOW = new Date("2026-09-14T23:59:59Z")

test("reserveDailyAiBudget returns 429 when the UTC daily budget is exhausted", async () => {
  const reserve = workerModule.reserveDailyAiBudget
  assert.equal(typeof reserve, "function", "reserveDailyAiBudget must be exported")

  const response = await reserve(
    {
      DEEPSEEK_API_KEY: "test-secret",
      AI_DAILY_LIMIT: "25",
      AI_BUDGET: {
        getByName(name) {
          assert.equal(name, "2026-09-14")
          return { reserve: async () => ({ allowed: false, remaining: 0 }) }
        },
      },
    },
    SITE_ORIGIN,
    FIXED_NOW,
  )

  assert.equal(response.status, 429)
  assert.equal(response.headers.get("access-control-allow-origin"), SITE_ORIGIN)
  assert.deepEqual(await response.json(), { error: "daily AI budget exhausted" })
})

test("reserveDailyAiBudget fails closed when paid search has no budget binding", async () => {
  const reserve = workerModule.reserveDailyAiBudget
  assert.equal(typeof reserve, "function", "reserveDailyAiBudget must be exported")

  const response = await reserve(
    { DEEPSEEK_API_KEY: "test-secret", AI_BUDGET: undefined },
    SITE_ORIGIN,
    FIXED_NOW,
  )
  assert.equal(response.status, 503)
  assert.deepEqual(await response.json(), { error: "service unavailable" })
})

test("reserveDailyAiBudget skips quota storage when no paid provider key is configured", async () => {
  const reserve = workerModule.reserveDailyAiBudget
  assert.equal(typeof reserve, "function", "reserveDailyAiBudget must be exported")

  let namespaceRead = false
  const response = await reserve(
    {
      AI_BUDGET: {
        getByName() {
          namespaceRead = true
          throw new Error("must not read quota storage")
        },
      },
    },
    SITE_ORIGIN,
    FIXED_NOW,
  )
  assert.equal(response, null)
  assert.equal(namespaceRead, false)
})

test("reserveDailyAiBudget passes the configured daily hard limit to the UTC-day object", async () => {
  const reserve = workerModule.reserveDailyAiBudget
  assert.equal(typeof reserve, "function", "reserveDailyAiBudget must be exported")

  let observedLimit = null
  const response = await reserve(
    {
      DEEPSEEK_API_KEY: "test-secret",
      AI_DAILY_LIMIT: "25",
      AI_BUDGET: {
        getByName(name) {
          assert.equal(name, "2026-09-14")
          return {
            async reserve(limit) {
              observedLimit = limit
              return { allowed: true, remaining: 24 }
            },
          }
        },
      },
    },
    SITE_ORIGIN,
    FIXED_NOW,
  )

  assert.equal(response, null)
  assert.equal(observedLimit, 25)
})

test("DailyAiBudget reserves atomically up to its hard limit", async () => {
  const Budget = workerModule.DailyAiBudget
  assert.equal(typeof Budget, "function", "DailyAiBudget must be exported by the Worker module")
  assert.ok(Budget.prototype instanceof DurableObject)

  let count = 0
  let transactionCount = 0
  const state = {
    storage: {
      async transaction(callback) {
        transactionCount += 1
        return callback({
          async get(key) {
            assert.equal(key, "count")
            return count
          },
          async put(key, value) {
            assert.equal(key, "count")
            count = value
          },
        })
      },
    },
  }
  const budget = new Budget(state, {})

  assert.deepEqual(await budget.reserve(2), { allowed: true, remaining: 1 })
  assert.deepEqual(await budget.reserve(2), { allowed: true, remaining: 0 })
  assert.deepEqual(await budget.reserve(2), { allowed: false, remaining: 0 })
  assert.equal(count, 2)
  assert.equal(transactionCount, 3)
})
