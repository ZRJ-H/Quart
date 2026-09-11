# 自动知识库（Quartz + GitHub Pages）

这是一个会自动更新的中文知识库网站。Quartz 负责生成静态页面，GitHub Actions 每天采集内容并发布到 GitHub Pages；Cloudflare Worker 可选地提供 DeepSeek 流式问答。即使 Worker 没有配置或暂时不可用，页面也会自动切换到浏览器本地搜索。

## 架构

- `content/`：知识库 Markdown 内容。
- `crawlers/`：GitHub Trending、Hacker News、AI 新闻、时政和 arXiv 五类采集器，以及周报生成器。
- `scripts/build-wiki-index.py`：同时生成本地 SQLite、Worker 使用的完整 JSON 索引和浏览器使用的轻量 JSON 索引。
- `quartz/`：静态网站和搜索界面。
- `worker/`：Cloudflare Worker 搜索与 DeepSeek SSE 接口。
- `.github/workflows/deploy-pages.yml`：每日刷新、提交、构建和 GitHub Pages 发布。
- `server/`、`docker-compose.yml`：保留的本地或自托管运行方式；GitHub Pages 不依赖它们。

## 部署到 GitHub Pages

### 1. 推送仓库

工作流监听 `master` 和 `main`。如果本地仓库还没有远端，先在 GitHub 创建仓库，再执行：

```bash
git remote add origin https://github.com/FDogeLover/Quart.git
git push -u origin master
```

如果实际账户或仓库名不同，请替换上面的地址。工作流会自动推导 `账户名.github.io/仓库名`，无需修改源码。

### 2. 启用 Pages

在 GitHub 仓库的 **Settings → Pages → Build and deployment** 中，将 **Source** 设为 **GitHub Actions**。之后可在 **Actions → Refresh and deploy wiki → Run workflow** 手动执行首次发布。

工作流也会在每天北京时间 08:15 自动运行。周日额外生成周报；任意单个爬虫失败时，仍会使用其他来源和已有内容继续构建。

### 3. 配置 Cloudflare Worker（可选，但启用 AI 问答需要）

先编辑 `worker/wrangler.jsonc`：

- `SITE_ORIGIN`：浏览器 Origin，例如 `https://fdogelover.github.io`，不要带 `/Quart` 路径。
- `INDEX_URL`：Pages 上完整索引的 HTTPS 地址，例如 `https://fdogelover.github.io/Quart/wiki-index.json`。

然后部署：

```bash
cd worker
npm ci
npx wrangler login
npx wrangler secret put DEEPSEEK_API_KEY
npm run deploy
```

`DEEPSEEK_API_KEY` 只保存在 Cloudflare secret 中，不会进入网页或仓库。部署成功后记下 Worker 地址。

### 4. 连接网页与 Worker

在 GitHub 仓库的 **Settings → Secrets and variables → Actions → Variables** 新增：

- `AI_SEARCH_ENDPOINT`：完整端点，例如 `https://doge-wiki-search.example.workers.dev/api/search`。
- `SITE_DOMAIN`：可选。仅使用自定义域名时填写；普通项目 Pages 可不填。

如果希望 AI 新闻、时政、arXiv 爬虫使用 DeepSeek 摘要，再在 **Actions → Secrets** 新增 `DEEPSEEK_API_KEY`。这是可选项，和 Cloudflare secret 需要分别配置。

重新运行工作流后，页面会使用 Worker；变量为空或 Worker 请求失败时会自动使用静态搜索。

## 本地验证

```bash
npm ci
npm ci --prefix crawlers
npm ci --prefix worker
npm test
python -m unittest discover -s tests -v
npm --prefix worker test
npm run build:pages
npm run index:pages
```

构建产物位于 `public/`。可用任意静态文件服务器预览，例如：

```bash
python -m http.server 8080 -d public
```

访问 `http://localhost:8080/`。不设置 `AI_SEARCH_ENDPOINT` 时，本地预览直接使用静态搜索。

## 环境变量

复制 `.env.example` 后按需配置：

- `DEEPSEEK_API_KEY`：本地服务和爬虫的 DeepSeek 密钥。
- `SITE_DOMAIN`：Quartz 规范域名，不带 `https://`。
- `AI_SEARCH_ENDPOINT`：完整 Worker 搜索端点。
- `CONTENT_RETENTION_DAYS`：日报保留天数，默认 30。
- `REBUILD_INTERVAL_SECONDS`：Docker 本地自动重建间隔，默认 86400 秒。
- `GITHUB_TOKEN`：本地运行 GitHub 爬虫时可选；Actions 会自动提供。

不要提交 `.env`、`.dev.vars` 或任何真实密钥。
