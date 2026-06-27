#!/usr/bin/env python3
"""从URL采集文章原始内容，保存到 raw/articles/。

用法:
  python3 article-save.py <URL>                        # 抓取指定URL
  python3 article-save.py <URL1> <URL2> <URL3> ...    # 批量采集多个URL
  python3 article-save.py <URL> --stdin               # 从stdin读取正文内容

依赖: requests, beautifulsoup4
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from common import date_format, http_get, read_raw, safe_slug, setup_logging, write_wiki_page

log = logging.getLogger(__name__)

VAULT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(VAULT, "raw", "articles")
TODAY = date_format()

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def extract_meta(soup: BeautifulSoup, url: str) -> tuple[str, str, str, str]:
    """从 HTML 中提取标题、发布日期、作者与域名。

    Args:
        soup: 解析后的页面。
        url: 原始 URL。

    Returns:
        ``(title, pub_date, author, domain)`` 元组。
    """
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    # Try og:title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    # Try h1
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    pub_date = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content", "")
        if name == "date" or prop == "article:published_time":
            pub_date = content[:10]
            break
    # Try time tag
    if not pub_date:
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            pub_date = time_tag["datetime"][:10]

    author = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        content = meta.get("content", "")
        if name == "author":
            author = content
            break

    domain = urlparse(url).netloc
    return title, pub_date, author, domain


def dedent_text(text: str) -> str:
    """规整文本：去除每行首尾空白，折叠连续空行，去掉尾部空行。

    Args:
        text: 原始文本。

    Returns:
        规整后的文本。
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.append(stripped)
        else:
            if result and result[-1] != "":
                result.append("")
    while result and result[-1] == "":
        result.pop()
    return "\n".join(result)


def extract_content(soup: BeautifulSoup) -> str:
    """从页面正文提取 markdown 文本。

    Args:
        soup: 解析后的页面。

    Returns:
        提取并规整后的正文 markdown。
    """
    body = soup.find("body")
    if not body:
        return ""

    for tag in body.find_all(["script", "style", "nav", "footer", "aside", "noscript", "iframe", "svg"]):
        tag.decompose()

    parts = []
    for el in body.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "blockquote", "hr", "br",
                             "div.entry-content", "article", "main", ".post-content", ".article-body"]):
        if isinstance(el, Tag):
            tag = el.name.lower()
            text = el.get_text(separator="\n", strip=True)
            if not text or len(text) < 20:
                continue

            if tag.startswith("h"):
                level = tag[1]
                parts.append(f"\n{'#' * int(level)} {text}\n")
            elif tag == "p":
                parts.append(f"{text}\n")
            elif tag == "li":
                parts.append(f"- {text}")
            elif tag == "pre":
                parts.append(f"```\n{text}\n```\n")
            elif tag == "blockquote":
                parts.append(f"> {text}\n")
            elif tag == "hr":
                parts.append("---\n")
            elif tag == "br":
                parts.append("")

    if not parts:
        for el in body.find_all(["p", "h1", "h2", "h3", "h4"]):
            text = el.get_text(separator="\n", strip=True)
            tag = el.name.lower()
            if not text:
                continue
            if tag.startswith("h"):
                level = tag[1]
                parts.append(f"\n{'#' * int(level)} {text}\n")
            else:
                parts.append(f"{text}\n")

    return dedent_text("\n".join(parts))


def build_page(
    url: str,
    title: str,
    pub_date: str,
    author: str,
    domain: str,
    content: str,
    stdin_content: Optional[str] = None,
) -> tuple[dict[str, Any], str]:
    """构建来源页的 frontmatter 与正文。

    Args:
        url: 原始 URL。
        title: 文章标题。
        pub_date: 发布日期。
        author: 作者。
        domain: 域名。
        content: 正文内容。
        stdin_content: 若提供，则覆盖 ``content``。

    Returns:
        ``(frontmatter, content)`` 元组。
    """
    if stdin_content:
        content = stdin_content

    frontmatter = {
        "type": "source",
        "title": f'"{title}"',
        "source_type": "article",
        "url": url,
        "date_accessed": TODAY,
        "date_published": pub_date or "?",
        "tags": ["article", domain],
    }

    body = f"""# {title}

## 基本信息
- **URL**: {url}
- **域名**: {domain}
- **作者**: {author or "?"}
- **发布日期**: {pub_date or "?"}
- **采集日期**: {TODAY}

## 正文
{content[:80000]}
"""
    return frontmatter, body


def fetch_url(url: str) -> str:
    """抓取 URL 的 HTML 文本。

    Args:
        url: 目标 URL。

    Returns:
        响应 HTML 文本。
    """
    return http_get(url, headers={"User-Agent": USER_AGENT})


def process_url(url: str, use_stdin: bool = False) -> tuple[bool, str]:
    """处理单个URL，返回 (success, url) 元组。

    Args:
        url: 目标 URL。
        use_stdin: 是否从 stdin 读取正文而非抓取页面。

    Returns:
        ``(是否成功, url)`` 元组。
    """
    try:
        slug = safe_slug(url)
        out_path = os.path.join(RAW_DIR, f"{slug}.md")

        if use_stdin:
            stdin_content = sys.stdin.read()
            title = url
            pub_date = TODAY
            author = ""
            domain = urlparse(url).netloc
            content = stdin_content
        else:
            log.info(f"Fetching {url}...")
            html = fetch_url(url)
            soup = BeautifulSoup(html, "html.parser")
            title, pub_date, author, domain = extract_meta(soup, url)
            content = extract_content(soup)
            log.info(f"  Title: {title}")
            log.info(f"  Date: {pub_date or '?'}")
            log.info(f"  Author: {author or '?'}")
            log.info(f"  Content: ~{len(content)} chars")

        frontmatter, body = build_page(url, title, pub_date, author, domain, content)
        write_wiki_page(out_path, frontmatter, body)

        kb = len(read_raw(out_path)) / 1024
        log.info(f"Saved: {out_path} ({kb:.0f} KB)")
        return True, url
    except Exception as e:
        log.error(f"ERROR: {url}: {e}")
        return False, url


def main() -> None:
    """脚本入口：解析参数并批量处理 URL。"""
    setup_logging()
    if len(sys.argv) < 2:
        log.error(f"Usage: python3 {sys.argv[0]} <URL> [<URL2> ...] [--stdin]")
        sys.exit(1)

    args = [a for a in sys.argv[1:] if a != "--stdin"]
    use_stdin = "--stdin" in sys.argv

    if not args:
        log.error(f"Usage: python3 {sys.argv[0]} <URL> [<URL2> ...] [--stdin]")
        sys.exit(1)

    urls = args
    total = len(urls)
    success = 0
    failed = 0

    for i, url in enumerate(urls):
        if total > 1:
            log.info(f"\n[{i+1}/{total}] {url}")
        ok, _ = process_url(url, use_stdin=use_stdin)
        if ok:
            success += 1
        else:
            failed += 1
        if total > 1 and i < total - 1:
            log.info("---")

    if total > 1:
        log.info(f"\n=== Done: {success} succeeded, {failed} failed, {total} total ===")
    else:
        log.info("Done.")


if __name__ == "__main__":
    main()
