;(function () {
  const input = document.getElementById("ai-search-input")
  const btn = document.getElementById("ai-search-btn")
  const status = document.getElementById("ai-search-status")
  const results = document.getElementById("ai-search-results")
  const answer = document.getElementById("ai-search-answer")
  const sources = document.getElementById("ai-search-sources")
  if (!input || !btn || !status || !results || !answer || !sources) return

  const workerUrl = input.dataset.worker || "https://doge-wiki-search.YOUR_SUBDOMAIN.workers.dev"

  let currentFilters = {
    tags: [],
    time: "all",
  }
  let currentSort = "relevance"
  let currentQuery = ""

  // 搜索建议数据（从 wiki-index-light.json 加载）
  let suggestionsData = []

  // 加载搜索建议数据（部署生成在站点根 /Quart/wiki-index-light.json，含 reference_count）
  async function loadSuggestionsData() {
    // 兼容不同基路径：优先站点根，回退旧路径
    const candidates = [
      "/Quart/wiki-index-light.json",
      "/wiki-index-light.json",
      "/worker/wiki-index-light.json",
    ]
    for (const url of candidates) {
      try {
        const response = await fetch(url)
        if (!response.ok) continue
        suggestionsData = await response.json()
        if (Array.isArray(suggestionsData) && suggestionsData.length) return
      } catch (error) {
        // 尝试下一个候选路径
      }
    }
    console.error("加载搜索建议数据失败：所有候选路径均不可用")
  }

  // 获取搜索建议
  function getSuggestions(query) {
    if (!query || query.length < 2) return []

    const q = query.toLowerCase()
    return suggestionsData
      .filter((entry) => entry.name.toLowerCase().includes(q))
      .slice(0, 5)
      .map((entry) => ({
        name: entry.name,
        category: entry.category,
        icon: getCategoryIcon(entry.category),
      }))
  }

  // 渲染搜索建议
  function renderSuggestions(suggestions) {
    const container = document.querySelector(".search-suggestions")
    const list = container.querySelector(".suggestions-list")

    if (suggestions.length === 0) {
      container.style.display = "none"
      return
    }

    list.innerHTML = suggestions
      .map(
        (s) => `
      <div class="suggestion-item" data-name="${s.name}">
        <span class="suggestion-icon">${s.icon}</span>
        <div class="suggestion-content">
          <div class="suggestion-name">${s.name}</div>
          <div class="suggestion-category">${s.category}</div>
        </div>
      </div>
    `,
      )
      .join("")

    container.style.display = "block"

    // 绑定点击事件
    list.querySelectorAll(".suggestion-item").forEach((item) => {
      item.addEventListener("click", () => {
        const name = item.dataset.name
        input.value = name
        container.style.display = "none"
        doSearch()
      })
    })
  }

  // 初始化搜索建议
  function initSuggestions() {
    const container = document.querySelector(".search-suggestions")

    let debounceTimer = null

    input.addEventListener("input", () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        const query = input.value.trim()
        const suggestions = getSuggestions(query)
        renderSuggestions(suggestions)
      }, 300)
    })

    // 点击外部关闭建议
    document.addEventListener("click", (e) => {
      if (!container.contains(e.target) && e.target !== input) {
        container.style.display = "none"
      }
    })
  }

  // 线条图标集替代 emoji：跨平台渲染一致（emoji 在不同系统/字体下样式差异很大），
  // 全部用 rect/circle/line/polygon 等基础图元绘制，避免手写曲线路径出错
  const ICON_PATHS = {
    building:
      '<rect x="5" y="3" width="14" height="18" rx="1"/><line x1="9" y1="8" x2="9" y2="8.01"/><line x1="15" y1="8" x2="15" y2="8.01"/><line x1="9" y1="12" x2="9" y2="12.01"/><line x1="15" y1="12" x2="15" y2="12.01"/><line x1="9" y1="16" x2="9" y2="16.01"/><line x1="15" y1="16" x2="15" y2="16.01"/>',
    briefcase:
      '<rect x="3" y="7" width="18" height="13" rx="2"/><rect x="8" y="3" width="8" height="4" rx="1"/><line x1="3" y1="13" x2="21" y2="13"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 20a8 8 0 0 1 16 0"/>',
    package:
      '<polygon points="12,3 21,8 21,16 12,21 3,16 3,8"/><polyline points="3,8 12,13 21,8"/><line x1="12" y1="13" x2="12" y2="21"/>',
    chip: '<rect x="6" y="6" width="12" height="12" rx="1"/><line x1="9" y1="2" x2="9" y2="6"/><line x1="15" y1="2" x2="15" y2="6"/><line x1="9" y1="18" x2="9" y2="22"/><line x1="15" y1="18" x2="15" y2="22"/><line x1="2" y1="9" x2="6" y2="9"/><line x1="2" y1="15" x2="6" y2="15"/><line x1="18" y1="9" x2="22" y2="9"/><line x1="18" y1="15" x2="22" y2="15"/>',
    sliders:
      '<line x1="4" y1="6" x2="20" y2="6"/><circle cx="9" cy="6" r="2"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="7" cy="18" r="2"/>',
    calendar:
      '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    document:
      '<rect x="5" y="2" width="14" height="20" rx="1"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="13" y2="15"/>',
    trending: '<polyline points="3,17 9,11 13,15 21,7"/><polyline points="15,7 21,7 21,13"/>',
    bot: '<rect x="5" y="9" width="14" height="10" rx="2"/><circle cx="9" cy="14" r="1.5"/><circle cx="15" cy="14" r="1.5"/><line x1="12" y1="9" x2="12" y2="5"/><circle cx="12" cy="3" r="1.5"/>',
    spark:
      '<circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/>',
    bookmark: '<polygon points="6,3 18,3 18,21 12,17 6,21"/>',
    newspaper:
      '<rect x="3" y="5" width="18" height="14" rx="1"/><line x1="7" y1="9" x2="11" y2="9"/><line x1="7" y1="13" x2="11" y2="13"/><line x1="14" y1="9" x2="17" y2="9"/><line x1="14" y1="13" x2="17" y2="13"/><line x1="14" y1="16" x2="17" y2="16"/><line x1="7" y1="16" x2="11" y2="16"/>',
    layers:
      '<rect x="3" y="3" width="12" height="12" rx="1"/><rect x="9" y="9" width="12" height="12" rx="1"/>',
    file: '<rect x="5" y="3" width="14" height="18" rx="1"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/>',
  }

  const CATEGORY_ICONS = {
    companies: "building",
    organizations: "building",
    business: "briefcase",
    people: "user",
    projects: "package",
    technologies: "chip",
    technical: "chip",
    tools: "sliders",
    events: "calendar",
    policies: "document",
    policy: "document",
    markets: "trending",
    trend: "trending",
    "ai-agents": "bot",
    concepts: "spark",
    concept: "spark",
    entity: "bookmark",
    source: "newspaper",
    sources: "newspaper",
    synthesis: "layers",
  }

  function svgIcon(name) {
    const inner = ICON_PATHS[name] || ICON_PATHS.file
    return `<svg class="cat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`
  }

  function getCategoryIcon(category) {
    return svgIcon(CATEGORY_ICONS[category] || "file")
  }

  function simpleMarkdown(text) {
    if (!text) return ""
    let html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>")
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>")
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>")
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>")
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>")
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>")
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>")
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
    html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>")
    html = html.replace(/\n\n/g, "</p><p>")
    html = "<p>" + html + "</p>"
    html = html.replace(/<p>\s*<\/p>/g, "")
    html = html.replace(/<p><\/p>/g, "")
    return html
  }

  function escapeHtml(text) {
    if (!text) return ""
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;")
  }

  function renderSourceCards(sourceList) {
    if (!sourceList || !sourceList.length) return ""
    return `
      <h3>📚 参考来源 (${sourceList.length})</h3>
      <div class="source-card-list">
        ${sourceList
          .map(
            (s) => `
          <div class="source-card">
            <div class="source-card-header">
              <span class="source-card-icon">${getCategoryIcon(s.category)}</span>
              <span class="source-card-name">${escapeHtml(s.name)}</span>
              <span class="source-card-category">${escapeHtml(s.category)}</span>
            </div>
            <div class="source-card-meta">
              <span class="source-card-date">${escapeHtml(s.last_updated)}</span>
              ${
                s.tags && s.tags.length > 0
                  ? `
                <span class="source-card-tags">
                  ${s.tags
                    .slice(0, 3)
                    .map((tag) => `#${escapeHtml(tag)}`)
                    .join(" ")}
                </span>
              `
                  : ""
              }
            </div>
            <div class="source-card-summary">${escapeHtml(s.summary)}</div>
          </div>
        `,
          )
          .join("")}
      </div>
    `
  }

  function renderEmptyState() {
    let picks = []
    if (suggestionsData && suggestionsData.length) {
      picks = [...suggestionsData]
        .sort((a, b) => (b.reference_count || 0) - (a.reference_count || 0))
        .slice(0, 8)
        .map((e) => e.name)
    }
    if (!picks.length) return ""
    const chips = picks
      .map(
        (n) =>
          `<button class="empty-suggestion" data-q="${escapeHtml(n)}" style="margin:4px;padding:6px 12px;border:1px solid var(--lightgray,#ccc);border-radius:16px;background:transparent;color:inherit;cursor:pointer;font-size:0.85em;">${escapeHtml(n)}</button>`,
      )
      .join("")
    return `<div class="ai-empty-state" style="padding:8px 0;"><p style="opacity:0.7;margin-bottom:8px;">换个说法，或试试这些热门主题：</p><div>${chips}</div></div>`
  }

  function bindEmptySuggestions() {
    document.querySelectorAll(".empty-suggestion").forEach((b) => {
      b.addEventListener("click", () => {
        input.value = b.dataset.q
        doSearch()
      })
    })
  }

  async function doSearch() {
    const query = input.value.trim()
    if (!query) return
    if (query.length < 2) {
      status.textContent = "请至少输入2个字"
      return
    }

    currentQuery = query
    btn.disabled = true
    status.textContent = "正在检索知识库..."
    results.style.display = "none"
    answer.innerHTML = ""
    sources.innerHTML = ""

    try {
      const resp = await fetch(`${workerUrl}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          filters: currentFilters,
          sort: currentSort,
        }),
      })
      const data = await resp.json()

      if (data.error) {
        status.textContent = ""
        answer.innerHTML = `<div class="ai-error">${data.error}</div>`
        results.style.display = "grid"
        btn.disabled = false
        return
      }

      status.textContent = ""

      answer.innerHTML = simpleMarkdown(data.answer)
      if (data.sources && data.sources.length > 0) {
        sources.innerHTML = renderSourceCards(data.sources)
      } else {
        sources.innerHTML = renderEmptyState()
        bindEmptySuggestions()
      }
      results.style.display = "grid"
    } catch (err) {
      status.textContent = ""
      answer.innerHTML = `<div class="ai-error">请求失败: ${err.message}</div>`
      results.style.display = "grid"
    } finally {
      btn.disabled = false
    }
  }

  function initFilters() {
    document.querySelectorAll(".filter-tag").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tag = btn.dataset.tag

        if (tag === "all") {
          currentFilters.tags = []
          document.querySelectorAll(".filter-tag").forEach((b) => b.classList.remove("active"))
          btn.classList.add("active")
        } else {
          document.querySelector('.filter-tag[data-tag="all"]').classList.remove("active")
          btn.classList.toggle("active")

          if (btn.classList.contains("active")) {
            currentFilters.tags.push(tag)
          } else {
            currentFilters.tags = currentFilters.tags.filter((t) => t !== tag)
          }
        }

        if (currentQuery) {
          doSearch()
        }
      })
    })

    document.querySelectorAll(".filter-time-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentFilters.time = btn.dataset.time
        document.querySelectorAll(".filter-time-btn").forEach((b) => b.classList.remove("active"))
        btn.classList.add("active")

        if (currentQuery) {
          doSearch()
        }
      })
    })

    document.querySelectorAll(".filter-sort-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentSort = btn.dataset.sort
        document.querySelectorAll(".filter-sort-btn").forEach((b) => b.classList.remove("active"))
        btn.classList.add("active")

        if (currentQuery) {
          doSearch()
        }
      })
    })
  }

  const HISTORY_KEY = "wiki-search-history"
  const MAX_HISTORY = 10

  function getSearchHistory() {
    const history = localStorage.getItem(HISTORY_KEY)
    return history ? JSON.parse(history) : []
  }

  function addSearchHistory(query) {
    const history = getSearchHistory()
    const newHistory = [
      { query, timestamp: Date.now() },
      ...history.filter((h) => h.query !== query),
    ].slice(0, MAX_HISTORY)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(newHistory))
    renderHistory()
  }

  function clearSearchHistory() {
    localStorage.removeItem(HISTORY_KEY)
    renderHistory()
  }

  function formatTime(timestamp) {
    const now = Date.now()
    const diff = now - timestamp

    if (diff < 60 * 60 * 1000) {
      const minutes = Math.floor(diff / (60 * 1000))
      return `${minutes}分钟前`
    }

    if (diff < 24 * 60 * 60 * 1000) {
      const hours = Math.floor(diff / (60 * 60 * 1000))
      return `${hours}小时前`
    }

    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days}天前`
  }

  function renderHistory() {
    const container = document.querySelector(".search-history")
    if (!container) return

    const history = getSearchHistory()
    const list = container.querySelector(".history-list")

    if (history.length === 0) {
      container.style.display = "none"
      return
    }

    container.style.display = "block"

    // 首页只展示最近 3 条，避免搜索历史占满首屏、压住内容入口
    list.innerHTML = history
      .slice(0, 3)
      .map((item) => {
        const time = formatTime(item.timestamp)
        return `
        <div class="history-item" data-query="${item.query}">
          <span class="history-icon">🔍</span>
          <div class="history-content">
            <div class="history-query">${item.query}</div>
            <div class="history-time">${time}</div>
          </div>
        </div>
      `
      })
      .join("")

    list.querySelectorAll(".history-item").forEach((item) => {
      item.addEventListener("click", () => {
        const query = item.dataset.query
        input.value = query
        doSearch()
      })
    })
  }

  function initHistory() {
    const clearBtn = document.querySelector(".history-clear")
    if (clearBtn) {
      clearBtn.addEventListener("click", clearSearchHistory)
    }
    renderHistory()
  }

  const _originalDoSearch = doSearch
  doSearch = async function () {
    const query = input.value.trim()
    if (!query || query.length < 2) return
    await _originalDoSearch()
    if (!answer.querySelector(".ai-error")) {
      addSearchHistory(query)
    }
  }

  btn.addEventListener("click", doSearch)
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch()
  })

  initFilters()
  loadSuggestionsData()
  initSuggestions()
  initHistory()
})()
