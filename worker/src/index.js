import { buildPrompt } from "./prompt.js"
import { searchEntries } from "./search.js"

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
const MAX_REQUEST_BYTES = 8192
const MAX_INDEX_BYTES = 8 * 1024 * 1024

function allowedOrigins(env) {
  return String(env.SITE_ORIGIN || "")
    .split(",")
    .map((origin) => origin.trim().replace(/\/+$/, ""))
    .filter(Boolean)
}

function requestOrigin(request) {
  return String(request.headers.get("origin") || "").replace(/\/+$/, "")
}

function corsHeaders(request, env) {
  const origin = requestOrigin(request)
  const headers = new Headers({
    vary: "Origin",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "Content-Type",
    "access-control-max-age": "86400",
  })
  if (allowedOrigins(env).includes(origin)) {
    headers.set("access-control-allow-origin", origin)
  }
  return headers
}

function json(payload, status, headers = new Headers()) {
  const responseHeaders = new Headers(headers)
  responseHeaders.set("content-type", "application/json; charset=utf-8")
  responseHeaders.set("x-content-type-options", "nosniff")
  return new Response(JSON.stringify(payload), { status, headers: responseHeaders })
}

function isAllowed(request, env) {
  return allowedOrigins(env).includes(requestOrigin(request))
}

async function readLimitedText(stream, byteLimit) {
  if (!stream) return ""
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let total = 0
  let output = ""
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      total += value.byteLength
      if (total > byteLimit) throw new RangeError("payload_too_large")
      output += decoder.decode(value, { stream: true })
    }
    output += decoder.decode()
    return output
  } finally {
    reader.releaseLock()
  }
}

async function readRequestJson(request) {
  const declaredLength = Number(request.headers.get("content-length") || 0)
  if (declaredLength > MAX_REQUEST_BYTES) throw new RangeError("payload_too_large")
  const body = await readLimitedText(request.body, MAX_REQUEST_BYTES)
  return JSON.parse(body)
}

async function loadIndex(env, fetchImpl) {
  const indexUrl = new URL(env.INDEX_URL)
  if (indexUrl.protocol !== "https:") throw new Error("invalid_index_url")
  const response = await fetchImpl(indexUrl.href, {
    headers: { accept: "application/json" },
    cf: { cacheEverything: true, cacheTtl: 300 },
  })
  if (!response.ok) throw new Error("index_unavailable")
  const declaredLength = Number(response.headers.get("content-length") || 0)
  if (declaredLength > MAX_INDEX_BYTES) throw new RangeError("index_too_large")
  const body = await readLimitedText(response.body, MAX_INDEX_BYTES)
  const entries = JSON.parse(body)
  if (!Array.isArray(entries)) throw new TypeError("invalid_index")
  return entries
}

function sourcePayload(results) {
  return results.map((entry) => ({
    id: entry.id,
    name: entry.name,
    category: entry.category || entry.type,
    summary: entry.summary || "",
    last_updated: entry.last_updated || "",
    tags: Array.isArray(entry.tags) ? entry.tags : [],
    score: Math.round((entry.score || 0) * 100) / 100,
    reference_count: entry.reference_count || 0,
    is_related: Boolean(entry.is_related),
    page_path: entry.page_path || null,
  }))
}

function sseEvent(payload) {
  return "data: " + JSON.stringify(payload) + "\n\n"
}

function streamDeepSeek(upstream, results, headers) {
  const encoder = new TextEncoder()
  const decoder = new TextDecoder()
  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(
        encoder.encode(sseEvent({ type: "sources", sources: sourcePayload(results) })),
      )
      const reader = upstream.body.getReader()
      let buffer = ""
      let completed = false
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue
            const data = line.slice(6).trim()
            if (data === "[DONE]") {
              controller.enqueue(encoder.encode(sseEvent({ type: "done" })))
              completed = true
              break
            }
            try {
              const chunk = JSON.parse(data).choices?.[0]?.delta?.content
              if (chunk)
                controller.enqueue(encoder.encode(sseEvent({ type: "chunk", text: chunk })))
            } catch {
              // Ignore a malformed provider line and continue the stream.
            }
          }
          if (completed) break
        }
        if (!completed) controller.enqueue(encoder.encode(sseEvent({ type: "done" })))
        controller.close()
      } catch {
        controller.enqueue(encoder.encode(sseEvent({ type: "error", message: "AI 响应中断" })))
        controller.close()
      } finally {
        reader.releaseLock()
      }
    },
  })

  const responseHeaders = new Headers(headers)
  responseHeaders.set("content-type", "text/event-stream; charset=utf-8")
  responseHeaders.set("cache-control", "no-cache, no-transform")
  responseHeaders.set("x-content-type-options", "nosniff")
  return new Response(stream, { status: 200, headers: responseHeaders })
}

async function handleSearch(request, env, fetchImpl) {
  const headers = corsHeaders(request, env)
  if (!isAllowed(request, env)) return json({ error: "origin_not_allowed" }, 403, headers)
  if (!env.DEEPSEEK_API_KEY || !env.INDEX_URL) {
    return json({ error: "service_not_configured" }, 503, headers)
  }

  let payload
  try {
    payload = await readRequestJson(request)
  } catch (error) {
    const status = error instanceof RangeError ? 413 : 400
    return json({ error: status === 413 ? "payload_too_large" : "invalid_json" }, status, headers)
  }

  const query = typeof payload.query === "string" ? payload.query.trim() : ""
  if (query.length < 2 || query.length > 200) {
    return json({ error: "query_length_must_be_2_to_200" }, 400, headers)
  }

  try {
    const entries = await loadIndex(env, fetchImpl)
    const results = searchEntries(entries, query, {
      filters: payload.filters || {},
      sort: payload.sort || "relevance",
      limit: payload.limit || 10,
    })
    if (results.length === 0) {
      const body = [
        sseEvent({ type: "sources", sources: [] }),
        sseEvent({ type: "chunk", text: "知识库中未找到相关内容。" }),
        sseEvent({ type: "done" }),
      ].join("")
      headers.set("content-type", "text/event-stream; charset=utf-8")
      return new Response(body, { status: 200, headers })
    }

    const upstream = await fetchImpl(DEEPSEEK_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer " + env.DEEPSEEK_API_KEY,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [{ role: "user", content: buildPrompt(query, results) }],
        temperature: 0.5,
        max_tokens: 2500,
        stream: true,
      }),
    })
    if (!upstream.ok || !upstream.body) {
      return json({ error: "ai_upstream_unavailable" }, 502, headers)
    }
    return streamDeepSeek(upstream, results, headers)
  } catch (error) {
    console.error(
      JSON.stringify({ event: "search_failed", message: String(error?.message || error) }),
    )
    return json({ error: "search_unavailable" }, 503, headers)
  }
}

export function createWorker({ fetchImpl = fetch } = {}) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url)
      const headers = corsHeaders(request, env)

      if (request.method === "OPTIONS") {
        return isAllowed(request, env)
          ? new Response(null, { status: 204, headers })
          : json({ error: "origin_not_allowed" }, 403, headers)
      }
      if (url.pathname === "/api/health" && request.method === "GET") {
        return json({ ok: true, mode: "static-index + deepseek" }, 200, headers)
      }
      if (url.pathname === "/api/search" && request.method === "POST") {
        return handleSearch(request, env, fetchImpl)
      }
      return json({ error: "not_found" }, 404, headers)
    },
  }
}

export default createWorker()
