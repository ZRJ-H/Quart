import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import style from "./styles/search-ai.scss"
import { JSX } from "preact"

interface SourceCardProps {
  id: string
  name: string
  category: string
  summary: string
  last_updated: string
  tags: string[]
  score: number
}

// \u7EBF\u6761\u56FE\u6807\u96C6\u66FF\u4EE3 emoji\uFF1A\u4E0E search-ai.inline.js \u7684 ICON_PATHS \u4FDD\u6301\u540C\u4E00\u5957\uFF0C
// \u5168\u90E8\u7528 rect/circle/line/polygon \u57FA\u7840\u56FE\u5143\u7ED8\u5236\uFF0C\u8DE8\u5E73\u53F0\u6E32\u67D3\u4E00\u81F4
const ICON_PATHS: Record<string, string> = {
  building:
    '<rect x="5" y="3" width="14" height="18" rx="1"/><line x1="9" y1="8" x2="9" y2="8.01"/><line x1="15" y1="8" x2="15" y2="8.01"/><line x1="9" y1="12" x2="9" y2="12.01"/><line x1="15" y1="12" x2="15" y2="12.01"/><line x1="9" y1="16" x2="9" y2="16.01"/><line x1="15" y1="16" x2="15" y2="16.01"/>',
  briefcase:
    '<rect x="3" y="7" width="18" height="13" rx="2"/><rect x="8" y="3" width="8" height="4" rx="1"/><line x1="3" y1="13" x2="21" y2="13"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 20a8 8 0 0 1 16 0"/>',
  package:
    '<polygon points="12,3 21,8 21,16 12,21 3,16 3,8"/><polyline points="3,8 12,13 21,8"/><line x1="12" y1="13" x2="12" y2="21"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="1"/><line x1="9" y1="2" x2="9" y2="6"/><line x1="15" y1="2" x2="15" y2="6"/><line x1="9" y1="18" x2="9" y2="22"/><line x1="15" y1="18" x2="15" y2="22"/><line x1="2" y1="9" x2="6" y2="9"/><line x1="2" y1="15" x2="6" y2="15"/><line x1="18" y1="9" x2="22" y2="9"/><line x1="18" y1="15" x2="22" y2="15"/>',
  sliders:
    '<line x1="4" y1="6" x2="20" y2="6"/><circle cx="9" cy="6" r="2"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="7" cy="18" r="2"/>',
  calendar:
    '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  document:
    '<rect x="5" y="2" width="14" height="20" rx="1"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="13" y2="15"/>',
  trending: '<polyline points="3,17 9,11 13,15 21,7"/><polyline points="15,7 21,7 21,13"/>',
  bot: '<rect x="5" y="9" width="14" height="10" rx="2"/><circle cx="9" cy="14" r="1.5"/><circle cx="15" cy="14" r="1.5"/><line x1="12" y1="9" x2="12" y2="5"/><circle cx="12" cy="3" r="1.5"/>',
  spark:
    '<circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/>',
  file: '<rect x="5" y="3" width="14" height="18" rx="1"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/>',
}

const CATEGORY_TO_ICON: Record<string, string> = {
  companies: "building",
  people: "user",
  projects: "package",
  technologies: "chip",
  events: "calendar",
  policies: "document",
  tools: "sliders",
  markets: "trending",
  "ai-agents": "bot",
  technical: "chip",
  trend: "trending",
  business: "briefcase",
}

function getCategoryIcon(category: string): JSX.Element {
  const name = CATEGORY_TO_ICON[category] || "file"
  const inner = ICON_PATHS[name] || ICON_PATHS.file
  return (
    <svg
      class="cat-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: inner }}
    />
  )
}

export default (() => {
  const SourceCard: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
    const sources = (fileData as any).searchSources || []

    if (sources.length === 0) return null

    return (
      <div class={classNames(displayClass, "source-cards")}>
        <h3>
          {"\u{1F4DA}"} 参考来源 ({sources.length})
        </h3>
        <div class="source-card-list">
          {sources.map((source: SourceCardProps) => (
            <div class="source-card" key={source.id}>
              <div class="source-card-header">
                <span class="source-card-icon">{getCategoryIcon(source.category)}</span>
                <span class="source-card-name">{source.name}</span>
                <span class="source-card-category">{source.category}</span>
              </div>
              <div class="source-card-meta">
                <span class="source-card-date">{source.last_updated}</span>
                {source.tags.length > 0 && (
                  <span class="source-card-tags">
                    {source.tags
                      .slice(0, 3)
                      .map((tag) => `#${tag}`)
                      .join(" ")}
                  </span>
                )}
              </div>
              <div class="source-card-summary">{source.summary}</div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  SourceCard.css = style

  return SourceCard
}) satisfies QuartzComponentConstructor
