#!/usr/bin/env python3
"""从YouTube视频提取元数据和字幕，保存为wiki原始文件。

用法:
  python3 youtube-save.py <YouTube-URL或视频ID>

输出: raw/youtube/{视频ID}.md
依赖: yt-dlp (需安装)
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from typing import Any, Union

from common import date_format, read_raw, setup_logging, write_wiki_page

log = logging.getLogger(__name__)

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "youtube")
TODAY = date_format()


def extract_id(url: str) -> str:
    """从 URL 或纯视频 ID 中提取 YouTube 视频 ID。

    Args:
        url: YouTube 链接、Shorts 链接、短链或 11 位视频 ID。

    Returns:
        视频 ID；无法匹配时返回去除空白后的原输入。
    """
    # Pure ID
    if re.match(r'^[A-Za-z0-9_-]{11}$', url.strip()):
        return url.strip()
    # Standard URL
    m = re.search(r'youtube\.com/watch\?v=([A-Za-z0-9_-]+)', url)
    if m:
        return m.group(1)
    # Shorts URL
    m = re.search(r'youtube\.com/shorts/([A-Za-z0-9_-]+)', url)
    if m:
        return m.group(1)
    # Short link
    m = re.search(r'youtu\.be/([A-Za-z0-9_-]+)', url)
    if m:
        return m.group(1)
    return url.strip()


def fmt_seconds(secs: Union[int, float]) -> str:
    """将秒数格式化为 ``H:MM:SS`` 或 ``M:SS``。

    Args:
        secs: 秒数。

    Returns:
        格式化后的时长字符串。
    """
    h, r = divmod(int(secs), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def run_ytdlp(*args: str) -> subprocess.CompletedProcess[str]:
    """调用 yt-dlp 子进程，失败时退出。

    Args:
        *args: 传给 yt-dlp 的参数。

    Returns:
        已完成的子进程对象。
    """
    result = subprocess.run(
        ["yt-dlp", "--quiet"] + list(args),
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        log.error(f"ERROR: yt-dlp failed: {result.stderr[:300]}")
        sys.exit(1)
    return result


def get_metadata(video_id: str) -> dict[str, Any]:
    """通过 yt-dlp 获取视频元数据 JSON。

    Args:
        video_id: 视频 ID。

    Returns:
        yt-dlp 导出的元数据字典。
    """
    result = run_ytdlp("--dump-json", f"https://www.youtube.com/watch?v={video_id}")
    return json.loads(result.stdout)


def get_transcript(video_id: str) -> str:
    """下载并解析英文自动字幕。

    Args:
        video_id: 视频 ID。

    Returns:
        逐行拼接的字幕文本；无字幕时返回空字符串。
    """
    run_ytdlp(
        "--write-auto-subs", "--sub-langs", "en",
        "--sub-format", "json3", "--skip-download",
        "-o", os.path.join(RAW_DIR, f"{video_id}.%(ext)s"),
        f"https://www.youtube.com/watch?v={video_id}",
    )
    json3_path = os.path.join(RAW_DIR, f"{video_id}.en.json3")
    if not os.path.exists(json3_path):
        return ""
    try:
        with open(json3_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return ""
    lines = []
    for event in data.get("events", []):
        segs = event.get("segs", [])
        text = "".join(s.get("utf8", "") for s in segs)
        if text.strip():
            lines.append(text.strip())
    os.remove(json3_path)
    return "\n".join(lines)


def format_duration(secs: Any) -> str:
    """格式化时长，非数值时原样转字符串。

    Args:
        secs: 时长秒数或其他值。

    Returns:
        时长字符串。
    """
    if isinstance(secs, (int, float)):
        return fmt_seconds(secs)
    return str(secs)


def build_page(meta: dict[str, Any], transcript: str, video_id: str) -> tuple[dict[str, Any], str]:
    """构建来源页的 frontmatter 与正文。

    Args:
        meta: 视频元数据。
        transcript: 字幕文本。
        video_id: 视频 ID。

    Returns:
        ``(frontmatter, content)`` 元组。
    """
    title = meta.get("title", video_id)
    channel = meta.get("channel", "?")
    duration = format_duration(meta.get("duration", 0))
    views = meta.get("view_count", 0)
    likes = meta.get("like_count", 0)
    upload = meta.get("upload_date", "?")
    pubdate = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) >= 8 else "?"
    subscribers = meta.get("channel_follower_count", 0)
    desc = (meta.get("description") or "")[:2000]

    # Get available languages
    auto_caps = meta.get("automatic_captions", {})
    sub_langs = sorted(auto_caps.keys()) if auto_caps else []
    sub_info = ", ".join(sub_langs[:20]) if sub_langs else "无"

    frontmatter = {
        "type": "source",
        "title": f'"{title}"',
        "source_type": "youtube",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "date_accessed": TODAY,
        "date_published": pubdate,
        "tags": ["youtube", channel],
    }

    content = f"""# {title}

## 基本信息
- **视频ID**: {video_id} | **频道**: [{channel}](https://www.youtube.com/channel/{meta.get('channel_id', '')})
- **时长**: {duration} | **播放**: {views:,}
- **点赞**: {likes:,} | **订阅**: {subscribers:,}
- **发布时间**: {pubdate}
- **可用字幕语言**: {sub_info}

## 简介
{desc[:1500]}

## 字幕稿
{transcript[:50000]}
"""
    return frontmatter, content


def main() -> None:
    """脚本入口：解析参数、采集并保存。"""
    setup_logging()
    if len(sys.argv) < 2:
        log.error(f"Usage: python3 {sys.argv[0]} <YouTube-URL or VIDEO_ID>")
        sys.exit(1)

    video_id = extract_id(sys.argv[1])
    os.makedirs(RAW_DIR, exist_ok=True)

    log.info(f"Fetching metadata for {video_id}...")
    meta = get_metadata(video_id)
    title = meta.get("title", video_id)
    channel = meta.get("channel", "?")
    log.info(f"  Title: {title}")
    log.info(f"  Channel: {channel} | Views: {meta.get('view_count', 0):,}")

    log.info("Downloading transcript...")
    transcript = get_transcript(video_id)
    lines = transcript.count("\n") + 1 if transcript else 0
    log.info(f"  Transcript: {lines} lines")

    frontmatter, content = build_page(meta, transcript, video_id)

    out_path = os.path.join(RAW_DIR, f"{video_id}.md")
    write_wiki_page(out_path, frontmatter, content)

    kb = len(read_raw(out_path)) / 1024
    log.info(f"Saved: {out_path} ({kb:.0f} KB)")
    log.info(f"Done: {video_id}")


if __name__ == "__main__":
    main()
