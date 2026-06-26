// DeepSeek 调用模块：从 worker/index.js 提取，SSE 适配 Express res

const DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions";

// 卡片摘要
function cardSnippet(content, name, limit = 150) {
  if (!content) return "";
  const lines = content.split("\n");
  if (lines.length && lines[0].trim() === (name || "").trim()) {
    lines.shift();
  }
  while (lines.length && !lines[0].trim()) lines.shift();
  return lines
    .join("\n")
    .replace(/\n{2,}/g, "\n")
    .trim()
    .slice(0, limit);
}

// 构建 Prompt
function buildPrompt(query, results, fullData, queryType) {
  const today = new Date().toJSON().slice(0, 10);
  const sources = results
    .map((r, i) => {
      const data = fullData[r.id];
      const body = data?.content || data?.summary || r.summary || "";
      return `[${i + 1}] ${r.name} (${r.category || r.type})\n正文: ${body}\n标签: ${(data?.tags || r.tags || []).join(", ")}\n更新时间: ${r.last_updated || "?"}`;
    })
    .join("\n\n");

  const queryTypeGuide = {
    comparison: "使用对比分析：表格对比关键维度 → 总结建议",
    timeline: "使用时间线：按时间顺序列出关键事件 → 趋势分析",
    overview: "使用概述结构：定义 → 核心要点 → 应用场景",
    comprehensive: "根据内容选择最合适结构",
  };

  return `你是知识库研究助手。今天是 ${today}。

## 回答原则

1. **核心回答**：直接回答用户问题，标注来源 [1][2]
2. **关联分析**：主动指出相关实体/概念之间的联系
   - 例如："A 和 B 都属于 X 领域"
   - 例如："这个概念在 Y 场景也有应用"
3. **背景补充**：对关键术语补充 1-2 句背景，帮助理解
4. **跨领域洞察**：如果发现不同领域间的共性或模式，简要点出
5. **时间维度**：如果有时间线信息，指出趋势或演变

## 回答结构

- 开头：直接回答 + 核心要点
- 中间：分点展开 + 关联分析
- 结尾：如有价值，补充洞察或延伸思考

## 查询类型

${queryTypeGuide[queryType] || queryTypeGuide.comprehensive}

## 注意事项

- 标注来源编号 [1][2]，便于追溯
- 使用 Markdown 格式
- 如果资料中确实没有相关信息，诚实说明并尝试给出相关方向
- 不要过度发散到无来源支撑的内容

## 可用来源

${sources}

## 用户查询

${query}`;
}

// 流式调用 DeepSeek（Express 版，用 res.write() 替代 TransformStream）
async function streamDeepSeek(prompt, apiKey, res) {
  try {
    const resp = await fetch(DEEPSEEK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.5,
        max_tokens: 2500,
        stream: true,
      }),
    });

    if (!resp.ok) {
      const err = await resp.text();
      res.write(
        `data: ${JSON.stringify({ type: "error", message: `DeepSeek ${resp.status}` })}\n\n`
      );
      res.end();
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (data === "[DONE]") {
          res.write(`data: ${JSON.stringify({ type: "done" })}\n\n`);
          res.end();
          return;
        }
        try {
          const delta = JSON.parse(data).choices?.[0]?.delta?.content;
          if (delta) {
            res.write(
              `data: ${JSON.stringify({ type: "chunk", text: delta })}\n\n`
            );
          }
        } catch {
          // 忽略 parse 失败（部分 chunk）
        }
      }
    }
    res.write(`data: ${JSON.stringify({ type: "done" })}\n\n`);
    res.end();
  } catch (err) {
    try {
      res.write(
        `data: ${JSON.stringify({ type: "error", message: err.message })}\n\n`
      );
    } catch {
      // 连接可能已关闭
    }
    res.end();
  }
}

// 非流式调用（用于爬虫摘要等场景）
async function callDeepSeek(prompt, apiKey) {
  const resp = await fetch(DEEPSEEK_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "deepseek-chat",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.5,
      max_tokens: 2500,
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`DeepSeek API error ${resp.status}: ${err}`);
  }

  const data = await resp.json();
  return data.choices[0].message.content;
}

module.exports = {
  cardSnippet,
  buildPrompt,
  streamDeepSeek,
  callDeepSeek,
};
