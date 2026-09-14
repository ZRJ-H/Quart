from __future__ import annotations

from datetime import date
from html import escape
from urllib.parse import quote, urlsplit, urlunsplit

from .models import Article
from .summarize import DigestSummary, ItemSummary


TAGS = {
    "AI科技动态": "[AI动态, 每日资讯]",
    "时政要闻": "[时政要闻, 每日资讯]",
    "AI论文日报": "[AI论文, 每日资讯]",
    "Hacker News": "[HN日报, 每日资讯]",
}


def _markdown_text(value: object) -> str:
    text = escape(str(value), quote=False).replace("\r", " ").replace("\n", " ")
    for character in ("\\", "[", "]", "*", "_", "(", ")"):
        text = text.replace(character, f"\\{character}")
    return text


def _markdown_url(value: object) -> str:
    raw = str(value).strip().replace("\r", "").replace("\n", "")
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return "about:blank"
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return "about:blank"
    try:
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return "about:blank"
    if (
        not hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() for character in parsed.netloc)
        or any(character in parsed.netloc for character in '<>"\'\\')
    ):
        return "about:blank"

    path = quote(parsed.path, safe="/:@-._~!$&'()*+,;=[]")
    query = quote(parsed.query, safe="/?:@-._~!$&'()*+,;=[]")
    fragment = quote(parsed.fragment, safe="/?:@-._~!$&'()*+,;=[]")
    safe_url = urlunsplit((parsed.scheme.lower(), parsed.netloc, path, query, fragment))
    for character in ("\\", "[", "]", "(", ")"):
        safe_url = safe_url.replace(character, f"\\{character}")
    return safe_url


def _details(category: str, article: Article, item: ItemSummary, detailed: bool) -> str:
    lines = [
        f"### [{_markdown_text(item.title_zh)}]({_markdown_url(article.url)})",
        "",
        f"- **原标题**：{_markdown_text(article.title)}",
        f"- **来源与时间**：{_markdown_text(article.source)} · {article.published_at.isoformat()}",
    ]
    if category == "Hacker News":
        lines.extend(
            [
                f"- **社区热度**：⭐ {article.score} · 💬 {article.comments}",
                f"- **讨论链接**：[Hacker News]({_markdown_url(article.discussion_url)})",
                f"- **社区讨论焦点**：{_markdown_text(item.discussion_focus)}",
            ]
        )
    if category == "AI论文日报":
        authors = "、".join(_markdown_text(value) for value in article.extra.get("authors", [])) or "来源未列出"
        categories = "、".join(_markdown_text(value) for value in article.extra.get("categories", [])) or "来源未列出"
        lines.append(f"- **作者/分类**：{authors} · {categories}")
        if detailed:
            lines.extend(
                [
                    f"- **研究问题**：{_markdown_text(item.research_problem)}",
                    f"- **方法**：{_markdown_text(item.method)}",
                    f"- **实验结果**：{_markdown_text(item.results)}",
                    f"- **局限**：{_markdown_text(item.limitations)}",
                    f"- **工程价值**：{_markdown_text(item.engineering_value)}",
                    f"- **价值点**：{_markdown_text(item.value)}",
                ]
            )
        else:
            lines.extend([f"- **核心摘要**：{_markdown_text(item.summary)}", f"- **价值点**：{_markdown_text(item.value)}"])
        return "\n".join(lines)
    lines.append(f"- **核心摘要**：{_markdown_text(item.summary)}")
    if detailed:
        lines.extend(
            [
                f"- **背景**：{_markdown_text(item.background)}",
                f"- **影响**：{_markdown_text(item.impact)}",
                f"- **后续观察**：{_markdown_text(item.watch)}",
            ]
        )
    lines.append(f"- **价值点**：{_markdown_text(item.value)}")
    return "\n".join(lines)


def render_digest(category: str, run_date: date, articles: list[Article], summary: DigestSummary) -> str:
    sources = "、".join(dict.fromkeys(_markdown_text(article.source) for article in articles))
    deep_count = min(3, len(articles))
    deep = "\n\n".join(_details(category, articles[index], summary.items[index], True) for index in range(deep_count))
    quick = "\n\n".join(_details(category, articles[index], summary.items[index], False) for index in range(deep_count, len(articles)))
    trends = "\n\n".join(
        f"### 趋势 {index}\n\n- **事实依据**：{_markdown_text(trend.fact)}\n- **编辑判断**：{_markdown_text(trend.inference)}"
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
