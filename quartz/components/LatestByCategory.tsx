import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { resolveRelative } from "../util/path"
import { classNames } from "../util/lang"

interface Category {
  slug: string
  icon: string
  label: string
}

const defaultCategories = (): Category[] => [
  { slug: "AI科技动态", icon: "", label: "AI动态" },
  { slug: "GitHub-Trending", icon: "", label: "GitHub" },
  { slug: "时政要闻", icon: "", label: "时政" },
  { slug: "AI论文日报", icon: "", label: "论文" },
  { slug: "Hacker-News", icon: "", label: "HN" },
]

const slugDate = (s: string): number => {
  const m = s.match(/(\d{4}-\d{2}-\d{2})/)
  return m ? +new Date(m[1]) : 0
}

export default (() => {
  const LatestByCategory: QuartzComponent = ({
    allFiles,
    fileData,
    displayClass,
  }: QuartzComponentProps) => {
    const categories = defaultCategories()

    return (
      <div class={classNames(displayClass, "latest-by-category")}>
        <span class="lbc-label"></span>
        {categories.map((cat) => {
          const latest = allFiles
            .filter((f) => f.slug?.startsWith(cat.slug as any) && f.slug !== cat.slug)
            .sort((a, b) => slugDate(b.slug!) - slugDate(a.slug!))[0]

          if (!latest) return null

          const title = (latest.frontmatter?.title ?? latest.slug?.split("/").pop() ?? "").slice(-5)

          return (
            <a
              href={resolveRelative(fileData.slug!, latest.slug!)}
              class="lbc-link internal"
            >
              {cat.icon} {cat.label} · {title}
            </a>
          )
        })}
      </div>
    )
  }

  LatestByCategory.css = `
  .latest-by-category {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    align-items: center;
    padding: 4px 0 6px;
    font-size: 0.9rem;
    border-bottom: 1px solid var(--lightgray);
    margin-bottom: 10px;
  }
  .lbc-label {
    font-size: 0.85rem;
    color: var(--gray);
    flex-shrink: 0;
  }
  .lbc-link {
    color: var(--darkgray);
    text-decoration: none;
    white-space: nowrap;
  }
  .lbc-link:hover {
    color: var(--secondary);
  }
  @media (max-width: 800px) {
    .latest-by-category { font-size: 0.82rem; gap: 8px; }
  }
  `
  return LatestByCategory
}) satisfies QuartzComponentConstructor
