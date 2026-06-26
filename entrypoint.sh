#!/bin/sh
set -e

echo "=== Wiki Quartz Builder ==="

# 首次启动：执行一次完整构建
echo "=== Initial build at $(date) ==="
echo ""

# 创建爬虫所需目录
mkdir -p /home/wiki/content/AI科技动态
mkdir -p /home/wiki/content/时政要闻
mkdir -p /home/wiki/content/GitHub-Trending
mkdir -p /home/wiki/content/AI论文日报
mkdir -p /home/wiki/content/Hacker-News
mkdir -p /home/wiki/content/周报

# 执行重建
/home/wiki/scripts/rebuild.sh || echo "WARN: Initial build had errors, continuing..."

echo ""
echo "=== Starting cron daemon ==="
exec crond -f -l 2
