export interface SearchIndexEntry {
  id?: string
  name?: string
  summary?: string
  category?: string
  tags?: string[]
  last_updated?: string
  score?: number
  page_path?: string | null
  [key: string]: unknown
}

export function normalizeEndpoint(value: unknown): string {
  return String(value || "")
    .trim()
    .replace(/\/+$/, "")
}

export function resolveIndexUrl(relativeRoot: unknown, filename: unknown): string {
  const root = String(relativeRoot || ".").replace(/\/+$/, "") || "."
  return root + "/" + String(filename || "").replace(/^\/+/, "")
}

export function escapeHtml(value: unknown): string {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

function tokenize(query: unknown): string[] {
  const normalized = String(query || "")
    .toLowerCase()
    .trim()
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

function scoreEntry(entry: SearchIndexEntry, terms: string[], exactQuery: string): number {
  const name = String(entry.name || "").toLowerCase()
  const summary = String(entry.summary || "").toLowerCase()
  const category = String(entry.category || "").toLowerCase()
  const tags = Array.isArray(entry.tags) ? entry.tags.join(" ").toLowerCase() : ""
  let score = 0

  if (name === exactQuery) score += 100
  else if (name.includes(exactQuery)) score += 50
  if (summary.includes(exactQuery)) score += 24
  if (tags.includes(exactQuery)) score += 20
  if (category.includes(exactQuery)) score += 12

  for (const term of terms) {
    if (name.includes(term)) score += 10
    if (tags.includes(term)) score += 7
    if (summary.includes(term)) score += 4
    if (category.includes(term)) score += 2
  }
  return score
}

export function scoreLocalEntries(
  query: unknown,
  entries: SearchIndexEntry[],
  limit = 10,
): SearchIndexEntry[] {
  const exactQuery = String(query || "")
    .toLowerCase()
    .trim()
  const terms = tokenize(exactQuery)
  if (!exactQuery || terms.length === 0 || !Array.isArray(entries)) return []

  return entries
    .map((entry) => ({ ...entry, score: scoreEntry(entry, terms, exactQuery) }))
    .filter((entry) => (entry.score || 0) > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return (b.score || 0) - (a.score || 0)
      return String(b.last_updated || "").localeCompare(String(a.last_updated || ""))
    })
    .slice(0, Math.max(0, limit))
}
