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


def _clip(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip(" ,;:，；：") + "…"


def _sentences(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+", value) if part.strip()]


def _matching_sentence(sentences: list[str], keywords: tuple[str, ...], fallback: str) -> str:
    for sentence in sentences:
        lowered = sentence.casefold()
        if any(keyword in lowered for keyword in keywords):
            return sentence
    return fallback


def _fallback(category: str, articles: list[Article]) -> DigestSummary:
    items: list[ItemSummary] = []
    for index, article in enumerate(articles):
        source_date = article.published_at.date().isoformat()
        evidence = re.sub(r"\s+", " ", article.summary or article.title).strip()
        if index < 3:
            summary = _clip(f"来源直接提供的核心信息是：{evidence}", 110)
            background = _clip(
                f"{article.source} 于 {source_date} 发布此条目。当前记录只采用标题、发布时间与来源摘要，未读取到的正文背景不作补写。",
                72,
            )
            impact = _clip(
                f"从现有证据可确认，该条目聚焦“{article.title}”；对行业、政策或用户的实际影响仍缺少可量化材料。",
                82,
            )
            watch = "后续应核验原文更新、方法或数据披露，并观察是否出现独立来源的交叉印证，同时记录不同来源间的事实冲突或口径变化。"
            value = "本条提供当天主题线索和可追溯原文，适合继续阅读，不把尚未披露的信息写成结论。"
        else:
            summary = _clip(
                f"{article.source} 于 {source_date} 发布“{article.title}”。来源可核验信息：{evidence}",
                98,
            )
            background = impact = watch = ""
            value = "提供当天线索与原文入口；更多背景、结果和影响需回到来源核验，当前不作证据之外的推断。"

        common = {
            "index": index,
            "title_zh": article.title,
            "summary": summary,
            "background": background,
            "impact": impact,
            "watch": watch,
            "value": value,
        }
        if category == "AI论文日报":
            sentences = _sentences(evidence)
            first = sentences[0] if sentences else article.title
            method_sentence = _matching_sentence(
                sentences,
                ("we propose", "we present", "method", "framework", "approach", "using"),
                first,
            )
            result_sentence = _matching_sentence(
                sentences,
                ("result", "achieve", "outperform", "improve", "reduce", "faster", "%"),
                "作者摘要未给出可单独提取的量化结果。",
            )
            common.update(
                research_problem=_clip(f"研究问题线索：{first}", 150),
                method=_clip(f"方法线索：{method_sentence}", 150),
                results=_clip(f"结果线索：{result_sentence}", 130),
                limitations="作者摘要没有系统披露全部实验边界、失败案例与外部有效性；自动日报也不能替代阅读全文和附录审查。",
                engineering_value="可作为复现和技术选型线索；进入生产前仍需核对代码、数据、成本、许可与目标场景的一致性。",
            )
        if category == "Hacker News":
            comments = [re.sub(r"\s+", " ", str(comment)).strip() for comment in article.extra.get("top_comments", [])]
            focus = "；".join(comment for comment in comments if comment)
            common["discussion_focus"] = _clip(
                f"高赞评论主要讨论：{focus}" if focus else "暂无可用的高赞评论证据。",
                180,
            )
        items.append(ItemSummary(**common))

    trends = []
    for article in (articles + articles[:1] * 3)[:3]:
        trends.append(
            TrendSummary(
                fact=f"{article.source} 发布了《{article.title}》。",
                inference="编辑判断：该主题是否形成持续趋势，仍需更多来源、后续数据或实际采用情况验证。",
            )
        )
    return DigestSummary(tuple(items), tuple(trends[:3]), "evidence-only")

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
    failures: list[str] = []
    for url, key, model in providers:
        try:
            body: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
            if model.startswith("openai/gpt-5"):
                body["max_completion_tokens"] = 6000
            else:
                body["temperature"] = 0.1
                body["max_tokens"] = 6000
            response = request(
                url,
                {"Authorization": f"Bearer {key}"},
                body,
            )
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return _parse_content(content, category, articles)
        except Exception as error:
            failure = f"{model}: {type(error).__name__}: {error}"
            failures.append(re.sub(r"\s+", " ", failure).strip())
            print(f"Summary provider failed for {category}: {error}")
    return _fallback(category, articles)
