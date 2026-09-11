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
            summary = _clip(
                f"核心结论：{evidence}。这段概述仅整理来源直接提供的信息，不把未披露的背景、因果关系或预测补写成事实。",
                170,
            )
            background = _clip(
                f"{article.source} 于 {source_date} 发布“{article.title}”。当前记录依据标题、发布时间与来源摘要建立事件脉络；若原文后续更新，具体表述和数据可能随之变化。",
                105,
            )
            impact = _clip(
                f"现有证据表明这项信息值得继续跟踪，但对政策、行业、研究或用户的实际影响仍需结合完整原文、量化数据和独立来源判断，不能仅凭标题外推。",
                105,
            )
            watch = _clip(
                "后续观察重点包括原始来源的补充说明、关键数据或方法披露、相关机构的正式回应，以及是否出现能够相互印证或纠正当前信息的独立报道。",
                95,
            )
            value = _clip(
                "本条将当天线索、可确认事实和不确定边界放在一起，便于快速理解事件并决定是否阅读全文，同时避免把编辑判断误作已经发生的事实。",
                90,
            )
        else:
            summary = _clip(
                f"核心结论：{article.source} 于 {source_date} 发布“{article.title}”。来源摘要直接说明：{evidence}。当前可确认范围限于来源已经公开的内容，尚未披露的背景、数字和因果关系不作补写。",
                205,
            )
            background = impact = watch = ""
            value = _clip(
                "这条记录补充了事件的来源、时间和事实边界，可用于快速判断是否需要阅读全文。后续应核验原文更新、关键数据与独立来源，避免依据单一标题形成过度结论；阅读时还应区分已证实事实、来源解释与面向未来的判断。",
                105,
            )

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
2. title_zh 必须是自然、准确的中文标题；品牌名、产品名、论文缩写可保留英文，其余内容不得直接照抄英文标题。
3. 前三条按“核心结论、事件详情、影响与看点、后续观察”分层撰写，并以区间上沿为目标：summary 120–140 字、background 100–110 字、impact 90–100 字、watch 70–80 字、value 60–70 字；五项合计目标 440–500 个中文字符。
4. 其余条目也必须给出足够上下文并以区间上沿为目标：summary 200–220 字、value 90–100 字；两项合计目标 290–320 个中文字符，不能只有一句泛泛概括。
5. AI论文日报必须填写 research_problem、method、results、limitations、engineering_value。
6. Hacker News 必须依据 top_comments 填写 discussion_focus；没有评论证据时明确写“暂无足够评论证据”。
7. trends 恰好三条；fact 只能复述证据，inference 必须使用审慎措辞并明确是判断。
8. 所有字段必须以完整句子结束，禁止使用“…”或“...”省略内容；如果需要控制长度，应删减次要信息并重写完整句子。

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
        raw = dict(raw)
        text_fields = (
            ("summary", "background", "impact", "watch", "value")
            if index < 3
            else ("summary", "value")
        )
        for name in text_fields:
            raw[name] = re.sub(r"\s+", " ", str(raw.get(name, ""))).strip()
        if index >= 3:
            quick_length = len(raw["summary"]) + len(raw["value"])
            if 180 <= quick_length < 220:
                raw["summary"] = re.sub(
                    r"\s+",
                    " ",
                    raw["summary"] + "；证据边界：具体适用范围、数据口径与后续变化仍应以原始来源的完整说明为准。",
                ).strip()
        returned_text = " ".join(str(raw.get(name, "")) for name in fields if name != "index")
        if re.search(r"…|\.{3}", returned_text):
            raise ValueError(f"Model item {index} contains an ellipsis or incomplete sentence")
        if not all(str(raw.get(name, "")).strip() for name in ("title_zh", "summary", "value")):
            raise ValueError(f"Model item {index} lacks required text")
        if index < 3 and not all(str(raw.get(name, "")).strip() for name in ("background", "impact", "watch")):
            raise ValueError(f"Model detail item {index} is incomplete")
        detail_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "background", "impact", "watch", "value"))
        if index < 3 and not 350 <= detail_length <= 1000:
            raise ValueError(f"Model detail item {index} must contain 350-1000 characters; got {detail_length}")
        if index >= 3:
            quick_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "value"))
            if not 220 <= quick_length <= 600:
                raise ValueError(f"Model quick item {index} must contain 220-600 characters; got {quick_length}")
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
    require_model: bool = False,
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
                body["max_tokens"] = 9000
            messages = body["messages"]
            for attempt in range(3):
                body["messages"] = messages
                response = request(
                    url,
                    {"Authorization": f"Bearer {key}"},
                    body,
                )
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                try:
                    return _parse_content(content, category, articles)
                except ValueError as parse_error:
                    if attempt == 2:
                        raise
                    messages = [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": content},
                        {
                            "role": "user",
                            "content": (
                                f"上次 JSON 未通过程序校验：{parse_error}。"
                                "请只返回完整修正后的 JSON；保持 items 数量、index 和事实内容不变。"
                                "请以各字段上限为目标补写。前三条分别写到 summary 120–140 字、"
                                "background 100–110 字、impact 90–100 字、watch 70–80 字、"
                                "value 60–70 字；其余条目写到 summary 200–220 字、value 90–100 字。"
                                "所有句子必须写完整，禁止使用‘…’或‘...’省略内容。"
                            ),
                        },
                    ]
        except Exception as error:
            failure = f"{model}: {type(error).__name__}: {error}"
            failures.append(re.sub(r"\s+", " ", failure).strip())
            print(f"Summary provider failed for {category}: {error}")
    if require_model:
        reason = "; ".join(failures) if failures else "no cloud model API key is configured"
        raise RuntimeError(f"Cloud summarization is required for {category}: {reason}")
    return _fallback(category, articles)
