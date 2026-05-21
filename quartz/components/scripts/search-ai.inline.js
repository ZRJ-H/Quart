(function () {
  const input = document.getElementById("ai-search-input")
  const btn = document.getElementById("ai-search-btn")
  const status = document.getElementById("ai-search-status")
  const result = document.getElementById("ai-search-result")
  if (!input || !btn || !status || !result) return

  const workerUrl = input.dataset.worker || "https://doge-wiki-search.YOUR_SUBDOMAIN.workers.dev"

  function simpleMarkdown(text) {
    if (!text) return ""
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
    // headers
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>")
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>")
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // bold / italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>")
    // inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>")
    // bullet lists
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>")
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
    // numbered lists
    html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>")
    // paragraphs (double newline)
    html = html.replace(/\n\n/g, "</p><p>")
    html = "<p>" + html + "</p>"
    // clean empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, "")
    html = html.replace(/<p><\/p>/g, "")
    return html
  }

  function renderSources(sources) {
    if (!sources || !sources.length) return ""
    const tags = sources.map((s) => {
      const label = s.type === "entity"
        ? "实体"
        : s.type === "concept"
        ? "概念"
        : s.type === "source"
        ? "来源"
        : s.type
      return `<span title="${(s.tags || []).join(", ")}">${label}: ${s.name}</span>`
    }).join("")
    return `<div class="ai-sources"><strong>参考来源:</strong> ${tags}</div>`
  }

  async function doSearch() {
    const query = input.value.trim()
    if (!query) return
    if (query.length < 2) {
      status.textContent = "请至少输入2个字"
      return
    }

    btn.disabled = true
    status.textContent = "正在检索知识库..."
    result.innerHTML = ""

    try {
      const resp = await fetch(`${workerUrl}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      })
      const data = await resp.json()

      if (data.error) {
        status.textContent = ""
        result.innerHTML = `<div class="ai-error">${data.error}</div>`
        btn.disabled = false
        return
      }

      status.textContent = data.sources?.length
        ? `从 ${data.sources.length} 个相关页面生成回答`
        : ""

      result.innerHTML = simpleMarkdown(data.answer) + renderSources(data.sources)
    } catch (err) {
      status.textContent = ""
      result.innerHTML = `<div class="ai-error">请求失败: ${err.message}</div>`
    } finally {
      btn.disabled = false
    }
  }

  btn.addEventListener("click", doSearch)
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch()
  })
})()
