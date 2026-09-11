function tokenize(query) {
  const normalized = String(query || "").toLowerCase().trim()
  const tokens = new Set(normalized.match(/[一-鿿]+|[a-z0-9]+/g) || [])
  for (const token of [...tokens]) {
    if (/^[一-鿿]{3,}$/.test(token)) {
      for (let index = 0; index < token.length - 1; index += 1) {
        tokens.add(token.slice(index, index + 2))
      }
    }
  }
  return [...tokens]
}

function text(value) {
  return String(value || "").toLowerCase()
}

function tagText(entry) {
  return Array.isArray(entry.tags) ? entry.tags.join(" ").toLowerCase() : ""
}

function scoreEntry(entry, terms, exactQuery) {
  const name = text(entry.name)
  const summary = text(entry.summary)
  const content = text(entry.content)
  const category = text(entry.category)
  const tags = tagText(entry)
  let score = 0

  if (name === exactQuery) score += 100
  else if (name.includes(exactQuery)) score += 50
  if (summary.includes(exactQuery)) score += 24
  if (tags.includes(exactQuery)) score += 20
  if (category.includes(exactQuery)) score += 12
  if (content.includes(exactQuery)) score += 10

  for (const term of terms) {
    if (name.includes(term)) score += 10
    if (tags.includes(term)) score += 7
    if (summary.includes(term)) score += 4
    if (category.includes(term)) score += 2
    if (content.includes(term)) score += 2
  }
  return score
}

function matchesFilters(entry, filters = {}) {
  if (Array.isArray(filters.tags) && filters.tags.length > 0) {
    const tags = Array.isArray(entry.tags) ? entry.tags : []
    if (
      !filters.tags.includes(entry.category) &&
      !tags.some((tag) => filters.tags.includes(tag))
    ) {
      return false
    }
  }

  if (filters.time && filters.time !== "all") {
    const days = filters.time === "7d" ? 7 : 30
    const cutoff = new Date()
    cutoff.setUTCDate(cutoff.getUTCDate() - days)
    if (String(entry.last_updated || "") < cutoff.toISOString().slice(0, 10)) {
      return false
    }
  }
  return true
}

function sortEntries(entries, sort) {
  return [...entries].sort((a, b) => {
    if (sort === "time") {
      return String(b.last_updated || "").localeCompare(String(a.last_updated || ""))
    }
    if (sort === "popularity") {
      return (b.reference_count || 0) - (a.reference_count || 0)
    }
    if (b.score !== a.score) return b.score - a.score
    return String(b.last_updated || "").localeCompare(String(a.last_updated || ""))
  })
}

export function searchEntries(entries, query, options = {}) {
  const exactQuery = text(query).trim()
  const terms = tokenize(exactQuery)
  const limit = Math.min(Math.max(Number(options.limit) || 10, 1), 15)
  if (!exactQuery || terms.length === 0 || !Array.isArray(entries)) return []

  const primary = sortEntries(
    entries
      .filter((entry) => matchesFilters(entry, options.filters))
      .map((entry) => ({ ...entry, score: scoreEntry(entry, terms, exactQuery) }))
      .filter((entry) => entry.score > 0),
    options.sort || "relevance",
  ).slice(0, limit)

  const selectedIds = new Set(primary.map((entry) => entry.id))
  const byName = new Map(entries.map((entry) => [text(entry.name), entry]))
  const related = []
  for (const entry of primary) {
    for (const target of Array.isArray(entry.links) ? entry.links : []) {
      const linked = byName.get(text(target))
      if (!linked || selectedIds.has(linked.id) || !matchesFilters(linked, options.filters)) continue
      selectedIds.add(linked.id)
      related.push({ ...linked, score: 0, is_related: true })
      if (primary.length + related.length >= limit) break
    }
    if (primary.length + related.length >= limit) break
  }

  return [...primary, ...related].slice(0, limit)
}
