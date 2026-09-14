import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import style from "./styles/search-ai-launcher.scss"

export default (() => {
  const SearchAIMobileLauncher: QuartzComponent = ({ displayClass }: QuartzComponentProps) => (
    <button
      class={classNames(displayClass, "search-fab")}
      type="button"
      aria-label="打开 AI 知识检索"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M12 3l1.15 3.35L16.5 7.5l-3.35 1.15L12 12l-1.15-3.35L7.5 7.5l3.35-1.15L12 3Z" />
        <path d="M18 13l.85 2.15L21 16l-2.15.85L18 19l-.85-2.15L15 16l2.15-.85L18 13Z" />
      </svg>
      <span>AI 检索</span>
    </button>
  )

  SearchAIMobileLauncher.css = style

  return SearchAIMobileLauncher
}) satisfies QuartzComponentConstructor
