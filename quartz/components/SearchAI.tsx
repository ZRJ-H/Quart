import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { joinSegments, pathToRoot } from "../util/path"
// @ts-ignore
import script from "./scripts/search-ai.inline"
import style from "./styles/search-ai.scss"

export interface SearchAIOptions {
  endpoint: string
}

const defaultOptions: SearchAIOptions = {
  endpoint: "",
}

export default ((userOpts?: Partial<SearchAIOptions>) => {
  const opts = { ...defaultOptions, ...userOpts }

  const SearchAI: QuartzComponent = ({ displayClass, fileData }: QuartzComponentProps) => {
    const root = pathToRoot(fileData.slug!)
    return (
      <div class={classNames(displayClass, "search-ai")}>
        <div class="ai-search-box" style="position: relative;">
          <input
            type="text"
            class="ai-search-input"
            placeholder="向知识库提问..."
            id="ai-search-input"
            autocomplete="off"
            data-endpoint={opts.endpoint}
            data-index-light={joinSegments(root, "wiki-index-light.json")}
            data-index-full={joinSegments(root, "wiki-index.json")}
          />
          <button class="ai-search-btn" id="ai-search-btn" aria-label="搜索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </button>
          <div class="search-suggestions" style="display: none;">
            <div class="suggestions-list"></div>
          </div>
        </div>
        <div class="ai-search-status" id="ai-search-status"></div>
        <div class="ai-search-results" id="ai-search-results" style="display: none;">
          <div class="ai-search-main">
            <div class="ai-search-answer" id="ai-search-answer"></div>
          </div>
          <div class="ai-search-sidebar">
            <div class="ai-search-sources" id="ai-search-sources"></div>
          </div>
        </div>
        <div class="search-history" style="display: none;">
          <div class="history-header">
            <h3>最近搜索</h3>
            <button class="history-clear">清除</button>
          </div>
          <div class="history-list"></div>
        </div>
      </div>
    )
  }

  SearchAI.css = style
  SearchAI.afterDOMLoaded = script

  return SearchAI
}) satisfies QuartzComponentConstructor
