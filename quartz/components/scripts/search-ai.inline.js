(function () {
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
    time: 'all'
  }
  let currentSort = 'relevance'
  let currentQuery = ''

  // 搜索建议数据（从 wiki-index-light.json 加载）
  let suggestionsData = []

  // 加载搜索建议数据
  async function loadSuggestionsData() {
    try {
      const response = await fetch('/wiki-index-light.json')
      suggestionsData = await response.json()
    } catch (error) {
      console.error('加载搜索建议数据失败:', error)
    }
  }

  // 获取搜索建议
  function getSuggestions(query) {
    if (!query || query.length < 2) return []

    const q = query.toLowerCase()
    return suggestionsData
      .filter(entry => entry.name.toLowerCase().includes(q))
      .slice(0, 5)
      .map(entry => ({
        name: entry.name,
        category: entry.category,
        icon: getCategoryIcon(entry.category)
      }))
  }

  // 渲染搜索建议
  function renderSuggestions(suggestions) {
    const container = document.querySelector('.search-suggestions')
    const list = container.querySelector('.suggestions-list')

    if (suggestions.length === 0) {
      container.style.display = 'none'
      return
    }

    list.innerHTML = suggestions.map(s => `
      <div class="suggestion-item" data-name="${s.name}">
        <span class="suggestion-icon">${s.icon}</span>
        <div class="suggestion-content">
          <div class="suggestion-name">${s.name}</div>
          <div class="suggestion-category">${s.category}</div>
        </div>
      </div>
    `).join('')

    container.style.display = 'block'

    // 绑定点击事件
    list.querySelectorAll('.suggestion-item').forEach(item => {
      item.addEventListener('click', () => {
        const name = item.dataset.name
        const input = document.querySelector('.ai-search-input')
        input.value = name
        container.style.display = 'none'
        doSearch()
      })
    })
  }

  // 初始化搜索建议
  function initSuggestions() {
    const container = document.querySelector('.search-suggestions')

    let debounceTimer = null

    input.addEventListener('input', () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        const query = input.value.trim()
        const suggestions = getSuggestions(query)
        renderSuggestions(suggestions)
      }, 300)
    })

    // 点击外部关闭建议
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target) && e.target !== input) {
        container.style.display = 'none'
      }
    })
  }

  const CATEGORY_ICONS = {
    'companies': '🏢',
    'people': '👤',
    'projects': '📦',
    'technologies': '⚙️',
    'events': '📅',
    'policies': '📜',
    'tools': '🔧',
    'markets': '📈',
    'ai-agents': '🤖'
  }

  function getCategoryIcon(category) {
    return CATEGORY_ICONS[category] || '📄'
  }

  function simpleMarkdown(text) {
    if (!text) return ""
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
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

  function renderSourceCards(sourceList) {
    if (!sourceList || !sourceList.length) return ""
    return `
      <h3>📚 参考来源 (${sourceList.length})</h3>
      <div class="source-card-list">
        ${sourceList.map(s => `
          <div class="source-card">
            <div class="source-card-header">
              <span class="source-card-icon">${CATEGORY_ICONS[s.category] || '📄'}</span>
              <span class="source-card-name">${s.name}</span>
              <span class="source-card-category">${s.category || ''}</span>
            </div>
            <div class="source-card-meta">
              <span class="source-card-date">${s.last_updated || ''}</span>
              ${(s.tags && s.tags.length > 0) ? `
                <span class="source-card-tags">
                  ${s.tags.slice(0, 3).map(tag => `#${tag}`).join(' ')}
                </span>
              ` : ''}
            </div>
            <div class="source-card-summary">${s.summary || ''}</div>
          </div>
        `).join('')}
      </div>
    `
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
          sort: currentSort
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

      status.textContent = data.sources?.length
        ? `从 ${data.sources.length} 个相关页面生成回答`
        : ""

      answer.innerHTML = simpleMarkdown(data.answer)
      if (data.sources && data.sources.length > 0) {
        sources.innerHTML = renderSourceCards(data.sources)
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
    document.querySelectorAll('.filter-tag').forEach(btn => {
      btn.addEventListener('click', () => {
        const tag = btn.dataset.tag

        if (tag === 'all') {
          currentFilters.tags = []
          document.querySelectorAll('.filter-tag').forEach(b => b.classList.remove('active'))
          btn.classList.add('active')
        } else {
          document.querySelector('.filter-tag[data-tag="all"]').classList.remove('active')
          btn.classList.toggle('active')

          if (btn.classList.contains('active')) {
            currentFilters.tags.push(tag)
          } else {
            currentFilters.tags = currentFilters.tags.filter(t => t !== tag)
          }
        }

        if (currentQuery) {
          doSearch()
        }
      })
    })

    document.querySelectorAll('.filter-time-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentFilters.time = btn.dataset.time
        document.querySelectorAll('.filter-time-btn').forEach(b => b.classList.remove('active'))
        btn.classList.add('active')

        if (currentQuery) {
          doSearch()
        }
      })
    })

    document.querySelectorAll('.filter-sort-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentSort = btn.dataset.sort
        document.querySelectorAll('.filter-sort-btn').forEach(b => b.classList.remove('active'))
        btn.classList.add('active')

        if (currentQuery) {
          doSearch()
        }
      })
    })
  }

  btn.addEventListener("click", doSearch)
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch()
  })

  initFilters()
  loadSuggestionsData()
  initSuggestions()
})()
