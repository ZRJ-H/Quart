from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Callable, Mapping
from zoneinfo import ZoneInfo

from .collectors import CollectionError
from .models import Article
from .render import render_digest
from .summarize import DigestSummary


LIMITS = {"AI科技动态": 8, "时政要闻": 8, "AI论文日报": 5, "Hacker News": 8}
MINIMUMS = {"AI科技动态": 3, "时政要闻": 3, "AI论文日报": 3, "Hacker News": 5}
SUMMARY_SCHEMA_VERSION = 4


def _article_dict(article: Article) -> dict:
    value = asdict(article)
    value["published_at"] = article.published_at.isoformat()
    return value


def _fingerprint(articles: list[Article]) -> str:
    payload = {"summary_schema_version": SUMMARY_SCHEMA_VERSION, "articles": [_article_dict(article) for article in articles]}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    for category in LIMITS:
        print(f"Collecting {category}...", flush=True)
        rows = collectors[category](now)[: LIMITS[category]]
        print(f"Collected {category}: {len(rows)} items", flush=True)
        if len(rows) < MINIMUMS[category]:
            raise CollectionError(f"{category} returned {len(rows)} items; minimum is {MINIMUMS[category]}")
        collected[category] = rows

    if raw_dir:
        raw_dir.mkdir(parents=True, exist_ok=True)
        for category, rows in collected.items():
            safe_name = category.replace(" ", "-")
            (raw_dir / f"{safe_name}.json").write_text(
                json.dumps([_article_dict(article) for article in rows], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    content_root.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for category, rows in collected.items():
        fingerprint = _fingerprint(rows)
        target = content_root / category / f"{run_date.isoformat()}.md"
        marker = f"<!-- source-fingerprint: {fingerprint} -->"
        if target.exists() and marker in target.read_text(encoding="utf-8", errors="replace"):
            outputs[category] = target.read_text(encoding="utf-8", errors="replace")
            continue
        digest = summarizer(category, rows)
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
