from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path


CATEGORIES = ("AI科技动态", "时政要闻", "AI论文日报", "Hacker News", "GitHub Trending")
ITEM_BLOCK = re.compile(
    r"^### \[([^]]+)]\((https?://[^)]+)\)\s*\n(.*?)(?=^### |\Z)",
    re.MULTILINE | re.DOTALL,
)
SUMMARY_FIELD = re.compile(
    r"^- \*\*(核心摘要|研究问题|背景|影响|后续观察|方法思路|关键结果|实验结果|局限性|工程价值|价值点)\*\*：(.+)$",
    re.MULTILINE,
)
BLOCKQUOTE = re.compile(r"^> (?!来源：)(.+)$", re.MULTILINE)


def _excerpt(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _compose_summary(fields: list[tuple[str, str]]) -> str:
    values = dict(fields)
    primary = values.get("核心摘要") or values.get("研究问题") or ""
    secondary = ""
    secondary_label = ""
    for field, label in (
        ("影响", "影响"),
        ("关键结果", "结果"),
        ("实验结果", "结果"),
        ("工程价值", "价值"),
        ("价值点", "价值"),
    ):
        if values.get(field):
            secondary = values[field]
            secondary_label = label
            break
    if primary and secondary:
        return f"{_excerpt(primary)} {secondary_label}：{_excerpt(secondary)}"
    return _excerpt(primary or secondary)


def _daily_items(text: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for title, url, body in ITEM_BLOCK.findall(text):
        fields = SUMMARY_FIELD.findall(body)
        if fields:
            summary = _compose_summary(fields)
        else:
            quote = BLOCKQUOTE.search(body)
            if quote and re.search(r"[\u3400-\u9fff]", quote.group(1)):
                summary = _excerpt(quote.group(1))
            elif quote:
                summary = "项目简介为英文，详情请查看 GitHub 项目主页。"
            else:
                summary = ""
        items.append((title, url, summary))
    return items


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
            matches = _daily_items(path.read_text(encoding="utf-8", errors="replace"))
            total += len(matches)
            headlines = []
            for title, url, summary in matches[:3]:
                lines = [f"  - [{title}]({url})"]
                if summary:
                    lines.append(f"    - 摘要：{summary}")
                headlines.append("\n".join(lines))
            notes.append(f"- [[{category}/{day.isoformat()}]]\n" + "\n".join(headlines))
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
