import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import { fileURLToPath } from "node:url"

import { build } from "esbuild"
import { toHtml } from "hast-util-to-html"
import remarkParse from "remark-parse"
import remarkRehype from "remark-rehype"
import { unified } from "unified"

const ofmUrl = new URL("../quartz/plugins/transformers/ofm.ts", import.meta.url)

async function loadOfm() {
  const result = await build({
    entryPoints: [fileURLToPath(ofmUrl)],
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
    loader: { ".scss": "text" },
    plugins: [
      {
        name: "inline-assets-as-text",
        setup(buildApi) {
          buildApi.onLoad({ filter: /\.inline\.(?:ts|js)$/ }, async ({ path }) => ({
            contents: await readFile(path, "utf8"),
            loader: "text",
          }))
        },
      },
    ],
  })
  const encoded = Buffer.from(result.outputFiles[0].text).toString("base64")
  return import(`data:text/javascript;base64,${encoded}`)
}

async function render(markdown) {
  const { ObsidianFlavoredMarkdown } = await loadOfm()
  const ofm = ObsidianFlavoredMarkdown()
  const processor = unified()
    .use(remarkParse)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(ofm.htmlPlugins())
  const tree = await processor.run(processor.parse(markdown))
  return toHtml(tree)
}

test("OFM raw HTML removes executable elements, handlers, and unsafe protocols", async () => {
  const html = await render(
    [
      "<script>alert(1)</script>",
      '<img src="x" onerror="alert(2)">',
      '<a href="javascript:alert(3)">owned</a>',
      "<strong>safe formatting</strong>",
    ].join("\n"),
  )

  assert.doesNotMatch(html, /<script|onerror|javascript:/i)
  assert.match(html, /<strong>safe formatting<\/strong>/)
})

test("OFM keeps only local media assets and local PDF frames", async () => {
  const html = await render(
    [
      '<video src="./media/clip.mp4" controls></video>',
      '<audio src="/Quart/media/voice.mp3" controls></audio>',
      '<iframe src="./docs/guide.pdf" class="pdf"></iframe>',
      '<iframe src="https://evil.example/payload.pdf"></iframe>',
      '<iframe src="./docs/not-a-pdf.html"></iframe>',
      '<video src="javascript:alert(1)"></video>',
    ].join("\n"),
  )

  assert.match(html, /<video[^>]+clip\.mp4[^>]+controls/)
  assert.match(html, /<audio[^>]+voice\.mp3[^>]+controls/)
  assert.match(html, /<iframe[^>]+guide\.pdf[^>]+class="pdf"/)
  assert.doesNotMatch(html, /evil\.example|not-a-pdf|javascript:/)
})
