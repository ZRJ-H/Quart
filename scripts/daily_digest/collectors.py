from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode

from .feeds import clean_html, deduplicate, parse_feed, select_recent
from .http import fetch_json as default_fetch_json
from .http import fetch_text as default_fetch_text
from .models import Article
from .sources import FeedSource


class CollectionError(RuntimeError):
    pass


def collect_feed_category(
    sources: tuple[FeedSource, ...],
    now: datetime,
    limit: int,
    *,
    fetch_text: Callable[[str], str] = default_fetch_text,
) -> list[Article]:
    articles: list[Article] = []
    errors: list[str] = []
    for source in sources:
        try:
            articles.extend(parse_feed(fetch_text(source.url), source.name))
        except Exception as error:
            errors.append(f"{source.name}: {error}")
    if not articles:
        raise CollectionError("All configured feeds failed: " + "; ".join(errors))
    ordered = sorted(articles, key=lambda article: article.published_at, reverse=True)
    return select_recent(deduplicate(ordered), now, limit)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _arxiv_id(value: str) -> str:
    match = re.search(r"/abs/([^/]+?)(?:v\d+)?$", value)
    return match.group(1) if match else value


def collect_arxiv(
    now: datetime,
    limit: int = 5,
    *,
    fetch_text: Callable[[str], str] = default_fetch_text,
) -> list[Article]:
    params = urlencode(
        {
            "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
            "start": 0,
            "max_results": 50,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    xml_text = fetch_text(f"https://export.arxiv.org/api/query?{params}")
    root = ET.fromstring(xml_text)
    metadata: dict[str, dict[str, list[str]]] = {}
    for entry in [node for node in root if _local_name(node.tag) == "entry"]:
        entry_id = ""
        authors: list[str] = []
        categories: list[str] = []
        for child in entry:
            name = _local_name(child.tag)
            if name == "id":
                entry_id = _arxiv_id((child.text or "").strip())
            elif name == "author":
                authors.extend("".join(node.itertext()).strip() for node in child if _local_name(node.tag) == "name")
            elif name == "category" and child.attrib.get("term"):
                categories.append(child.attrib["term"])
        metadata.setdefault(entry_id, {"authors": authors, "categories": categories})

    normalized: list[Article] = []
    for article in parse_feed(xml_text, "arXiv"):
        paper_id = _arxiv_id(article.id)
        normalized.append(replace(article, id=paper_id, extra=metadata.get(paper_id, {"authors": [], "categories": []})))
    ordered = sorted(normalized, key=lambda article: article.published_at, reverse=True)
    return select_recent(deduplicate(ordered), now, limit)


def collect_hacker_news(
    now: datetime,
    limit: int = 8,
    *,
    fetch_json: Callable[[str], Any] = default_fetch_json,
) -> list[Article]:
    base = "https://hacker-news.firebaseio.com/v0"
    story_ids = fetch_json(f"{base}/topstories.json")
    articles: list[Article] = []
    for story_id in story_ids[: max(40, limit * 4)]:
        item = fetch_json(f"{base}/item/{story_id}.json")
        if not isinstance(item, dict) or item.get("type") != "story" or item.get("dead") or item.get("deleted"):
            continue
        discussion_url = f"https://news.ycombinator.com/item?id={story_id}"
        url = item.get("url") or discussion_url
        comment_texts: list[str] = []
        for comment_id in (item.get("kids") or [])[:3]:
            comment = fetch_json(f"{base}/item/{comment_id}.json")
            if isinstance(comment, dict) and not comment.get("dead") and not comment.get("deleted"):
                text = clean_html(str(comment.get("text") or ""))
                if text:
                    comment_texts.append(text)
        try:
            articles.append(
                Article(
                    str(story_id),
                    clean_html(str(item.get("title") or "")),
                    str(url),
                    "Hacker News",
                    datetime.fromtimestamp(int(item.get("time") or 0), timezone.utc),
                    clean_html(str(item.get("text") or item.get("title") or "")),
                    score=int(item.get("score") or 0),
                    comments=int(item.get("descendants") or 0),
                    discussion_url=discussion_url,
                    extra={"top_comments": comment_texts},
                )
            )
        except (TypeError, ValueError, OverflowError):
            continue
    recent = select_recent(deduplicate(articles), now, max(limit * 2, limit))
    return sorted(recent, key=lambda article: (article.score, article.comments), reverse=True)[:limit]
