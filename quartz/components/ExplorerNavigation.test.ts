import assert from "node:assert/strict"
import test from "node:test"
import { readFile } from "node:fs/promises"
import { build } from "esbuild"

async function renderExplorer() {
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import render from "preact-render-to-string"',
        'import ExplorerConstructor from "./quartz/components/Explorer.tsx"',
        "const Explorer = ExplorerConstructor({",
        '  folderDefaultState: "open",',
        '  filterFn: (node) => node.slugSegment !== "hidden",',
        "  sortFn: (a, b) => a.displayName.localeCompare(b.displayName),",
        "})",
        "const props = {",
        '  cfg: { locale: "zh-CN" },',
        '  fileData: { slug: "index" },',
        "  allFiles: [",
        '    { slug: "z-note", relativePath: "z-note.md", frontmatter: { title: "Z Note" } },',
        '    { slug: "a-note", relativePath: "a-note.md", frontmatter: { title: "A Note" } },',
        '    { slug: "hidden/note", relativePath: "hidden/note.md", frontmatter: { title: "Hidden" } },',
        "  ],",
        "}",
        "export default render(Explorer(props))",
      ].join("\n"),
      loader: "tsx",
      resolveDir: process.cwd(),
    },
    loader: { ".scss": "text" },
    plugins: [
      {
        name: "inline-script-as-text",
        setup(builder) {
          builder.onLoad({ filter: /\.inline\.ts$/ }, async ({ path }) => ({
            contents: await readFile(path, "utf8"),
            loader: "text",
          }))
        },
      },
    ],
  })

  const source = Buffer.from(result.outputFiles[0].text).toString("base64")
  const module = await import("data:text/javascript;base64," + source)
  return module.default as string
}

test("Explorer renders its filtered and sorted navigation before client scripts run", async () => {
  const html = await renderExplorer()

  const firstVisibleItem = html.indexOf(">A Note</a>")
  const secondVisibleItem = html.indexOf(">Z Note</a>")

  assert.notEqual(firstVisibleItem, -1)
  assert.notEqual(secondVisibleItem, -1)
  assert.ok(firstVisibleItem < secondVisibleItem)
  assert.doesNotMatch(html, />Hidden</)
})
