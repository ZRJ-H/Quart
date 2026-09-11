from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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
    def load(source: FeedSource) -> tuple[list[Article], str]:
        try:
            return parse_feed(fetch_text(source.url), source.name), ""
        except Exception as error:
            return [], f"{source.name}: {error}"

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(sources)))) as executor:
        results = list(executor.map(load, sources))
    articles = [article for rows, _error in results for article in rows]
    errors = [error for _rows, error in results if error]
    if not articles:
        raise CollectionError("All configured feeds failed: " + "; ".join(errors))
    ordered = sorted(articles, key=lambda article: article.published_at, reverse=True)
    return select_recent(deduplicate(ordered), now, limit)

def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _arxiv_id(value: str) -> str:
    match = re.search(r"(?:/abs/|arXiv\.org:)([^/]+?)(?:v\d+)?$", value)
    return match.group(1) if match else value


def _normalize_arxiv(xml_text: str) -> list[Article]:
    root = ET.fromstring(xml_text)
    metadata: dict[str, dict[str, list[str]]] = {}
    for entry in [node for node in root.iter() if _local_name(node.tag) in {"entry", "item"}]:
        entry_id = ""
        entry_link = ""
        authors: list[str] = []
        categories: list[str] = []
        for child in entry:
            name = _local_name(child.tag)
            if name in {"id", "guid"}:
                entry_id = (child.text or "").strip()
            elif name == "link":
                entry_link = (child.attrib.get("href") or child.text or "").strip()
            elif name == "author":
                authors.extend("".join(node.itertext()).strip() for node in child if _local_name(node.tag) == "name")
            elif name == "creator" and (child.text or "").strip():
                authors.append((child.text or "").strip())
            elif name == "category":
                category = child.attrib.get("term") or (child.text or "").strip()
                if category:
                    categories.append(category)
        paper_id = _arxiv_id(entry_link or entry_id)
        metadata.setdefault(paper_id, {"authors": authors, "categories": categories})

    normalized: list[Article] = []
    for article in parse_feed(xml_text, "arXiv"):
        paper_id = _arxiv_id(article.url or article.id)
        normalized.append(replace(article, id=paper_id, extra=metadata.get(paper_id, {"authors": [], "categories": []})))
    return normalized


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
    api_url = f"https://export.arxiv.org/api/query?{params}"
    try:
        normalized = _normalize_arxiv(fetch_text(api_url))
        if not normalized:
            raise CollectionError("arXiv API returned no papers")
    except Exception as api_error:
        rss_urls = tuple(f"https://rss.arxiv.org/rss/{category}" for category in ("cs.AI", "cs.LG", "cs.CL"))

        def load_rss(url: str) -> tuple[list[Article], str]:
            try:
                return _normalize_arxiv(fetch_text(url)), ""
            except Exception as error:
                return [], f"{url}: {error}"

        with ThreadPoolExecutor(max_workers=len(rss_urls)) as executor:
            results = list(executor.map(load_rss, rss_urls))
        normalized = [paper for rows, _error in results for paper in rows]
        if not normalized:
            rss_errors = "; ".join(error for _rows, error in results if error)
            raise CollectionError(f"arXiv API and RSS feeds failed: {api_error}; {rss_errors}") from api_error

    ordered = sorted(normalized, key=lambda article: article.published_at, reverse=True)
    return select_recent(deduplicate(ordered), now, limit)

def collect_hacker_news(
    now: datetime,
    limit: int = 8,
    *,
    fetch_json: Callable[[str], Any] = default_fetch_json,
) -> list[Article]:
    base = "https://hacker-news.firebaseio.com/v0"
    story_ids = fetch_json(f"{base}/topstories.json")[: max(24, limit * 3)]

    def load_story(story_id: int) -> Article | None:
        item = fetch_json(f"{base}/item/{story_id}.json")
        if not isinstance(item, dict) or item.get("type") != "story" or item.get("dead") or item.get("deleted"):
            return None
        discussion_url = f"https://news.ycombinator.com/item?id={story_id}"
        try:
            return Article(
                str(story_id),
                clean_html(str(item.get("title") or "")),
                str(item.get("url") or discussion_url),
                "Hacker News",
                datetime.fromtimestamp(int(item.get("time") or 0), timezone.utc),
                clean_html(str(item.get("text") or item.get("title") or "")),
                score=int(item.get("score") or 0),
                comments=int(item.get("descendants") or 0),
                discussion_url=discussion_url,
                extra={"comment_ids": list(item.get("kids") or [])[:3]},
            )
        except (TypeError, ValueError, OverflowError):
            return None

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(story_ids)))) as executor:
        loaded = list(executor.map(load_story, story_ids))
    candidates = [article for article in loaded if article is not None]
    recent = select_recent(deduplicate(candidates), now, max(limit * 2, limit))
    selected = sorted(recent, key=lambda article: (article.score, article.comments), reverse=True)[:limit]

    def add_discussion(article: Article) -> Article:
        comments: list[str] = []
        for comment_id in article.extra.get("comment_ids", []):
            comment = fetch_json(f"{base}/item/{comment_id}.json")
            if isinstance(comment, dict) and not comment.get("dead") and not comment.get("deleted"):
                text = clean_html(str(comment.get("text") or ""))
                if text:
                    comments.append(text)
        return replace(article, extra={"top_comments": comments})

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(selected)))) as executor:
        return list(executor.map(add_discussion, selected))
