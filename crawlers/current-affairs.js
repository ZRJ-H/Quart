// 爬虫：时政要闻 — RSS 聚合 + LLM 摘要
//
// 用法: node current-affairs.js [outputDir]
// 输出: {outputDir}/时政要闻/YYYY-MM-DD.md
// 需要: DEEPSEEK_API_KEY 环境变量

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || "";

// RSS 订阅源
const RSS_SOURCES = [
  { name: "财新网", lang: "zh", url: "https://rsshub.app/caixin/latest" },
  { name: "36氪", lang: "zh", url: "https://36kr.com/feed" },
  { name: "澎湃新闻", lang: "zh", url: "https://rsshub.app/thepaper/feature" },
  { name: "华尔街见闻", lang: "zh", url: "https://rsshub.app/wallstreetcn/latest" },
];

// 简易 RSS 解析
function parseRSS(xml) {
  const items = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1];
    const titleMatch = item.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>|<title>(.*?)<\/title>/);
    const linkMatch = item.match(/<link><!\[CDATA\[(.*?)\]\]><\/link>|<link>(.*?)<\/link>/);
    const descMatch = item.match(/<description><!\[CDATA\[(.*?)\]\]><\/description>|<description>(.*?)<\/description>/);
    const dateMatch = item.match(/<pubDate>(.*?)<\/pubDate>/);

    if (!titleMatch) continue;

    const title = (titleMatch[1] || titleMatch[2] || "").replace(/<[^>]*>/g, "").trim();
    const link = (linkMatch?.[1] || "").trim();
    const desc = (descMatch?.[1] || descMatch?.[2] || "").replace(/<[^>]*>/g, "").trim();
    const pubDate = dateMatch?.[1] || "";

    if (title) items.push({ title, link, description: desc, pubDate });
  }
  return items;
}

function httpGet(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    client
      .get(url, { headers: { "User-Agent": "wiki-crawler/1.0" } }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          return httpGet(res.headers.location).then(resolve).catch(reject);
        }
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      })
      .on("error", reject);
  });
}

async function summarizeWithLLM(articles) {
  if (!DEEPSEEK_API_KEY) {
    console.warn("[Affairs] No DEEPSEEK_API_KEY, using raw titles");
    return articles.map((a) => ({
      ...a,
      zhSummary: a.description.slice(0, 100) || a.title,
    }));
  }

  const prompt = `你是时政财经新闻编辑。请为以下今日文章各写一句40-60字的中文摘要。客观准确、不主观评论。
${articles.map((a, i) => `[${i + 1}] [${a.source}] ${a.title}\n${(a.description || "").slice(0, 300)}`).join("\n\n")}

共 ${articles.length} 篇，请逐篇写摘要，格式："[N] 摘要内容"`;

  console.log("[Affairs] Calling DeepSeek for summarization...");

  try {
    const resp = await fetch("https://api.deepseek.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.3,
        max_tokens: articles.length * 120,
      }),
    });

    if (!resp.ok) throw new Error(`DeepSeek ${resp.status}`);
    const data = await resp.json();
    const result = data.choices[0].message.content;

    const lines = result.split("\n").filter((l) => l.trim());
    articles.forEach((a, i) => {
      if (i < lines.length) {
        a.zhSummary = lines[i].replace(/^\[\d+\]\s*/, "").trim();
      } else {
        a.zhSummary = a.description.slice(0, 100) || a.title;
      }
    });
  } catch (err) {
    console.error("[Affairs] LLM error:", err.message);
    articles.forEach((a) => {
      a.zhSummary = a.description.slice(0, 100) || a.title;
    });
  }

  return articles;
}

function deduplicate(articles, threshold = 0.5) {
  const result = [];
  for (const a of articles) {
    const isDuplicate = result.some((b) => {
      const wordsA = new Set(a.title.toLowerCase().split(/\s+/));
      const wordsB = new Set(b.title.toLowerCase().split(/\s+/));
      const intersection = [...wordsA].filter((w) => wordsB.has(w)).length;
      const union = new Set([...wordsA, ...wordsB]).size;
      return intersection / union > threshold;
    });
    if (!isDuplicate) result.push(a);
  }
  return result;
}

async function main() {
  const today = new Date();
  const dateStr = today.toISOString().slice(0, 10);
  const todayStr = today.toDateString();

  console.log("[Affairs] Fetching from", RSS_SOURCES.length, "sources...");

  const allArticles = [];
  for (const source of RSS_SOURCES) {
    try {
      const xml = await httpGet(source.url);
      const items = parseRSS(xml);
      const todayItems = items.filter((item) => {
        try {
          const d = new Date(item.pubDate);
          return d.toDateString() === todayStr;
        } catch {
          return true;
        }
      });
      console.log(`[Affairs] ${source.name}: ${todayItems.length} articles today`);
      todayItems.forEach((item) => allArticles.push({ ...item, source: source.name }));
    } catch (err) {
      console.error(`[Affairs] ${source.name} error:`, err.message);
    }
  }

  const deduped = deduplicate(allArticles, 0.5);
  console.log(`[Affairs] After dedup: ${deduped.length} (was ${allArticles.length})`);

  const weights = { "财新网": 3, "华尔街见闻": 3, "澎湃新闻": 2, "36氪": 2 };
  deduped.sort((a, b) => (weights[b.source] || 1) - (weights[a.source] || 1));

  const top15 = deduped.slice(0, 15);
  const summarized = await summarizeWithLLM(top15);

  // 生成 Markdown
  const lines = [
    "---",
    `tags: [时政, 财经, ${dateStr}]`,
    "---",
    "",
    `# 时政要闻 — ${dateStr}`,
    "",
    "> 每日时政财经动态",
    "",
    "## 今日要闻",
    "",
  ];

  for (const a of summarized) {
    lines.push(
      `### ${a.title}`,
      "",
      `- ${a.zhSummary || a.description.slice(0, 150)}`,
      a.link ? `- [来源: ${a.source}](${a.link})` : `- 来源: ${a.source}`,
      ""
    );
  }

  if (summarized.length === 0) {
    lines.push("> 今日暂无时政动态数据", "");
  }

  lines.push(
    "---",
    "",
    `> 数据来源: 财新网, 华尔街见闻, 澎湃新闻, 36氪 · 翻译: DeepSeek · 更新时间: ${dateStr}`
  );

  const outputDir = path.join(CONTENT_DIR, "时政要闻");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateStr}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[Affairs] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[Affairs] Fatal:", err);
  process.exit(1);
});
