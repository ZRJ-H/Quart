# 搜索增强设计文档

**日期**: 2026-06-21  
**范围**: DogeLover 知识库 — 搜索框全站常驻 + 日报内容全量索引

---

## 1. 背景与目标

### 现状问题
- SearchAI 搜索框仅出现在首页，用户读日报时无法搜索
- 搜索索引只包含 wiki 实体（2,076 条），不含任何日报内容
- 网站显示 7 天滚动窗口，但搜索应作为长期记忆独立运作

### 目标
1. 搜索框在所有页面右侧栏常驻（全站可用）
2. 所有日报历史内容（45 天 × 5 栏目）以文章级粒度纳入搜索索引
3. 之后每日新增内容自动增量索引，历史内容永久保留

---

## 2. 方向 1：搜索框全站常驻（右侧栏）

### 改动文件
`/home/taskflow/Quart/quartz.layout.ts`

### 方案
将 SearchAI 加入默认内容页 layout 的 `right` 数组首位，无条件限制：

```ts
// defaultPageLayout.right
right: [
  Component.SearchAI({ workerUrl: "https://doge-wiki-search.zstufjj2004.workers.dev" }),
  Component.DesktopOnly(Component.TableOfContents()),
  Component.Backlinks(),
],
```

同样加入 `defaultListPageLayout.right`（栏目首页列表页）。

首页 `beforeBody` 的 SearchAI 保留不变（大搜索框入口）。

### 边界说明
- 移动端：右侧栏收起，SearchAI 不可见；首页 beforeBody 入口仍可用
- Wiki 页面：同样显示，可搜索 wiki 内容

---

## 3. 方向 2：日报内容全量索引

### 改动文件
`/home/taskflow/Quart/scripts/build-wiki-index.py`

### 索引粒度：文章级（H3 为单位）

每个 H3 事件块作为一条独立条目。

**条目结构**：
```json
{
  "id": "daily/AI科技动态/2026-06-21#john-jumper-anthropic",
  "name": "AlphaFold之父 John Jumper 离开 Google DeepMind 加入 Anthropic",
  "category": "ai-news",
  "tags": ["AI动态", "每日资讯", "2026-06-21"],
  "content": "来源: CNBC | 摘要: ... | 价值点: ...",
  "last_updated": "2026-06-21",
  "source_file": "AI科技动态/2026-06-21"
}
```

### 栏目 category 映射
| 目录 | category |
|---|---|
| AI科技动态 | ai-news |
| 时政要闻 | daily-news |
| GitHub Trending | github-trending |
| Hacker News | hn-daily |
| AI论文日报 | arxiv-daily |

### H3 解析规则（经实际文件核查）

提取以下 H2 章节下的 H3：
- **AI科技动态**：`## 重大事件`、`## 新产品/新模型`、`## 融资与并购`、`## 跟进事件`
- **时政要闻**：`## 今日要闻`
- **GitHub Trending**：`## 今日精选`、`## 其余热榜`
- **Hacker News**：`## 今日精选`
- **AI论文日报**：`## 今日精选`

排除章节：`## 今日概览`、`## 连续在榜项目`、`## 趋势观察`、`## 数据说明`、`## 今日关键词`、`## 信息来源说明`、`## 与其他线的关联`

容错规则：文件内 H3 数量为 0（旧表格格式文件）则跳过该文件，不报错。

### 历史内容回填
- 首次构建：扫描 vault 全部 45 天历史文件，约 2,250 条新条目
- 历史内容永久保留，不设过期删除
- 现有 `filter-changed.py` 识别变化条目，首次全量嵌入后每日增量约 50 条

### 索引体积估算
| 类型 | 条目数 | 估算大小 |
|---|---|---|
| 现有 wiki | 2,076 | ~2 MB |
| 日报历史回填（45天） | ~2,250 | ~2 MB |
| 合计 | ~4,300 | ~4 MB |

Cloudflare KV 免费 1 GB，Vectorize 免费 5,000 万向量，远在限制之内。

---

## 4. 不改动的部分

- Worker `index.js`：搜索逻辑不变
- Quartz `RemoveOldNotes` 过滤器：网站 7 天窗口不变
- `upload-to-kv.py`、`embeddings-to-ndjson.py`：不变
- GitHub Actions deploy workflow：不变（`build-wiki-index.py` 已在流程中）

---

## 5. 执行顺序

1. 修改 `build-wiki-index.py`，加入 `build_daily_index()` 函数
2. 本地验证解析结果（检查各栏目 H3 条目数量和结构）
3. 修改 `quartz.layout.ts`，SearchAI 加入右侧栏
4. 提交、推送、触发 deploy（自动完成回填 + 嵌入 + 上线）
5. 验证：搜索"John Jumper"返回 AI科技动态文章条目

---

## 6. 风险与应对

| 风险 | 应对 |
|---|---|
| H2 章节名因 AI 自由发挥而偏差 | 步骤 2 本地验证时检查各栏目覆盖率，覆盖不足时补充白名单 |
| 首次嵌入 2,250 条 GitHub Actions 超时 | 检查 Actions 超时配置；必要时手动跑脚本后再 deploy |
| 旧格式文件（表格）H3 为 0 | 容错跳过，不报错 |
| 右侧栏移动端不可见 | 首页 beforeBody 入口仍在，可接受 |
