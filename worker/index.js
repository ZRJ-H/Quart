import wikiIndex from "./wiki-index-light.json"

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

// 评分阈值配置
const SCORE_CONFIG = {
  MIN_THRESHOLD: 8,        // 最低入选分数
  HIGH_RELEVANCE: 20,      // 高相关性阈值
  MAX_RESULTS: 15,         // 最大结果数
  DYNAMIC_RATIO: 0.4,      // 动态阈值比例（最高分的40%）
}

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

function filterResults(results, filters) {
  let filtered = results

  if (filters.tags && filters.tags.length > 0) {
    filtered = filtered.filter(entry => 
      filters.tags.includes(entry.category) ||
      (entry.tags && entry.tags.some(tag => filters.tags.includes(tag)))
    )
  }

  if (filters.time && filters.time !== 'all') {
    const days = filters.time === '7d' ? 7 : 30
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - days)
    const cutoffStr = cutoff.toISOString().slice(0, 10)
    filtered = filtered.filter(entry => 
      (entry.last_updated || "") >= cutoffStr
    )
  }

  return filtered
}

function sortResults(results, sort) {
  switch (sort) {
    case 'time':
      return [...results].sort((a, b) => 
        (b.last_updated || "").localeCompare(a.last_updated || "")
      )
    case 'popularity':
      return [...results].sort((a, b) => 
        (b.reference_count || 0) - (a.reference_count || 0)
      )
    case 'relevance':
    default:
      return [...results].sort((a, b) => {
        // 先按主分数排序
        if (b.score !== a.score) return b.score - a.score
        // 分数相同时按质量分数排序
        const aQuality = a.quality_score || 0
        const bQuality = b.quality_score || 0
        if (bQuality !== aQuality) return bQuality - aQuality
        // 最后按更新时间排序
        return (b.last_updated || "").localeCompare(a.last_updated || "")
      })
  }
}

function detectQueryType(query) {
  const q = query.toLowerCase()
  
  if ((q.includes('和') && q.includes('区别')) || q.includes('vs') || q.includes('对比')) {
    return 'comparison'
  }
  
  if (q.includes('历史') || q.includes('发展') || q.includes('时间线') || q.includes('事件')) {
    return 'timeline'
  }
  
  if (q.includes('是什么') || q.includes('介绍') || q.includes('概述')) {
    return 'overview'
  }
  
  return 'comprehensive'
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

  return keywordResults
}

/**
 * 智能选择相关页面
 * 基于分数阈值和动态比例选择最优结果集
 */
function selectRelevantResults(scoredResults) {
  if (scoredResults.length === 0) return []

  // 按分数降序排序
  const sorted = [...scoredResults].sort((a, b) => b.score - a.score)
  const maxScore = sorted[0].score

  // 动态阈值：最高分的一定比例，但不低于最低阈值
  const dynamicThreshold = Math.max(
    SCORE_CONFIG.MIN_THRESHOLD,
    Math.floor(maxScore * SCORE_CONFIG.DYNAMIC_RATIO)
  )

  // 选择所有超过阈值的结果
  let selected = sorted.filter(r => r.score >= dynamicThreshold)

  // 如果高相关性结果太少，放宽阈值
  if (selected.length < 3) {
    selected = sorted.filter(r => r.score >= SCORE_CONFIG.MIN_THRESHOLD)
  }

  // 硬上限
  if (selected.length > SCORE_CONFIG.MAX_RESULTS) {
    selected = selected.slice(0, SCORE_CONFIG.MAX_RESULTS)
  }

  return selected
}

/**
 * 计算页面质量分数（用于辅助排序）
 */
function calculateQualityScore(entry) {
  let quality = 0

  // 引用次数权重
  quality += Math.min((entry.reference_count || 0) * 2, 20)

  // 内容长度权重（有详细内容的页面更有价值）
  if (entry.content_length > 1000) quality += 5
  if (entry.content_length > 3000) quality += 5

  // 更新时间权重（近期更新的页面略优先）
  if (entry.last_updated) {
    const daysSinceUpdate = (Date.now() - new Date(entry.last_updated).getTime()) / (1000 * 60 * 60 * 24)
    if (daysSinceUpdate < 7) quality += 3
    else if (daysSinceUpdate < 30) quality += 1
  }

  return quality
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

function buildPrompt(query, results, fullData, queryType) {
  const today = new Date().toJSON().slice(0, 10)
  const sources = results
    .map((r, i) => {
      const data = fullData[r.id]
      return `[${i + 1}] ${r.name} (${r.category || r.type})
摘要: ${data?.summary || r.summary}
标签: ${(data?.tags || r.tags || []).join(', ')}
更新时间: ${r.last_updated || "?"}`
    })
    .join("\n\n")

  const structureGuide = {
    overview: '使用结构化回答：开头概述 → 分点列出核心要点 → 总结',
    comparison: '使用对比分析：开头说明对比对象 → 表格对比关键维度 → 总结建议',
    timeline: '使用时间线：开头概述 → 按时间顺序列出关键事件 → 趋势分析',
    comprehensive: '使用混合结构：开头概述 → 根据内容选择合适结构 → 总结'
  }

  return `你是知识库助手。今天是 ${today}。根据查询类型，选择最合适的回答结构。

查询类型：${queryType}
回答指导：${structureGuide[queryType] || structureGuide.comprehensive}

要求：
1. 回答要有条理、有逻辑
2. 在回答中标注来源编号 [1][2]
3. 使用 Markdown 格式
4. 保持简洁，避免冗余
5. 只有当资料中确实没有任何相关信息时，才说"资料中未提及"

可用来源：
${sources}

用户查询：${query}`
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
        const filters = body.filters || {}
        const sort = body.sort || 'relevance'
        const limit = body.limit || 10
        if (!query) {
          return new Response(JSON.stringify({ error: "query required" }), {
            status: 400,
            headers,
          })
        }

        // 1. 关键词匹配（返回所有匹配结果）
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

        // 2. 智能选择相关页面（基于评分阈值）
        let selectedResults = selectRelevantResults(keywordResults)

        // 3. 从 KV 读取关键词匹配结果的完整内容
        const keywordData = await fetchFullData(env.WIKI_DATA, selectedResults.map(r => r.id))

        // 4. 提取关联页面（从高分页面中提取）
        const relatedIds = new Set()
        const highScoreResults = selectedResults.filter(r => r.score >= SCORE_CONFIG.HIGH_RELEVANCE)
        for (const r of highScoreResults) {
          const full = keywordData[r.id]
          if (full && full.content) {
            const linked = extractLinkedPages(full.content)
            for (const name of linked) {
              const page = findByName(name)
              if (page && !selectedResults.some(kr => kr.id === page.id)) {
                relatedIds.add(page.id)
              }
            }
          }
        }

        // 5. 合并结果：关键词结果 + 关联页面
        let allResults = [...selectedResults]
        if (relatedIds.size > 0) {
          const relatedPages = [...relatedIds]
            .map(id => wikiIndex.find(e => e.id === id))
            .filter(Boolean)
            .slice(0, 5)  // 关联页面最多5个
            .map(e => ({ 
              ...e, 
              score: 0,
              quality_score: calculateQualityScore(e),
              is_related: true
            }))
          allResults = [...selectedResults, ...relatedPages]
        }

        // 6. 过滤和排序
        allResults = filterResults(allResults, filters)
        allResults = sortResults(allResults, sort)
        allResults = allResults.slice(0, limit)

        // 6. 从 KV 读取所有结果的完整内容
        const allIds = allResults.map(r => r.id)
        const existingData = keywordData
        const newIds = allIds.filter(id => !existingData[id])
        const newData = await fetchFullData(env.WIKI_DATA, newIds)
        const fullData = { ...existingData, ...newData }

        // 7. 构建 prompt 并调用 DeepSeek
        const queryType = detectQueryType(query)
        const prompt = buildPrompt(query, allResults, fullData, queryType)
        const answer = await callDeepSeek(prompt, env.DEEPSEEK_API_KEY)

        return new Response(
          JSON.stringify({
            answer,
            sources: allResults.map((r) => ({
              id: r.id,
              name: r.name,
              category: r.category || r.type,
              summary: fullData[r.id]?.summary || r.summary,
              last_updated: r.last_updated,
              tags: fullData[r.id]?.tags || r.tags || [],
              score: r.score,
              quality_score: r.quality_score || calculateQualityScore(r),
              reference_count: fullData[r.id]?.reference_count || 0,
              is_related: r.is_related || false
            })),
            metadata: {
              total: allResults.length,
              query_type: queryType,
              scoring: {
                max_score: allResults.length > 0 ? Math.max(...allResults.map(r => r.score)) : 0,
                min_score: allResults.length > 0 ? Math.min(...allResults.map(r => r.score)) : 0,
                threshold_used: SCORE_CONFIG.MIN_THRESHOLD
              }
            }
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
