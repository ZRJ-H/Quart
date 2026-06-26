#!/bin/sh
# Wiki 全量重建脚本
# 流程: 爬虫 → 清理旧内容 → 建索引 → Quartz构建 → 通知搜索服务重载
set -e

LOG_FILE="/var/log/wiki-rebuild.log"
CONTENT_DIR="/home/wiki/content"
SCRIPTS_DIR="/home/wiki/scripts"
CRAWLERS_DIR="/home/wiki/crawlers"
SERVER_PORT="${SERVER_PORT:-3000}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Wiki Rebuild Started ==="

# Step 1: 运行爬虫（如果存在）
if [ -d "$CRAWLERS_DIR" ]; then
    log "[1/5] Running crawlers..."
    cd "$CRAWLERS_DIR"

    # GitHub Trending & Hacker News (不需要 LLM, 先跑)
    if [ -f "github-trending.js" ]; then
        log "  - GitHub Trending..."
        node github-trending.js "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: GitHub Trending failed"
    fi
    if [ -f "hacker-news.js" ]; then
        log "  - Hacker News..."
        node hacker-news.js "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: Hacker News failed"
    fi

    # AI 动态 & 时政 & 论文 (需要 LLM, 后跑)
    if [ -f "ai-news.js" ]; then
        log "  - AI News..."
        node ai-news.js "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: AI News failed"
    fi
    if [ -f "current-affairs.js" ]; then
        log "  - Current Affairs..."
        node current-affairs.js "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: Current Affairs failed"
    fi
    if [ -f "arxiv-papers.js" ]; then
        log "  - arXiv Papers..."
        node arxiv-papers.js "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: arXiv Papers failed"
    fi
fi

# Step 2: 清理超过7天的旧内容
log "[2/5] Filtering old content..."
if [ -f "$SCRIPTS_DIR/filter-old-content.py" ]; then
    python3 "$SCRIPTS_DIR/filter-old-content.py" "$CONTENT_DIR" >> "$LOG_FILE" 2>&1 || log "  WARN: Filter failed"
fi

# Step 3: 构建 SQLite 搜索索引
log "[3/5] Building search index..."
python3 "$SCRIPTS_DIR/build-wiki-index.py" "$CONTENT_DIR" -o /home/wiki/server/wiki.db >> "$LOG_FILE" 2>&1 || log "  WARN: Index build failed"

# Step 4: Quartz 静态站点构建
log "[4/5] Building Quartz static site..."
cd /home/wiki
npx quartz build >> "$LOG_FILE" 2>&1 || log "  WARN: Quartz build failed"

# Step 5: 通知搜索服务热重载索引
log "[5/5] Reloading search server..."
curl -s -X POST "http://localhost:${SERVER_PORT}/api/reload" >> "$LOG_FILE" 2>&1 || log "  WARN: Server reload failed (server may not be running)"

log "=== Wiki Rebuild Completed ==="
