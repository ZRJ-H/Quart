import json
import unittest
from datetime import date, datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.render import render_digest
from scripts.daily_digest.summarize import DigestSummary, ItemSummary, TrendSummary, summarize


RUN_DATE = date(2026, 9, 11)
PAPERS = [
    Article(
        f"2609.0000{index}",
        f"Paper {index}",
        f"https://arxiv.org/abs/2609.0000{index}",
        "arXiv",
        datetime(2026, 9, 11, index, tzinfo=timezone.utc),
        f"Evidence summary {index} with measured results.",
        extra={"authors": [f"Author {index}"], "categories": ["cs.AI"]},
    )
    for index in range(1, 6)
]


def valid_item(index):
    return ItemSummary(
        index=index,
        title_zh=f"论文 {index} 中文标题",
        summary="论文基于可核验输入说明研究目标和主要结论。",
        background="现有方法在可靠性和成本之间存在明确限制。",
        impact="结果影响模型评估与工程部署方式。",
        watch="后续需要独立复现并扩大测试范围。",
        value="提供了可直接比较的实验结果。",
        research_problem="如何在受控任务中提高系统可靠性。",
        method="使用对照实验和消融分析比较方法差异。",
        results="在十二项任务中报告可量化提升。",
        limitations="样本规模和任务覆盖范围有限。",
        engineering_value="可用于评估生产系统的取舍。",
    )


VALID_SUMMARY = DigestSummary(
    items=tuple(valid_item(index) for index in range(5)),
    trends=(
        TrendSummary("多篇论文评估可靠性。", "可靠性评测可能成为共同基线。"),
        TrendSummary("研究报告了资源效率指标。", "部署成本受到更多关注。"),
        TrendSummary("作者公开了实验设置。", "复现性将影响后续采用。"),
    ),
    mode="model",
)


class DailyRenderingTests(unittest.TestCase):
    def test_layered_digest_keeps_sources_and_category_fields(self):
        markdown = render_digest("AI论文日报", RUN_DATE, PAPERS, VALID_SUMMARY)

        self.assertIn("## 深度解读", markdown)
        self.assertIn("## 快速浏览", markdown)
        self.assertIn("**研究问题**", markdown)
        self.assertIn("**实验结果**", markdown)
        self.assertIn("**局限**", markdown)
        self.assertIn("https://arxiv.org/abs/2609.00001", markdown)
        self.assertEqual(markdown.count("**事实依据**"), 3)
        self.assertEqual(markdown.count("**编辑判断**"), 3)

    def test_invalid_model_output_falls_back_to_source_evidence(self):
        articles = PAPERS[:3]

        def fake_invalid_request(url, headers, body):
            return {"choices": [{"message": {"content": '{"items": [], "trends": []}'}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, request=fake_invalid_request)
        markdown = render_digest("AI科技动态", RUN_DATE, articles, result)

        self.assertEqual(result.mode, "deterministic")
        self.assertIn(articles[0].summary, markdown)
        self.assertIn(articles[0].url, markdown)

    def test_model_detail_that_is_too_short_is_rejected(self):
        articles = PAPERS[:3]
        payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": "短标题",
                    "summary": "太短",
                    "background": "太短",
                    "impact": "太短",
                    "watch": "太短",
                    "value": "太短",
                }
                for index in range(3)
            ],
            "trends": [
                {"fact": "来源发布了信息。", "inference": "仍需继续观察。"},
                {"fact": "来源提供了摘要。", "inference": "影响尚不确定。"},
                {"fact": "条目附有链接。", "inference": "可以进一步核验。"},
            ],
        }

        def fake_short_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, request=fake_short_request)

        self.assertEqual(result.mode, "deterministic")
    def test_hacker_news_renders_heat_and_discussion_focus(self):
        article = Article(
            "101",
            "A useful tool",
            "https://example.com/tool",
            "Hacker News",
            datetime(2026, 9, 11, 1, tzinfo=timezone.utc),
            "A useful tool was released.",
            score=420,
            comments=88,
            discussion_url="https://news.ycombinator.com/item?id=101",
            extra={"top_comments": ["Users discuss deployment trade-offs."]},
        )
        item = ItemSummary(
            0,
            "一个实用工具",
            "工具已经发布。",
            background="项目提供公开实现。",
            impact="可能降低部署成本。",
            watch="观察后续维护情况。",
            value="具有直接工程价值。",
            discussion_focus="社区主要讨论部署复杂度与维护成本。",
        )
        digest = DigestSummary((item,), VALID_SUMMARY.trends, "model")

        markdown = render_digest("Hacker News", RUN_DATE, [article], digest)

        self.assertIn("⭐ 420", markdown)
        self.assertIn("💬 88", markdown)
        self.assertIn("社区讨论焦点", markdown)
        self.assertIn(article.discussion_url, markdown)


if __name__ == "__main__":
    unittest.main()
