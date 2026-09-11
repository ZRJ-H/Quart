from __future__ import annotations

import json
import time
import urllib.request
from typing import Any


USER_AGENT = "OtaeKnowledgeBot/1.0 (+https://github.com/ZRJ-H/Quart)"


def fetch_text(url: str, *, timeout: int = 20, retries: int = 2) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml, application/rss+xml, text/xml;q=0.9, */*;q=0.5"})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise OSError(f"Failed to fetch {url} after {retries + 1} attempts") from last_error


def fetch_json(url: str, *, timeout: int = 20, retries: int = 2) -> Any:
    return json.loads(fetch_text(url, timeout=timeout, retries=retries))
