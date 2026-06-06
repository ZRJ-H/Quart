import wikiIndex from "./wiki-index-light.json"

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

// 同义词缓存
let synonymsCache = null
let synonymsCacheTime = 0
const SYNONYMS_CACHE_TTL = 3600 * 1000  // 1小时缓存

async function loadSynonyms(kv) {
  const now = Date.now()
  if (synonymsCache && (now - synonymsCacheTime) < SYNONYMS_CACHE_TTL) {
    return synonymsCache
  }

  try {
    const data = await kv.get('synonyms', 'json')
    if (data) {
      const reverseIndex = {}
      for (const [key, values] of Object.entries(data)) {
        if (!Array.isArray(values)) continue

        const allWords = [key, ...values].map(w => w.toLowerCase())
        // 对包含空格的词进行分词，把每个单词都加入索引
        const allTokens = new Set()
        for (const word of allWords) {
          allTokens.add(word)
          // 分词：把 "ai agent" 拆分成 "ai" 和 "agent"
          if (word.includes(' ')) {
            for (const token of word.split(/\s+/)) {
              if (token.length >= 2) allTokens.add(token)
            }
          }
        }
        
        for (const token of allTokens) {
          if (!reverseIndex[token]) {
            reverseIndex[token] = new Set()
          }
          for (const related of allWords) {
            reverseIndex[token].add(related.toLowerCase())
          }
        }
      }

      synonymsCache = { forward: data, reverse: reverseIndex }
      synonymsCacheTime = now
      return synonymsCache
    }
  } catch (err) {
    console.error('Failed to load synonyms:', err.message)
  }

  return { forward: {}, reverse: {} }
}

function expandQuery(query, synonyms) {
  const q = query.toLowerCase()
  const words = q.split(/\s+/).filter(Boolean)
  const expanded = new Set(words)

  const reverseIndex = synonyms.reverse || {}

  for (const word of words) {
    if (word.length < 2) continue

    if (reverseIndex[word]) {
      for (const related of reverseIndex[word]) {
        expanded.add(related)
      }
    }
  }

  return [...expanded]
}

// 评分阈值配置
const SCORE_CONFIG = {
  MIN_THRESHOLD: 8,
  HIGH_RELEVANCE: 20,
  MAX_RESULTS: 15,
  DYNAMIC_RATIO: 0.4,
  SYNONYM_SCORE_FACTOR: 0.6,
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

function searchIndex(query, limit = 10, expandedTerms = null) {
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

    // 精确匹配（最高权重）
    if (name.includes(q)) score += 20
    if (name === q) score += 40

    // 分词匹配
    const qWords = q.split(/\s+/).filter(Boolean)
    for (const w of qWords) {
      if (name.includes(w)) score += 8
      if (tags.includes(w)) score += 8  // 标签权重从 6 提升到 8
      if (category.includes(w)) score += 4
      const matches = (summary.match(new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length
      score += Math.min(matches, 5)
    }

    // 同义词扩展匹配（降权 SYNONYM_SCORE_FACTOR）
    if (expandedTerms) {
      const qWords = q.split(/\s+/).filter(Boolean)
      for (const term of expandedTerms) {
        if (qWords.includes(term)) continue

        if (name.includes(term)) score += 20 * SCORE_CONFIG.SYNONYM_SCORE_FACTOR
        if (tags.includes(term)) score += 8 * SCORE_CONFIG.SYNONYM_SCORE_FACTOR
        const termMatches = (summary.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length
        score += Math.min(termMatches, 3) * SCORE_CONFIG.SYNONYM_SCORE_FACTOR
      }
    }

    return { ...entry, score }
  })

  return scored
    .filter((e) => e.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score
      return (b.last_updated || "").localeCompare(a.last_updated || "")
    })
}

/**
 * 向量搜索：调用 Vectorize API
 * @param {string} query - 用户查询
 * @param {object} vectorize - Vectorize 绑定
 * @param {number} topK - 返回结果数量
 * @returns {Array} 向量搜索结果
 */
async function vectorSearch(query, vectorize, topK = 10) {
  try {
    // 调用 Vectorize 查询
    const result = await vectorize.query(query, {
      topK,
      returnMetadata: "all",
    })

    // 转换结果格式
    return result.matches.map(match => ({
      id: match.id,
      score: match.score,
      metadata: match.metadata,
    }))
  } catch (err) {
    console.error('Vector search failed:', err.message)
    return []
  }
}

/**
 * 混合搜索：融合关键词和向量搜索结果
 * 使用 RRF (Reciprocal Rank Fusion) 算法
 * @param {string} query - 用户查询
 * @param {Array} keywordResults - 关键词搜索结果
 * @param {Array} vectorResults - 向量搜索结果
 * @param {number} rrfK - RRF 参数（默认 60）
 * @returns {Array} 融合后的结果
 */
function hybridSearch(query, keywordResults, vectorResults, rrfK = 60) {
  const scores = new Map()
  const keywordRank = new Map()
  const vectorRank = new Map()

  // 记录关键词搜索排名
  keywordResults.forEach((result, index) => {
    keywordRank.set(result.id, index + 1)
  })

  // 记录向量搜索排名
  vectorResults.forEach((result, index) => {
    vectorRank.set(result.id, index + 1)
  })

  // 计算 RRF 分数
  const allIds = new Set([...keywordRank.keys(), ...vectorRank.keys()])

  for (const id of allIds) {
    const keywordScore = keywordRank.has(id) ? 1 / (rrfK + keywordRank.get(id)) : 0
    const vectorScore = vectorRank.has(id) ? 1 / (rrfK + vectorRank.get(id)) : 0
    scores.set(id, keywordScore + vectorScore)
  }

  // 按 RRF 分数排序
  const sortedIds = [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([id]) => id)

  // 构建结果
  const keywordMap = new Map(keywordResults.map(r => [r.id, r]))
  const vectorMap = new Map(vectorResults.map(r => [r.id, r]))

  return sortedIds.map(id => {
    const keywordResult = keywordMap.get(id)
    const vectorResult = vectorMap.get(id)

    return {
      id,
      name: keywordResult?.name || vectorResult?.metadata?.name || id,
      category: keywordResult?.category || vectorResult?.metadata?.category || '',
      summary: keywordResult?.summary || vectorResult?.metadata?.summary || '',
      last_updated: keywordResult?.last_updated || vectorResult?.metadata?.last_updated || '',
      tags: keywordResult?.tags || vectorResult?.metadata?.tags || [],
      score: scores.get(id),
      keyword_rank: keywordRank.get(id) || null,
      vector_rank: vectorRank.get(id) || null,
    }
  })
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

  const queryTypeGuide = {
    comparison: '使用对比分析：表格对比关键维度 → 总结建议',
    timeline: '使用时间线：按时间顺序列出关键事件 → 趋势分析',
    overview: '使用概述结构：定义 → 核心要点 → 应用场景',
    comprehensive: '根据内容选择最合适结构'
  }

  return `你是知识库研究助手。今天是 ${today}。

## 回答原则

1. **核心回答**：直接回答用户问题，标注来源 [1][2]
2. **关联分析**：主动指出相关实体/概念之间的联系
   - 例如："A 和 B 都属于 X 领域"
   - 例如："这个概念在 Y 场景也有应用"
3. **背景补充**：对关键术语补充 1-2 句背景，帮助理解
4. **跨领域洞察**：如果发现不同领域间的共性或模式，简要点出
5. **时间维度**：如果有时间线信息，指出趋势或演变

## 回答结构

- 开头：直接回答 + 核心要点
- 中间：分点展开 + 关联分析
- 结尾：如有价值，补充洞察或延伸思考

## 查询类型

${queryTypeGuide[queryType] || queryTypeGuide.comprehensive}

## 注意事项

- 标注来源编号 [1][2]，便于追溯
- 使用 Markdown 格式
- 如果资料中确实没有相关信息，诚实说明并尝试给出相关方向
- 不要过度发散到无来源支撑的内容

## 可用来源

${sources}

## 用户查询

${query}`
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
      temperature: 0.5,  // 从 0.3 提升到 0.5，增加创造性
      max_tokens: 2500,  // 从 1500 提升到 2500，允许更深入回答
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
          mode: "light-index + kv + vectorize",
          vectorize: !!env.VECTORIZE,
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

        // 1. 加载同义词并扩展查询
        const synonyms = await loadSynonyms(env.WIKI_DATA)
        const expandedTerms = expandQuery(query, synonyms)

        // 2. 关键词搜索
        const keywordResults = searchIndex(query, limit * 2, expandedTerms)

        // 3. 向量搜索（如果 Vectorize 可用）
        let vectorResults = []
        if (env.VECTORIZE) {
          try {
            vectorResults = await vectorSearch(query, env.VECTORIZE, limit * 2)
          } catch (err) {
            console.error('Vector search error:', err.message)
          }
        }

        // 4. 混合搜索（融合关键词和向量结果）
        let searchResults
        if (vectorResults.length > 0) {
          searchResults = hybridSearch(query, keywordResults, vectorResults)
        } else {
          searchResults = keywordResults
        }

        if (!searchResults.length) {
          return new Response(
            JSON.stringify({
              answer: "知识库中未找到相关内容。",
              sources: [],
            }),
            { headers }
          )
        }

        // 5. 智能选择相关页面
        let selectedResults = selectRelevantResults(searchResults)

        // 6. 从 KV 读取完整内容
        const keywordData = await fetchFullData(env.WIKI_DATA, selectedResults.map(r => r.id))

        // 7. 提取关联页面
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

        // 8. 合并结果
        let allResults = [...selectedResults]
        if (relatedIds.size > 0) {
          const relatedPages = [...relatedIds]
            .map(id => wikiIndex.find(e => e.id === id))
            .filter(Boolean)
            .slice(0, 5)
            .map(e => ({ 
              ...e, 
              score: 0,
              quality_score: calculateQualityScore(e),
              is_related: true
            }))
          allResults = [...selectedResults, ...relatedPages]
        }

        // 9. 过滤和排序
        allResults = filterResults(allResults, filters)
        allResults = sortResults(allResults, sort)
        allResults = allResults.slice(0, limit)

        // 10. 读取所有结果的完整内容
        const allIds = allResults.map(r => r.id)
        const existingData = keywordData
        const newIds = allIds.filter(id => !existingData[id])
        const newData = await fetchFullData(env.WIKI_DATA, newIds)
        const fullData = { ...existingData, ...newData }

        // 11. 构建 prompt 并调用 DeepSeek
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
              expanded_terms: expandedTerms.length > 1 ? expandedTerms : undefined,
              vector_search: vectorResults.length > 0,
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
