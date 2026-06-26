// Wiki AI 搜索服务 — Express + SQLite + DeepSeek
require("dotenv").config({ path: require("path").join(__dirname, "..", ".env") });

const express = require("express");
const cors = require("cors");
const Database = require("better-sqlite3");
const path = require("path");
const fs = require("fs");

const {
  buildReverseIndex,
  expandQuery,
  searchIndex,
  extractLinkedPages,
  findByName,
  findById,
  filterResults,
  sortResults,
  detectQueryType,
  selectRelevantResults,
  calculateQualityScore,
} = require("./search");

const { cardSnippet, buildPrompt, streamDeepSeek } = require("./deepseek");

const app = express();
app.use(cors());
app.use(express.json());

// ========== SQLite ==========
const DB_PATH = process.env.DB_PATH || path.join(__dirname, "wiki.db");
let db;

function openDb() {
  db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");
  db.pragma("cache_size = -64000"); // 64MB
  db.pragma("busy_timeout = 5000");
}

function closeDb() {
  if (db && db.open) db.close();
}

// ========== 同义词 ==========
const synonymsPath = path.join(__dirname, "synonyms.json");
let synonyms = { forward: {}, reverse: {} };

function loadSynonyms() {
  try {
    const data = JSON.parse(fs.readFileSync(synonymsPath, "utf8"));
    synonyms = { forward: data, reverse: buildReverseIndex(data) };
    console.log(`Synonyms loaded: ${Object.keys(data).length} groups`);
  } catch (err) {
    console.warn("Failed to load synonyms:", err.message);
    synonyms = { forward: {}, reverse: {} };
  }
}

// ========== POST /api/search ==========
app.post("/api/search", async (req, res) => {
  const { query, filters, sort, limit = 10 } = req.body;
  if (!query || !query.trim()) {
    return res.status(400).json({ error: "query required" });
  }

  // SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  try {
    const apiKey = process.env.DEEPSEEK_API_KEY;
    if (!apiKey) {
      res.write(
        `data: ${JSON.stringify({ type: "error", message: "DEEPSEEK_API_KEY not configured" })}\n\n`
      );
      res.end();
      return;
    }

    // 1. 同义词扩展
    const expandedTerms = expandQuery(query, synonyms);

    // 2. 搜索
    const keywordResults = searchIndex(db, query, limit * 2, expandedTerms);

    if (keywordResults.length === 0) {
      res.write(
        `data: ${JSON.stringify({ type: "answer", text: "知识库中未找到相关内容。" })}\n\n`
      );
      res.write(`data: ${JSON.stringify({ type: "done" })}\n\n`);
      res.end();
      return;
    }

    // 3. 智能选择
    const selected = selectRelevantResults(keywordResults);

    // 4. 提取关联页面
    const relatedIds = new Set();
    const highScoreResults = selected.filter(
      (r) => r.score >= 20
    );
    for (const r of highScoreResults) {
      if (r.content) {
        const linked = extractLinkedPages(r.content);
        for (const name of linked) {
          const page = findByName(db, name);
          if (page && !selected.find((s) => s.id === page.id)) {
            relatedIds.add(page.id);
          }
        }
      }
    }
    const relatedPages = [...relatedIds]
      .map((id) => findById(db, id))
      .filter(Boolean)
      .map((e) => ({ ...e, score: 0, is_related: true }))
      .slice(0, 5);

    // 5. 合并 + 过滤 + 排序
    let allResults = [...selected, ...relatedPages];
    allResults = filterResults(allResults, filters || {});
    allResults = sortResults(allResults, sort || "relevance");
    allResults = allResults.slice(0, limit);

    // 6. 发送 sources
    res.write(
      `data: ${JSON.stringify({
        type: "sources",
        sources: allResults.map((r) => ({
          id: r.id,
          name: r.name,
          category: r.category || r.type,
          summary:
            typeof cardSnippet === "function"
              ? cardSnippet(r.content || r.summary, r.name)
              : (r.summary || "").slice(0, 150),
          last_updated: r.last_updated,
          tags: Array.isArray(r.tags) ? r.tags : JSON.parse(r.tags || "[]"),
          score: Math.round((r.score || 0) * 100) / 100,
          quality_score: r.quality_score || calculateQualityScore(r),
          reference_count: r.reference_count || 0,
          is_related: r.is_related || false,
        })),
      })}\n\n`
    );

    // 7. 构建 fullData map（结果已含 content 字段，无需额外查）
    const fullData = {};
    for (const r of allResults) {
      fullData[r.id] = { content: r.content, summary: r.summary, tags: r.tags };
    }

    // 8. 流式调用 DeepSeek
    const queryType = detectQueryType(query);
    const prompt = buildPrompt(query, allResults, fullData, queryType);
    await streamDeepSeek(prompt, apiKey, res);
  } catch (err) {
    console.error("Search error:", err);
    try {
      res.write(
        `data: ${JSON.stringify({ type: "error", message: err.message })}\n\n`
      );
    } catch {}
    res.end();
  }
});

// ========== GET /api/health ==========
app.get("/api/health", (req, res) => {
  let count = 0;
  try {
    count = db.prepare("SELECT COUNT(*) as n FROM entries").get().n;
  } catch {}
  res.json({ ok: true, pages: count, mode: "sqlite-fts5 + deepseek" });
});

// ========== POST /api/reload ==========
app.post("/api/reload", (req, res) => {
  try {
    closeDb();
    openDb();
    loadSynonyms();
    const count = db.prepare("SELECT COUNT(*) as n FROM entries").get().n;
    res.json({ ok: true, pages: count });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ========== 启动 ==========
const PORT = process.env.PORT || 3000;
openDb();
loadSynonyms();
app.listen(PORT, () => {
  console.log(`Wiki search server running on http://localhost:${PORT}`);
});

// 优雅退出
process.on("SIGINT", () => {
  closeDb();
  process.exit(0);
});
process.on("SIGTERM", () => {
  closeDb();
  process.exit(0);
});
