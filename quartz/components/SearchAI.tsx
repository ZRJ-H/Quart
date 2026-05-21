import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/search-ai.inline"
import style from "./styles/search-ai.scss"

export interface SearchAIOptions {
  workerUrl: string
}

const defaultOptions: SearchAIOptions = {
  workerUrl: "https://doge-wiki-search.YOUR_SUBDOMAIN.workers.dev",
}

export default ((userOpts?: Partial<SearchAIOptions>) => {
  const opts = { ...defaultOptions, ...userOpts }

  const SearchAI: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <div class={classNames(displayClass, "search-ai")}>
        <div class="ai-search-box">
          <input
            type="text"
            class="ai-search-input"
            placeholder="向知识库提问..."
            id="ai-search-input"
            autocomplete="off"
            data-worker={opts.workerUrl}
          />
          <button class="ai-search-btn" id="ai-search-btn" aria-label="搜索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <polyline points="4 4 12 4 20 4" />
              <polyline points="4 4 4 12 12 12" />
              <polyline points="20 4 20 20 12 20" />
              <line x1="7" y1="10" x2="7" y2="10" />
            </svg>
          </button>
        </div>
        <div class="ai-search-status" id="ai-search-status"></div>
        <div class="ai-search-result" id="ai-search-result"></div>
      </div>
    )
  }

  SearchAI.css = style
  SearchAI.afterDOMLoaded = script

  return SearchAI
}) satisfies QuartzComponentConstructor
