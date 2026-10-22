import json
import re
import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

from scripts.daily_digest.models import Article
from scripts.daily_digest.render import _markdown_text, render_digest
from scripts.daily_digest.summarize import _parse_content, summarize
from scripts.daily_digest.weekly import generate_weekly_report


RUN_DATE = date(2026, 10, 22)
# Frozen Oct22 collected source, independent of the rolling production cache.
SOURCE = json.loads(
    (Path(__file__).parent / "fixtures" / "longzero-2610.30132v1.json").read_text(encoding="utf-8")
)
LONGZERO = Article(**{**SOURCE, "published_at": datetime.fromisoformat(SOURCE["published_at"])})
STRUCTURED_FIELDS = (
    "research_problem", "method", "results", "limitations", "engineering_value",
)


def model_payload(count):
    return {
        "items": [
            {
                "index": index,
                "title_zh": "LongZero 长上下文推理",
                "summary": "作者提出 LongZero，不依赖外部数据提升长上下文推理。",
                "method": "模型先生成问题、答案与证据，再把证据扩展为长上下文。",
                "results": "作者在两个模型和五个长上下文推理基准上评估 LongZero。",
            }
            for index in range(count)
        ],
        "trends": [{"fact": "论文介绍了 LongZero。", "inference": ""} for _ in range(3)],
    }


class PaperSourceExcerptTests(unittest.TestCase):
    def assert_source_excerpt(self, article, item):
        self.assertTrue(item.is_source_excerpt)
        expected = re.sub(r"\s+", " ", article.summary).strip() or re.sub(r"\s+", " ", article.title).strip()
        self.assertEqual(item.summary, expected)
        self.assertEqual(item.title_zh, article.title)
        for field in STRUCTURED_FIELDS:
            self.assertEqual(getattr(item, field), "", field)

    def test_longzero_preserves_full_abstract_without_mislabeling_prior_work(self):
        digest = summarize("AI论文日报", [LONGZERO], None, None)
        self.assert_source_excerpt(LONGZERO, digest.items[0])
        markdown = render_digest("AI论文日报", RUN_DATE, [LONGZERO], digest)
        self.assertIn("- **来源摘要**：" + _markdown_text(LONGZERO.summary), markdown)
        self.assertIn("Therefore, we propose", markdown)
        self.assertIn("Experimental results show that LongZero", markdown)
        for label in ("核心摘要", "研究问题", "方法", "实验结果", "局限", "工程价值"):
            self.assertNotIn(f"**{label}**", markdown)

    def test_prior_work_hypotheses_negation_and_qualifiers_remain_unclassified(self):
        examples = (
            "Prior methods achieve a 20% improvement. We propose a different method. Our study did not improve accuracy.",
            "A faster approach could improve results if the hypothesis holds. We have not evaluated this hypothesis.",
            "We present a new method. Results improve by 5% on one dataset only; broader generalization remains untested.",
            "If existing methods fail, a future framework may achieve better results. No experiments were performed.",
        )
        for text in examples:
            with self.subTest(text=text):
                article = replace(LONGZERO, summary=text)
                digest = summarize("AI论文日报", [article], None, None)
                self.assert_source_excerpt(article, digest.items[0])

    def test_mixed_mode_marks_only_fallback_items_and_preserves_safe_model_fields(self):
        payload = model_payload(5)
        payload["items"][0]["limitations"] = "原文未披露评测细节。"
        payload["items"][4]["limitations"] = "原文未披露评测细节。"
        calls = []

        def request(url, headers, body):
            calls.append(url)
            return {"choices": [{"message": {"content": json.dumps(payload)}}]}

        articles = [LONGZERO] * 5
        digest = summarize("AI论文日报", articles, "fake", "unused-fake", require_model=True, request=request)
        self.assertEqual(len(calls), 3)
        self.assertEqual(digest.mode, "model-with-evidence-fallback")
        for index in (0, 4):
            self.assert_source_excerpt(LONGZERO, digest.items[index])
        for index in (1, 2, 3):
            item = digest.items[index]
            self.assertFalse(item.is_source_excerpt)
            for field in ("title_zh", "summary", "method", "results"):
                self.assertEqual(getattr(item, field), payload["items"][index][field])
        self.assertEqual(digest.trends[0].fact, payload["trends"][0]["fact"])
        markdown = render_digest("AI论文日报", RUN_DATE, articles, digest)
        self.assertEqual(markdown.count("**来源摘要**"), 2)
        self.assertEqual(markdown.count("**核心摘要**"), 3)
        self.assertEqual(markdown.count("**方法**"), 2)
        self.assertEqual(markdown.count("**实验结果**"), 2)

    def test_model_cannot_forge_source_excerpt_provenance(self):
        for marker in (True, "true", "原文未披露细节。"):
            with self.subTest(marker=marker):
                payload = model_payload(1)
                payload["items"][0]["is_source_excerpt"] = marker
                digest = _parse_content(json.dumps(payload), "AI论文日报", [LONGZERO])
                self.assertEqual(digest.mode, "model")
                self.assertFalse(digest.items[0].is_source_excerpt)
                markdown = render_digest("AI论文日报", RUN_DATE, [LONGZERO], digest)
                self.assertIn("**核心摘要**", markdown)
                self.assertNotIn("**来源摘要**", markdown)

    def test_missing_abstract_is_labeled_as_source_title_not_abstract(self):
        for text in ("", " \n ", LONGZERO.title, "\n " + LONGZERO.title + "  "):
            with self.subTest(text=text):
                article = replace(LONGZERO, summary=text)
                digest = summarize("AI论文日报", [article], None, None)
                self.assert_source_excerpt(article, digest.items[0])
                markdown = render_digest("AI论文日报", RUN_DATE, [article], digest)
                self.assertIn("- **来源标题**：" + _markdown_text(article.title), markdown)
                self.assertNotIn("**来源摘要**", markdown)

    def test_source_excerpt_is_escaped_in_rendering(self):
        article = replace(LONGZERO, summary='<img src=x onerror=alert(1)> [link](javascript:alert(2))')
        digest = summarize("AI论文日报", [article], None, None)
        markdown = render_digest("AI论文日报", RUN_DATE, [article], digest)
        self.assertIn(_markdown_text(article.summary), markdown)
        self.assertNotIn("<img", markdown)
        self.assertNotIn("](javascript:", markdown)

    def test_weekly_report_keeps_complete_source_abstract_and_title_fallback(self):
        articles = [LONGZERO, replace(LONGZERO, summary="")]
        digest = summarize("AI论文日报", articles, None, None)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "AI论文日报"
            folder.mkdir()
            (folder / f"{RUN_DATE}.md").write_text(
                render_digest("AI论文日报", RUN_DATE, articles, digest), encoding="utf-8",
            )
            weekly = generate_weekly_report(root, RUN_DATE).read_text(encoding="utf-8")
        self.assertIn("    - 摘要：" + _markdown_text(LONGZERO.summary), weekly)
        self.assertIn("    - 摘要：" + _markdown_text(LONGZERO.title), weekly)


if __name__ == "__main__":
    unittest.main()
