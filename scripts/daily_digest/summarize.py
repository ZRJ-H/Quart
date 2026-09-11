from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .http import USER_AGENT
from .models import Article


@dataclass(frozen=True, slots=True)
class ItemSummary:
    index: int
    title_zh: str
    summary: str
    background: str = ""
    impact: str = ""
    watch: str = ""
    value: str = ""
    research_problem: str = ""
    method: str = ""
    results: str = ""
    limitations: str = ""
    engineering_value: str = ""
    discussion_focus: str = ""


@dataclass(frozen=True, slots=True)
class TrendSummary:
    fact: str
    inference: str


@dataclass(frozen=True, slots=True)
class DigestSummary:
    items: tuple[ItemSummary, ...]
    trends: tuple[TrendSummary, ...]
    mode: str


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT, **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def _fallback(category: str, articles: list[Article]) -> DigestSummary:
    items: list[ItemSummary] = []
    for index, article in enumerate(articles):
        source_date = article.published_at.date().isoformat()
        evidence = article.summary or article.title
        common = {
            "index": index,
            "title_zh": article.title,
            "summary": evidence,
            "background": f"该信息由 {article.source} 于 {source_date} 发布，当前仅使用来源提供的内容。",
            "impact": "来源没有提供足够证据支持进一步影响判断，请以原文后续更新为准。",
            "watch": "关注原始页面更新及其他独立来源的后续印证。",
            "value": "保留来源、时间和原文链接，便于直接核验。",
        }
        if category == "AI论文日报":
            common.update(
                research_problem=evidence,
                method="来源摘要未提供可安全扩写的完整方法细节，请查阅论文原文。",
                results="当前仅保留作者摘要中明确报告的结果。",
                limitations="自动采集无法替代对论文实验设计和附录的完整审阅。",
                engineering_value="需要完成独立复现后再判断工程适用性。",
            )
        if category == "Hacker News":
            comments = article.extra.get("top_comments", [])
            common["discussion_focus"] = " ".join(comments) if comments else "暂无可用的高赞评论证据。"
        items.append(ItemSummary(**common))

    trends = []
    for article in (articles + articles[:1] * 3)[:3]:
        trends.append(
            TrendSummary(
                fact=f"{article.source} 发布了《{article.title}》。",
                inference="该主题的重要性仍需结合更多来源和后续进展判断。",
            )
        )
    return DigestSummary(tuple(items), tuple(trends[:3]), "deterministic")


def _prompt(category: str, articles: list[Article]) -> str:
    evidence = []
    for index, article in enumerate(articles):
        row = asdict(article)
        row["index"] = index
        row["published_at"] = article.published_at.isoformat()
        evidence.append(row)
    return f"""你是 Otae 知识库的事实编辑。仅根据下方 JSON 证据生成 {category} 中文摘要，不得补充证据中没有的人名、数字、背景或结论。

返回严格 JSON，不要 Markdown 代码围栏。结构为：
{{"items":[{{"index":0,"title_zh":"","summary":"","background":"","impact":"","watch":"","value":"","research_problem":"","method":"","results":"","limitations":"","engineering_value":"","discussion_focus":""}}],"trends":[{{"fact":"","inference":""}},{{"fact":"","inference":""}},{{"fact":"","inference":""}}]}}

要求：
1. items 数量和 index 必须与输入完全一致，保留原顺序。
2. 前三条的 summary、background、impact、watch、value 合计 250–400 个中文字符；其余条目的 summary 和 value 合计 80–150 字。
3. AI论文日报必须填写 research_problem、method、results、limitations、engineering_value。
4. Hacker News 必须依据 top_comments 填写 discussion_focus；没有评论证据时明确写“暂无足够评论证据”。
5. trends 恰好三条；fact 只能复述证据，inference 必须使用审慎措辞并明确是判断。

证据 JSON：
{json.dumps(evidence, ensure_ascii=False)}"""


def _parse_content(content: str, category: str, articles: list[Article]) -> DigestSummary:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    raw_items = payload.get("items")
    raw_trends = payload.get("trends")
    if not isinstance(raw_items, list) or len(raw_items) != len(articles):
        raise ValueError("Model item count does not match evidence")
    if not isinstance(raw_trends, list) or len(raw_trends) != 3:
        raise ValueError("Model must return exactly three trends")
    if [item.get("index") for item in raw_items] != list(range(len(articles))):
        raise ValueError("Model item indexes do not match evidence")

    fields = tuple(ItemSummary.__dataclass_fields__)
    items: list[ItemSummary] = []
    for index, raw in enumerate(raw_items):
        if not all(str(raw.get(name, "")).strip() for name in ("title_zh", "summary", "value")):
            raise ValueError(f"Model item {index} lacks required text")
        if index < 3 and not all(str(raw.get(name, "")).strip() for name in ("background", "impact", "watch")):
            raise ValueError(f"Model detail item {index} is incomplete")
        detail_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "background", "impact", "watch", "value"))
        if index < 3 and not 250 <= detail_length <= 400:
            raise ValueError(f"Model detail item {index} must contain 250-400 characters")
        if index >= 3:
            quick_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "value"))
            if not 80 <= quick_length <= 150:
                raise ValueError(f"Model quick item {index} must contain 80-150 characters")
        if category == "AI论文日报" and not all(
            str(raw.get(name, "")).strip()
            for name in ("research_problem", "method", "results", "limitations", "engineering_value")
        ):
            raise ValueError(f"Model paper item {index} is incomplete")
        values = {name: raw.get(name, "") for name in fields}
        values["index"] = index
        items.append(ItemSummary(**values))

    trends = tuple(TrendSummary(str(item.get("fact", "")).strip(), str(item.get("inference", "")).strip()) for item in raw_trends)
    if not all(trend.fact and trend.inference for trend in trends):
        raise ValueError("Model trends lack fact or inference")
    return DigestSummary(tuple(items), trends, "model")


def summarize(
    category: str,
    articles: list[Article],
    api_key: str | None,
    go_key: str | None,
    *,
    request: Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]] = _post_json,
) -> DigestSummary:
    providers: list[tuple[str, str, str]] = []
    if api_key:
        providers.append(("https://api.deepseek.com/chat/completions", api_key, "deepseek-chat"))
    if go_key:
        providers.append(("https://opencode.ai/zen/go/v1/chat/completions", go_key, "deepseek-v4-pro"))
    prompt = _prompt(category, articles)
    for url, key, model in providers:
        try:
            response = request(
                url,
                {"Authorization": f"Bearer {key}"},
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 6000,
                    "response_format": {"type": "json_object"},
                },
            )
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return _parse_content(content, category, articles)
        except Exception as error:
            print(f"Summary provider failed for {category}: {error}")
    return _fallback(category, articles)
