import { FullSlug, simplifySlug } from "../../util/path"

type MaybeHTMLElement = HTMLElement | undefined

interface ParsedOptions {
  folderClickBehavior: "collapse" | "link"
  folderDefaultState: "collapsed" | "open"
  useSavedState: boolean
}

type FolderState = {
  path: string
  collapsed: boolean
}

let currentExplorerState: Array<FolderState>
function toggleExplorer(this: HTMLElement) {
  const nearestExplorer = this.closest(".explorer") as HTMLElement
  if (!nearestExplorer) return
  const explorerCollapsed = nearestExplorer.classList.toggle("collapsed")
  const isExpanded = !explorerCollapsed
  nearestExplorer.setAttribute("aria-expanded", isExpanded.toString())
  this.setAttribute("aria-expanded", isExpanded.toString())

  if (isExpanded) {
    document.documentElement.classList.add("mobile-no-scroll")
  } else {
    document.documentElement.classList.remove("mobile-no-scroll")
  }
}

function toggleFolder(evt: MouseEvent) {
  evt.stopPropagation()
  const target = evt.target as MaybeHTMLElement
  if (!target) return

  const isSvg = target.nodeName === "svg"
  const folderContainer = (
    isSvg ? target.parentElement : target.parentElement?.parentElement
  ) as MaybeHTMLElement
  if (!folderContainer) return
  const childFolderContainer = folderContainer.nextElementSibling as MaybeHTMLElement
  if (!childFolderContainer) return

  childFolderContainer.classList.toggle("open")
  const isCollapsed = !childFolderContainer.classList.contains("open")
  setFolderState(childFolderContainer, isCollapsed)

  const currentFolderState = currentExplorerState.find(
    (item) => item.path === folderContainer.dataset.folderpath,
  )
  if (currentFolderState) {
    currentFolderState.collapsed = isCollapsed
  } else {
    currentExplorerState.push({
      path: folderContainer.dataset.folderpath as FullSlug,
      collapsed: isCollapsed,
    })
  }

  localStorage.setItem("fileTree", JSON.stringify(currentExplorerState))
}

function setupExplorer(currentSlug: FullSlug) {
  const allExplorers = document.querySelectorAll("div.explorer") as NodeListOf<HTMLElement>

  for (const explorer of allExplorers) {
    const opts: ParsedOptions = {
      folderClickBehavior: (explorer.dataset.behavior || "collapse") as "collapse" | "link",
      folderDefaultState: (explorer.dataset.collapsed || "collapsed") as "collapsed" | "open",
      useSavedState: explorer.dataset.savestate === "true",
    }

    const storageTree = localStorage.getItem("fileTree")
    const serializedExplorerState = storageTree && opts.useSavedState ? JSON.parse(storageTree) : []
    const oldIndex = new Map<string, boolean>(
      serializedExplorerState.map((entry: FolderState) => [entry.path, entry.collapsed]),
    )

    const folderContainers = explorer.querySelectorAll(
      ".folder-container[data-folderpath]",
    ) as NodeListOf<HTMLElement>
    currentExplorerState = Array.from(folderContainers, (folderContainer) => {
      const path = folderContainer.dataset.folderpath as FullSlug
      const previousState = oldIndex.get(path)
      const collapsed =
        previousState === undefined ? opts.folderDefaultState === "collapsed" : previousState

      const simpleFolderPath = simplifySlug(path)
      const folderIsPrefixOfCurrentSlug =
        simpleFolderPath === currentSlug.slice(0, simpleFolderPath.length)
      const folderOuter = folderContainer.nextElementSibling as MaybeHTMLElement
      if (folderOuter) {
        setFolderState(folderOuter, collapsed && !folderIsPrefixOfCurrentSlug)
      }

      return { path, collapsed }
    })

    const explorerUl = explorer.querySelector(".explorer-ul")
    if (!explorerUl) continue

    const scrollTop = sessionStorage.getItem("explorerScrollTop")
    if (scrollTop) {
      explorerUl.scrollTop = parseInt(scrollTop)
    } else {
      const activeElement = explorerUl.querySelector(".active")
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: "smooth" })
      }
    }

    const explorerButtons = explorer.getElementsByClassName(
      "explorer-toggle",
    ) as HTMLCollectionOf<HTMLElement>
    for (const button of explorerButtons) {
      button.addEventListener("click", toggleExplorer)
      window.addCleanup(() => button.removeEventListener("click", toggleExplorer))
    }

    if (opts.folderClickBehavior === "collapse") {
      const folderButtons = explorer.getElementsByClassName(
        "folder-button",
      ) as HTMLCollectionOf<HTMLElement>
      for (const button of folderButtons) {
        button.addEventListener("click", toggleFolder)
        window.addCleanup(() => button.removeEventListener("click", toggleFolder))
      }
    }

    const folderIcons = explorer.getElementsByClassName(
      "folder-icon",
    ) as HTMLCollectionOf<HTMLElement>
    for (const icon of folderIcons) {
      icon.addEventListener("click", toggleFolder)
      window.addCleanup(() => icon.removeEventListener("click", toggleFolder))
    }
  }
}

document.addEventListener("prenav", async () => {
  const explorer = document.querySelector(".explorer-ul")
  if (!explorer) return
  sessionStorage.setItem("explorerScrollTop", explorer.scrollTop.toString())
})

document.addEventListener("nav", (e: CustomEventMap["nav"]) => {
  const currentSlug = e.detail.url
  setupExplorer(currentSlug)

  for (const explorer of document.getElementsByClassName("explorer")) {
    const mobileExplorer = explorer.querySelector(".mobile-explorer")
    if (!mobileExplorer) return

    if (mobileExplorer.checkVisibility()) {
      explorer.classList.add("collapsed")
      explorer.setAttribute("aria-expanded", "false")
      mobileExplorer.setAttribute("aria-expanded", "false")
      document.documentElement.classList.remove("mobile-no-scroll")
    }

    mobileExplorer.classList.remove("hide-until-loaded")
  }
})

window.addEventListener("resize", function () {
  const explorer = document.querySelector(".explorer")
  if (explorer && !explorer.classList.contains("collapsed")) {
    document.documentElement.classList.add("mobile-no-scroll")
    return
  }
})

function setFolderState(folderElement: HTMLElement, collapsed: boolean) {
  return collapsed ? folderElement.classList.remove("open") : folderElement.classList.add("open")
}
