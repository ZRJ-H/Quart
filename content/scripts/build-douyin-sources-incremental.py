#!/usr/bin/env python3
"""从 raw/douyin/ 增量生成 wiki/sources/ 来源页（只处理新增文件）。"""

from __future__ import annotations

import glob
import logging
import os
import re

from common import date_format, extract_frontmatter, read_raw, setup_logging, write_wiki_page

log = logging.getLogger(__name__)

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "douyin")
SRC_DIR = os.path.join(VAULT, "wiki", "sources")
INDEX_PATH = os.path.join(VAULT, "wiki", "index.md")
LOG_PATH = os.path.join(VAULT, "wiki", "log.md")

TODAY = date_format()


def extract_short_name(title: str) -> str:
    """从标题生成简短的文件名片段。

    Args:
        title: 视频标题。

    Returns:
        去除特殊字符并截断后的短名。
    """
    # 移除特殊字符
    name = re.sub(r'["""\'\'「」《》]', '', title)
    name = name.replace(" ", "").replace("?", "").replace("？", "").replace(":", "").replace("：", "")
    if len(name) > 24:
        name = name[:24]
    return name


def build_source_page(raw_path: str) -> tuple[str, str, str]:
    """从单个原始文件生成来源页内容（不写盘）。

    Args:
        raw_path: raw/douyin 下的原始文件路径。

    Returns:
        ``(filename, page, title)`` 元组。
    """
    text = read_raw(raw_path)

    fm = extract_frontmatter(text)
    title = fm.get("title", os.path.basename(raw_path).replace(".md", ""))
    url = fm.get("url", "")
    video_id = os.path.basename(raw_path).replace(".md", "").replace("douyin-", "")

    short = extract_short_name(title)
    filename = f"抖音-{TODAY}-{short}.md"

    # 提取描述内容
    lines = text.split("\n")
    description = []
    in_desc = False
    for line in lines:
        if line.startswith("## 描述"):
            in_desc = True
            continue
        if in_desc:
            if line.startswith("## "):
                break
            if line.strip():
                description.append(line.strip())

    summary = "\n\n".join(description[:3]) if description else "无描述"

    frontmatter = f"""type: source
title: "{title}"
source_type: douyin
url: {url}
date_accessed: {TODAY}
tags: ['抖音', '视频']"""
    body = f"""# {title}

## 基本信息
- 视频ID: {video_id} | 来源: 抖音

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

## 个人思考
> ⚠ 待后续AI摄取完善"""
    return filename, frontmatter, body, title


def main() -> None:
    """脚本入口：仅为新增原始文件创建来源页并更新日志。"""
    setup_logging()
    # 创建目录
    os.makedirs(RAW_DIR, exist_ok=True)

    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.md")))
    if not raw_files:
        log.info("没有找到原始文件")
        return

    # 检查哪些来源页已存在
    existing_sources = set()
    for f in os.listdir(SRC_DIR):
        if f.endswith(".md"):
            existing_sources.add(f)

    new_files = []
    for raw_path in raw_files:
        filename, frontmatter, body, title = build_source_page(raw_path)
        if filename not in existing_sources:
            new_files.append((raw_path, filename, frontmatter, body, title))

    if not new_files:
        log.info("没有新增的来源页需要创建")
        return

    log.info(f"找到 {len(new_files)} 个新增文件")

    # 创建新的来源页
    for raw_path, filename, frontmatter, body, title in new_files:
        out_path = os.path.join(SRC_DIR, filename)
        write_wiki_page(out_path, frontmatter, body)
        log.info(f"  创建: {filename}")

    # 更新 log.md
    log_text = read_raw(LOG_PATH)

    for raw_path, filename, frontmatter, body, title in new_files:
        video_id = os.path.basename(raw_path).replace(".md", "").replace("douyin-", "")
        entry = f"""

## [{TODAY}] 抖音视频采集 | {title}
- 采集来源: 抖音 (douyin.com)
- 视频标题: {title}
- 保存位置: raw/douyin/douyin-{video_id}.md
- 来源摘要页: wiki/sources/{filename}
- 概念页更新: 待检查"""
        log_text = log_text.replace("# Wiki 操作日志", "# Wiki 操作日志" + entry)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(log_text)
    log.info("已更新 log.md")

    log.info(f"\n完成: {len(new_files)} 个新来源页已创建")


if __name__ == "__main__":
    main()
