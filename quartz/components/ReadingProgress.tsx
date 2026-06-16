// @ts-ignore
import readingProgressScript from "./scripts/readingprogress.inline"
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"

const ReadingProgress: QuartzComponent = (_props: QuartzComponentProps) => {
  return <div class="reading-progress-bar" />
}

ReadingProgress.afterDOMLoaded = readingProgressScript
ReadingProgress.css = `
.reading-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  width: 0%;
  background: var(--accent);
  z-index: 1000;
  pointer-events: none;
}
`

export default (() => ReadingProgress) satisfies QuartzComponentConstructor
