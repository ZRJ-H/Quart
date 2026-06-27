#!/usr/bin/env python3
"""从 raw/bilibili/ 批量生成 wiki/sources/ 来源页。"""

from __future__ import annotations

import glob
import logging
import os
import re
from typing import Any

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
        去除特殊字符并截断后的短名。
    """
    name = re.sub(r"【世界周刊】", "", title).strip()
    name = re.sub(r"[「」“”\"'《》]", "", name)
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


def build_source_page(raw_path: str) -> dict[str, Any]:
    """从单个原始文件生成来源页并写入磁盘。

    Args:
        raw_path: raw/bilibili 下的原始文件路径。

    Returns:
        含 ``filename`` / ``title`` / ``date`` / ``out_path`` 的字典。
    """
    text = read_raw(raw_path)

    fm = extract_frontmatter(text)
    title = fm.get("title", os.path.basename(raw_path).replace(".md", ""))
    pubdate = fm.get("date_published", "?")
    url = fm.get("url", "")
    bvid = os.path.basename(raw_path).replace(".md", "")

    date_str = pubdate[:10] if len(pubdate) >= 10 else pubdate
    short = extract_short_name(title)
    filename = f"世界周刊-{date_str}-{short}.md"
    safe_name = filename.replace(".md", "").replace(":", "").replace("/", "-")

    blocks = extract_subtitle_blocks(text)
    summary = generate_summary(blocks)
    meta = extract_meta_block(text)

    tags = ["世界周刊", "央视新闻", "时政"]
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

    if not short:
        short = bvid
        filename = f"世界周刊-{date_str}-{bvid}.md"

    out_path = os.path.join(SRC_DIR, filename)
    write_wiki_page(out_path, frontmatter, body)

    return {
        "filename": filename,
        "title": title,
        "date": date_str,
        "out_path": out_path,
    }


def update_index(entries: list[dict[str, Any]]) -> None:
    """将来源页条目写入 wiki/index.md 的「B站世界周刊」小节。

    Args:
        entries: ``build_source_page`` 返回的条目列表。
    """
    idx = read_raw(INDEX_PATH)

    header = "\n## B站世界周刊\n\n| 来源 | 类型 | 日期 | 链接 |\n|------|------|------|------|\n"
    rows = []
    for e in sorted(entries, key=lambda x: x["date"], reverse=True):
        name = e["filename"].replace(".md", "")
        rows.append(f"| {e['title']} | bilibili-世界周刊 | {e['date']} | [[{name}]] |")

    block = header + "\n".join(rows) + "\n"

    if "## B站世界周刊" in idx:
        idx = re.sub(r"## B站世界周刊.*?(?=\n## |\n---|\Z)", block.rstrip(), idx, flags=re.DOTALL)
    else:
        marker = "## 综合分析"
        if marker in idx:
            idx = idx.replace(marker, block + "\n" + marker)
        else:
            idx = idx.rstrip() + "\n" + block

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(idx)


def update_log(entries: list[dict[str, Any]]) -> None:
    """向 wiki/log.md 追加一条批量建源记录。

    Args:
        entries: ``build_source_page`` 返回的条目列表。
    """
    log_text = read_raw(LOG_PATH)

    count = len(entries)
    dates = sorted(set(e["date"] for e in entries))
    entry = f"""## [{TODAY}] 世界周刊批量建源 | B站央视新闻 33期

- 操作类型: 批量新建来源页
- 来源渠道: B站 央视新闻「世界周刊」
- 覆盖时间: {dates[0]} 至 {dates[-1]}
- 新建来源页: {count} 个
- 更新 index.md 索引

"""

    if log_text.startswith("# Wiki 操作日志"):
        log_text = log_text.replace("# Wiki 操作日志\n\n", "# Wiki 操作日志\n\n" + entry[:-2] + "\n---\n\n")
    else:
        log_text = entry + "\n" + log_text

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(log_text)


def main() -> None:
    """脚本入口：全量重建 B站来源页并更新索引与日志。"""
    setup_logging()
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "BV*.md")))
    if not raw_files:
        log.error("ERROR: No raw/bilibili/BV*.md files found")
        return

    os.makedirs(SRC_DIR, exist_ok=True)
    log.info(f"Found {len(raw_files)} raw files")

    entries = []
    for rf in raw_files:
        e = build_source_page(rf)
        entries.append(e)
        log.info(f"  {e['date']} | {e['title'][:50]} | -> {e['filename']}")

    update_index(entries)
    log.info(f"\nUpdated {INDEX_PATH}")

    update_log(entries)
    log.info(f"Updated {LOG_PATH}")

    total_kb = sum(len(read_raw(e["out_path"])) for e in entries) / 1024
    log.info(f"\nDone: {len(entries)} source pages ({total_kb:.0f} KB)")


if __name__ == "__main__":
    main()
