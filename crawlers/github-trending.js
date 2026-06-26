// 爬虫：GitHub Trending — 纯 API，零 LLM
//
// 用法: node github-trending.js [outputDir]
// 输出: {outputDir}/GitHub-Trending/YYYY-MM-DD.md

const https = require("https");
const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";

function githubApi(urlPath) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: "api.github.com",
      path: urlPath,
      headers: {
        "User-Agent": "wiki-crawler/1.0",
        Accept: "application/vnd.github+json",
      },
    };
    if (GITHUB_TOKEN) {
      options.headers.Authorization = `Bearer ${GITHUB_TOKEN}`;
    }

    https
      .get(options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          if (res.statusCode !== 200) {
            reject(new Error(`GitHub API ${res.statusCode}: ${data}`));
            return;
          }
          resolve(JSON.parse(data));
        });
      })
      .on("error", reject);
  });
}

function formatNumber(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return String(n);
}

async function main() {
  const today = new Date();
  const dateStr = today.toISOString().slice(0, 10);

  // 取昨天的日期用于筛选
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().slice(0, 10);

  console.log(`[GitHub Trending] Fetching repos created after ${yesterdayStr}...`);

  let repos;
  try {
    const data = await githubApi(
      `/search/repositories?q=created:>${yesterdayStr}&sort=stars&order=desc&per_page=15`
    );
    repos = data.items || [];
  } catch (err) {
    console.error("[GitHub Trending] API error:", err.message);
    process.exit(1);
  }

  // 过滤低质量项目
  repos = repos.filter((r) => r.stargazers_count >= 10 && !r.archived);

  console.log(`[GitHub Trending] Found ${repos.length} repos`);

  // 生成 Markdown
  const lines = [
    "---",
    `tags: [GitHub, Trending, ${dateStr}]`,
    "---",
    "",
    `# GitHub Trending — ${dateStr}`,
    "",
    "> 每日热门开源项目精选",
    "",
    "## 今日热门项目",
    "",
  ];

  for (const repo of repos) {
    const lang = repo.language ? ` | ${repo.language}` : "";
    const desc = repo.description
      ? repo.description.replace(/\n/g, " ").slice(0, 200)
      : "";
    lines.push(
      `### [${repo.full_name}](${repo.html_url})`,
      "",
      `- ⭐ ${formatNumber(repo.stargazers_count)} stars today${lang}`,
      `- ${desc}`,
      `- [github.com/${repo.full_name}](${repo.html_url})`,
      ""
    );
  }

  if (repos.length === 0) {
    lines.push("> 今日暂无热门项目数据", "");
  }

  lines.push(
    "---",
    "",
    `> 数据来源: [GitHub Search API](https://api.github.com/search/repositories) · 更新时间: ${dateStr}`
  );

  // 写入文件
  const outputDir = path.join(CONTENT_DIR, "GitHub-Trending");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateStr}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[GitHub Trending] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[GitHub Trending] Fatal:", err);
  process.exit(1);
});
