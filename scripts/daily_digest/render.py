from __future__ import annotations

from datetime import date

from .models import Article
from .summarize import DigestSummary, ItemSummary


TAGS = {
    "AI科技动态": "[AI动态, 每日资讯]",
    "时政要闻": "[时政要闻, 每日资讯]",
    "AI论文日报": "[AI论文, 每日资讯]",
    "Hacker News": "[HN日报, 每日资讯]",
}


def _details(category: str, article: Article, item: ItemSummary, detailed: bool) -> str:
    lines = [
        f"### [{item.title_zh}]({article.url})",
        "",
        f"- **原标题**：{article.title}",
        f"- **来源与时间**：{article.source} · {article.published_at.isoformat()}",
    ]
    if category == "Hacker News":
        lines.extend(
            [
                f"- **社区热度**：⭐ {article.score} · 💬 {article.comments}",
                f"- **讨论链接**：[Hacker News]({article.discussion_url})",
                f"- **社区讨论焦点**：{item.discussion_focus}",
            ]
        )
    if category == "AI论文日报":
        authors = "、".join(article.extra.get("authors", [])) or "来源未列出"
        categories = "、".join(article.extra.get("categories", [])) or "来源未列出"
        lines.append(f"- **作者/分类**：{authors} · {categories}")
        if detailed:
            lines.extend(
                [
                    f"- **研究问题**：{item.research_problem}",
                    f"- **方法**：{item.method}",
                    f"- **实验结果**：{item.results}",
                    f"- **局限**：{item.limitations}",
                    f"- **工程价值**：{item.engineering_value}",
                    f"- **价值点**：{item.value}",
                ]
            )
        else:
            lines.extend([f"- **核心摘要**：{item.summary}", f"- **价值点**：{item.value}"])
        return "\n".join(lines)
    lines.append(f"- **核心摘要**：{item.summary}")
    if detailed:
        lines.extend(
            [
                f"- **背景**：{item.background}",
                f"- **影响**：{item.impact}",
                f"- **后续观察**：{item.watch}",
            ]
        )
    lines.append(f"- **价值点**：{item.value}")
    return "\n".join(lines)


def render_digest(category: str, run_date: date, articles: list[Article], summary: DigestSummary) -> str:
    sources = "、".join(dict.fromkeys(article.source for article in articles))
    deep_count = min(3, len(articles))
    deep = "\n\n".join(_details(category, articles[index], summary.items[index], True) for index in range(deep_count))
    quick = "\n\n".join(_details(category, articles[index], summary.items[index], False) for index in range(deep_count, len(articles)))
    trends = "\n\n".join(
        f"### 趋势 {index}\n\n- **事实依据**：{trend.fact}\n- **编辑判断**：{trend.inference}"
        for index, trend in enumerate(summary.trends, start=1)
    )
    quick_section = f"\n\n## 快速浏览\n\n{quick}" if quick else ""
    return f"""---
created: {run_date.isoformat()}
tags: {TAGS.get(category, '[每日资讯]')}
---

# {category} - {run_date.isoformat()}

> 来源：{sources} · 共 {len(articles)} 条 · 常规取最近 48 小时，不足时依次扩至 72 小时和 7 天 · 摘要模式：{summary.mode}

## 今日概览

- **收录数量**：{len(articles)} 条
- **深度解读**：{deep_count} 条
- **来源覆盖**：{sources}

## 深度解读

{deep}{quick_section}

## 今日趋势判断

{trends}

---

> 自动生成于 {run_date.isoformat()}；事实以链接中的原始来源为准，编辑判断不等同于已发生事实。
"""
