import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"

export default (() => {
  const SearchSuggestions: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
    return (
      <div class={classNames(displayClass, "search-suggestions")} style="display: none;">
        <div class="suggestions-list"></div>
      </div>
    )
  }

  return SearchSuggestions
}) satisfies QuartzComponentConstructor
