from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str
    score: int = 0
    comments: int = 0
    discussion_url: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Article URL must use HTTP or HTTPS")
        if self.discussion_url:
            discussion = urlparse(self.discussion_url)
            if discussion.scheme not in {"http", "https"} or not discussion.netloc:
                raise ValueError("Discussion URL must use HTTP or HTTPS")
        if not self.title.strip():
            raise ValueError("Article title must not be empty")
        if not self.source.strip():
            raise ValueError("Article source must not be empty")
        if self.published_at.tzinfo is None:
            object.__setattr__(self, "published_at", self.published_at.replace(tzinfo=timezone.utc))
