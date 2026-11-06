import json
import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.daily_digest.models import Article
from scripts.daily_digest.render import _markdown_text, render_digest
from scripts.daily_digest.summarize import _parse_content
from scripts.daily_digest.weekly import generate_weekly_report


RUN_DATE = date(2026, 10, 26)
# Frozen reproduction of the Oct 26 model page; no live source or model calls.
ARTICLE = Article(
    "2610.32982v1", "The Language of Instruction: Genre and Generative AI",
    "https://arxiv.org/abs/2610.32982v1", "arXiv",
    datetime(2026, 10, 23, 17, 59, 56, tzinfo=timezone.utc),
    "This article argues that instruction-fine-tuned language models should be "
    "understood as implementing a genre, what is proposed as the "
    "instructional-conversational genre.",
)
CONCLUSION = "作者主张该体裁是生成模型与人类过往对话话语的混合，并递归经过大型神经网络。"


def model_digest(results):
    payload = {
        "items": [{
            "index": 0, "title_zh": "指令的语言：体裁与生成式AI",
            "summary": "作者提出指令微调语言模型应被理解为实现一种指令—对话体裁。",
            "results": results,
            "engineering_value": "可以提供分析视角。",
        }],
        "trends": [{"fact": "作者提出体裁分析观点。", "inference": ""}] * 3,
    }
    return _parse_content(json.dumps(payload), "AI论文日报", [ARTICLE])


class PaperConclusionsTests(unittest.TestCase):
    def test_conceptual_model_results_have_neutral_label(self):
        digest = model_digest(CONCLUSION)
        self.assertEqual(digest.mode, "model")
        self.assertFalse(digest.items[0].is_source_excerpt)
        self.assertEqual(digest.items[0].results, CONCLUSION)
        markdown = render_digest("AI论文日报", RUN_DATE, [ARTICLE], digest)
        self.assertIn("- **主要结论**：" + CONCLUSION, markdown)
        self.assertNotIn("**实验结果**", markdown)
        self.assertNotIn("**来源摘要**", markdown)

    def test_empirical_results_and_qualifiers_are_preserved_and_escaped(self):
        results = "在12项任务中准确率从64%升至78%，仅限测试集；[比较] <baseline>。"
        digest = model_digest(results)
        markdown = render_digest("AI论文日报", RUN_DATE, [ARTICLE], digest)
        self.assertIn("- **主要结论**：" + _markdown_text(results), markdown)
        self.assertEqual(digest.items[0].results, results)

    def test_empty_results_and_quick_items_do_not_gain_a_conclusion(self):
        digest = model_digest("")
        markdown = render_digest("AI论文日报", RUN_DATE, [ARTICLE], digest)
        self.assertNotIn("**主要结论**", markdown)
        item = model_digest(CONCLUSION).items[0]
        digest = replace(digest, items=tuple(replace(item, index=i) for i in range(4)))
        markdown = render_digest("AI论文日报", RUN_DATE, [ARTICLE] * 4, digest)
        self.assertEqual(markdown.count("**主要结论**"), 3)
        self.assertNotIn("**主要结论**", markdown.split("## 快速浏览")[1])

    def test_weekly_keeps_new_conclusions_and_legacy_empirical_results(self):
        modern = render_digest("AI论文日报", RUN_DATE, [ARTICLE], model_digest(CONCLUSION))
        legacy_result = "在十二项任务中报告可量化提升，外部泛化仍待验证。"
        legacy = (
            "### [旧论文](https://arxiv.org/abs/2609.00001)\n\n"
            "- **核心摘要**：旧日报的实验摘要。\n"
            "- **实验结果**：" + legacy_result + "\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "AI论文日报"
            folder.mkdir()
            daily = folder / f"{RUN_DATE}.md"
            daily.write_text(modern + "\n" + legacy, encoding="utf-8")
            before = daily.read_bytes()
            weekly = generate_weekly_report(root, RUN_DATE).read_text(encoding="utf-8")
            self.assertEqual(daily.read_bytes(), before)
        self.assertIn("结论：" + CONCLUSION, weekly)
        self.assertIn("结果：" + legacy_result, weekly)
        self.assertNotIn("价值：可以提供分析视角。", weekly)


if __name__ == "__main__":
    unittest.main()
