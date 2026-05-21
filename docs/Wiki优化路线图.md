# Wiki 知识库优化路线图

## 当前架构

```
262 页 wiki (309KB JSON) → Cloudflare Worker (1MB 限制) → DeepSeek API
Quartz 网站 → GitHub Pages (7 天内容)
Worker 部署 → 手动脚本
```

---

## 一、Worker 容量扩展

**现状瓶颈**：Worker 脚本限制 1MB，当前 `wiki-data.json` 309KB/262 页。每页约 1.2KB，预计 **~800 页时**触及上限。

### 方案 1.1：KV 存储（推荐）

| 项目 | 说明 |
|------|------|
| 原理 | 将 `wiki-data.json` 存入 Cloudflare KV 而非 Worker 代码中 |
| 限制 | 免费层 1GB 存储，25MB/key |
| 改动 | Worker 从 `import wikiData` 改为 `env.WIKI_KV.get("index", "json")` |
| 成本 | 免费额度内零成本 |

```js
// 改造后
const data = await env.WIKI_KV.get("index", "json")
```

### 方案 1.2：分片索引

当 kv 单个 key 逼近 25MB 限制时，按 wiki 分类拆分：

```
WIKI_KV:
  wiki:entities    → 实体页 JSON
  wiki:concepts    → 概念页 JSON
  wiki:sources     → 来源页 JSON
  wiki:synthesis   → 综合分析 JSON

Worker 并行查询四个 key，合并结果。
```

### 方案 1.3：R2 对象存储

| 触发条件 | 说明 |
|----------|------|
| KV 25MB 不够 | 升级到 R2（10GB 免费） |
| 需要存更多信息 | 全文内容、embedding 向量一起存 |

---

## 二、检索质量升级

**现状瓶颈**：纯关键词匹配。随着页数增多，检索精度下降（噪音增加，匹配变弱）。

### 路线图

```
关键词检索            → 混合检索              → 语义检索
(当前)                (阶段 1)                (阶段 2)
```

### 阶段 1：加标签权重

在现有关键词匹配基础上增强：
- 标题匹配 +40 分（已有）
- 标签精确匹配 +20 分
- frontmatter type 匹配 +10 分
- category 匹配 +5 分

改动量极小，改 `worker/index.js` 的 `searchIndex` 函数。

### 阶段 2：向量语义检索

```
构建时                         查询时
wiki 页面                      用户问题
  │                              │
  ▼                              ▼
DeepSeek Embedding API         同一个 API 向量化
  │                              │
  ▼                              ▼
存储向量到 KV/Vectorize         余弦相似度匹配
                                 │
                                 ▼
                              Top 5 喂给 LLM
```

| 组件 | 服务 | 成本 |
|------|------|------|
| embedding | DeepSeek Embedding API | ¥0.0001/1K tokens |
| 向量存储 | Cloudflare Vectorize | 免费 5M 向量 |
| 检索计算 | Worker 内余弦相似度 | 零额外成本 |

### 阶段 3：HyDE 检索

> HyDE = Hypothetical Document Embeddings

用户提问时，先让 LLM 生成一个假设答案，用假设答案做向量检索而非直接搜原问题。检索精度提升显著，代价是每次查询多一次 LLM 调用。

---

## 三、成本控制

**现状**：每次搜索调用 DeepSeek Chat API（`deepseek-chat` 模型）。

| 项目 | 单价 |
|------|------|
| DeepSeek Chat 输入 | ¥0.001/1K tokens |
| DeepSeek Chat 输出 | ¥0.002/1K tokens |
| 单次查询估算 | ~¥0.005-0.01（3K 上下文 + 500 输出） |

### 优化手段

#### 3.1 缓存

```js
// 相同问题 24 小时内不重复调 API
const cacheKey = `cache:${hash(query)}`
const cached = await env.WIKI_KV.get(cacheKey)
if (cached) return cached
// ... call API ...
await env.WIKI_KV.put(cacheKey, result, { expirationTtl: 86400 })
```

#### 3.2 查询分类路由

| 查询类型 | 策略 | 模型 |
|----------|------|------|
| 简单事实查询（"Anthropic 估值多少"） | 直接检索，不调 LLM | 无 |
| 统计查询（"wiki 有多少实体"） | Worker 内计算 | 无 |
| 综合分析查询 | 调 LLM | deepseek-chat |

#### 3.3 上下文裁切

当前每个页面取 800 字。可以更精确：
- 标题匹配 >50% → 取 800 字
- 中等匹配 → 取 300 字  
- 弱匹配 → 只取标题+标签

#### 3.4 速率限制

防止恶意或异常高频调用：
```js
const ip = request.headers.get("CF-Connecting-IP")
const count = await env.RATE_LIMIT.get(ip) || 0
if (count > 50) return error // 每小时 50 次
```

---

## 四、网站内容扩展

**现状**：只显示 7 天内的动态内容，wiki 完全隐藏。

### 方向

| 功能 | 说明 | 难度 |
|------|------|------|
| **wiki 浏览页** | 精选 wiki 实体/概念页面公开可见 | 低 |
| **归档视图** | 按月份/标签查看历史动态 | 中 |
| **时间线视图** | 按时间轴浏览事件（Anthropic 融资、Google I/O 等） | 中 |
| **关系图谱** | 可视化实体间关联（类似 Obsidian Graph） | 高 |
| **RSS 多频道** | AI动态 / 时政 / GitHub 分别输出 RSS | 低 |

---

## 五、部署自动化

**现状**：Worker 手动部署，网站自动。

### 5.1 GitHub Actions 自动部署 Worker

需要换一个 **有 workflow scope 的 GitHub token**（Classic PAT 或 GitHub App token）。

部署后 `deploy.yaml` 可以加一步：
```yaml
- name: Deploy Worker
  run: |
    python3 scripts/build-wiki-index.py vault-content -o worker/wiki-data.json
    cd worker && npx wrangler deploy
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
```

### 5.2 触发器联动

```
Obsidian vault push → GitHub Actions → 
  ├─ 网站构建部署 (已有)
  └─ wiki 索引重建 + Worker 部署 (待加)
```

---

## 六、性能监控

### 建议添加的指标

| 指标 | 监控方式 |
|------|---------|
| Worker 冷启动时间 | Cloudflare Dashboard Analytics |
| 每次搜索耗时 | Worker 内 `console.log`，用 `wrangler tail` 查看 |
| API 调用量/费用 | DeepSeek Dashboard |
| 搜索结果点击率 | Worker 统计 + 前端打点 |
| 搜索无结果率 | 当检索到 0 个页面时打日志 |

---

## 七、优先级矩阵

| 优化项 | 触发条件 | 优先级 | 预计工作量 |
|--------|----------|--------|-----------|
| KV 存储 | wiki > 600 页 | 中 | 2h |
| 标签权重搜索 | wiki > 400 页 | 中 | 30min |
| 查询缓存 | 日搜索 > 50 次 | 高 | 1h |
| 向量检索 | wiki > 1000 页 | 低 | 4h |
| 速率限制 | 出现异常流量 | 高 | 30min |
| Worker 自动部署 | 每次手动部署烦了 | 中 | 问题在 token |
| RSS 多频道 | 用户想订阅 | 低 | 1h |
| wiki 公开浏览 | 想分享知识体系 | 低 | 1h |

---

## 附录：当前关键数字

| 指标 | 值 |
|------|-----|
| wiki 总页数 | 262 |
| 索引文件大小 | 309 KB |
| Worker 总上传 | 496 KB (gzip: 105 KB) |
| 1MB 限制剩余 | ~500 KB（约 400 页余量） |
| 网站日内容 | ~3 页/天 × 7 天 = 21 页 |
| Worker 冷启动 | <50ms |
| 单次搜索 DeepSeek 费用 | ~¥0.005-0.01 |
