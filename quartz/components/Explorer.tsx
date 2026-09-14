import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import style from "./styles/explorer.scss"

// @ts-ignore
import script from "./scripts/explorer.inline"
import { classNames } from "../util/lang"
import { i18n } from "../i18n"
import { FileTrieNode } from "../util/fileTrie"
import { FullSlug, resolveRelative, simplifySlug } from "../util/path"
import type { ContentDetails } from "../plugins/emitters/contentIndex"
import { QuartzPluginData } from "../plugins/vfile"
import OverflowListFactory from "./OverflowList"
import { concatenateResources } from "../util/resources"

type OrderEntries = "sort" | "filter" | "map"

export interface Options {
  title?: string
  folderDefaultState: "collapsed" | "open"
  folderClickBehavior: "collapse" | "link"
  useSavedState: boolean
  sortFn: (a: FileTrieNode, b: FileTrieNode) => number
  filterFn: (node: FileTrieNode) => boolean
  mapFn: (node: FileTrieNode) => void
  order: OrderEntries[]
}

const defaultOptions: Options = {
  folderDefaultState: "collapsed",
  folderClickBehavior: "link",
  useSavedState: true,
  mapFn: (node) => {
    return node
  },
  sortFn: (a, b) => {
    // Sort order: folders first, then files. Sort folders and files alphabetically.
    if ((!a.isFolder && !b.isFolder) || (a.isFolder && b.isFolder)) {
      return a.displayName.localeCompare(b.displayName, undefined, {
        numeric: true,
        sensitivity: "base",
      })
    }

    return !a.isFolder && b.isFolder ? 1 : -1
  },
  filterFn: (node) => node.slugSegment !== "tags",
  order: ["filter", "map", "sort"],
}

export type FolderState = {
  path: string
  collapsed: boolean
}

function buildExplorerTree(allFiles: QuartzPluginData[], opts: Options) {
  const entries: [FullSlug, ContentDetails][] = []

  for (const file of allFiles) {
    if (!file.slug || !file.relativePath) continue
    entries.push([
      file.slug,
      {
        slug: file.slug,
        filePath: file.relativePath,
        title: file.frontmatter?.title ?? file.slug,
        links: file.links ?? [],
        tags: file.frontmatter?.tags ?? [],
        content: file.text ?? "",
      },
    ])
  }

  const trie = FileTrieNode.fromEntries(entries)
  for (const fn of opts.order) {
    switch (fn) {
      case "filter":
        trie.filter(opts.filterFn)
        break
      case "map":
        trie.map(opts.mapFn)
        break
      case "sort":
        trie.sort(opts.sortFn)
        break
    }
  }

  return trie
}

let numExplorers = 0
export default ((userOpts?: Partial<Options>) => {
  const opts: Options = { ...defaultOptions, ...userOpts }
  const { OverflowList, overflowListAfterDOMLoaded } = OverflowListFactory()
  let cachedFiles: QuartzPluginData[] | undefined
  let cachedTree: FileTrieNode | undefined

  const Explorer: QuartzComponent = ({
    cfg,
    displayClass,
    allFiles,
    fileData,
  }: QuartzComponentProps) => {
    const id = `explorer-${numExplorers++}`
    const currentSlug = fileData.slug ?? ("index" as FullSlug)

    if (cachedFiles !== allFiles || !cachedTree) {
      cachedFiles = allFiles
      cachedTree = buildExplorerTree(allFiles, opts)
    }

    const renderNode = (node: FileTrieNode) => {
      if (!node.isFolder) {
        return (
          <li>
            <a
              href={resolveRelative(currentSlug, node.slug)}
              data-for={node.slug}
              class={currentSlug === node.slug ? "active" : undefined}
            >
              {node.displayName}
            </a>
          </li>
        )
      }

      const folderPath = node.slug
      const simpleFolderPath = simplifySlug(folderPath)
      const folderIsPrefixOfCurrentSlug =
        simpleFolderPath === currentSlug.slice(0, simpleFolderPath.length)
      const folderIsOpen = opts.folderDefaultState === "open" || folderIsPrefixOfCurrentSlug

      return (
        <li>
          <div
            class={currentSlug === folderPath ? "folder-container active" : "folder-container"}
            data-folderpath={folderPath}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="12"
              height="12"
              viewBox="5 8 14 8"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="folder-icon"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
            <div>
              {opts.folderClickBehavior === "link" ? (
                <a
                  href={resolveRelative(currentSlug, folderPath)}
                  data-for={folderPath}
                  class="folder-title"
                >
                  {node.displayName}
                </a>
              ) : (
                <button type="button" class="folder-button">
                  <span class="folder-title">{node.displayName}</span>
                </button>
              )}
            </div>
          </div>
          <div class={folderIsOpen ? "folder-outer open" : "folder-outer"}>
            <ul class="content">{node.children.map(renderNode)}</ul>
          </div>
        </li>
      )
    }

    return (
      <div
        class={classNames(displayClass, "explorer")}
        data-behavior={opts.folderClickBehavior}
        data-collapsed={opts.folderDefaultState}
        data-savestate={opts.useSavedState}
      >
        <button
          type="button"
          class="explorer-toggle mobile-explorer hide-until-loaded"
          data-mobile={true}
          aria-controls={id}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="lucide-menu"
          >
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </svg>
        </button>
        <button
          type="button"
          class="title-button explorer-toggle desktop-explorer"
          data-mobile={false}
          aria-controls={id}
          aria-expanded={true}
        >
          <h2>{opts.title ?? i18n(cfg.locale).components.explorer.title}</h2>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="5 8 14 8"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="fold"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <div id={id} class="explorer-content" aria-expanded={false} role="group">
          <OverflowList class="explorer-ul">{cachedTree.children.map(renderNode)}</OverflowList>
        </div>
      </div>
    )
  }

  Explorer.css = style
  Explorer.afterDOMLoaded = concatenateResources(script, overflowListAfterDOMLoaded)
  return Explorer
}) satisfies QuartzComponentConstructor
