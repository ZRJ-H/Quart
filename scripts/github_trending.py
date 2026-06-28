#!/usr/bin/env python3
"""
Fetch GitHub Trending-like repository data with the GitHub Search API.

This script intentionally uses only the Python standard library so it can run
inside GitHub Actions without extra setup.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}
LANGUAGES = ["", "python", "javascript", "typescript", "go", "rust", "java"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def github_search(query: str, per_page: int, token: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(per_page, 100),
        }
    )
    req = urllib.request.Request(
        f"https://api.github.com/search/repositories?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "otae-wiki-trending/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read()).get("items", [])
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[WARN] GitHub API HTTP {exc.code}: {body[:240]}", file=sys.stderr)
    except Exception as exc:
        print(f"[WARN] GitHub API error: {exc}", file=sys.stderr)
    return []


def fetch_trending(period: str, limit: int, language: str, token: str) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=PERIOD_DAYS[period])).strftime(
        "%Y-%m-%d"
    )
    seen: set[str] = set()
    repos: list[dict] = []

    languages = [language] if language else LANGUAGES
    for lang in languages:
        if len(repos) >= limit * 2:
            break
        lang_filter = f" language:{lang}" if lang else ""
        min_stars = 10 if lang else 50
        query = f"pushed:>={since} stars:>={min_stars}{lang_filter}"
        for item in github_search(query, per_page=limit * 2, token=token):
            name = item.get("full_name")
            if name and name not in seen:
                seen.add(name)
                repos.append(item)

    repos.sort(key=lambda repo: repo.get("stargazers_count", 0), reverse=True)
    return repos[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub trending repositories")
    parser.add_argument("--period", choices=PERIOD_DAYS.keys(), default="daily")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--language", default="")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--output", default="", help="Write JSON output to this file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    print(f"[INFO] Fetching GitHub trending: {args.period}", file=sys.stderr)
    repos = fetch_trending(args.period, args.limit, args.language, args.token)
    if not repos:
        print("[ERROR] No repositories fetched", file=sys.stderr)
        sys.exit(1)

    output = [
        {
            "rank": index,
            "name": repo["full_name"],
            "url": repo["html_url"],
            "description": repo.get("description") or "",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language") or "",
            "topics": repo.get("topics", []),
        }
        for index, repo in enumerate(repos, 1)
    ]

    if args.json:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fp:
                json.dump(output, fp, ensure_ascii=False, indent=2)
        else:
            json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    else:
        for repo in output:
            print(f"#{repo['rank']} {repo['name']} {repo['stars']} stars")


if __name__ == "__main__":
    main()
