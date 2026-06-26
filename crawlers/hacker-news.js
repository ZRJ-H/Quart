// 爬虫：Hacker News — 纯 API，零 LLM
//
// 用法: node hacker-news.js [outputDir]
// 输出: {outputDir}/Hacker-News/YYYY-MM-DD.md

const https = require("https");
const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const HN_BASE = "hacker-news.firebaseio.com";
const TOP_COUNT = 50;
const MIN_SCORE = 20;
const MAX_RESULTS = 20;

function hnApi(urlPath) {
  return new Promise((resolve, reject) => {
    https
      .get(
        {
          hostname: HN_BASE,
          path: `/v0${urlPath}`,
          headers: { "User-Agent": "wiki-crawler/1.0" },
        },
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => resolve(JSON.parse(data)));
        }
      )
      .on("error", reject);
  });
}

async function main() {
  const today = new Date();
  const dateStr = today.toISOString().slice(0, 10);

  console.log("[Hacker News] Fetching top stories...");

  // 1. 获取 top story IDs
  let ids;
  try {
    ids = (await hnApi("/topstories.json")).slice(0, TOP_COUNT);
  } catch (err) {
    console.error("[Hacker News] API error:", err.message);
    process.exit(1);
  }

  console.log(`[Hacker News] Fetching ${ids.length} stories...`);

  // 2. 并发获取每条详情
  const stories = (
    await Promise.all(
      ids.map((id) =>
        hnApi(`/item/${id}.json`).catch(() => null)
      )
    )
  ).filter(Boolean);

  // 3. 筛选
  let selected = stories
    .filter((s) => s.type === "story" && (s.score || 0) >= MIN_SCORE)
    .sort((a, b) => (b.score || 0) - (a.score || 0))
    .slice(0, MAX_RESULTS);

  console.log(
    `[Hacker News] Selected ${selected.length} stories (min score: ${MIN_SCORE})`
  );

  // 4. 生成 Markdown
  const lines = [
    "---",
    `tags: [HackerNews, ${dateStr}]`,
    "---",
    "",
    `# Hacker News 精选 — ${dateStr}`,
    "",
    "> 每日 HN 精选技术讨论",
    "",
    "## 今日精选",
    "",
  ];

  for (const story of selected) {
    const title = story.title || "(无标题)";
    const url = story.url
      ? story.url
      : `https://news.ycombinator.com/item?id=${story.id}`;
    const hnLink = `https://news.ycombinator.com/item?id=${story.id}`;
    lines.push(
      `### [${title}](${url})`,
      "",
      `- ${story.score} points | ${story.descendants || 0} comments`,
      `- [HN 讨论](${hnLink})`,
      ""
    );
  }

  if (selected.length === 0) {
    lines.push("> 今日暂无精选内容", "");
  }

  lines.push(
    "---",
    "",
    `> 数据来源: [Hacker News API](https://github.com/HackerNews/API) · 更新时间: ${dateStr}`
  );

  // 写入文件
  const outputDir = path.join(CONTENT_DIR, "Hacker-News");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateStr}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[Hacker News] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[Hacker News] Fatal:", err);
  process.exit(1);
});
