#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from daily_digest.collectors import collect_arxiv, collect_feed_category, collect_hacker_news, collect_news_category
from daily_digest.pipeline import run_pipeline
from daily_digest.sources import AI_SOURCES, DOMESTIC_NEWS_SOURCES, INTERNATIONAL_NEWS_SOURCES
from daily_digest.summarize import summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Otae daily knowledge notes")
    parser.add_argument("--content-root", type=Path, default=Path("content"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--no-model", action="store_true")
    parser.add_argument("--require-model", action="store_true")
    args = parser.parse_args()
    collectors = {
        "AI科技动态": lambda now: collect_feed_category(AI_SOURCES, now, 8, minimum=3),
        "时政要闻": lambda now: collect_news_category(
            DOMESTIC_NEWS_SOURCES,
            INTERNATIONAL_NEWS_SOURCES,
            now,
            limit=8,
            domestic_minimum=5,
        ),
        "AI论文日报": lambda now: collect_arxiv(now, 5, minimum=3),
        "Hacker News": lambda now: collect_hacker_news(now, 8),
    }
    if args.no_model and args.require_model:
        parser.error("--no-model and --require-model cannot be used together")
    deepseek_key = None if args.no_model else os.environ.get("DEEPSEEK_API_KEY")
    go_key = None if args.no_model else os.environ.get("GO_API_KEY")
    paths = run_pipeline(
        args.content_root,
        args.date,
        collectors,
        lambda category, rows: summarize(
            category,
            rows,
            deepseek_key,
            go_key,
            require_model=args.require_model,
        ),
        args.raw_dir,
    )
    for path in paths:
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
