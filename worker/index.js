import wikiData from "./wiki-data.json"

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

function searchIndex(query, limit = 5) {
  const today = new Date().toJSON().slice(0, 10)

  let cleanQuery = query
  let timeFilter = null

  if (/今日|今天/.test(cleanQuery)) {
    timeFilter = (d) => d === today
    cleanQuery = cleanQuery.replace(/今日|今天/g, "").trim()
  }

  const candidates = timeFilter
    ? wikiData.filter((e) => timeFilter(e.last_updated))
    : wikiData

  if (timeFilter && !cleanQuery) {
    return candidates
      .sort((a, b) => (b.last_updated || "").localeCompare(a.last_updated || ""))
      .slice(0, limit)
      .map((e) => ({ ...e, score: 1 }))
  }

  const q = cleanQuery.toLowerCase()
  const scored = candidates.map((entry) => {
    let score = 0
    const name = (entry.name || "").toLowerCase()
    const content = (entry.content || "").toLowerCase()
    const tags = (entry.tags || []).join(" ").toLowerCase()
    const category = (entry.category || "").toLowerCase()

    // exact phrase bonus
    if (name.includes(q)) score += 20
    if (name === q) score += 40

    // word-level match
    const qWords = q.split(/\s+/).filter(Boolean)
    for (const w of qWords) {
      if (name.includes(w)) score += 8
      if (tags.includes(w)) score += 6
      if (category.includes(w)) score += 4
      // count content matches
      const matches = (content.match(new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length
      score += Math.min(matches, 5)
    }

    return { ...entry, score }
  })

  return scored
    .filter((e) => e.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      const da = a.last_updated || "1970-01-01"
      const db = b.last_updated || "1970-01-01"
      return db.localeCompare(da)
    })
    .slice(0, limit)
}

function buildPrompt(query, results) {
  const today = new Date().toJSON().slice(0, 10)
  const ctx = results
    .map((r) => `### ${r.name} (${r.type} | ${r.last_updated || "?"})\n标签: ${(r.tags || []).join(", ")}\n${r.content}`)
    .join("\n\n")

  return `你是一位知识库助手。今天是 ${today}。基于以下资料回答用户问题。

规则:
- 只根据提供的资料回答，不要编造
- 资料中没有的信息，直接说"资料中未提及"
- 引用具体来源（页面名称）
- 用户问"今日/今天"时，结合资料标注的日期和实际日期 ${today} 判断
- 回答简洁有条理，中文

资料（每条目标注了最后更新日期）:
${ctx}

用户问题: ${query}`
}

async function callDeepSeek(prompt, apiKey) {
  const resp = await fetch(DEEPSEEK_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "deepseek-chat",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.3,
      max_tokens: 1500,
    }),
  })

  if (!resp.ok) {
    const err = await resp.text()
    throw new Error(`DeepSeek API error ${resp.status}: ${err}`)
  }

  const data = await resp.json()
  return data.choices[0].message.content
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)

    const headers = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Content-Type": "application/json; charset=utf-8",
    }

    if (request.method === "OPTIONS") {
      return new Response(null, { headers })
    }

    // Health check
    if (url.pathname === "/api/health") {
      return new Response(
        JSON.stringify({ ok: true, pages: wikiData.length }),
        { headers }
      )
    }

    // Search endpoint
    if (url.pathname === "/api/search" && request.method === "POST") {
      try {
        const body = await request.json()
        const query = (body.query || "").trim()
        if (!query) {
          return new Response(JSON.stringify({ error: "query required" }), {
            status: 400,
            headers,
          })
        }

        const results = searchIndex(query)
        if (!results.length) {
          return new Response(
            JSON.stringify({
              answer: "知识库中未找到相关内容。",
              sources: [],
            }),
            { headers }
          )
        }

        const prompt = buildPrompt(query, results)
        const answer = await callDeepSeek(prompt, env.DEEPSEEK_API_KEY)

        return new Response(
          JSON.stringify({
            answer,
            sources: results.map((r) => ({
              name: r.name,
              type: r.type,
              tags: r.tags,
            })),
          }),
          { headers }
        )
      } catch (err) {
        return new Response(
          JSON.stringify({ error: err.message }),
          { status: 500, headers }
        )
      }
    }

    return new Response(JSON.stringify({ error: "not found" }), {
      status: 404,
      headers,
    })
  },
}
