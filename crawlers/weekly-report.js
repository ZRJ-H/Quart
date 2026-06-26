// 爬虫：周报 — 汇总一周5个板块数据，LLM 生成趋势报告
//
// 用法: node weekly-report.js [outputDir]
// 输出: {outputDir}/周报/YYYY-WXX.md
// 需要: DEEPSEEK_API_KEY 环境变量

const fs = require("fs");
const path = require("path");

const CONTENT_DIR = process.argv[2] || path.join(__dirname, "..", "content");
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || "";

const CATEGORIES = ["AI科技动态", "时政要闻", "GitHub-Trending", "AI论文日报", "Hacker-News"];

// 读取目录下本周所有 md 文件内容
function readWeekFiles(dir, sinceDate) {
  const catPath = path.join(CONTENT_DIR, dir);
  if (!fs.existsSync(catPath)) return [];

  const files = fs.readdirSync(catPath).filter((f) => f.endsWith(".md"));

  const entries = [];
  for (const f of files) {
    const dateStr = f.replace(".md", "");
    if (dateStr >= sinceDate) {
      const content = fs.readFileSync(path.join(catPath, f), "utf8");
      // 提取 H3 标题
      const titles = [];
      const titleRegex = /^### (.+)$/gm;
      let match;
      while ((match = titleRegex.exec(content)) !== null) {
        titles.push(match[1]);
      }
      entries.push({ date: dateStr, titles, file: f });
    }
  }
  return entries.sort((a, b) => a.date.localeCompare(b.date));
}

function getWeekRange() {
  const now = new Date();
  const dayOfWeek = now.getDay(); // 0=Sun
  const daysSinceMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
  const monday = new Date(now);
  monday.setDate(now.getDate() - daysSinceMonday);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  const fmt = (d) => d.toISOString().slice(0, 10);
  return {
    monday: fmt(monday),
    sunday: fmt(sunday),
    weekNum: getWeekNumber(now),
  };
}

function getWeekNumber(d) {
  const start = new Date(d.getFullYear(), 0, 1);
  const diff = d - start;
  return `W${String(Math.ceil((diff / 86400000 + start.getDay() + 1) / 7)).padStart(2, "0")}`;
}

async function generateWeeklyReport(weekData, weekRange) {
  if (!DEEPSEEK_API_KEY) {
    console.warn("[Weekly] No DEEPSEEK_API_KEY, generating simple report");
    return generateSimpleReport(weekData, weekRange);
  }

  // 构建统计摘要（减少 token）
  const stats = {};
  for (const [cat, entries] of Object.entries(weekData)) {
    stats[cat] = {
      days: entries.length,
      totalArticles: entries.reduce((sum, e) => sum + e.titles.length, 0),
      highlights: entries
        .flatMap((e) => e.titles)
        .slice(0, 10), // 每天最多取10个标题
    };
  }

  const prompt = `你是知识库周报编辑。请根据本周（${weekRange.monday} ~ ${weekRange.sunday}）各板块数据生成周报。

## 数据统计
${Object.entries(stats)
  .map(([cat, s]) => `${cat}: ${s.days}天内容, ${s.totalArticles}篇文章\n代表标题: ${s.highlights.slice(0, 5).join("; ")}`)
  .join("\n\n")}

## 要求
1. **本周热点**（2-3个最值得关注的趋势/事件）
2. **板块回顾**（每个板块 1-2 句总结）
3. **关键词云**（5-8个本周高频词汇）
4. **下周关注**（1-2个值得持续关注的方向）

使用 Markdown 格式，控制在 400 字以内。`;

  console.log("[Weekly] Calling DeepSeek...");

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
        temperature: 0.5,
        max_tokens: 1500,
      }),
    });

    if (!resp.ok) throw new Error(`DeepSeek ${resp.status}`);
    const data = await resp.json();
    return data.choices[0].message.content;
  } catch (err) {
    console.error("[Weekly] LLM error:", err.message);
    return generateSimpleReport(weekData, weekRange);
  }
}

function generateSimpleReport(weekData, weekRange) {
  const lines = [];
  lines.push("## 本周热点\n");
  lines.push("> 本周数据汇总（不含 AI 分析）\n");

  for (const [cat, entries] of Object.entries(weekData)) {
    const total = entries.reduce((sum, e) => sum + e.titles.length, 0);
    lines.push(`### ${cat}`);
    lines.push(`- ${entries.length} 天内容，共 ${total} 篇文章`);
    lines.push("");
  }

  return lines.join("\n");
}

async function main() {
  const weekRange = getWeekRange();
  console.log(`[Weekly] Week ${weekRange.weekNum}: ${weekRange.monday} ~ ${weekRange.sunday}`);

  // 收集各板块数据
  const weekData = {};
  for (const cat of CATEGORIES) {
    const entries = readWeekFiles(cat, weekRange.monday);
    console.log(`[Weekly] ${cat}: ${entries.length} days, ${entries.reduce((s, e) => s + e.titles.length, 0)} articles`);
    weekData[cat] = entries;
  }

  // LLM 生成报告
  const report = await generateWeeklyReport(weekData, weekRange);

  // 生成 Markdown
  const lines = [
    "---",
    `tags: [周报, ${weekRange.weekNum}]`,
    `date: ${weekRange.sunday}`,
    "---",
    "",
    `# 周报 — 2026-${weekRange.weekNum}`,
    "",
    `> ${weekRange.monday} ~ ${weekRange.sunday} 综合趋势报告`,
    "",
    report,
    "",
    "---",
    "",
    `> 数据来源: 本周各板块每日内容汇总 · 生成: DeepSeek · ${weekRange.sunday}`,
  ];

  const outputDir = path.join(CONTENT_DIR, "周报");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `2026-${weekRange.weekNum}.md`);
  fs.writeFileSync(outputPath, lines.join("\n"), "utf8");
  console.log(`[Weekly] Written: ${outputPath}`);
}

main().catch((err) => {
  console.error("[Weekly] Fatal:", err);
  process.exit(1);
});
