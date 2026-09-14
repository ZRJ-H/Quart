import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import path from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

import { build } from "esbuild"

const searchUrl = new URL("../quartz/components/scripts/search.inline.ts", import.meta.url)

async function loadHighlight() {
  const source = await readFile(searchUrl, "utf8")
  const start = source.indexOf("const tokenizeTerm")
  const end = source.indexOf("\nfunction highlightHTML", start)
  assert.notEqual(start, -1)
  assert.notEqual(end, -1)
  const functionSource = source.slice(start, end)
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import { escapeHTML } from "../../util/escape"',
        functionSource,
        "export { highlight }",
      ].join("\n"),
      loader: "ts",
      resolveDir: path.dirname(fileURLToPath(searchUrl)),
    },
  })
  const encoded = Buffer.from(result.outputFiles[0].text).toString("base64")
  return import(`data:text/javascript;base64,${encoded}`)
}

async function loadHighlightTags() {
  const source = await readFile(searchUrl, "utf8")
  const start = source.indexOf("  function highlightTags")
  const end = source.indexOf("\n\n  function resolveUrl", start)
  assert.notEqual(start, -1)
  assert.notEqual(end, -1)
  const functionSource = source.slice(start, end).replace(/^  /gm, "")
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import { escapeHTML } from "../../util/escape"',
        'let searchType = "tags"',
        "const numTagResults = 5",
        functionSource,
        "export { highlightTags }",
      ].join("\n"),
      loader: "ts",
      resolveDir: path.dirname(fileURLToPath(searchUrl)),
    },
  })
  const encoded = Buffer.from(result.outputFiles[0].text).toString("base64")
  return import(`data:text/javascript;base64,${encoded}`)
}

async function loadHighlightHtml() {
  const source = await readFile(searchUrl, "utf8")
  const start = source.indexOf("const tokenizeTerm")
  const end = source.indexOf("\nasync function setupSearch", start)
  assert.notEqual(start, -1)
  assert.notEqual(end, -1)
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import { escapeHTML } from "../../util/escape"',
        source.slice(start, end),
        "export { highlightHTML }",
      ].join("\n"),
      loader: "ts",
      resolveDir: path.dirname(fileURLToPath(searchUrl)),
    },
  })
  const encoded = Buffer.from(result.outputFiles[0].text).toString("base64")
  return import(`data:text/javascript;base64,${encoded}`)
}

async function loadTagResultFormatter() {
  const source = await readFile(searchUrl, "utf8")
  const start = source.indexOf("  const formatForDisplay")
  const end = source.indexOf("\n\n  function highlightTags", start)
  assert.notEqual(start, -1)
  assert.notEqual(end, -1)
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import { escapeHTML } from "../../util/escape"',
        'const searchType = "tags"',
        'const idDataMap = { 1: "malicious" }',
        'const data = { malicious: { title: "<img src=x onerror=alert(1)>", content: "", tags: [] } }',
        "const highlight = (_term, text) => text",
        "const highlightTags = () => []",
        source.slice(start, end).replace(/^  /gm, ""),
        "export { formatForDisplay }",
      ].join("\n"),
      loader: "ts",
      resolveDir: path.dirname(fileURLToPath(searchUrl)),
    },
  })
  const encoded = Buffer.from(result.outputFiles[0].text).toString("base64")
  return import(`data:text/javascript;base64,${encoded}`)
}

test("basic search escapes indexed title and content before adding highlight markup", async () => {
  const { highlight } = await loadHighlight()
  const html = highlight("safe", "<img src=x onerror=alert(1)> safe")

  assert.doesNotMatch(html, /<img/i)
  assert.match(html, /&lt;img/)
  assert.match(html, /<span class="highlight">safe<\/span>/)
})

test("tag search escapes indexed tag names before rendering list markup", async () => {
  const { highlightTags } = await loadHighlightTags()
  const [html] = highlightTags("svg", ["<svg onload=alert(1)>"])

  assert.doesNotMatch(html, /<svg/i)
  assert.match(html, /&lt;svg/)
})

test("tag search escapes the indexed page title", async () => {
  const { formatForDisplay } = await loadTagResultFormatter()
  const result = formatForDisplay("#svg", 1)

  assert.doesNotMatch(result.title, /<img/i)
  assert.match(result.title, /&lt;img/)
})

test("HTML highlighting treats regular expression metacharacters as literal text", async () => {
  const { highlightHTML } = await loadHighlightHtml()
  globalThis.Node = { TEXT_NODE: 3, ELEMENT_NODE: 1 }
  globalThis.DOMParser = class {
    parseFromString() {
      return { body: { nodeType: 3, nodeValue: "safe text" } }
    }
  }

  assert.doesNotThrow(() => highlightHTML("[", { innerHTML: "safe text" }))
})
