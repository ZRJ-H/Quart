#!/usr/bin/env python3
"""从 raw/bilibili/ 增量生成 wiki/sources/ 来源页（只处理新增文件）。"""

from __future__ import annotations

import glob
import logging
import os
import re

from common import date_format, extract_frontmatter, read_raw, setup_logging, write_wiki_page

log = logging.getLogger(__name__)

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "bilibili")
SRC_DIR = os.path.join(VAULT, "wiki", "sources")
INDEX_PATH = os.path.join(VAULT, "wiki", "index.md")
LOG_PATH = os.path.join(VAULT, "wiki", "log.md")

SKIP_PATTERNS = [
    re.compile(r"^(本周|世界周刊|大家|观众朋友|各位|欢迎)"),
    re.compile(r"^\d+$"),
    re.compile(r"^[A-Za-z\s\.']+$"),
]

TODAY = date_format()


def extract_subtitle_blocks(text: str) -> list[str]:
    """提取「字幕稿」小节中第一个语言块的文本行。

    Args:
        text: 原始 markdown 文本。

    Returns:
        第一个字幕块的文本行列表；无字幕时返回空列表。
    """
    lines = text.split("\n")
    in_subtitle = False
    blocks = []
    current: list[str] = []
    for line in lines:
        if line.startswith("## 字幕稿"):
            in_subtitle = True
            continue
        if in_subtitle:
            if line.startswith("## ") and "弹幕" in line:
                break
            if line.startswith("### "):
                if current:
                    blocks.append(current)
                current = []
                continue
            stripped = line.strip()
            if stripped and not stripped.startswith("-"):
                current.append(stripped)
    if current:
        blocks.append(current)
    return blocks[0] if blocks else []


def extract_meta_block(text: str) -> str:
    """提取「基本信息」小节的整段文本。

    Args:
        text: 原始 markdown 文本。

    Returns:
        基本信息小节文本；未找到时返回空字符串。
    """
    m = re.search(r"## 基本信息\n(.*?)(?=\n## )", text, re.DOTALL)
    if not m:
        return ""
    return m.group(0)


def extract_short_name(title: str) -> str:
    """从标题生成简短的文件名片段。

    Args:
        title: 视频标题。

    Returns:
        去除特殊字符（含中文弯引号）并截断后的短名。
    """
    name = re.sub(r"【世界周刊】", "", title).strip()
    # 移除所有类型的引号（含中文弯引号）
    name = re.sub(r'["""\'\'“”「」《》]', '', name)
    name = name.replace(" ", "").replace("?", "").replace("？", "").replace(":", "").replace("：", "").replace("丨", "-").replace("|", "-")
    if len(name) > 24:
        name = name[:24]
    return name


def generate_summary(blocks: list[str]) -> str:
    """从字幕块生成摘要。

    Args:
        blocks: 字幕文本行列表。

    Returns:
        过滤后拼接的摘要文本。
    """
    if not blocks:
        return "无字幕"
    filtered = []
    for b in blocks:
        if len(b) < 10:
            continue
        if any(p.search(b) for p in SKIP_PATTERNS):
            continue
        filtered.append(b)
    if not filtered:
        return "无有效字幕摘要"
    parts = filtered[:5]
    lines = []
    for p in parts:
        lines.append(p[:300])
    return "\n\n".join(lines)


def build_source_page(raw_path: str) -> tuple[str, str, str, str]:
    """从单个原始文件生成来源页内容（不写盘）。

    Args:
        raw_path: raw/bilibili 下的原始文件路径。

    Returns:
        ``(filename, page, title, date_str)`` 元组。
    """
    text = read_raw(raw_path)

    fm = extract_frontmatter(text)
    title = fm.get("title", os.path.basename(raw_path).replace(".md", ""))
    pubdate = fm.get("date_published", "?")
    url = fm.get("url", "")
    bvid = os.path.basename(raw_path).replace(".md", "")

    date_str = pubdate[:10] if len(pubdate) >= 10 else pubdate

    # 判断是否为世界周刊
    is_world_weekly = "世界周刊" in title
    short = extract_short_name(title)

    if is_world_weekly:
        filename = f"世界周刊-{date_str}-{short}.md"
        tags = ["世界周刊", "央视新闻", "时政"]
    else:
        # 非世界周刊视频，使用标题作为文件名
        filename = f"{date_str}-{short}.md"
        tags = ["视频", "B站"]

    safe_name = filename.replace(".md", "").replace(":", "").replace("/", "-")

    blocks = extract_subtitle_blocks(text)
    summary = generate_summary(blocks)
    meta = extract_meta_block(text)
    meta_fields = {}
    for line in meta.split("\n"):
        for m in re.finditer(r"\*\*(.+?)\*\*:\s*(\S+)", line):
            meta_fields[m.group(1)] = m.group(2)

    up = meta_fields.get("UP主", "央视新闻")
    up = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', up)
    duration = meta_fields.get("时长", "?")
    views = meta_fields.get("播放量", "?")
    danmaku = meta_fields.get("弹幕", "?")
    comments = meta_fields.get("评论", "?")
    favorites = meta_fields.get("收藏", "?")
    likes = meta_fields.get("点赞", "?")

    frontmatter = f"""type: source
title: "{title}"
source_type: bilibili-世界周刊
url: {url}
date_accessed: {TODAY}
date_published: {pubdate}
tags: {tags}"""
    body = f"""# {title}

## 基本信息
- BV号: {bvid} | UP主: {up}
- 时长: {duration} | 播放: {views}
- 弹幕: {danmaku} | 评论: {comments} | 收藏: {favorites} | 点赞: {likes}

## 摘要
{summary}

## 关键要点
> ⚠ 待后续AI摄取完善

## 相关实体
> ⚠ 待后续AI摄取完善

## 相关概念
> ⚠ 待后续AI摄取完善

## 相关来源
- 原始视频: {url}
- 完整字幕稿: [[{bvid}]]

## 个人思考
> ⚠ 待后续AI摄取完善"""
    return filename, frontmatter, body, title, date_str


def main() -> None:
    """脚本入口：仅为新增原始文件创建来源页并更新索引与日志。"""
    setup_logging()
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.md")))
    if not raw_files:
        log.info("No raw files found")
        return

    # 检查哪些来源页已存在
    existing_sources = set()
    for f in os.listdir(SRC_DIR):
        if f.endswith(".md"):
            existing_sources.add(f)

    new_files = []
    for raw_path in raw_files:
        filename, frontmatter, body, title, date_str = build_source_page(raw_path)
        if filename not in existing_sources:
            new_files.append((raw_path, filename, frontmatter, body, title, date_str))

    if not new_files:
        log.info("没有新增的来源页需要创建")
        return

    log.info(f"找到 {len(new_files)} 个新增文件")

    # 创建新的来源页
    for raw_path, filename, frontmatter, body, title, date_str in new_files:
        out_path = os.path.join(SRC_DIR, filename)
        write_wiki_page(out_path, frontmatter, body)
        log.info(f"  创建: {filename}")

    # 更新 index.md
    index = read_raw(INDEX_PATH)

    updated = False
    for _, filename, _, _, title, date_str in new_files:
        entry = f"| {title} | 视频 | {date_str} | [[{filename[:-3]}]] |"
        if entry not in index:
            # 找到来源部分的最后
            lines = index.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('## 综合分析'):
                    lines.insert(i, entry)
                    index = '\n'.join(lines)
                    updated = True
                    break

    if updated:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(index)
        log.info("Updated index.md")

    # 更新 log.md
    log_text = read_raw(LOG_PATH)

    for raw_path, filename, _, title, date_str in new_files:
        bvid = os.path.basename(raw_path).replace(".md", "")
        entry = f"""

## [{TODAY}] B站视频采集 | {title}
- 采集来源: B站 (bilibili.com)
- 视频标题: {title}
- 保存位置: raw/bilibili/{bvid}.md
- 来源摘要页: wiki/sources/{filename}
- 概念页更新: 待检查"""
        log_text = log_text.replace("# Wiki 操作日志", "# Wiki 操作日志" + entry)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(log_text)
    log.info("Updated log.md")

    log.info(f"\nDone: {len(new_files)} new source pages created")


if __name__ == "__main__":
    main()
