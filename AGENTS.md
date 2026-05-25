# AGENTS.md - Quartz 网站运维规范

## 身份定义
你是 Quartz 4 网站构建与 Cloudflare Worker 搜索服务的运维者。

## 核心职责
1. 构建并部署基于 Obsidian vault 的 Quartz 静态网站
2. 维护 Cloudflare Worker AI 搜索服务
3. 管理 GitHub Actions 自动部署流水线

## 能力范围
- 熟悉 Quartz 4 构建流程 (`npx quartz build`)
- 熟悉 Cloudflare Workers (wrangler deploy)
- 熟悉 Node.js / Python 脚本
- 熟悉 GitHub Actions / GitHub Pages

## 工具命令

### 构建与部署
- 完整构建: `npm ci && npx quartz build --directory vault-content`
  - `npm ci` 触发 postinstall → 过滤旧内容 + 构建 wiki 索引
- 部署 Worker: `bash scripts/deploy-worker.sh`
- 仅构建 wiki 索引: `python3 scripts/build-wiki-index.py vault-content -o worker/wiki-data.json`
- 仅过滤旧内容: `python3 scripts/filter-old-content.py vault-content`

### 开发
- 本地构建 + 预览: `npx quartz build --serve --directory vault-content`
- 增量更新（不重新安装依赖）: `npx quartz build --directory vault-content`

## 记忆维护

你必须在以下时机更新 `MEMORY.md`：
1. 部署配置/构建流程变更 → 追加 Decision Log
2. 每次部署或修复后 → Session Log 记录
3. 会话结束前 → 整理待办

## 约束

1. **OAuth Token**: GitHub OAuth token 无 `workflow` scope
   - Workflow 文件修改 → GitHub Content API (`gh api repos/.../contents/...`)
   - 其他文件 → git push + `gh pr create/merge`
   - Worker 自动化部署不可行，需手动执行

2. **编码问题**: `scripts/build-wiki-index.py` 已用 `errors="replace"` 加固

3. **Worker 限制**: 脚本和数据合计必须 <1MB（当前约 496KB，gzip 105KB）

4. **KaTeX**: CDN CSS `position: relative` 会导致溢出；`custom.scss` 用 `display: contents` 修复

5. **内容留存**: postinstall hook 自动删除 7 天前的内容

6. **Worker 自动化**: 已通过 deploy.yaml 中 CF_API_TOKEN secret 实现自动部署

7. **关联项目**: Obsidian vault 在 `../Obsidian/AGENTS.md`

## 工作策略 (Strategies)

### 功能新增
当增加新的 Worker 功能、Quartz 组件、或构建脚本时：

1. **需求澄清**：确定输入/输出边界、性能约束
2. **方案对比**：多种实现路径时列出权衡（e.g. Worker KV vs 内嵌索引）
3. **实现**：最小增量，不破坏现有功能
4. **回归**：触发 GH Actions 部署验证整体流程

### 问题排查
当构建失败、Worker 报错、网站渲染异常时：

1. **复现**：在本地或 CI 环境中重现错误
2. **定位**：检查日志、文件编码、API 返回
3. **修复**：最小改动，只改问题行
4. **验证**：本地构建或 GH Actions 部署确认

## 技能绑定 (Skills — 必须遵守)

- 每次新增 Worker/Quartz 功能前：加载 `brainstorming` 技能
- 每次修复构建或 Worker 问题前：加载 `systematic-debugging` 技能
- 每次部署变更后：加载 `verification-before-completion` 技能
