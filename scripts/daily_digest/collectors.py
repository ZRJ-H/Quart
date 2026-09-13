from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urlencode

from .feeds import clean_html, deduplicate, parse_feed, select_recent
from .http import fetch_json as default_fetch_json
from .http import fetch_text as default_fetch_text
from .models import Article
from .sources import FeedSource


class CollectionError(RuntimeError):
    pass


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.description = ""
        self.paragraphs: list[str] = []
        self._paragraph_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "p":
            self._paragraph_parts = []
            return
        if tag.casefold() != "meta" or self.description:
            return
        values = {key.casefold(): value or "" for key, value in attrs}
        name = (values.get("name") or values.get("property") or "").casefold()
        if name in {"description", "og:description"}:
            self.description = clean_html(values.get("content", ""))

    def handle_data(self, data: str) -> None:
        if self._paragraph_parts is not None:
            self._paragraph_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "p" or self._paragraph_parts is None:
            return
        paragraph = clean_html(" ".join(self._paragraph_parts))
        if len(paragraph) >= 20:
            self.paragraphs.append(paragraph)
        self._paragraph_parts = None


def collect_xinhua_politics(
    source: FeedSource,
    now: datetime,
    limit: int = 8,
    *,
    minimum: int | None = None,
    fetch_text: Callable[[str], str] = default_fetch_text,
) -> list[Article]:
    listing = fetch_text(source.url)
    link_pattern = re.compile(
        r"<a\b[^>]*\bhref\s*=\s*(['\"])(https?://www\.news\.cn/(?:politics/)?(\d{8})/[^'\"]+/c\.html)\1[^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    candidates: list[Article] = []
    for match in link_pattern.finditer(listing):
        url, raw_date, raw_title = match.group(2), match.group(3), match.group(4)
        title = clean_html(raw_title)
        if not title:
            continue
        try:
            published = datetime.strptime(raw_date, "%Y%m%d").replace(tzinfo=timezone.utc)
            candidates.append(Article(url, title, url, source.name, published, title))
        except ValueError:
            continue

    recent = select_recent(deduplicate(candidates), now, max(limit * 2, limit), minimum=minimum)

    def add_description(article: Article) -> Article:
        try:
            parser = _MetadataParser()
            parser.feed(fetch_text(article.url))
            title_key = re.sub(r"\W+", "", article.title)
            description_key = re.sub(r"\W+", "", parser.description)
            evidence = []
            if parser.description and len(description_key) > len(title_key) + 10:
                evidence.append(parser.description)
            evidence.extend(parser.paragraphs)
            summary = clean_html(" ".join(dict.fromkeys(evidence)))[:1600] or article.title
            return replace(article, summary=summary)
        except Exception:
            return article

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(recent)))) as executor:
        return list(executor.map(add_description, recent[:limit]))


def collect_feed_category(
    sources: tuple[FeedSource, ...],
    now: datetime,
    limit: int,
    *,
    minimum: int | None = None,
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
    return select_recent(deduplicate(ordered), now, limit, minimum=minimum)


def collect_news_category(
    domestic_sources: tuple[FeedSource, ...],
    international_sources: tuple[FeedSource, ...],
    now: datetime,
    limit: int = 8,
    domestic_minimum: int = 5,
    *,
    fetch_text: Callable[[str], str] = default_fetch_text,
) -> list[Article]:
    if not 0 <= domestic_minimum <= limit:
        raise ValueError("domestic_minimum must be between zero and limit")

    domestic: list[Article] = []
    feed_sources = tuple(source for source in domestic_sources if source.kind == "feed")
    if feed_sources:
        domestic.extend(
            collect_feed_category(feed_sources, now, limit, minimum=domestic_minimum, fetch_text=fetch_text)
        )
    for source in domestic_sources:
        if source.kind == "xinhua-politics":
            domestic.extend(
                collect_xinhua_politics(source, now, limit, minimum=domestic_minimum, fetch_text=fetch_text)
            )
        elif source.kind != "feed":
            raise ValueError(f"Unsupported domestic news source kind: {source.kind}")
    domestic = select_recent(deduplicate(domestic), now, limit, minimum=domestic_minimum)
    if len(domestic) < domestic_minimum:
        raise CollectionError(
            f"Domestic official news returned {len(domestic)} items; minimum is {domestic_minimum}"
        )

    international_limit = limit - domestic_minimum
    try:
        international = collect_feed_category(
            international_sources,
            now,
            international_limit,
            fetch_text=fetch_text,
        )
    except CollectionError:
        international = []

    selected = domestic[:domestic_minimum] + international[:international_limit]
    if len(selected) < limit:
        selected.extend(domestic[domestic_minimum : domestic_minimum + limit - len(selected)])
    return selected[:limit]


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
                candidate_link = (child.attrib.get("href") or child.text or "").strip()
                if child.attrib.get("rel", "alternate") == "alternate" or not entry_link:
                    entry_link = candidate_link
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


def _normalize_hugging_face_papers(json_text: str) -> list[Article]:
    payload = json.loads(json_text)
    if not isinstance(payload, list):
        raise ValueError("Hugging Face daily papers response must be a list")
    normalized: list[Article] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        paper = row.get("paper")
        if not isinstance(paper, dict):
            continue
        paper_id = str(paper.get("id") or "").strip()
        title = clean_html(str(paper.get("title") or row.get("title") or ""))
        summary = clean_html(str(paper.get("summary") or row.get("summary") or ""))
        surfaced_at = str(
            paper.get("submittedOnDailyAt")
            or row.get("submittedOnDailyAt")
            or row.get("publishedAt")
            or paper.get("publishedAt")
            or ""
        ).strip()
        if not paper_id or not title or not surfaced_at:
            continue
        try:
            published_at = datetime.fromisoformat(surfaced_at.replace("Z", "+00:00"))
            authors = [
                clean_html(str(author.get("name") or ""))
                for author in paper.get("authors", [])
                if isinstance(author, dict) and author.get("name")
            ]
            score = int(row.get("upvotes") or paper.get("upvotes") or 0)
            normalized.append(
                Article(
                    paper_id,
                    title,
                    f"https://arxiv.org/abs/{paper_id}",
                    "Hugging Face Daily Papers / arXiv",
                    published_at,
                    summary or title,
                    score=score,
                    extra={"authors": authors, "categories": []},
                )
            )
        except (TypeError, ValueError, OverflowError):
            continue
    return normalized


def collect_arxiv(
    now: datetime,
    limit: int = 5,
    *,
    minimum: int | None = None,
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
            backup_params = urlencode({"date": now.date().isoformat(), "limit": max(20, limit * 4)})
            backup_url = f"https://huggingface.co/api/daily_papers?{backup_params}"
            try:
                normalized = _normalize_hugging_face_papers(fetch_text(backup_url))
                if not normalized:
                    raise CollectionError("Hugging Face daily papers returned no papers")
            except Exception as backup_error:
                raise CollectionError(
                    f"arXiv API and RSS feeds failed: {api_error}; {rss_errors}; "
                    f"Hugging Face backup failed: {backup_error}"
                ) from api_error

    ordered = sorted(normalized, key=lambda article: article.published_at, reverse=True)
    return select_recent(deduplicate(ordered), now, limit, minimum=minimum)

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
