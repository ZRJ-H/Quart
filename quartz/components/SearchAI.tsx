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
        <div class="ai-search-intro">
          <span class="ai-search-mark" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M12 3l1.15 3.35L16.5 7.5l-3.35 1.15L12 12l-1.15-3.35L7.5 7.5l3.35-1.15L12 3Z" />
              <path d="M18 13l.85 2.15L21 16l-2.15.85L18 19l-.85-2.15L15 16l2.15-.85L18 13Z" />
              <path d="M6 14l.7 1.8 1.8.7-1.8.7L6 19l-.7-1.8-1.8-.7 1.8-.7L6 14Z" />
            </svg>
          </span>
          <span class="ai-search-copy">
            <strong class="ai-search-title">AI 知识检索</strong>
            <span class="ai-search-description">用自然语言提问，快速找到知识库里的答案</span>
          </span>
        </div>
        <div class="ai-search-box" style="position: relative;">
          <input
            type="text"
            class="ai-search-input"
            placeholder="输入你的问题..."
            id="ai-search-input"
            autocomplete="off"
            data-worker={opts.workerUrl}
          />
          <button class="ai-search-btn" id="ai-search-btn" aria-label="向 AI 提问">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <span class="ai-search-btn-label">提问</span>
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
