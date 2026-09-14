import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"
import vm from "node:vm"

class FakeElement {
  constructor() {
    this.dataset = {}
    this.listeners = {}
    this.style = {}
    this.value = ""
    this.disabled = false
    this.innerHTML = ""
  }

  addEventListener(type, listener) {
    this.listeners[type] = listener
  }

  contains() {
    return false
  }

  closest() {
    return null
  }

  hasAttribute() {
    return false
  }

  querySelector(selector) {
    return this.children?.[selector] || null
  }

  querySelectorAll() {
    return []
  }
}

test("AI search treats suggestion, history, and transport error text as text", async () => {
  const sourceUrl = new URL("../quartz/components/scripts/search-ai.inline.js", import.meta.url)
  const source = (await readFile(sourceUrl, "utf8")).replace("  initModal()\n", "")

  const input = new FakeElement()
  input.dataset.worker = "https://worker.example"
  const button = new FakeElement()
  const status = new FakeElement()
  const results = new FakeElement()
  const answer = new FakeElement()
  const sources = new FakeElement()
  const suggestionList = new FakeElement()
  const suggestions = new FakeElement()
  suggestions.children = { ".suggestions-list": suggestionList }
  const historyList = new FakeElement()
  const history = new FakeElement()
  history.children = { ".history-list": historyList }

  const byId = {
    "ai-search-input": input,
    "ai-search-btn": button,
    "ai-search-status": status,
    "ai-search-results": results,
    "ai-search-answer": answer,
    "ai-search-sources": sources,
  }
  const localData = new Map([
    [
      "wiki-search-history",
      JSON.stringify([{ query: '"><img src=x onerror=alert(1)>', timestamp: Date.now() }]),
    ],
  ])
  const context = vm.createContext({
    AbortController,
    Element: FakeElement,
    TextDecoder,
    cancelAnimationFrame() {},
    clearTimeout() {},
    console,
    document: {
      addEventListener() {},
      getElementById(id) {
        return byId[id] || null
      },
      querySelector(selector) {
        if (selector === ".search-suggestions") return suggestions
        if (selector === ".search-history") return history
        return null
      },
      querySelectorAll() {
        return []
      },
    },
    fetch: async () => ({
      ok: true,
      async json() {
        return [{ name: '"><img src=x onerror=alert(1)>', category: "<svg onload=alert(1)>" }]
      },
    }),
    localStorage: {
      getItem(key) {
        return localData.get(key) || null
      },
      removeItem(key) {
        localData.delete(key)
      },
      setItem(key, value) {
        localData.set(key, value)
      },
    },
    navigator: { userAgent: "test" },
    requestAnimationFrame(callback) {
      callback()
      return 1
    },
    setTimeout(callback) {
      callback()
      return 1
    },
    window: {
      location: {
        origin: "https://zrj-h.github.io",
        pathname: "/Quart/",
      },
    },
  })

  vm.runInContext(source, context)
  await new Promise((resolve) => setImmediate(resolve))

  input.value = "im"
  input.listeners.input()
  assert.doesNotMatch(suggestionList.innerHTML, /<img|<svg\s+onload/i)
  assert.match(suggestionList.innerHTML, /&lt;img/)
  assert.doesNotMatch(historyList.innerHTML, /<img/i)
  assert.match(historyList.innerHTML, /&lt;img/)

  context.fetch = async () => {
    throw new Error("<img src=x onerror=alert(1)>")
  }
  input.value = "AI"
  await button.listeners.click()
  assert.doesNotMatch(answer.innerHTML, /<img/i)
  assert.match(answer.innerHTML, /&lt;img/)
})
