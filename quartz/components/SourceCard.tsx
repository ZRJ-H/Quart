import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import style from "./styles/search-ai.scss"

interface SourceCardProps {
  id: string
  name: string
  category: string
  summary: string
  last_updated: string
  tags: string[]
  score: number
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    companies: "\u{1F3E2}",
    people: "\u{1F464}",
    projects: "\u{1F4E6}",
    technologies: "\u2699\uFE0F",
    events: "\u{1F4C5}",
    policies: "\u{1F4DC}",
    tools: "\u{1F527}",
    markets: "\u{1F4C8}",
    "ai-agents": "\u{1F916}",
    technical: "\u{1F4A1}",
    trend: "\u{1F4CA}",
    business: "\u{1F4BC}",
  }
  return icons[category] || "\u{1F4C4}"
}

export default (() => {
  const SourceCard: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
    const sources = (fileData as any).searchSources || []

    if (sources.length === 0) return null

    return (
      <div class={classNames(displayClass, "source-cards")}>
        <h3>{"\u{1F4DA}"} 参考来源 ({sources.length})</h3>
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
