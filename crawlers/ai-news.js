// 爬虫：AI科技动态 — RSS 聚合 + LLM 摘要
//
// 用法: node ai-news.js [outputDir]
// 输出: {outputDir}/AI科技动态/YYYY-MM-DD.md
// 需要: DEEPSEEK_API_KEY 环境变量

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || "";

// RSS 订阅源
const RSS_SOURCES = [
  { name: "TechCrunch", lang: "en", url: "https://techcrunch.com/category/artificial-intelligence/feed/" },
  { name: "The Verge", lang: "en", url: "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml" },
  { name: "机器之心", lang: "zh", url: "https://rsshub.app/jiqizhixin/latest" },
  { name: "量子位", lang: "zh", url: "https://rsshub.app/qbitai" },
];

// 简易 RSS 解析（不依赖外部库）
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

    if (title) {
      items.push({ title, link, description: desc, pubDate });
    }
  }
  return items;
}

// 简易 HTTP GET
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    client
      .get(url, { headers: { "User-Agent": "wiki-crawler/1.0" } }, (res) => {
        // 处理重定向
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

// LLM 摘要
async function summarizeWithLLM(articles) {
  if (!DEEPSEEK_API_KEY) {
    console.warn("[AI News] No DEEPSEEK_API_KEY, using raw titles");
    return articles.map((a) => ({
      ...a,
      zhSummary: a.description.slice(0, 100) || a.title,
    }));
  }

  const prompt = `你是AI科技新闻编辑。请为以下今日文章各写一句30-50字的中文摘要。准确概括、不编造。
${articles.map((a, i) => `[${i + 1}] [${a.source}] ${a.title}\n${(a.description || "").slice(0, 300)}`).join("\n\n")}

共 ${articles.length} 篇，请逐篇写摘要，格式："[N] 摘要内容"`;

  console.log("[AI News] Calling DeepSeek for summarization...");

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
        max_tokens: articles.length * 100,
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
    console.error("[AI News] LLM error:", err.message);
    articles.forEach((a) => {
      a.zhSummary = a.description.slice(0, 100) || a.title;
    });
  }

  return articles;
}

// 标题去重（简易版：Jaccard 相似度）
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

  console.log("[AI News] Fetching from", RSS_SOURCES.length, "sources...");

  // 1. 拉取所有 RSS 源
  const allArticles = [];
  for (const source of RSS_SOURCES) {
    try {
      const xml = await httpGet(source.url);
      const items = parseRSS(xml);
      // 只取今天的文章
      const todayItems = items.filter((item) => {
        try {
          const d = new Date(item.pubDate);
          return d.toDateString() === todayStr;
        } catch {
          return true; // 无法解析日期则保留
        }
      });
      console.log(`[AI News] ${source.name}: ${todayItems.length} articles today`);
      todayItems.forEach((item) => allArticles.push({ ...item, source: source.name }));
    } catch (err) {
      console.error(`[AI News] ${source.name} error:`, err.message);
    }
  }

  // 2. 去重
  const deduped = deduplicate(allArticles, 0.5);
  console.log(`[AI News] After dedup: ${deduped.length} (was ${allArticles.length})`);

  // 3. 排序（按来源权重）
  const weights = { TechCrunch: 3, "The Verge": 3, "机器之心": 3, "量子位": 2 };
  deduped.sort((a, b) => (weights[b.source] || 1) - (weights[a.source] || 1));

  const top15 = deduped.slice(0, 15);

  // 4. LLM 摘要
  const summarized = await summarizeWithLLM(top15);

  // 5. 生成 Markdown
  const lines = [
    "---",
    `tags: [AI, 科技动态, ${dateStr}]`,
    "---",
    "",
    `# AI科技动态 — ${dateStr}`,
    "",
    "> 每日 AI 前沿资讯",
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
    lines.push("> 今日暂无 AI 动态数据", "");
  }

  lines.push(
    "---",
    "",
    `> 数据来源: TechCrunch, The Verge, 机器之心, 量子位 · 翻译: DeepSeek · 更新时间: ${dateStr}`
  );

  const outputDir = path.join(CONTENT_DIR, "AI科技动态");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateStr}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[AI News] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[AI News] Fatal:", err);
  process.exit(1);
});
