import assert from "node:assert/strict"
import test from "node:test"
import { existsSync } from "node:fs"
import { readFile } from "node:fs/promises"
import { build } from "esbuild"

async function renderComponent(importPath: string, constructorExpression: string) {
  const result = await build({
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    stdin: {
      contents: [
        'import render from "preact-render-to-string"',
        'import ComponentConstructor from "' + importPath + '"',
        "const Component = " + constructorExpression,
        "export default render(Component({}))",
      ].join("\n"),
      loader: "tsx",
      resolveDir: process.cwd(),
    },
    loader: { ".scss": "text" },
    plugins: [
      {
        name: "inline-script-as-text",
        setup(builder) {
          builder.onLoad({ filter: /\.inline\.js$/ }, async ({ path }) => ({
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

function renderSearchAI() {
  return renderComponent(
    "./quartz/components/SearchAI.tsx",
    'ComponentConstructor({ workerUrl: "https://example.com" })',
  )
}

function renderMobileLauncher() {
  const componentPath = "quartz/components/SearchAIMobileLauncher.tsx"
  if (!existsSync(componentPath)) return Promise.resolve("")
  return renderComponent("./quartz/components/SearchAIMobileLauncher.tsx", "ComponentConstructor()")
}

test("desktop search entry identifies itself as AI knowledge retrieval", async () => {
  const html = await renderSearchAI()

  assert.match(html, />AI 知识检索</)
  assert.match(html, />用自然语言提问，快速找到知识库里的答案</)
  assert.match(html, />提问</)
})

test("sidebar search entry does not own the mobile launcher", async () => {
  const html = await renderSearchAI()

  assert.doesNotMatch(html, /class="search-fab"/)
})

test("mobile AI search launcher renders outside the sidebar component", async () => {
  const html = await renderMobileLauncher()

  assert.match(html, /class="search-fab"/)
  assert.match(html, /aria-label="打开 AI 知识检索"/)
  assert.match(html, />AI 检索</)
})
