import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.daily_digest.collectors import CollectionError
from scripts.daily_digest.models import Article
from scripts.daily_digest.pipeline import run_pipeline
from scripts.daily_digest.summarize import summarize
from scripts.daily_digest.weekly import generate_weekly_report


RUN_DATE = date(2026, 9, 11)


def articles(category, count):
    result = []
    for index in range(count):
        extra = {"authors": ["Author"], "categories": ["cs.AI"]} if category == "AI论文日报" else {}
        if category == "Hacker News":
            extra = {"top_comments": ["A concrete discussion point."]}
        result.append(
            Article(
                f"{category}-{index}",
                f"{category} item {index}",
                f"https://example.com/{category}/{index}",
                "Fixture Source",
                datetime(2026, 9, 11, index % 12, tzinfo=timezone.utc),
                f"Evidence summary for {category} item {index}.",
                score=100 - index,
                comments=20 - index,
                discussion_url=f"https://news.ycombinator.com/item?id={index + 1}" if category == "Hacker News" else "",
                extra=extra,
            )
        )
    return result


FIXTURES = {
    "AI科技动态": articles("AI科技动态", 8),
    "时政要闻": articles("时政要闻", 8),
    "AI论文日报": articles("AI论文日报", 5),
    "Hacker News": articles("Hacker News", 8),
}


def fixture_collectors(overrides=None):
    values = {**FIXTURES, **(overrides or {})}
    return {category: (lambda now, rows=rows: rows) for category, rows in values.items()}


def fallback_summarizer(category, rows):
    return summarize(category, rows, api_key=None, go_key=None)


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class DailyPipelineTests(unittest.TestCase):
    def test_pipeline_writes_four_valid_today_files_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            first = run_pipeline(root, RUN_DATE, fixture_collectors(), fallback_summarizer)
            before = snapshot(root)
            second = run_pipeline(root, RUN_DATE, fixture_collectors(), fallback_summarizer)

            expected = {
                "AI科技动态/2026-09-11.md",
                "时政要闻/2026-09-11.md",
                "AI论文日报/2026-09-11.md",
                "Hacker News/2026-09-11.md",
            }
            self.assertEqual({path.relative_to(root).as_posix() for path in first}, expected)
            self.assertEqual({path.relative_to(root).as_posix() for path in second}, expected)
            self.assertEqual(snapshot(root), before)
            for relative in expected:
                self.assertIn("https://example.com/", (root / relative).read_text(encoding="utf-8"))

    def test_pipeline_replaces_local_codex_note_when_sources_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_pipeline(root, RUN_DATE, fixture_collectors(), fallback_summarizer)
            reviewed = root / "AI科技动态" / "2026-09-11.md"
            reviewed.write_text("摘要模式：Codex 中文精修\n人工核验内容\n", encoding="utf-8")
            changed = articles("AI科技动态", 8)
            changed[0] = Article(
                "changed",
                "Changed source",
                "https://example.com/changed",
                "Fixture Source",
                datetime(2026, 9, 11, 10, tzinfo=timezone.utc),
                "Changed evidence.",
            )

            run_pipeline(root, RUN_DATE, fixture_collectors({"AI科技动态": changed}), fallback_summarizer)

            updated = reviewed.read_text(encoding="utf-8")
            self.assertNotIn("摘要模式：Codex 中文精修", updated)
            self.assertIn("https://example.com/changed", updated)
    def test_failed_category_leaves_existing_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "AI科技动态" / "2026-09-11.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("existing", encoding="utf-8")
            before = snapshot(root)

            with self.assertRaisesRegex(CollectionError, "AI论文日报"):
                run_pipeline(root, RUN_DATE, fixture_collectors({"AI论文日报": []}), fallback_summarizer)

            self.assertEqual(snapshot(root), before)

    def test_weekly_report_uses_current_iso_week_and_daily_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            long_summary = "这是一段用于周报的中文简要描述，说明事件发生了什么、关键事实是什么以及后续值得关注的影响。" * 5
            for category in FIXTURES:
                folder = root / category
                folder.mkdir(parents=True)
                (folder / "2026-09-10.md").write_text(
                    f"# {category}\n\n### [已核验的中文标题](https://example.com/{category})\n\n- **原标题**：Verified headline\n- **核心摘要**：{long_summary}\n",
                    encoding="utf-8",
                )

            report = generate_weekly_report(root, RUN_DATE)
            text = report.read_text(encoding="utf-8")

            self.assertEqual(report.relative_to(root).as_posix(), "周报/2026-W37.md")
            self.assertIn("[[AI科技动态/2026-09-10]]", text)
            self.assertIn("已核验的中文标题", text)
            self.assertIn("摘要：这是一段用于周报的中文简要描述", text)
            excerpt = next(line for line in text.splitlines() if line.strip().startswith("- 摘要："))
            self.assertGreaterEqual(len(excerpt.removeprefix("    - 摘要：")), 120)
            self.assertLessEqual(len(excerpt.removeprefix("    - 摘要：")), 180)
            self.assertIn("https://example.com/", text)


    def test_weekly_report_does_not_repeat_english_trending_description(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "GitHub Trending"
            folder.mkdir(parents=True)
            (folder / "2026-09-11.md").write_text(
                "# GitHub Trending\n\n"
                "### [owner/repo](https://github.com/owner/repo)\n\n"
                "> An English-only project description.\n",
                encoding="utf-8",
            )

            text = generate_weekly_report(root, RUN_DATE).read_text(encoding="utf-8")

            self.assertNotIn("An English-only project description", text)
            self.assertIn("项目简介为英文，详情请查看 GitHub 项目主页", text)
    def test_weekly_report_composes_summary_from_core_and_impact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "AI科技动态"
            folder.mkdir(parents=True)
            core = "核心事实完整交代事件主体、动作、关键数据和直接结果。" * 3
            impact = "影响判断说明为什么值得关注以及下一步观察方向。" * 3
            (folder / "2026-09-11.md").write_text(
                "# AI科技动态\n\n"
                "### [中文标题](https://example.com/story)\n\n"
                f"- **核心摘要**：{core}\n"
                "- **背景**：不应优先拼进周报。\n"
                f"- **影响**：{impact}\n",
                encoding="utf-8",
            )

            text = generate_weekly_report(root, RUN_DATE).read_text(encoding="utf-8")

            excerpt = next(line for line in text.splitlines() if line.strip().startswith("- 摘要："))
            self.assertIn("影响：", excerpt)
            self.assertNotIn("不应优先拼进周报", excerpt)

if __name__ == "__main__":
    unittest.main()
