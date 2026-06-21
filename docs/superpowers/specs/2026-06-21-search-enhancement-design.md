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
3. 之后每日新增内容自动增量索引

---

## 2. 方向 1：搜索框全站常驻

### 改动文件
`/home/taskflow/Quart/quartz.layout.ts`

### 当前状态
SearchAI 组件在 `beforeBody` 区，带条件 `slug === "index"`，仅首页可见。

右侧栏（所有内容页）：
```ts
right: [Component.DesktopOnly(Component.TableOfContents()), Component.Backlinks()],
```

### 改动方案
将 SearchAI 加入**默认内容页 layout** 的 `right` 数组首位，不加条件限制，全站常驻：

```ts
right: [
  Component.SearchAI({ workerUrl: "https://doge-wiki-search.zstufjj2004.workers.dev" }),
  Component.DesktopOnly(Component.TableOfContents()),
  Component.Backlinks(),
],
```

同时保留首页 `beforeBody` 里的 SearchAI 不变（首页正文区显示大搜索框，右侧栏也有，双入口）。

### 边界说明
- 移动端：右侧栏在 Quartz 移动端会收起，SearchAI 不可见。首页 `beforeBody` 的入口仍可用
- 列表页（栏目首页）：同样加入 `defaultListPageLayout.right`
- Wiki 页面：同样显示，搜索 wiki 内容本身就有意义

---

## 3. 方向 2：日报内容全量索引

### 改动文件
`/home/taskflow/Quart/scripts/build-wiki-index.py`

### 索引粒度：文章级（H3 为单位）

每个 H3 事件块作为一条独立索引条目，而非整个日报文件。

**日报文件结构**（已统一为 H3+ul 卡片格式）：
```markdown
## 重大事件          ← H2 章节
### 事件标题         ← 每条为一个索引条目
- **来源**: ...
- **摘要**: ...
- **价值点**: ...
```

**生成的索引条目结构**：
```json
{
  "id": "daily/AI科技动态/2026-06-21#john-jumper-anthropic",
  "name": "AlphaFold之父 John Jumper 离开 Google DeepMind 加入 Anthropic",
  "category": "ai-news",
  "tags": ["AI动态", "每日资讯", "2026-06-21"],
  "content": "来源: CNBC | 摘要: ... | 影响: ... | 价值点: ...",
  "last_updated": "2026-06-21",
  "source_file": "AI科技动态/2026-06-21"
}
```

### 五个栏目的 category 映射
| 目录 | category |
|---|---|
| AI科技动态 | ai-news |
| 时政要闻 | daily-news |
| GitHub Trending | github-trending |
| Hacker News | hn-daily |
| AI论文日报 | arxiv-daily |

### H3 解析规则
- 扫描 H2 章节，只提取以下 H2 下的 H3（排除非事件章节）：
  - **AI科技动态**：`## 重大事件`、`## 重要动态`
  - **时政要闻**：`## 重大事件`、`## 重要动态`
  - **GitHub Trending**：`## 今日精选`、`## 其余热榜`
  - **Hacker News**：`## 精选讨论`、`## 热点话题`
  - **AI论文日报**：`## 今日精选`
- 排除：`## 今日概览`、`## 连续在榜项目`、`## 趋势观察`、`## 数据说明`、`## 今日关键词` 等非文章章节

### 历史内容回填
- 首次构建：扫描 vault 中全部 45 天历史文件（约 2,250 条新条目）
- 现有 `filter-changed.py` 比对新旧 full JSON，识别变化条目
- 首次运行 `build-embeddings.py` 会对全部新条目计算向量（一次性成本）
- 之后每日 deploy：只有当天新增的 ~50 条触发增量嵌入

### 索引体积估算
| 类型 | 条目数 | 估算大小 |
|---|---|---|
| 现有 wiki | 2,076 | ~2 MB |
| 日报历史回填（45天） | ~2,250 | ~2 MB |
| 合计 | ~4,300 | ~4 MB |

KV 免费 1 GB，Vectorize 免费 5,000 万向量，远在限制之内。

---

## 4. 不改动的部分

- Worker `index.js`：搜索逻辑、AI 回答生成不变
- Quartz `RemoveOldNotes` 过滤器：网站显示窗口保持 7 天不变
- `upload-to-kv.py`、`embeddings-to-ndjson.py`：不变
- GitHub Actions deploy workflow：不变（`build-wiki-index.py` 已在流程中）

---

## 5. 执行顺序

**Step 1**：修改 `build-wiki-index.py`，加入 `build_daily_index()` 函数  
**Step 2**：本地验证解析结果（检查生成条目结构正确）  
**Step 3**：修改 `quartz.layout.ts`，SearchAI 加入右侧栏  
**Step 4**：提交、推送、触发 deploy（自动完成回填 + 嵌入 + 上线）  
**Step 5**：验证搜索"John Jumper"能返回 AI科技动态的文章条目  

---

## 6. 风险与边界

| 风险 | 说明 | 应对 |
|---|---|---|
| H3 解析遗漏章节 | 某些日报 H2 名称与预设不符 | Step 2 本地验证时检查各栏目覆盖率 |
| 首次嵌入耗时 | 2,250 条一次性嵌入，GitHub Actions 可能超时 | 检查现有超时配置，必要时分批 |
| 旧格式文件（表格格式） | 45 天内有些旧文件是表格而非 H3 | 解析时容错：H3 数量为 0 则跳过，不报错 |
| 右侧栏搜索框移动端不可见 | 首页 beforeBody 入口仍在 | 可接受，不影响主要用例 |
