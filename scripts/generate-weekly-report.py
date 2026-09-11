#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from daily_digest.weekly import generate_weekly_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a weekly report from daily notes")
    parser.add_argument("--content-root", type=Path, default=Path("content"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    print(f"Generated {generate_weekly_report(args.content_root, args.date)}")


if __name__ == "__main__":
    main()
