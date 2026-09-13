from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Article


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_html(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(html.unescape(value or ""))
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _text(element: ET.Element, *names: str) -> str:
    for name in names:
        matches = _children(element, name)
        if matches:
            return "".join(matches[0].itertext()).strip()
    return ""


def _parse_datetime(value: str) -> datetime:
    value = value.strip()
    if not value:
        return datetime.fromtimestamp(0, timezone.utc)
    try:
        result = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _atom_link(entry: ET.Element) -> str:
    links = _children(entry, "link")
    for link in links:
        if link.attrib.get("rel", "alternate") == "alternate" and link.attrib.get("href"):
            return link.attrib["href"].strip()
    return links[0].attrib.get("href", "").strip() if links else ""


def parse_feed(xml_text: str, source: str) -> list[Article]:
    root = ET.fromstring(xml_text)
    is_atom = _local_name(root.tag) == "feed"
    entries = [node for node in root.iter() if _local_name(node.tag) == ("entry" if is_atom else "item")]
    articles: list[Article] = []
    for entry in entries:
        title = clean_html(_text(entry, "title"))
        url = _atom_link(entry) if is_atom else _text(entry, "link")
        article_id = _text(entry, "id", "guid") or url
        published = _text(entry, "published", "updated", "pubDate", "date")
        summary = clean_html(_text(entry, "summary", "description", "content", "encoded"))
        if not title or not url or not published:
            continue
        try:
            articles.append(Article(article_id, title, url, source, _parse_datetime(published), summary))
        except (ValueError, OverflowError):
            continue
    return articles


def _normalized_url(value: str) -> str:
    parts = urlsplit(value)
    query = urlencode([(key, val) for key, val in parse_qsl(parts.query) if not key.lower().startswith("utm_")])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def deduplicate(articles: list[Article]) -> list[Article]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    result: list[Article] = []
    for article in articles:
        url_key = _normalized_url(article.url)
        title_key = re.sub(r"\W+", "", article.title).casefold()
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        result.append(article)
    return result


def select_recent(
    articles: list[Article],
    now: datetime,
    limit: int,
    window_hours: int = 48,
    *,
    minimum: int | None = None,
    fallback_window_hours: tuple[int, ...] = (72, 168),
) -> list[Article]:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    utc_now = now.astimezone(timezone.utc)

    def select(window: int) -> list[Article]:
        cutoff = utc_now - timedelta(hours=window)
        recent = [article for article in articles if cutoff <= article.published_at.astimezone(timezone.utc) <= utc_now]
        return sorted(recent, key=lambda article: article.published_at, reverse=True)[:limit]

    selected = select(window_hours)
    if minimum is None or len(selected) >= minimum:
        return selected
    for fallback_window in fallback_window_hours:
        if fallback_window <= window_hours:
            continue
        selected = select(fallback_window)
        if len(selected) >= minimum:
            break
    return selected
