import assert from "node:assert/strict"
import test from "node:test"
import render from "preact-render-to-string"

import HeadConstructor from "../quartz/components/Head.tsx"

function renderHead() {
  const Head = HeadConstructor()
  const cfg = {
    pageTitle: "Wiki",
    pageTitleSuffix: "",
    locale: "zh-CN",
    baseUrl: "zrj-h.github.io/Quart",
    theme: { cdnCaching: false, fontOrigin: "local" },
  }
  const fileData = {
    slug: "index",
    frontmatter: { title: "Home" },
    description: "Home",
  }
  const externalResources = {
    css: [],
    js: [
      {
        loadTime: "beforeDOMReady",
        contentType: "inline",
        script: 'const fetchData = fetch("./static/contentIndex.json").then(data => data.json())',
      },
    ],
    additionalHead: [],
  }
  const ctx = { cfg: { plugins: { emitters: [] } } }
  return render(Head({ cfg, fileData, externalResources, ctx }))
}

test("static pages emit a script-safe CSP with hashes for required inline bootstrap code", () => {
  const html = renderHead()

  assert.match(html, /http-equiv="Content-Security-Policy"/)
  assert.match(html, /sha256-[A-Za-z0-9+/]+=*/)
  assert.match(html, /object-src 'none'/)
  assert.doesNotMatch(html, /script-src[^;]*(?:unsafe-inline|unsafe-eval)/)
})
