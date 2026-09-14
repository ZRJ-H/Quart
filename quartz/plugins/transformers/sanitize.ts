import { defaultSchema } from "rehype-sanitize"
import { Root } from "hast"
import { SKIP, visit } from "unist-util-visit"

const localAssetOrigin = "https://quartz.invalid"
const safeMediaExtensions = {
  video: new Set([".mp4", ".webm", ".ogv", ".mov", ".mkv"]),
  audio: new Set([".mp3", ".webm", ".wav", ".m4a", ".ogg", ".3gp", ".flac"]),
  iframe: new Set([".pdf"]),
}

const withClassName = (attributes: readonly unknown[] | undefined) => [
  ...(attributes ?? []),
  "className",
]

export const quartzSanitizeSchema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames ?? []), "audio", "video", "iframe"],
  attributes: {
    ...defaultSchema.attributes,
    blockquote: [
      ...withClassName(defaultSchema.attributes?.blockquote),
      "dataCallout",
      "dataCalloutFold",
      "dataCalloutMetadata",
    ],
    button: [
      ...withClassName(defaultSchema.attributes?.button),
      "ariaLabel",
      "dataViewComponent",
      "type",
    ],
    div: withClassName(defaultSchema.attributes?.div),
    img: withClassName(defaultSchema.attributes?.img),
    audio: ["src", "controls"],
    video: ["src", "controls"],
    iframe: ["src", "className", "title"],
    input: withClassName(defaultSchema.attributes?.input),
    span: withClassName(defaultSchema.attributes?.span),
  },
}

function isSafeLocalMediaSource(tagName: keyof typeof safeMediaExtensions, value: unknown) {
  if (typeof value !== "string" || !value || value.startsWith("//") || value.includes("\\")) {
    return false
  }
  try {
    const url = new URL(value, localAssetOrigin)
    if (url.origin !== localAssetOrigin) return false
    const path = url.pathname.toLowerCase()
    return [...safeMediaExtensions[tagName]].some((extension) => path.endsWith(extension))
  } catch {
    return false
  }
}

export const removeUnsafeMediaEmbeds = () => (tree: Root) => {
  visit(tree, "element", (node, index, parent) => {
    if (!(node.tagName in safeMediaExtensions)) return
    const tagName = node.tagName as keyof typeof safeMediaExtensions
    if (isSafeLocalMediaSource(tagName, node.properties.src)) return
    if (parent && typeof index === "number") {
      parent.children.splice(index, 1)
      return [SKIP, index]
    }
  })
}
