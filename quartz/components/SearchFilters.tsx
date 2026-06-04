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

  return SearchFilters
}) satisfies QuartzComponentConstructor
