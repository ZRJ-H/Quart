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

        self.assertIn("常规取最近 48 小时，不足时依次扩至 72 小时和 7 天", markdown)
        self.assertIn("## 深度解读", markdown)
        self.assertIn("## 快速浏览", markdown)
        self.assertIn("**研究问题**", markdown)
        self.assertEqual(markdown.count("**研究问题**"), 3)
        self.assertEqual(markdown.count("**核心摘要**"), 5)
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

        self.assertEqual(result.mode, "evidence-only")
        self.assertIn(articles[0].summary, markdown)
        self.assertIn(articles[0].url, markdown)

    def test_model_detail_without_a_summary_is_rejected(self):
        articles = PAPERS[:3]
        payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": "短标题",
                    "summary": "",
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

        self.assertEqual(result.mode, "evidence-only")
    def test_model_fields_are_preserved_in_full_without_programmatic_ellipsis(self):
        articles = PAPERS[:3]
        payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": f"中文标题 {index}",
                    "summary": "摘" * 180,
                    "background": "背" * 150,
                    "impact": "影" * 140,
                    "watch": "观" * 120,
                    "value": "值" * 100,
                }
                for index in range(3)
            ],
            "trends": [
                {"fact": "来源发布信息。", "inference": "仍需观察。"},
                {"fact": "来源提供摘要。", "inference": "影响待验证。"},
                {"fact": "条目附有链接。", "inference": "可以继续核验。"},
            ],
        }

        def fake_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, require_model=True, request=fake_request)

        self.assertEqual(result.mode, "model")
        for item in result.items:
            self.assertEqual(item.summary, "摘" * 180)
            self.assertEqual(item.background, "背" * 150)
            self.assertEqual(item.impact, "影" * 140)
            self.assertEqual(item.watch, "观" * 120)
            self.assertEqual(item.value, "值" * 100)
            self.assertNotIn("…", "".join((item.summary, item.background, item.impact, item.watch, item.value)))

    def test_model_ellipsis_is_repaired_before_publishing(self):
        articles = PAPERS[:3]
        complete_items = [
            {
                "index": index,
                "title_zh": f"中文标题 {index}",
                "summary": "完整核心事实。" * 18,
                "background": "完整背景信息。" * 12,
                "impact": "完整影响判断。" * 10,
                "watch": "完整后续观察。" * 8,
                "value": "完整阅读价值。" * 7,
            }
            for index in range(3)
        ]
        trends = [
            {"fact": "来源发布信息。", "inference": "仍需观察。"},
            {"fact": "来源提供摘要。", "inference": "影响待验证。"},
            {"fact": "条目附有链接。", "inference": "可以继续核验。"},
        ]
        incomplete_items = [dict(item) for item in complete_items]
        incomplete_items[0]["summary"] = complete_items[0]["summary"][:-1] + "…"
        responses = [
            {"items": incomplete_items, "trends": trends},
            {"items": complete_items, "trends": trends},
        ]

        def fake_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(responses.pop(0), ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, require_model=True, request=fake_request)

        self.assertEqual(result.items[0].summary, complete_items[0]["summary"])
        self.assertEqual(responses, [])
    def test_concise_quick_item_is_preserved_without_evidence_padding(self):
        articles = PAPERS[:4]
        payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": f"中文标题 {index}",
                    "summary": "摘" * 100,
                    "background": "背" * 70,
                    "impact": "影" * 70,
                    "watch": "观" * 70,
                    "value": "值" * 70,
                }
                for index in range(3)
            ]
            + [
                {
                    "index": 3,
                    "title_zh": "中文标题 3",
                    "summary": "摘" * 128,
                    "value": "值" * 64,
                }
            ],
            "trends": [
                {"fact": "来源发布信息。", "inference": "仍需观察。"},
                {"fact": "来源提供摘要。", "inference": "影响待验证。"},
                {"fact": "条目附有链接。", "inference": "可以继续核验。"},
            ],
        }

        def fake_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, require_model=True, request=fake_request)
        quick = result.items[3]

        self.assertEqual(quick.summary, payload["items"][3]["summary"])
        self.assertEqual(quick.value, payload["items"][3]["value"])
        self.assertNotIn("证据边界", quick.summary + quick.value)

    def test_missing_model_summary_is_repaired_up_to_two_times(self):
        articles = PAPERS[:3]
        short_payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": f"中文标题 {index}",
                    "summary": "",
                    "background": "太短",
                    "impact": "太短",
                    "watch": "太短",
                    "value": "太短",
                }
                for index in range(3)
            ],
            "trends": [
                {"fact": "来源发布信息。", "inference": "仍需观察。"},
                {"fact": "来源提供摘要。", "inference": "影响待验证。"},
                {"fact": "条目附有链接。", "inference": "可以继续核验。"},
            ],
        }
        repaired_payload = {
            "items": [
                {
                    "index": index,
                    "title_zh": f"中文标题 {index}",
                    "summary": "摘" * 100,
                    "background": "背" * 70,
                    "impact": "影" * 70,
                    "watch": "观" * 70,
                    "value": "值" * 70,
                }
                for index in range(3)
            ],
            "trends": short_payload["trends"],
        }
        responses = [short_payload, short_payload, repaired_payload]

        def fake_request(url, headers, body):
            payload = responses.pop(0)
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, require_model=True, request=fake_request)

        self.assertEqual(result.mode, "model")
        self.assertEqual(responses, [])

    def test_evidence_only_fallback_does_not_invent_analysis_or_fill_length(self):
        result = summarize("AI科技动态", PAPERS, api_key=None, go_key=None)

        for article, item in zip(PAPERS, result.items):
            self.assertEqual(item.summary, article.summary)
            self.assertEqual((item.background, item.impact, item.watch, item.value), ("", "", "", ""))
        self.assertTrue(all(not trend.inference for trend in result.trends))
        markdown = render_digest("AI科技动态", RUN_DATE, PAPERS, result)
        for label in ("**背景**", "**影响**", "**后续观察**", "**价值点**", "**编辑判断**"):
            self.assertNotIn(label, markdown)

    def test_required_cloud_summary_rejects_evidence_only_fallback(self):
        with self.assertRaisesRegex(RuntimeError, "Cloud summarization is required"):
            summarize("AI科技动态", PAPERS[:3], api_key=None, go_key=None, require_model=True)

    def test_deterministic_fallback_clips_long_paper_and_comment_evidence(self):
        long_paper = Article(
            "2609.99999",
            "Long paper",
            "https://arxiv.org/abs/2609.99999",
            "arXiv",
            datetime(2026, 9, 11, 1, tzinfo=timezone.utc),
            "We propose a method. We evaluate it on twelve tasks. Results improve by 30 percent. " * 30,
        )
        paper_item = summarize("AI论文日报", [long_paper], api_key=None, go_key=None).items[0]
        self.assertLessEqual(len(paper_item.summary), 205)
        self.assertLessEqual(len(paper_item.research_problem), 180)

        long_comment = "Users discuss deployment cost, reliability, and benchmark quality. " * 30
        hn_article = Article(
            "999",
            "A launch",
            "https://example.com/launch",
            "Hacker News",
            datetime(2026, 9, 11, 1, tzinfo=timezone.utc),
            "A launch was announced.",
            discussion_url="https://news.ycombinator.com/item?id=999",
            extra={"top_comments": [long_comment]},
        )
        hn_item = summarize("Hacker News", [hn_article], api_key=None, go_key=None).items[0]
        self.assertLessEqual(len(hn_item.discussion_focus), 180)

    def test_concise_supported_summary_and_real_uncertainty_are_preserved(self):
        articles = PAPERS[:3]
        text = "团队发布了测试版工具，支持导出项目配置。作者称测试仅覆盖 Linux，Windows 兼容性尚未验证。"
        payload = {
            "items": [{"index": i, "title_zh": f"工具更新 {i}", "summary": text} for i in range(3)],
            "trends": [{"fact": "来源介绍了测试版工具。", "inference": ""} for _ in range(3)],
        }
        calls = []

        def fake_request(url, headers, body):
            calls.append(body)
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI科技动态", articles, api_key="key", go_key=None, require_model=True, request=fake_request)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result.items[0].summary, text)
        self.assertEqual(result.items[0].impact, "")
        prompt = calls[0]["messages"][0]["content"]
        self.assertIn("事实充足时合计约 350–500 字", prompt)
        self.assertIn("没有提供某项信息，不等于它没有发生", prompt)
        self.assertIn("不同的重要限制不能因追求简洁而删除", prompt)
        self.assertNotIn("以区间上沿为目标", prompt)
        self.assertNotIn("inference 必须使用审慎措辞", prompt)

    def test_repair_prompt_does_not_request_padding(self):
        responses = [
            {"items": [], "trends": []},
            {"items": [{"index": i, "title_zh": "工具更新", "summary": "团队发布了支持导出项目配置的工具。"} for i in range(3)],
             "trends": [{"fact": "来源发布了工具。", "inference": ""} for _ in range(3)]},
        ]
        calls = []

        def fake_request(url, headers, body):
            calls.append(list(body["messages"]))
            return {"choices": [{"message": {"content": json.dumps(responses.pop(0), ensure_ascii=False)}}]}

        summarize("AI科技动态", PAPERS[:3], api_key="key", go_key=None, require_model=True, request=fake_request)
        self.assertEqual(len(calls), 2)
        repair = calls[1][-1]["content"]
        self.assertIn("只修正校验指出的问题", repair)
        self.assertNotIn("上限为目标补写", repair)

    def test_optional_paper_fields_can_be_absent_without_claiming_no_results(self):
        payload = {
            "items": [{"index": i, "title_zh": "论文摘要", "summary": "作者介绍了一种压缩模型的方法。"} for i in range(3)],
            "trends": [{"fact": "摘要介绍了模型压缩。", "inference": ""} for _ in range(3)],
        }

        def fake_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI论文日报", PAPERS[:3], api_key="key", go_key=None, require_model=True, request=fake_request)
        markdown = render_digest("AI论文日报", RUN_DATE, PAPERS[:3], result)
        self.assertIn("作者介绍了一种压缩模型的方法。", markdown)
        self.assertNotIn("**局限**", markdown)
        self.assertNotIn("没有结果", markdown)

    def test_paper_limits_are_displayed_when_present(self):
        markdown = render_digest("AI论文日报", RUN_DATE, PAPERS, VALID_SUMMARY)
        self.assertIn("样本规模和任务覆盖范围有限。", markdown)
        self.assertIn("**工程价值**", markdown)

    def test_fallback_excerpts_do_not_end_with_artificial_ellipsis(self):
        result = summarize("AI科技动态", [Article(
            "long", "工具测试", "https://example.com/tool", "测试来源",
            datetime(2026, 9, 11, tzinfo=timezone.utc),
            "团队发布了工具。" + "这是一条很长的来源原句" * 40 + "。",
        )], api_key=None, go_key=None)
        self.assertEqual(result.items[0].summary, "团队发布了工具。")
        self.assertNotIn("…", result.items[0].summary)

    def test_partial_paper_fields_do_not_hide_summary_results_or_limits(self):
        text = "作者报告准确率提高 12%，但实验只覆盖一个英文数据集，中文效果未验证。"
        payload = {
            "items": [{"index": i, "title_zh": "评测论文", "summary": text,
                       "research_problem": "如何提升模型准确率。"} for i in range(3)],
            "trends": [{"fact": "作者报告了评测结果。", "inference": ""} for _ in range(3)],
        }

        def fake_request(url, headers, body):
            return {"choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]}

        result = summarize("AI论文日报", PAPERS[:3], api_key="key", go_key=None, require_model=True, request=fake_request)
        markdown = render_digest("AI论文日报", RUN_DATE, PAPERS[:3], result)
        self.assertEqual(markdown.count(text), 3)
        self.assertIn("**研究问题**", markdown)
        self.assertNotIn("**实验结果**", markdown)

    def test_long_first_source_sentence_and_comments_are_not_discarded(self):
        sentence = "A team released a tool with configurable project export, " + "auditable deployment controls and " * 8 + "manual review."
        self.assertGreater(len(sentence), 205)
        article = Article(
            "long", "A tool", "https://example.com/tool", "Source",
            datetime(2026, 9, 11, tzinfo=timezone.utc), sentence,
            discussion_url="https://news.ycombinator.com/item?id=1",
            extra={"top_comments": [sentence]},
        )
        item = summarize("Hacker News", [article], api_key=None, go_key=None).items[0]
        self.assertEqual(item.summary, sentence)
        self.assertEqual(item.discussion_focus, sentence)
        no_boundary = sentence.rstrip(".")
        article = Article("raw", "Raw input", "https://example.com/raw", "Source",
                          datetime(2026, 9, 11, tzinfo=timezone.utc), no_boundary)
        self.assertEqual(summarize("AI科技动态", [article], api_key=None, go_key=None).items[0].summary, no_boundary)

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
