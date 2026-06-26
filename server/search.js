// 搜索模块：从 worker/index.js 提取，适配 SQLite FTS5

// 评分阈值
const SCORE_CONFIG = {
  MIN_THRESHOLD: 8,
  HIGH_RELEVANCE: 20,
  MAX_RESULTS: 15,
  DYNAMIC_RATIO: 0.4,
  SYNONYM_SCORE_FACTOR: 0.6,
};

// 同义词反向索引构建（从 worker/index.js 搬过来，逻辑不变）
function buildReverseIndex(data) {
  const reverseIndex = {};
  for (const [key, values] of Object.entries(data)) {
    if (!Array.isArray(values)) continue;

    const allWords = [key, ...values].map((w) => w.toLowerCase());
    const allTokens = new Set();
    for (const word of allWords) {
      allTokens.add(word);
      if (word.includes(" ")) {
        for (const token of word.split(/\s+/)) {
          if (token.length >= 2) allTokens.add(token);
        }
      }
    }

    for (const token of allTokens) {
      if (!reverseIndex[token]) reverseIndex[token] = new Set();
      for (const related of allWords) {
        reverseIndex[token].add(related.toLowerCase());
      }
    }
  }
  return reverseIndex;
}

// 查询扩展：同义词
function expandQuery(query, synonyms) {
  const q = query.toLowerCase();
  const words = q.split(/\s+/).filter(Boolean);
  const expanded = new Set(words);

  const reverseIndex = synonyms.reverse || {};

  for (const word of words) {
    if (word.length < 2) continue;
    if (reverseIndex[word]) {
      for (const related of reverseIndex[word]) {
        expanded.add(related);
      }
    }
  }
  return [...expanded];
}

// 中英文混合分词（用于同义词扩展前的预处理）
function tokenize(query) {
  const q = (query || "").toLowerCase();
  const tokens = new Set();
  const segments = q.match(/[一-龥]+|[a-z0-9]+/g) || [];
  for (const seg of segments) {
    if (/^[a-z0-9]+$/.test(seg)) {
      tokens.add(seg);
    } else if (seg.length <= 2) {
      tokens.add(seg);
    } else {
      tokens.add(seg);
      for (let i = 0; i < seg.length - 1; i++) {
        tokens.add(seg.slice(i, i + 2));
      }
    }
  }
  return [...tokens].filter(Boolean);
}

// FTS5 全文搜索
function searchIndex(db, query, limit = 10, expandedTerms = null) {
  const today = new Date().toJSON().slice(0, 10);
  const todayMs = Date.parse(today);

  let cleanQuery = query;
  let recencyBoost = false;

  if (/今日|今天|最新|最近|近期|这几天|近几天|本周|这周/.test(cleanQuery)) {
    recencyBoost = true;
    cleanQuery = cleanQuery
      .replace(/今日|今天|最新|最近|近期|这几天|近几天|本周|这周/g, "")
      .trim();
  }

  // 纯时间查询：返回最新条目
  if (recencyBoost && !cleanQuery) {
    const stmt = db.prepare(`
      SELECT *, NULL as rank FROM entries
      ORDER BY last_updated DESC
      LIMIT ?
    `);
    return stmt.all(limit).map((e, i) => ({ ...e, score: 100 - i }));
  }

  const q = cleanQuery.toLowerCase();

  // 构建 FTS5 查询
  let ftsTerms;
  if (expandedTerms && expandedTerms.length > 0) {
    ftsTerms = expandedTerms
      .map((t) => `"${t.replace(/"/g, '""')}"`)
      .join(" OR ");
  } else {
    const tokens = tokenize(cleanQuery);
    ftsTerms = tokens.map((t) => `"${t.replace(/"/g, '""')}"`).join(" OR ");
  }

  if (!ftsTerms) {
    // 无有效搜索词，返回空
    return [];
  }

  let rows;
  try {
    const stmt = db.prepare(`
      SELECT e.*, fts.rank as fts_rank
      FROM entries_fts fts
      JOIN entries e ON fts.rowid = e.rowid
      WHERE entries_fts MATCH ?
      ORDER BY fts.rank
      LIMIT ?
    `);
    rows = stmt.all(ftsTerms, limit * 2);
  } catch {
    // FTS5 查询语法错误（特殊字符等），回退到 LIKE 查询
    const likePattern = `%${q}%`;
    const stmt = db.prepare(`
      SELECT *, 0 as fts_rank FROM entries
      WHERE name LIKE ? OR summary LIKE ? OR content LIKE ?
      LIMIT ?
    `);
    rows = stmt.all(likePattern, likePattern, likePattern, limit * 2);
  }

  // 额外加权（弥补 FTS5 对中文精确匹配的不足）
  const scored = rows.map((entry) => {
    let extra = 0;
    const name = (entry.name || "").toLowerCase();
    const tags = ((entry.tags && typeof entry.tags === "string" ? JSON.parse(entry.tags) : entry.tags) || [])
      .join(" ")
      .toLowerCase();

    if (name === q) extra += 40;
    if (name.includes(q)) extra += 20;

    const qWords = tokenize(q);
    for (const w of qWords) {
      if (name.includes(w)) extra += 8;
      if (tags.includes(w)) extra += 8;
    }

    // 同义词额外加分
    if (expandedTerms) {
      for (const term of expandedTerms) {
        if (qWords.includes(term)) continue;
        if (name.includes(term))
          extra += 20 * SCORE_CONFIG.SYNONYM_SCORE_FACTOR;
        if (tags.includes(term))
          extra += 8 * SCORE_CONFIG.SYNONYM_SCORE_FACTOR;
      }
    }

    // 时间意图加权
    if (recencyBoost && extra > 0 && entry.last_updated) {
      const daysAgo =
        (todayMs - Date.parse(entry.last_updated)) / 86400000;
      if (daysAgo <= 1) extra += 40;
      else if (daysAgo <= 2) extra += 28;
      else if (daysAgo <= 4) extra += 16;
      else if (daysAgo <= 7) extra += 8;
      else if (daysAgo <= 30) extra += 3;
    }

    return {
      ...entry,
      tags: typeof entry.tags === "string" ? JSON.parse(entry.tags) : entry.tags || [],
      score: (entry.fts_rank || 0) * -1 + extra, // FTS5 rank 越负越相关，反转后加分
    };
  });

  return scored
    .filter((e) => e.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (b.last_updated || "").localeCompare(a.last_updated || "");
    });
}

// 从内容中提取 [[wikilink]]
function extractLinkedPages(content) {
  if (!content) return [];
  const links = [];
  const regex = /\[\[([^\]|]+)(?:\|[^\]]*)?\]\]/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    links.push(match[1].trim());
  }
  return [...new Set(links)];
}

// 按名称查找条目
function findByName(db, name) {
  try {
    return db
      .prepare("SELECT * FROM entries WHERE name = ? OR id LIKE ?")
      .get(name, `%/${name}`);
  } catch {
    return null;
  }
}

// 按 ID 查找
function findById(db, id) {
  try {
    return db.prepare("SELECT * FROM entries WHERE id = ?").get(id);
  } catch {
    return null;
  }
}

// 过滤
function filterResults(results, filters) {
  let filtered = results;

  if (filters.tags && filters.tags.length > 0) {
    filtered = filtered.filter(
      (entry) =>
        filters.tags.includes(entry.category) ||
        (entry.tags &&
          entry.tags.some((tag) => filters.tags.includes(tag)))
    );
  }

  if (filters.time && filters.time !== "all") {
    const days = filters.time === "7d" ? 7 : 30;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const cutoffStr = cutoff.toISOString().slice(0, 10);
    filtered = filtered.filter(
      (entry) => (entry.last_updated || "") >= cutoffStr
    );
  }

  return filtered;
}

// 排序
function sortResults(results, sort) {
  switch (sort) {
    case "time":
      return [...results].sort((a, b) =>
        (b.last_updated || "").localeCompare(a.last_updated || "")
      );
    case "popularity":
      return [...results].sort(
        (a, b) => (b.reference_count || 0) - (a.reference_count || 0)
      );
    case "relevance":
    default:
      return [...results].sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        const aQuality = a.quality_score || 0;
        const bQuality = b.quality_score || 0;
        if (bQuality !== aQuality) return bQuality - aQuality;
        return (b.last_updated || "").localeCompare(a.last_updated || "");
      });
  }
}

// 检测查询类型
function detectQueryType(query) {
  const q = query.toLowerCase();

  if (
    (q.includes("和") && q.includes("区别")) ||
    q.includes("vs") ||
    q.includes("对比")
  ) {
    return "comparison";
  }

  if (
    q.includes("历史") ||
    q.includes("发展") ||
    q.includes("时间线") ||
    q.includes("事件")
  ) {
    return "timeline";
  }

  if (q.includes("是什么") || q.includes("介绍") || q.includes("概述")) {
    return "overview";
  }

  return "comprehensive";
}

// 智能选择相关结果
function selectRelevantResults(scoredResults) {
  if (scoredResults.length === 0) return [];

  const sorted = [...scoredResults].sort((a, b) => b.score - a.score);
  const maxScore = sorted[0].score;

  const dynamicThreshold = Math.max(
    SCORE_CONFIG.MIN_THRESHOLD,
    Math.floor(maxScore * SCORE_CONFIG.DYNAMIC_RATIO)
  );

  let selected = sorted.filter((r) => r.score >= dynamicThreshold);

  if (selected.length < 3) {
    selected = sorted.filter((r) => r.score >= SCORE_CONFIG.MIN_THRESHOLD);
  }

  if (selected.length > SCORE_CONFIG.MAX_RESULTS) {
    selected = selected.slice(0, SCORE_CONFIG.MAX_RESULTS);
  }

  return selected;
}

// 计算质量分数
function calculateQualityScore(entry) {
  let quality = 0;

  quality += Math.min((entry.reference_count || 0) * 2, 20);

  if (entry.content_length > 1000) quality += 5;
  if (entry.content_length > 3000) quality += 5;

  if (entry.last_updated) {
    const daysSinceUpdate =
      (Date.now() - new Date(entry.last_updated).getTime()) /
      (1000 * 60 * 60 * 24);
    if (daysSinceUpdate < 7) quality += 3;
    else if (daysSinceUpdate < 30) quality += 1;
  }

  return quality;
}

module.exports = {
  buildReverseIndex,
  expandQuery,
  tokenize,
  searchIndex,
  extractLinkedPages,
  findByName,
  findById,
  filterResults,
  sortResults,
  detectQueryType,
  selectRelevantResults,
  calculateQualityScore,
};
