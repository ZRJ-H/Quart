import { DurableObject } from "cloudflare:workers"
import { jsonResponse, safeLog } from "./security-boundary.js"

const DEFAULT_DAILY_LIMIT = 100

function configuredDailyLimit(env) {
  const value = Number(env.AI_DAILY_LIMIT ?? DEFAULT_DAILY_LIMIT)
  return Number.isSafeInteger(value) && value > 0 ? value : null
}

function secondsUntilNextUtcDay(now) {
  const next = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1)
  return Math.max(1, Math.ceil((next - now.getTime()) / 1000))
}

export class DailyAiBudget extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env)
  }

  async reserve(limit) {
    if (!Number.isSafeInteger(limit) || limit <= 0) {
      throw new Error("invalid daily limit")
    }

    return this.ctx.storage.transaction(async (transaction) => {
      const used = (await transaction.get("count")) ?? 0
      if (used >= limit) return { allowed: false, remaining: 0 }

      const next = used + 1
      await transaction.put("count", next)
      return { allowed: true, remaining: limit - next }
    })
  }
}

export async function reserveDailyAiBudget(env, origin, now = new Date()) {
  if (!env.DEEPSEEK_API_KEY) return null

  const limit = configuredDailyLimit(env)
  if (!env.AI_BUDGET || !limit) {
    safeLog("error", "daily_ai_budget_unavailable")
    return jsonResponse({ error: "service unavailable" }, 503, origin)
  }

  try {
    const day = now.toISOString().slice(0, 10)
    const result = await env.AI_BUDGET.getByName(day).reserve(limit)
    if (!result.allowed) {
      safeLog("warn", "daily_ai_budget_exhausted", { remaining: 0 })
      return jsonResponse({ error: "daily AI budget exhausted" }, 429, origin, {
        "Retry-After": String(secondsUntilNextUtcDay(now)),
      })
    }
    return null
  } catch {
    safeLog("error", "daily_ai_budget_failed")
    return jsonResponse({ error: "service unavailable" }, 503, origin)
  }
}
