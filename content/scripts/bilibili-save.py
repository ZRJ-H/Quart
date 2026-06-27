#!/usr/bin/env python3
"""采集 B站视频信息并保存为 wiki 归档格式。

用法:
  python3 bilibili-save.py <bilibili-url-or-BV号>

输出: raw/bilibili/{BV号}.md
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime
from typing import Any, Optional

from common import date_format, setup_logging, write_wiki_page

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}

API_VIEW = "https://api.bilibili.com/x/web-interface/view"
API_SUBTITLE = "https://api.bilibili.com/x/player/wbi/v2"
API_DANMAKU = "https://api.bilibili.com/x/v1/dm/list.so"
API_COMMENTS = "https://api.bilibili.com/x/v2/reply"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raw", "bilibili")


def sessdata() -> str:
    """获取 B站登录态 SESSDATA。

    优先读环境变量，其次回退到 opencode 配置文件；均缺失则报错退出。

    Returns:
        SESSDATA 字符串。
    """
    v = os.environ.get("SESSDATA")
    if v:
        return v
    config = os.path.expanduser("~/.config/opencode/opencode.json")
    try:
        with open(config) as f:
            d = json.load(f)
            return d["mcp"]["bilibili"]["environment"]["SESSDATA"]
    except Exception:
        pass
    log.error("ERROR: SESSDATA not found in env or opencode.json")
    sys.exit(1)


def request(
    url: str,
    params: Optional[dict[str, Any]] = None,
    need_auth: bool = False,
) -> bytes:
    """发起 B站 API 请求并返回原始字节（处理 deflate 压缩）。

    Args:
        url: 请求 URL。
        params: 查询参数。
        need_auth: 是否附带 SESSDATA Cookie。

    Returns:
        响应原始字节。
    """
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=dict(HEADERS))
    if need_auth:
        req.add_header("Cookie", f"SESSDATA={sessdata()}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "deflate":
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        return raw


def extract_bvid(input_str: str) -> Optional[str]:
    """从输入字符串或短链中提取 BV 号。

    Args:
        input_str: URL、短链或直接的 BV 号。

    Returns:
        BV 号；无法提取时返回 ``None``。
    """
    m = re.search(r"BV[a-zA-Z0-9_]+", input_str)
    if m:
        return m.group(0)
    if "b23.tv" in input_str:
        req = urllib.request.Request(
            input_str, headers=dict(HEADERS), method="HEAD"
        )
        final = urllib.request.urlopen(req).geturl()
        m = re.search(r"BV[a-zA-Z0-9_]+", final)
        if m:
            return m.group(0)
    return None


def get_metadata(bvid: str) -> dict[str, Any]:
    """获取视频元数据。

    Args:
        bvid: BV 号。

    Returns:
        归一化后的元数据字典。

    Raises:
        Exception: 当 API 返回非 0 错误码时。
    """
    data = json.loads(request(API_VIEW, {"bvid": bvid}))
    if data["code"] != 0:
        raise Exception(f"API error: {data}")
    d = data["data"]
    owner = d.get("owner", {})
    stat = d.get("stat", {})
    dur = d.get("duration", 0)
    pub = datetime.fromtimestamp(d.get("pubdate", 0))
    return {
        "title": d.get("title", ""),
        "bvid": d.get("bvid", bvid),
        "aid": d.get("aid"),
        "cid": d.get("cid"),
        "owner_name": owner.get("name", ""),
        "owner_uid": owner.get("mid", ""),
        "view": stat.get("view", 0),
        "danmaku_count": stat.get("danmaku", 0),
        "reply_count": stat.get("reply", 0),
        "favorite": stat.get("favorite", 0),
        "like": stat.get("like", 0),
        "coin": stat.get("coin", 0),
        "share": stat.get("share", 0),
        "duration": dur,
        "duration_str": f"{dur // 60}:{dur % 60:02d}",
        "pubdate": pub.strftime("%Y-%m-%d %H:%M:%S"),
        "pubdate_ts": d.get("pubdate", 0),
        "desc": d.get("desc", ""),
        "copyright": "自制" if d.get("copyright") == 1 else "转载",
        "pic": d.get("pic", ""),
        "videos": d.get("videos", 1),
    }


def get_subtitles(aid: Optional[int], cid: Optional[int]) -> list[dict[str, Any]]:
    """获取视频字幕（按语言）。

    Args:
        aid: 视频 aid。
        cid: 视频 cid。

    Returns:
        字幕列表，每项含 ``lan`` 与 ``content``。
    """
    data = json.loads(request(API_SUBTITLE, {"aid": aid, "cid": cid}, need_auth=True))
    if data.get("code") != 0:
        return []
    subs = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
    results = []
    for s in subs:
        url = s.get("subtitle_url", "")
        if url.startswith("//"):
            url = f"https:{url}"
        if not url:
            continue
        try:
            content = json.loads(request(url, need_auth=True))
            body = [item.get("content", "") for item in content.get("body", [])]
            results.append({"lan": s.get("lan", ""), "content": body})
        except Exception:
            pass
    return results


def get_danmaku(cid: Optional[int]) -> list[str]:
    """获取弹幕列表。

    Args:
        cid: 视频 cid。

    Returns:
        弹幕文本列表。
    """
    raw = request(API_DANMAKU, {"oid": cid}, need_auth=True)
    text = raw.decode("utf-8", errors="replace")
    root = ET.fromstring(text)
    return [d.text or "" for d in root.findall("d")]


def get_comments(aid: Optional[int]) -> list[dict[str, Any]]:
    """获取热门评论。

    Args:
        aid: 视频 aid。

    Returns:
        评论列表，每项含 ``user`` / ``content`` / ``likes``。
    """
    data = json.loads(
        request(API_COMMENTS, {"type": 1, "oid": aid, "sort": 2}, need_auth=True)
    )
    if data.get("code") != 0:
        return []
    replies = data.get("data", {}).get("replies", [])
    return [
        {
            "user": r.get("member", {}).get("uname", ""),
            "content": r.get("content", {}).get("message", ""),
            "likes": r.get("like", 0),
        }
        for r in replies
    ]


def save_markdown(
    meta: dict[str, Any],
    subtitles: list[dict[str, Any]],
    danmaku: list[str],
    comments: list[dict[str, Any]],
) -> str:
    """将采集结果写入 raw/bilibili/{BV号}.md。

    Args:
        meta: 视频元数据。
        subtitles: 字幕列表。
        danmaku: 弹幕列表。
        comments: 热门评论列表。

    Returns:
        写入的文件路径。
    """
    bvid = meta["bvid"]
    path = os.path.join(OUTPUT_DIR, f"{bvid}.md")

    frontmatter = {
        "type": "source",
        "title": f"\"{meta['title']}\"",
        "source_type": "bilibili",
        "url": f"\"https://www.bilibili.com/video/{bvid}\"",
        "date_accessed": date_format(),
        "date_published": meta["pubdate"],
        "tags": ["bilibili", meta.get("owner_name", "")],
    }

    lines: list[str] = []
    lines.append(f"# {meta['title']}")
    lines.append("")
    lines.append("## 基本信息")
    lines.append(f"- **BV号**: {bvid}")
    lines.append(f"- **UP主**: [{meta['owner_name']}](https://space.bilibili.com/{meta['owner_uid']})")
    lines.append(f"- **时长**: {meta['duration_str']}")
    lines.append(f"- **发布时间**: {meta['pubdate']}")
    lines.append(f"- **播放量**: {meta['view']:,}")
    lines.append(f"- **弹幕**: {meta['danmaku_count']:,} | **评论**: {meta['reply_count']:,}")
    lines.append(f"- **收藏**: {meta['favorite']:,} | **点赞**: {meta['like']:,} | **投币**: {meta['coin']:,} | **分享**: {meta['share']:,}")
    lines.append(f"- **版权**: {meta['copyright']}")
    if meta["desc"]:
        lines.append(f"- **简介**: {meta['desc']}")
    lines.append("")
    lines.append("## 字幕稿")
    lines.append("")
    if subtitles:
        for sub in subtitles:
            lines.append(f"### {sub['lan']}")
            lines.append("")
            for line in sub["content"]:
                lines.append(line)
                lines.append("")
    else:
        lines.append("无字幕")
        lines.append("")
    lines.append("")
    lines.append("## 弹幕")
    lines.append("")
    for dm in danmaku[:200]:
        dm_clean = dm.strip()
        if dm_clean and len(dm_clean) < 200:
            lines.append(f"- {dm_clean}")
    if len(danmaku) > 200:
        lines.append(f"- ... (共 {len(danmaku)} 条弹幕)")
    lines.append("")
    lines.append("## 热门评论")
    lines.append("")
    if comments:
        lines.append("| 用户 | 评论 | 点赞 |")
        lines.append("|------|------|------|")
        for c in comments:
            content = c["content"].replace("\n", " ").replace("|", "\\|")
            lines.append(f"| {c['user']} | {content[:120]} | {c['likes']} |")
    else:
        lines.append("无热门评论")
    lines.append("")

    write_wiki_page(path, frontmatter, "\n".join(lines))

    size = os.path.getsize(path)
    log.info(f"Saved: {path} ({size:,} bytes)")
    return path


def main() -> None:
    """脚本入口：解析参数、采集并保存。"""
    setup_logging()
    if len(sys.argv) < 2:
        log.error(f"Usage: {sys.argv[0]} <bilibili-url-or-BV号>")
        sys.exit(1)

    input_str = sys.argv[1]
    bvid = extract_bvid(input_str)
    if not bvid:
        log.error(f"ERROR: Cannot extract BV号 from: {input_str}")
        sys.exit(1)

    log.info(f"BV号: {bvid}")

    meta = get_metadata(bvid)
    log.info(f"标题: {meta['title']}")
    log.info(f"UP主: {meta['owner_name']} | 播放: {meta['view']:,} | {meta['pubdate']}")

    subtitles = get_subtitles(meta["aid"], meta["cid"])
    log.info(f"字幕: {len(subtitles)} 种语言")

    danmaku = get_danmaku(meta["cid"])
    log.info(f"弹幕: {len(danmaku)} 条")

    comments = get_comments(meta["aid"])
    log.info(f"评论: {len(comments)} 条热门")

    path = save_markdown(meta, subtitles, danmaku, comments)
    log.info(f"Done: {path}")


if __name__ == "__main__":
    main()
