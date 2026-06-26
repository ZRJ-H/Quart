import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { resolveRelative } from "../util/path"
import { classNames } from "../util/lang"
import { QuartzPluginData } from "../plugins/vfile"

interface Category {
  slug: string
  label: string
}

const categories = (): Category[] => [
  { slug: "AI科技动态", label: "AI动态" },
  { slug: "时政要闻", label: "时政" },
  { slug: "GitHub-Trending", label: "GitHub" },
  { slug: "AI论文日报", label: "论文" },
  { slug: "Hacker-News", label: "HN" },
]

const DAYS_SHOWN = 7
const INTENSITY_LEVELS = 4

const dateFromSlug = (s: string): string | null => {
  const m = s.match(/(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : null
}

// 信息价值权重：字数（内容量）+ 跨链接数（与其他条目的关联密度）+ 数字密度（⭐/%/亿/万等具体数据点）
// 三类笔记结构差异很大（叙事型 vs 表格型），用通用信号而非关键词，保证跨类别都适用
const NUMBER_TOKEN = /[\d,]+(\.\d+)?\s*(%|⭐|亿|万|美元|元|\$|K|M|倍)/g

function infoValue(file: QuartzPluginData): number {
  const text = (file.text as string) ?? ""
  const linkCount = (file.links as string[] | undefined)?.length ?? 0
  const numberDensity = (text.match(NUMBER_TOKEN) ?? []).length
  return text.length / 250 + linkCount * 3 + numberDensity * 2
}

export default (() => {
  const CalendarHeatmap: QuartzComponent = ({
    allFiles,
    fileData,
    displayClass,
  }: QuartzComponentProps) => {
    const cats = categories()

    // 最近 N 天（按所有类别笔记里出现过的日期取并集，倒序取前 N 天）
    const allDates = new Set<string>()
    for (const cat of cats) {
      for (const f of allFiles) {
        if (!f.slug?.startsWith(cat.slug) || f.slug === cat.slug) continue
        const d = dateFromSlug(f.slug)
        if (d) allDates.add(d)
      }
    }
    const days = [...allDates].sort().slice(-DAYS_SHOWN)
    if (days.length === 0) return null

    // 每个类别：日期 -> 文件 + 分值；按本类别内的分值范围归一化档位
    const rows = cats.map((cat) => {
      const byDate = new Map<string, { file: QuartzPluginData; score: number }>()
      for (const f of allFiles) {
        if (!f.slug?.startsWith(cat.slug) || f.slug === cat.slug) continue
        const d = dateFromSlug(f.slug)
        if (!d) continue
        byDate.set(d, { file: f, score: infoValue(f) })
      }
      const scores = [...byDate.values()].map((v) => v.score)
      const min = Math.min(...scores, 0)
      const max = Math.max(...scores, 0)
      const range = max - min || 1

      const cells = days.map((d) => {
        const entry = byDate.get(d)
        if (!entry) return { date: d, level: -1, href: null, score: 0 }
        const level = Math.max(
          0,
          Math.min(INTENSITY_LEVELS, Math.round(((entry.score - min) / range) * INTENSITY_LEVELS)),
        )
        return {
          date: d,
          level,
          href: resolveRelative(fileData.slug!, entry.file.slug!),
          score: entry.score,
        }
      })

      return { cat, cells }
    })

    return (
      <div class={classNames(displayClass, "calendar-heatmap")}>
        <div class="cal-heatmap-grid">
          {rows.map(({ cat, cells }) => (
            <div class="cal-heatmap-row">
              <span class="cal-heatmap-label">{cat.label}</span>
              <div class="cal-heatmap-cells">
                {cells.map((cell) =>
                  cell.href ? (
                    <a
                      href={cell.href}
                      class="cal-heatmap-cell internal"
                      data-level={cell.level}
                      title={`${cat.label} · ${cell.date} · 信息密度 ${cell.level}/${INTENSITY_LEVELS}`}
                    />
                  ) : (
                    <span
                      class="cal-heatmap-cell"
                      data-level={-1}
                      title={`${cat.label} · ${cell.date} · 无数据`}
                    />
                  ),
                )}
              </div>
            </div>
          ))}
          <div class="cal-heatmap-row cal-heatmap-dates">
            <span class="cal-heatmap-label"></span>
            <div class="cal-heatmap-cells">
              {days.map((d) => (
                <span class="cal-heatmap-date">{d.slice(5)}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  CalendarHeatmap.css = `
  .calendar-heatmap {
    margin-bottom: 14px;
    width: 100%;
  }
  .cal-heatmap-grid {
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
  }
  .cal-heatmap-row {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
  }
  .cal-heatmap-label {
    font-size: 0.8rem;
    color: var(--gray);
    width: 48px;
    flex-shrink: 0;
    text-align: right;
  }
  .cal-heatmap-cells {
    display: flex;
    gap: 6px;
    flex: 1 1 auto;
    min-width: 0;
  }
  .cal-heatmap-cell {
    flex: 1 1 0;
    min-width: 0;
    height: 26px;
    border-radius: 4px;
    display: inline-block;
    background: var(--lightgray);
    opacity: 0.5;
    transition: transform 120ms ease, opacity 120ms ease;
  }
  a.cal-heatmap-cell {
    cursor: pointer;
  }
  a.cal-heatmap-cell:hover {
    transform: scaleY(1.15);
    opacity: 1;
  }
  .cal-heatmap-cell[data-level="0"] { background: var(--accent); opacity: 0.18; }
  .cal-heatmap-cell[data-level="1"] { background: var(--accent); opacity: 0.4; }
  .cal-heatmap-cell[data-level="2"] { background: var(--accent); opacity: 0.6; }
  .cal-heatmap-cell[data-level="3"] { background: var(--accent); opacity: 0.8; }
  .cal-heatmap-cell[data-level="4"] { background: var(--accent); opacity: 1; }
  .cal-heatmap-date {
    flex: 1 1 0;
    min-width: 0;
    font-size: 0.72rem;
    color: var(--gray);
    text-align: center;
    white-space: nowrap;
  }
  .cal-heatmap-dates {
    margin-top: 1px;
  }
  @media (max-width: 800px) {
    .cal-heatmap-cell { height: 20px; }
    .cal-heatmap-date { font-size: 0.62rem; }
    .cal-heatmap-label { width: 36px; font-size: 0.72rem; }
  }
  `
  return CalendarHeatmap
}) satisfies QuartzComponentConstructor
