import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"

export default (() => {
  const SearchFilters: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <div class={classNames(displayClass, "search-filters")}>
        <div class="filter-group">
          <label>标签：</label>
          <div class="filter-tags">
            <button class="filter-tag active" data-tag="all">全部</button>
            <button class="filter-tag" data-tag="ai-agents">AI</button>
            <button class="filter-tag" data-tag="policies">政策</button>
            <button class="filter-tag" data-tag="companies">公司</button>
            <button class="filter-tag" data-tag="technologies">技术</button>
            <button class="filter-tag" data-tag="events">事件</button>
            <button class="filter-tag" data-tag="people">人物</button>
          </div>
        </div>
        <div class="filter-group">
          <label>时间：</label>
          <div class="filter-time">
            <button class="filter-time-btn active" data-time="all">全部</button>
            <button class="filter-time-btn" data-time="7d">7天</button>
            <button class="filter-time-btn" data-time="30d">30天</button>
          </div>
        </div>
        <div class="filter-group">
          <label>排序：</label>
          <div class="filter-sort">
            <button class="filter-sort-btn active" data-sort="relevance">相关性</button>
            <button class="filter-sort-btn" data-sort="time">时间</button>
            <button class="filter-sort-btn" data-sort="popularity">热度</button>
          </div>
        </div>
      </div>
    )
  }

  SearchFilters.css = `
  .search-filters {
    background: var(--light);
    border-radius: 8px;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    display: flex;
  }
  @media (max-width: 800px) {
    .search-filters {
      flex-direction: column;
      gap: .75rem;
    }
  }
  .search-filters .filter-group {
    align-items: center;
    gap: .5rem;
    display: flex;
  }
  .search-filters .filter-group label {
    color: var(--gray);
    white-space: nowrap;
    font-size: .9rem;
  }
  .search-filters .filter-tags,
  .search-filters .filter-time,
  .search-filters .filter-sort {
    flex-wrap: wrap;
    gap: .25rem;
    display: flex;
  }
  .search-filters .filter-tag,
  .search-filters .filter-time-btn,
  .search-filters .filter-sort-btn {
    border: 1px solid var(--lightgray);
    cursor: pointer;
    background: var(--light);
    border-radius: 4px;
    padding: .25rem .75rem;
    font-size: .85rem;
    transition: all .2s;
    color: var(--darkgray);
  }
  .search-filters .filter-tag:hover,
  .search-filters .filter-time-btn:hover,
  .search-filters .filter-sort-btn:hover {
    border-color: var(--secondary);
    color: var(--secondary);
  }
  .search-filters .filter-tag.active,
  .search-filters .filter-time-btn.active,
  .search-filters .filter-sort-btn.active {
    background: var(--secondary);
    color: #fff;
    border-color: var(--secondary);
  }
  `

  return SearchFilters
}) satisfies QuartzComponentConstructor
