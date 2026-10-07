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
    # Evidence-only excerpts end at an existing sentence boundary; never add prose.
    sentences = re.findall(r".*?(?:[。！？]|[.!?](?=\s|$))", value)
    excerpt = ""
    for sentence in sentences:
        candidate = (excerpt + " " + sentence.strip()).strip()
        if len(candidate) > limit:
            # A complete source sentence is more useful than an empty excerpt.
            return excerpt or sentence.strip()
        excerpt = candidate
    return excerpt or value


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
        evidence = re.sub(r"\s+", " ", article.summary or article.title).strip()
        summary = _clip(evidence, 205) or f"{article.source} 发布了《{article.title}》。"
        background = impact = watch = value = ""

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
                "",
            )
            result_sentence = _matching_sentence(
                sentences,
                ("result", "achieve", "outperform", "improve", "reduce", "faster", "%"),
                "",
            )
            common.update(
                research_problem=_clip(first, 150),
                method=_clip(method_sentence, 150),
                results=_clip(result_sentence, 130),
                limitations="",
                engineering_value="",
            )
        if category == "Hacker News":
            comments = [re.sub(r"\s+", " ", str(comment)).strip() for comment in article.extra.get("top_comments", [])]
            focus = "；".join(comment for comment in comments if comment)
            common["discussion_focus"] = _clip(
                focus if focus else "本次未采集到评论。",
                180,
            )
        items.append(ItemSummary(**common))

    trends = []
    for article in (articles + articles[:1] * 3)[:3]:
        trends.append(
            TrendSummary(
                fact=f"{article.source} 发布了《{article.title}》。",
                inference="",
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
3. 前三条保留分层深读：summary 写清主体、动作和关键细节；background、impact、watch、value 只填证据支持且不重复的信息。事实充足时合计约 350–500 字；信息较少时可以更短，不设最低字数，不为填满栏目补写套话，无内容的可选字段返回空字符串。
4. 其余条目用 summary 概括具体事实，value 仅补充不重复的阅读价值。事实充足时合计约 220–320 字；信息较少时可以更短，事实讲完即止。
5. AI论文日报返回 research_problem、method、results、limitations、engineering_value；只填写摘要实际支持的内容，缺失时返回空字符串。保留作者报告、测试条件、量化结果及真实局限；不要为每篇论文追加通用的复现或生产部署提醒。
6. Hacker News 的 discussion_focus 只概括 top_comments；没有评论输入时写“本次未采集到评论。”，不要推断社区没有讨论。
7. trends 恰好三条；fact 复述具体观察，inference 仅写证据支持的解释，并以“从这些信息看”等自然表述区分判断。没有实质判断时返回空字符串，不强行上升为行业趋势；页面会标注事实与编辑判断。
8. 所有字段必须以完整句子结束，禁止使用“…”或“...”省略内容；如果需要控制长度，应删减次要信息并重写完整句子。

写作规则：
- 先写发生了什么，再写具体变化和直接影响。用具体动词、自然中文，不写审稿报告。
- 不主动讨论来源没有提出的战略、定价或未来走向。没有提供某项信息，不等于它没有发生；不要把“材料未提到”改写成“官方未宣布”或“政策未变化”。
- 保留消息来源、作者主张、条件和真正重要的不确定性。同一个不确定点只说明一次；不同的重要限制不能因追求简洁而删除。
- 避免堆叠“不能认为”“没有足够证据表明”“仍需进一步验证”等空泛保留意见；若争议或证据不足本身就是新闻重点，应直接写清具体争议和依据，不机械禁词。
- 每句话提供新事实、必要背景、具体影响或重要限制。删掉重复解释、空洞过渡、机械展望和“值得关注”等自我评价。
- 输出前自行检查并改写套话，不增加事实、不加强原结论；只返回最终 JSON，不展示检查过程。

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
        returned_text = " ".join(str(raw.get(name, "")) for name in fields if name != "index")
        if re.search(r"…|\.{3}", returned_text):
            raise ValueError(f"Model item {index} contains an ellipsis or incomplete sentence")
        if not all(str(raw.get(name, "")).strip() for name in ("title_zh", "summary")):
            raise ValueError(f"Model item {index} lacks required text")
        detail_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "background", "impact", "watch", "value"))
        if index < 3 and detail_length > 1000:
            raise ValueError(f"Model detail item {index} must not exceed 1000 characters; got {detail_length}")
        if index >= 3:
            quick_length = sum(len(str(raw.get(name, "")).strip()) for name in ("summary", "value"))
            if quick_length > 600:
                raise ValueError(f"Model quick item {index} must not exceed 600 characters; got {quick_length}")
        values = {name: raw.get(name, "") for name in fields}
        values["index"] = index
        items.append(ItemSummary(**values))

    trends = tuple(TrendSummary(str(item.get("fact", "")).strip(), str(item.get("inference", "")).strip()) for item in raw_trends)
    if not all(trend.fact for trend in trends):
        raise ValueError("Model trends lack facts")
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
                                "只修正校验指出的问题。信息已经完整时无需扩写；"
                                "不要为凑字数添加免责声明、泛化影响或无依据的背景。"
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
