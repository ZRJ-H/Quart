// 爬虫：AI论文日报 — arXiv API + LLM 翻译摘要
//
// 用法: node arxiv-papers.js [outputDir]
// 输出: {outputDir}/AI论文日报/YYYY-MM-DD.md
// 需要: DEEPSEEK_API_KEY 环境变量

const https = require("https");
const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const DEEPSEEK_API_KEY =
  process.env.DEEPSEEK_API_KEY || "";

// arXiv API 查询
function arxivApi(query) {
  return new Promise((resolve, reject) => {
    const url = `http://export.arxiv.org/api/query?${query}`;
    https
      .get(url, { headers: { "User-Agent": "wiki-crawler/1.0" } }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      })
      .on("error", reject);
  });
}

// 简易解析 arXiv Atom 响应
function parseArxivXml(xml) {
  const entries = [];
  const entryRegex =
    /<entry>([\s\S]*?)<\/entry>/g;
  let match;

  while ((match = entryRegex.exec(xml)) !== null) {
    const entry = match[1];
    const idMatch = entry.match(/<id>(.*?)<\/id>/);
    const titleMatch = entry.match(
      /<title>(.*?)<\/title>/
    );
    const summaryMatch = entry.match(
      /<summary>(.*?)<\/summary>/
    );
    const publishedMatch = entry.match(
      /<published>(.*?)<\/published>/
    );
    const linkMatch = entry.match(
      /<link title="pdf" href="(.*?)"/
    );
    const catMatches = entry.match(
      /<category term="([^"]*?)"/g
    );

    if (!titleMatch) continue;

    const title = titleMatch[1]
      .replace(/\s+/g, " ")
      .trim();
    const summary = (summaryMatch?.[1] || "")
      .replace(/\s+/g, " ")
      .trim();
    const published = (publishedMatch?.[1] || "").slice(0, 10);
    const arxivId = idMatch
      ? idMatch[1].replace("http://arxiv.org/abs/", "").replace(/v\d+$/, "")
      : "";
    const pdfUrl = linkMatch?.[1] || `https://arxiv.org/pdf/${arxivId}`;
    const categories = catMatches
      ? catMatches.map((c) => c.match(/"([^"]+)/)[1])
      : [];

    entries.push({
      id: arxivId,
      title,
      summary,
      published,
      pdfUrl,
      categories,
      arxivUrl: `https://arxiv.org/abs/${arxivId}`,
    });
  }

  return entries;
}

// 调用 DeepSeek 翻译+摘要（非流式）
async function translateWithLLM(papers) {
  if (!DEEPSEEK_API_KEY) {
    console.warn(
      "[arXiv] No DEEPSEEK_API_KEY set, using original English titles"
    );
    return papers.map((p) => ({
      ...p,
      zhTitle: p.title,
      zhSummary: p.summary.slice(0, 200),
    }));
  }

  const prompt = `请将以下英文学术论文标题和摘要翻译为中文。每篇一行，格式：
**中文标题** — 一句话中文摘要（≤60字）

${papers
    .map(
      (p, i) => `
[${i + 1}]
标题: ${p.title}
摘要: ${p.summary.slice(0, 500)}
`
    )
    .join("\n")}

共 ${papers.length} 篇，请逐一翻译。`;

  console.log("[arXiv] Calling DeepSeek for translation...");

  try {
    const resp = await fetch(
      "https://api.deepseek.com/v1/chat/completions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
        },
        body: JSON.stringify({
          model: "deepseek-chat",
          messages: [{ role: "user", content: prompt }],
          temperature: 0.3,
          max_tokens: papers.length * 150,
        }),
      }
    );

    if (!resp.ok) {
      const err = await resp.text();
      console.error("[arXiv] DeepSeek error:", err);
      return papers.map((p) => ({
        ...p,
        zhTitle: p.title,
        zhSummary: p.summary.slice(0, 200),
      }));
    }

    const data = await resp.json();
    const translation = data.choices[0].message.content;

    // 解析翻译结果（每行格式：**中文标题** — 摘要）
    const lines = translation.split("\n").filter((l) => l.trim());
    papers.forEach((p, i) => {
      if (i < lines.length) {
        const line = lines[i].replace(/^\[\d+\]\s*/, "");
        const parts = line.split(/[—–-]/);
        if (parts.length >= 2) {
          p.zhTitle = parts[0].replace(/\*\*/g, "").trim();
          p.zhSummary = parts.slice(1).join("—").trim();
        } else {
          p.zhTitle = line;
          p.zhSummary = "";
        }
      } else {
        p.zhTitle = p.title;
        p.zhSummary = p.summary.slice(0, 200);
      }
    });

    return papers;
  } catch (err) {
    console.error("[arXiv] LLM translation error:", err.message);
    return papers.map((p) => ({
      ...p,
      zhTitle: p.title,
      zhSummary: p.summary.slice(0, 200),
    }));
  }
}

async function main() {
  const today = new Date();
  const dateStr = today.toISOString().slice(0, 10);

  // 查询昨天+今天的论文（时差原因）
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 2);
  const searchDate = yesterday.toISOString().slice(0, 10);

  console.log(`[arXiv] Searching papers since ${searchDate}...`);

  const query = [
    "search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.CV+OR+cat:cs.LG",
    "sortBy=submittedDate",
    "sortOrder=descending",
    `start=0`,
    `max_results=30`,
  ].join("&");

  let papers;
  try {
    const xml = await arxivApi(query);
    papers = parseArxivXml(xml);
  } catch (err) {
    console.error("[arXiv] API error:", err.message);
    process.exit(1);
  }

  // 筛选
  papers = papers
    .filter((p) => p.title.length > 20)
    .filter((p) => !p.title.toLowerCase().includes("survey"))
    .slice(0, 20);

  console.log(`[arXiv] Got ${papers.length} papers, translating...`);

  // LLM 翻译
  papers = await translateWithLLM(papers);

  // 生成 Markdown
  const lines = [
    "---",
    `tags: [AI论文, arXiv, ${dateStr}]`,
    "---",
    "",
    `# AI论文日报 — ${dateStr}`,
    "",
    "> 每日 arXiv AI 论文精选",
    "",
    "## 今日精选",
    "",
  ];

  for (const p of papers) {
    lines.push(
      `### ${p.zhTitle}`,
      "",
      `- ${p.zhSummary}`,
      `- 📄 [arXiv:${p.id}](${p.arxivUrl})`,
      `- 分类: ${p.categories.slice(0, 3).join(", ")}`,
      ""
    );
  }

  if (papers.length === 0) {
    lines.push("> 今日暂无论文数据", "");
  }

  lines.push(
    "---",
    "",
    `> 数据来源: [arXiv API](https://arxiv.org/help/api) · 翻译: DeepSeek · 更新时间: ${dateStr}`
  );

  const outputDir = path.join(CONTENT_DIR, "AI论文日报");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateStr}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[arXiv] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[arXiv] Fatal:", err);
  process.exit(1);
});
