from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path


CATEGORIES = ("AI科技动态", "时政要闻", "AI论文日报", "Hacker News", "GitHub Trending")
HEADING = re.compile(r"^### \[([^]]+)]\((https?://[^)]+)\)", re.MULTILINE)


def generate_weekly_report(content_root: Path, run_date: date) -> Path:
    iso_year, iso_week, weekday = run_date.isocalendar()
    monday = run_date - timedelta(days=weekday - 1)
    sections: list[str] = []
    total = 0
    for category in CATEGORIES:
        notes: list[str] = []
        for offset in range((run_date - monday).days + 1):
            day = monday + timedelta(days=offset)
            path = content_root / category / f"{day.isoformat()}.md"
            if not path.exists():
                continue
            matches = HEADING.findall(path.read_text(encoding="utf-8", errors="replace"))
            total += len(matches)
            headlines = "\n".join(f"  - [{title}]({url})" for title, url in matches[:3])
            notes.append(f"- [[{category}/{day.isoformat()}]]\n{headlines}".rstrip())
        if notes:
            sections.append(f"## {category}\n\n" + "\n".join(notes))

    if not sections:
        raise ValueError("No daily notes are available for the requested ISO week")
    output = content_root / "周报" / f"{iso_year}-W{iso_week:02d}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    text = f"""---
created: {run_date.isoformat()}
tags: [周报, 趋势总结]
---

# {iso_year}-W{iso_week:02d} 知识周报

> 统计区间：{monday.isoformat()} 至 {run_date.isoformat()} · 汇总条目：{total} 条

{"\n\n".join(sections)}

## 本周说明

- 本页只汇总本周已采集日报，并保留日报与原始来源链接。
- 每周一自动生成完整上周报告；周内手动运行时生成截至当天的快照。
"""
    output.write_text(text, encoding="utf-8", newline="\n")
    return output
