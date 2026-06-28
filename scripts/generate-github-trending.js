import fs from "fs"
import path from "path"

const today = new Date().toISOString().slice(0, 10)
const rawPath = process.env.TRENDING_JSON || "/tmp/trending.json"
const contentRoot = process.env.CONTENT_ROOT || "content"
const trendingDir = path.join(contentRoot, "GitHub Trending")
const archiveDir = path.join(contentRoot, "GitHub 项目档案")

const rawData = JSON.parse(fs.readFileSync(rawPath, "utf-8"))

function readPreviousStars(key) {
  const file = path.join(archiveDir, `${key}.md`)
  if (!fs.existsSync(file)) return { file, stars: 0, exists: false }

  const content = fs.readFileSync(file, "utf-8")
  const rows = content.match(/\| \d{4}-\d{2}-\d{2} \|[^\n]+/g) || []
  if (!rows.length) return { file, stars: 0, exists: true }

  const cells = rows[rows.length - 1]
    .split("|")
    .map((cell) => cell.trim())
    .filter(Boolean)
  const stars = Number.parseInt((cells[2] || "0").replace(/,/g, ""), 10)
  return { file, stars: Number.isFinite(stars) ? stars : 0, exists: true }
}

function classify(item, previousStars, hasArchive) {
  const delta = hasArchive ? item.stars - previousStars : item.stars
  if (!hasArchive) return { type: "新晋", delta }
  if (delta >= 500) return { type: "爆火", delta }
  if (delta >= 200) return { type: "跃升", delta }
  if (delta < 0) return { type: "回落", delta }
  return { type: "常驻", delta }
}

const items = rawData.map((item) => {
  const [owner, repo] = item.name.split("/")
  const key = `${owner}-${repo}`.replace(/[^\w.-]/g, "-")
  const archive = readPreviousStars(key)
  return {
    ...item,
    owner,
    repo,
    key,
    archive,
    ...classify(item, archive.stars, archive.exists),
  }
})

const groups = {
  新晋: items.filter((item) => item.type === "新晋"),
  爆火: items.filter((item) => item.type === "爆火"),
  跃升: items.filter((item) => item.type === "跃升"),
  回落: items.filter((item) => item.type === "回落"),
  常驻: items.filter((item) => item.type === "常驻"),
}

function formatDelta(delta) {
  return delta >= 0 ? `+${delta.toLocaleString()}` : delta.toLocaleString()
}

function fallbackAnalysis() {
  const top = [...items].sort((a, b) => b.delta - a.delta)[0]
  const hot = [...groups.爆火, ...groups.跃升, ...groups.新晋].slice(0, 5)
  return `## 深度解读

### 本日之星：${top ? top.name : "暂无"}

${top ? `${top.name} 当前总星数 ${top.stars.toLocaleString()}，本次记录增量 ${formatDelta(top.delta)}。${top.description || ""}` : "今日没有拿到可分析项目。"}

### 趋势脉动

${hot.length ? hot.map((item) => `- **${item.name}**：${item.type}，${item.language || "-"}，${formatDelta(item.delta)}⭐。`).join("\n") : "- 今日榜单变化较平缓。"}

> 未配置 AI Key，本段为规则生成。`
}

async function aiAnalysis() {
  const deepseekKey = process.env.DEEPSEEK_API_KEY
  const goKey = process.env.GO_API_KEY
  if (!deepseekKey && !goKey) return fallbackAnalysis()

  const table = items
    .map(
      (item) =>
        `| ${item.type} | #${item.rank} | ${item.name} | ${item.stars} | ${formatDelta(item.delta)} | ${item.language || "-"} | ${(item.description || "").slice(0, 100)} |`,
    )
    .join("\n")

  const prompt = `请基于今天 GitHub Trending 数据写一段中文 Markdown 分析，不要泛泛而谈，要引用项目名和数字。

| 类型 | 排名 | 项目 | 总星 | 增量 | 语言 | 描述 |
|---|---:|---|---:|---:|---|---|
${table}

输出结构：
## 深度解读
### 本日之星
### 趋势脉动
### 项目生态关联`

  const request =
    deepseekKey
      ? {
          url: "https://api.deepseek.com/chat/completions",
          headers: { Authorization: `Bearer ${deepseekKey}` },
          body: { model: "deepseek-chat", messages: [{ role: "user", content: prompt }], max_tokens: 1200 },
        }
      : {
          url: "https://opencode.ai/zen/go/v1/chat/completions",
          headers: { Authorization: `Bearer ${goKey}` },
          body: { model: "deepseek-v4-pro", messages: [{ role: "user", content: prompt }], max_tokens: 1200 },
        }

  try {
    const response = await fetch(request.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...request.headers },
      body: JSON.stringify(request.body),
    })
    if (!response.ok) throw new Error(`AI HTTP ${response.status}: ${(await response.text()).slice(0, 200)}`)
    const data = await response.json()
    return data.choices?.[0]?.message?.content || fallbackAnalysis()
  } catch (error) {
    console.error(`AI analysis failed: ${error.message}`)
    return fallbackAnalysis()
  }
}

function section(title, list) {
  if (!list.length) return ""
  return `\n---\n\n## ${title}\n\n${list
    .map(
      (item) => `### [${item.owner}/${item.repo}](${item.url})

> ${item.description || "暂无描述"}

- **排名**: #${item.rank}
- **语言**: ${item.language || "-"}
- **总星数**: ${item.stars.toLocaleString()}
- **本次增量**: ${formatDelta(item.delta)}⭐
- **项目档案**: [[${item.key}]]
`,
    )
    .join("\n")}`
}

fs.mkdirSync(trendingDir, { recursive: true })
fs.mkdirSync(archiveDir, { recursive: true })

const analysis = await aiAnalysis()
const top5 = [...items].sort((a, b) => b.delta - a.delta).slice(0, 5)

const markdown = `# GitHub Trending - ${today}

## 今日增量

- **新晋项目**: ${groups.新晋.length} 个
- **爆火项目**: ${groups.爆火.length} 个
- **跃升项目**: ${groups.跃升.length} 个
- **回落项目**: ${groups.回落.length} 个
- **常驻项目**: ${groups.常驻.length} 个

${section("新晋热门", groups.新晋)}
${section("今日爆火", groups.爆火)}
${section("快速上升", groups.跃升)}
${section("热度回落", groups.回落)}

---

## 今日增长 TOP 5

| 排名 | 项目 | 增量 | 类型 |
|---:|---|---:|---|
${top5.map((item, index) => `| ${index + 1} | [${item.name}](${item.url}) | ${formatDelta(item.delta)}⭐ | ${item.type} |`).join("\n")}

---

${analysis}

---

标签: #github #trending #opensource #${today}

自动生成于 ${new Date().toISOString()}
`

fs.writeFileSync(path.join(trendingDir, `${today}.md`), markdown)

for (const item of items) {
  const file = path.join(archiveDir, `${item.key}.md`)
  const row = `| ${today} | #${item.rank} | ${item.stars.toLocaleString()} | ${formatDelta(item.delta)}⭐ | ${item.type} |`

  if (!fs.existsSync(file)) {
    fs.writeFileSync(
      file,
      `---
first_seen: ${today}
last_seen: ${today}
language: ${item.language || ""}
tags: [github, trending]
---

# ${item.owner}/${item.repo}

> ${item.description || "暂无描述"}

## 基本信息

- **GitHub**: ${item.url}
- **语言**: ${item.language || "-"}
- **总星数**: ${item.stars.toLocaleString()}

## 历史趋势

| 日期 | 排名 | 星数 | 增量 | 类型 |
|---|---:|---:|---:|---|
${row}
`,
    )
  } else {
    let content = fs.readFileSync(file, "utf-8")
    content = content.replace(/last_seen:.*/, `last_seen: ${today}`)
    if (!content.includes(row)) {
      const marker = "\n## 历史趋势"
      const tableIndex = content.indexOf(marker)
      if (tableIndex >= 0) {
        const nextSection = content.indexOf("\n## ", tableIndex + marker.length)
        const insertAt = nextSection >= 0 ? nextSection : content.length
        content = `${content.slice(0, insertAt).trimEnd()}\n${row}\n${content.slice(insertAt)}`
      } else {
        content += `\n\n## 历史趋势\n\n| 日期 | 排名 | 星数 | 增量 | 类型 |\n|---|---:|---:|---:|---|\n${row}\n`
      }
    }
    fs.writeFileSync(file, content)
  }
}

console.log(`Generated GitHub Trending note for ${today}: ${items.length} projects`)
