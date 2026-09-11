function detectQueryType(query) {
  const value = String(query || "").toLowerCase()
  if ((value.includes("和") && value.includes("区别")) || value.includes("vs") || value.includes("对比")) {
    return "使用对比结构：关键维度对比，然后总结建议。"
  }
  if (value.includes("历史") || value.includes("发展") || value.includes("时间线")) {
    return "使用时间线结构：按时间列出事件，然后总结趋势。"
  }
  if (value.includes("是什么") || value.includes("介绍") || value.includes("概述")) {
    return "使用概述结构：定义、核心要点、应用场景。"
  }
  return "根据来源内容选择最清晰的回答结构。"
}

export function buildPrompt(query, results) {
  const today = new Date().toISOString().slice(0, 10)
  const sources = results
    .map((entry, index) => {
      return (
        "[" + (index + 1) + "] " + entry.name + " (" + (entry.category || entry.type || "未分类") + ")\n" +
        "正文: " + (entry.content || entry.summary || "") + "\n" +
        "标签: " + (Array.isArray(entry.tags) ? entry.tags.join(", ") : "") + "\n" +
        "更新时间: " + (entry.last_updated || "?")
      )
    })
    .join("\n\n")

  return [
    "你是知识库研究助手。今天是 " + today + "。",
    "",
    "只根据可用来源回答，直接给出核心结论，并用 [1][2] 标注来源。",
    "资料不足时必须明确说明，不要编造。使用简洁 Markdown。",
    detectQueryType(query),
    "",
    "## 可用来源",
    sources,
    "",
    "## 用户查询",
    String(query),
  ].join("\n")
}
