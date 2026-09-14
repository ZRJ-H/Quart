const MAX_REQUEST_BYTES = 8192
const MAX_QUERY_LENGTH = 500
const MAX_SEARCH_LIMIT = 15
const MAX_FILTER_TAGS = 10
const MAX_FILTER_TAG_LENGTH = 80

const API_METHODS = new Map([
  ["/api/health", "GET"],
  ["/api/search", "POST"],
])
const ALLOWED_SORTS = new Set(["relevance", "time", "popularity"])
const ALLOWED_TIMES = new Set(["all", "7d", "30d"])

export class SafeHttpError extends Error {
  constructor(status, publicMessage) {
    super(publicMessage)
    this.status = status
    this.publicMessage = publicMessage
  }
}

export function safeLog(level, event, details = {}) {
  const record = JSON.stringify({
    level,
    event,
    timestamp: new Date().toISOString(),
    ...details,
  })
  const logger = level === "error" ? console.error : level === "warn" ? console.warn : console.log
  logger(record)
}

function configuredOrigins(env) {
  const configured = env.ALLOWED_ORIGINS || env.SITE_BASE_URL || ""
  return new Set(
    configured
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean)
      .map((value) => {
        try {
          return new URL(value).origin
        } catch {
          return ""
        }
      })
      .filter(Boolean),
  )
}

export function allowedRequestOrigin(request, env) {
  const origin = request.headers.get("Origin")
  if (!origin) return null
  return configuredOrigins(env).has(origin) ? origin : false
}

export function corsHeaders(origin, contentType = "application/json; charset=utf-8") {
  const headers = new Headers({
    "Content-Type": contentType,
    Vary: "Origin",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
  })
  if (origin) {
    headers.set("Access-Control-Allow-Origin", origin)
    headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type")
  }
  return headers
}

export function jsonResponse(payload, status, origin, extraHeaders = {}) {
  const headers = corsHeaders(origin)
  for (const [name, value] of Object.entries(extraHeaders)) headers.set(name, value)
  return new Response(JSON.stringify(payload), { status, headers })
}

export function safeErrorResponse(error, origin) {
  if (error instanceof SafeHttpError) {
    return jsonResponse({ error: error.publicMessage }, error.status, origin)
  }
  return jsonResponse({ error: "internal error" }, 500, origin)
}

export function handlePreflight(request, env, pathname) {
  const expectedMethod = API_METHODS.get(pathname)
  if (!expectedMethod) return jsonResponse({ error: "not found" }, 404, null)

  const origin = allowedRequestOrigin(request, env)
  if (!origin) return jsonResponse({ error: "origin not allowed" }, 403, null)

  const requestedMethod = request.headers.get("Access-Control-Request-Method")
  const requestedHeaders = (request.headers.get("Access-Control-Request-Headers") || "")
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean)
  if (
    requestedMethod !== expectedMethod ||
    requestedHeaders.some((header) => header !== "content-type")
  ) {
    return jsonResponse({ error: "invalid preflight" }, 403, null)
  }
  return new Response(null, { status: 204, headers: corsHeaders(origin) })
}

async function readLimitedBody(request) {
  const contentLength = request.headers.get("Content-Length")
  if (contentLength !== null) {
    const declaredLength = Number(contentLength)
    if (!Number.isFinite(declaredLength) || declaredLength > MAX_REQUEST_BYTES) {
      throw new SafeHttpError(413, "request too large")
    }
  }
  if (!request.body) return ""

  const reader = request.body.getReader()
  const decoder = new TextDecoder()
  let total = 0
  let text = ""
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    total += value.byteLength
    if (total > MAX_REQUEST_BYTES) {
      await reader.cancel()
      throw new SafeHttpError(413, "request too large")
    }
    text += decoder.decode(value, { stream: true })
  }
  return text + decoder.decode()
}

export async function parseSearchRequest(request) {
  const contentType = (request.headers.get("Content-Type") || "")
    .split(";", 1)[0]
    .trim()
    .toLowerCase()
  if (contentType !== "application/json") {
    throw new SafeHttpError(415, "application/json required")
  }

  const text = await readLimitedBody(request)
  let body
  try {
    body = JSON.parse(text)
  } catch {
    throw new SafeHttpError(400, "invalid JSON")
  }

  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new SafeHttpError(400, "invalid request")
  }
  const allowedKeys = new Set(["query", "filters", "sort", "limit"])
  if (Object.keys(body).some((key) => !allowedKeys.has(key))) {
    throw new SafeHttpError(400, "invalid request")
  }

  if (typeof body.query !== "string") throw new SafeHttpError(400, "invalid request")
  const query = body.query.trim()
  if (query.length < 2 || query.length > MAX_QUERY_LENGTH) {
    throw new SafeHttpError(400, "invalid request")
  }

  const filters = body.filters ?? {}
  if (!filters || typeof filters !== "object" || Array.isArray(filters)) {
    throw new SafeHttpError(400, "invalid request")
  }
  if (Object.keys(filters).some((key) => key !== "tags" && key !== "time")) {
    throw new SafeHttpError(400, "invalid request")
  }
  const rawTags = filters.tags ?? []
  const time = filters.time ?? "all"
  if (
    !Array.isArray(rawTags) ||
    rawTags.length > MAX_FILTER_TAGS ||
    rawTags.some(
      (tag) =>
        typeof tag !== "string" ||
        tag.trim().length < 1 ||
        tag.trim().length > MAX_FILTER_TAG_LENGTH ||
        /[\u0000-\u001f\u007f]/.test(tag),
    ) ||
    typeof time !== "string" ||
    !ALLOWED_TIMES.has(time)
  ) {
    throw new SafeHttpError(400, "invalid request")
  }
  const tags = rawTags.map((tag) => tag.trim())

  const sort = body.sort ?? "relevance"
  if (typeof sort !== "string" || !ALLOWED_SORTS.has(sort)) {
    throw new SafeHttpError(400, "invalid request")
  }

  const requestedLimit = body.limit ?? 10
  if (typeof requestedLimit !== "number" || !Number.isFinite(requestedLimit)) {
    throw new SafeHttpError(400, "invalid request")
  }
  const limit = Math.min(MAX_SEARCH_LIMIT, Math.max(1, Math.trunc(requestedLimit)))
  return { query, filters: { tags, time }, sort, limit }
}

export async function enforceSearchRateLimit(request, env, origin, pathname) {
  if (!env.SEARCH_RATE_LIMITER) {
    safeLog("error", "search_rate_limiter_unavailable", { pathname })
    return jsonResponse({ error: "service unavailable" }, 503, origin)
  }

  const client = request.headers.get("CF-Connecting-IP") || "unknown"
  try {
    const result = await env.SEARCH_RATE_LIMITER.limit({ key: `${client}:${pathname}` })
    if (!result.success) {
      safeLog("warn", "search_rate_limited", { pathname })
      return jsonResponse({ error: "rate limit exceeded" }, 429, origin, { "Retry-After": "60" })
    }
  } catch {
    safeLog("error", "search_rate_limiter_failed", { pathname })
    return jsonResponse({ error: "service unavailable" }, 503, origin)
  }
  return null
}
