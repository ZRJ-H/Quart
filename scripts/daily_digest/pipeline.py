from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping
from zoneinfo import ZoneInfo

from .collectors import CollectionError
from .models import Article
from .render import render_digest
from .summarize import DigestSummary


LIMITS = {"AI科技动态": 8, "时政要闻": 8, "AI论文日报": 5, "Hacker News": 8}
MINIMUMS = {"AI科技动态": 3, "时政要闻": 3, "AI论文日报": 3, "Hacker News": 5}
SUMMARY_SCHEMA_VERSION = 7


def _github_error(title: str, detail: str) -> None:
    escaped = str(detail).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title={title}::{escaped}", flush=True)


def _github_warning(title: str, detail: str) -> None:
    escaped = str(detail).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::warning title={title}::{escaped}", flush=True)


def _article_dict(article: Article) -> dict:
    value = asdict(article)
    value["published_at"] = article.published_at.isoformat()
    return value


def _fingerprint(articles: list[Article]) -> str:
    payload = {"summary_schema_version": SUMMARY_SCHEMA_VERSION, "articles": [_article_dict(article) for article in articles]}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cache_path(raw_dir: Path, category: str) -> Path:
    return raw_dir / f"{category.replace(' ', '-')}.json"


def _load_cached_articles(raw_dir: Path | None, category: str, now: datetime) -> list[Article]:
    if raw_dir is None:
        return []
    try:
        payload = json.loads(_cache_path(raw_dir, category).read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(str(payload["cached_at"]))
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        age = now.astimezone(timezone.utc) - cached_at.astimezone(timezone.utc)
        if age < timedelta(0) or age > timedelta(days=7):
            return []
        return [
            Article(
                id=str(item["id"]),
                title=str(item["title"]),
                url=str(item["url"]),
                source=str(item["source"]),
                published_at=datetime.fromisoformat(str(item["published_at"])),
                summary=str(item.get("summary") or item["title"]),
                score=int(item.get("score") or 0),
                comments=int(item.get("comments") or 0),
                discussion_url=str(item.get("discussion_url") or ""),
                extra=item.get("extra") if isinstance(item.get("extra"), dict) else {},
            )
            for item in payload["articles"]
            if isinstance(item, dict)
        ]
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return []


def run_pipeline(
    content_root: Path,
    run_date: date,
    collectors: Mapping[str, Callable[[datetime], list[Article]]],
    summarizer: Callable[[str, list[Article]], DigestSummary],
    raw_dir: Path | None = None,
) -> list[Path]:
    missing = set(LIMITS) - set(collectors)
    if missing:
        raise CollectionError("Missing collectors: " + ", ".join(sorted(missing)))
    shanghai = ZoneInfo("Asia/Shanghai")
    local_today = datetime.now(shanghai).date()
    now = datetime.now(shanghai) if run_date == local_today else datetime.combine(run_date, time(23, 59), shanghai)

    collected: dict[str, list[Article]] = {}
    fresh_categories: set[str] = set()
    for category in LIMITS:
        print(f"Collecting {category}...", flush=True)
        try:
            rows = collectors[category](now)[: LIMITS[category]]
            print(f"Collected {category}: {len(rows)} items", flush=True)
            if len(rows) < MINIMUMS[category]:
                raise CollectionError(f"{category} returned {len(rows)} items; minimum is {MINIMUMS[category]}")
            fresh_categories.add(category)
        except Exception as error:
            cached = _load_cached_articles(raw_dir, category, now)[: LIMITS[category]]
            if len(cached) < MINIMUMS[category]:
                _github_error("Daily collection failed", str(error))
                raise
            rows = [replace(article, source=f"{article.source}（最近成功缓存）") for article in cached]
            _github_warning("Using cached daily sources", f"{category}: {error}")
        collected[category] = rows

    if raw_dir:
        raw_dir.mkdir(parents=True, exist_ok=True)
        for category in fresh_categories:
            rows = collected[category]
            _cache_path(raw_dir, category).write_text(
                json.dumps(
                    {"cached_at": now.isoformat(), "articles": [_article_dict(article) for article in rows]},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    content_root.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for category, rows in collected.items():
        fingerprint = _fingerprint(rows)
        target = content_root / category / f"{run_date.isoformat()}.md"
        marker = f"<!-- source-fingerprint: {fingerprint} -->"
        existing_text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
        if marker in existing_text:
            outputs[category] = existing_text
            continue
        try:
            digest = summarizer(category, rows)
        except Exception as error:
            _github_error("Daily summarization failed", f"{category}: {error}")
            raise
        outputs[category] = render_digest(category, run_date, rows, digest).rstrip() + f"\n\n{marker}\n"

    written: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="daily-digest-", dir=content_root) as directory:
        staging = Path(directory)
        for category, text in outputs.items():
            staged = staging / category / f"{run_date.isoformat()}.md"
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(text, encoding="utf-8", newline="\n")
        for category in LIMITS:
            staged = staging / category / f"{run_date.isoformat()}.md"
            target = content_root / category / staged.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != staged.read_bytes():
                os.replace(staged, target)
            written.append(target)
    return written
