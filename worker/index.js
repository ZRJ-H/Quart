import wikiIndex from "./wiki-index-light.json"

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

function extractLinkedPages(content) {
  if (!content) return []
  const links = []
  const regex = /\[\[([^\]|]+)(?:\|[^\]]*)?\]\]/g
  let match
  while ((match = regex.exec(content)) !== null) {
    links.push(match[1].trim())
  }
  return [...new Set(links)]
}

function findByName(name) {
  return wikiIndex.find(e => e.name === name || e.id.endsWith("/" + name))
}

function searchIndex(query, limit = 10) {
  const today = new Date().toJSON().slice(0, 10)

  let cleanQuery = query
  let timeFilter = null

  if (/今日|今天/.test(cleanQuery)) {
    timeFilter = (d) => d === today
    cleanQuery = cleanQuery.replace(/今日|今天/g, "").trim()
  }

  const candidates = timeFilter
    ? wikiIndex.filter((e) => timeFilter(e.last_updated))
    : wikiIndex

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
    const summary = (entry.summary || "").toLowerCase()
    const tags = (entry.tags || []).join(" ").toLowerCase()
    const category = (entry.category || "").toLowerCase()

    if (name.includes(q)) score += 20
    if (name === q) score += 40

    const qWords = q.split(/\s+/).filter(Boolean)
    for (const w of qWords) {
      if (name.includes(w)) score += 8
      if (tags.includes(w)) score += 6
      if (category.includes(w)) score += 4
      const matches = (summary.match(new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length
      score += Math.min(matches, 5)
    }

    return { ...entry, score }
  })

  const keywordResults = scored
    .filter((e) => e.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      return (b.last_updated || "").localeCompare(a.last_updated || "")
    })
    .slice(0, 5)

  return keywordResults
}

async function fetchFullData(kv, ids) {
  if (!kv || !ids.length) return {}

  const data = {}
  const promises = ids.map(async (id) => {
    try {
      const result = await kv.get(id, "json")
      if (result) data[id] = result
    } catch (err) {
      console.error(`KV read failed for ${id}:`, err.message)
    }
  })
  await Promise.all(promises)
  return data
}

function buildPrompt(query, results, fullData) {
  const today = new Date().toJSON().slice(0, 10)
  const ctx = results
    .map((r) => {
      const full = fullData[r.id]
      const content = full ? full.content : r.summary
      return `### ${r.name} (${r.type} | ${r.last_updated || "?"})\n标签: ${(r.tags || []).join(", ")}\n${content}`
    })
    .join("\n\n")

  return `你是一位知识库助手。今天是 ${today}。基于以下资料回答用户问题。

规则:
- 仔细阅读资料中的所有内容，尽可能从中提取回答
- 只有当资料中确实没有任何相关信息时，才说"资料中未提及"
- 引用具体来源（页面名称）
- 用户问"今日/今天"时，结合资料标注的日期和实际日期 ${today} 判断
- 回答简洁有条理，中文
- 如果多个页面有关联，综合分析它们的关系

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

    if (url.pathname === "/api/health") {
      return new Response(
        JSON.stringify({
          ok: true,
          pages: wikiIndex.length,
          mode: "light-index + kv",
        }),
        { headers }
      )
    }

    // Debug endpoint: test KV read
    if (url.pathname === "/api/debug" && request.method === "GET") {
      const testKey = url.searchParams.get("key") || "concepts/AI模型永久降价"
      try {
        const kvResult = await env.WIKI_DATA.get(testKey, "json")
        return new Response(
          JSON.stringify({
            key: testKey,
            kv_binding_exists: !!env.WIKI_DATA,
            kv_result_exists: !!kvResult,
            kv_result_preview: kvResult ? JSON.stringify(kvResult).slice(0, 300) : null,
          }),
          { headers }
        )
      } catch (err) {
        return new Response(
          JSON.stringify({
            key: testKey,
            error: err.message,
            kv_binding_exists: !!env.WIKI_DATA,
          }),
          { headers }
        )
      }
    }

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

        // 1. 关键词匹配
        const keywordResults = searchIndex(query)
        if (!keywordResults.length) {
          return new Response(
            JSON.stringify({
              answer: "知识库中未找到相关内容。",
              sources: [],
            }),
            { headers }
          )
        }

        // 2. 从 KV 读取关键词匹配结果的完整内容
        const keywordData = await fetchFullData(env.WIKI_DATA, keywordResults.map(r => r.id))

        // 3. 提取关联页面
        const relatedIds = new Set()
        for (const r of keywordResults) {
          const full = keywordData[r.id]
          if (full && full.content) {
            const linked = extractLinkedPages(full.content)
            for (const name of linked) {
              const page = findByName(name)
              if (page && !keywordResults.some(kr => kr.id === page.id)) {
                relatedIds.add(page.id)
              }
            }
          }
        }

        // 4. 合并结果：关键词结果 + 关联页面（最多 10 个）
        let allResults = [...keywordResults]
        if (relatedIds.size > 0) {
          const relatedPages = [...relatedIds]
            .map(id => wikiIndex.find(e => e.id === id))
            .filter(Boolean)
            .slice(0, 10 - keywordResults.length)
            .map(e => ({ ...e, score: 0 }))
          allResults = [...keywordResults, ...relatedPages]
        }

        // 5. 从 KV 读取所有结果的完整内容
        const allIds = allResults.map(r => r.id)
        const existingData = keywordData
        const newIds = allIds.filter(id => !existingData[id])
        const newData = await fetchFullData(env.WIKI_DATA, newIds)
        const fullData = { ...existingData, ...newData }

        // 6. 构建 prompt 并调用 DeepSeek
        const prompt = buildPrompt(query, allResults, fullData)
        const answer = await callDeepSeek(prompt, env.DEEPSEEK_API_KEY)

        return new Response(
          JSON.stringify({
            answer,
            sources: allResults.map((r) => ({
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
