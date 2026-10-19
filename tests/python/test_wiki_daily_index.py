import contextlib
import importlib.util
import io
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.daily_digest.models import Article
from scripts.daily_digest.render import render_digest
from scripts.daily_digest.summarize import DigestSummary, ItemSummary, TrendSummary


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build-wiki-index.py"
SPEC = importlib.util.spec_from_file_location("wiki_daily_index", SCRIPT)
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class WikiDailyIndexTests(unittest.TestCase):
    def render(self, category, count):
        articles = [
            Article(
                str(index), f"Source title {index}", f"https://example.com/{index}",
                "Test source", datetime(2026, 10, 19, tzinfo=timezone.utc),
                f"Source evidence {index}.",
            )
            for index in range(count)
        ]
        summaries = tuple(
            ItemSummary(
                index, f"测试条目 {index}", f"核心事实 {index}。",
                background="有据背景。", impact="有据影响。", watch="后续观察。",
                value="阅读价值。", discussion_focus="评论观点。",
                research_problem=f"研究问题 {index}。", method="论文方法。",
                results="实验结果。", limitations="实验局限。",
                engineering_value="工程价值。",
            )
            for index in range(count)
        )
        summary = DigestSummary(
            summaries,
            tuple(TrendSummary(f"趋势依据 {index}。", "编辑判断。") for index in range(3)),
            "model",
        )
        return render_digest(category, date(2026, 10, 19), articles, summary)

    def parse(self, category, markdown):
        _, body = INDEX.parse_frontmatter(markdown)
        return INDEX.parse_h3_blocks(body, INDEX.DAILY_DIRS[category])

    def build(self, root):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return INDEX.build_daily_index(str(root))

    def test_current_hn_renderer_indexes_all_eight_items(self):
        markdown = self.render("Hacker News", 8)
        self.assertIn("## 深度解读", markdown)
        self.assertIn("## 快速浏览", markdown)
        articles = self.parse("Hacker News", markdown)
        self.assertEqual(len(articles), 8)
        self.assertEqual([title for title, _ in articles], [f"[测试条目 {i}](https://example.com/{i})" for i in range(8)])

    def test_current_paper_renderer_indexes_all_five_items(self):
        articles = self.parse("AI论文日报", self.render("AI论文日报", 5))
        self.assertEqual(len(articles), 5)
        self.assertIn("研究问题 0", articles[0][1])
        self.assertIn("核心事实 4", articles[4][1])

    def test_legacy_featured_section_is_preserved(self):
        markdown = "## 📰 今日精选\n\n### [旧条目](https://example.com/legacy)\n旧正文。\n"
        for category in ("Hacker News", "AI论文日报"):
            with self.subTest(category=category):
                self.assertEqual(self.parse(category, markdown), [("[旧条目](https://example.com/legacy)", "旧正文。\n")])

    def test_modern_sections_accept_existing_emoji_normalization(self):
        markdown = "## 🔬 深度解读\n### 深读条目\n深读正文。\n## ⚡ 快速浏览\n### 快览条目\n快览正文。\n"
        for category in ("Hacker News", "AI论文日报"):
            with self.subTest(category=category):
                self.assertEqual([title for title, _ in self.parse(category, markdown)], ["深读条目", "快览条目"])

    def test_overview_trends_and_unknown_sections_stay_excluded(self):
        markdown = "\n".join(
            f"## {section}\n### 不是文章\n说明。"
            for section in ("今日概览", "今日趋势判断", "信息来源说明", "未来新增栏目")
        )
        for category in ("Hacker News", "AI论文日报"):
            with self.subTest(category=category):
                self.assertEqual(self.parse(category, markdown), [])

    def test_transitions_do_not_include_trend_headings_or_duplicate_articles(self):
        for category, count in (("Hacker News", 8), ("AI论文日报", 5)):
            with self.subTest(category=category):
                articles = self.parse(category, self.render(category, count))
                self.assertEqual(len(articles), count)
                self.assertEqual(len({title for title, _ in articles}), count)
                self.assertFalse(any("趋势依据" in body for _, body in articles))

    def test_light_and_full_indexes_cover_both_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for category, count in (("Hacker News", 8), ("AI论文日报", 5)):
                folder = root / category
                folder.mkdir()
                (folder / "2026-10-19.md").write_text(self.render(category, count), encoding="utf-8")
            light, full = self.build(root)
        self.assertEqual(len(light), 13)
        self.assertEqual(len(full), 13)
        self.assertEqual([x["id"] for x in light], [x["id"] for x in full])
        self.assertEqual(len({x["id"] for x in full}), 13)
        self.assertEqual(sum(x["category"] == "hn-daily" for x in full), 8)
        self.assertEqual(sum(x["category"] == "arxiv-daily" for x in full), 5)
        self.assertTrue(all(x["last_updated"] == "2026-10-19" for x in full))
        self.assertTrue(all(x["source_file"].endswith("/2026-10-19") for x in full))

    def test_legacy_and_current_days_coexist_without_rewriting_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "Hacker News"
            folder.mkdir()
            legacy = folder / "2026-06-27.md"
            legacy.write_text("## 今日精选\n### 旧条目\n旧正文。\n", encoding="utf-8")
            modern = folder / "2026-10-19.md"
            modern.write_text(self.render("Hacker News", 8), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            light, full = self.build(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
        self.assertEqual(len(full), 9)
        self.assertEqual({x["source_file"] for x in full}, {"Hacker News/2026-06-27", "Hacker News/2026-10-19"})

    def test_other_daily_category_selection_is_unchanged(self):
        markdown = "## 今日概览\n### 不应收录\n说明。\n## 深度解读\n### 原有条目\n正文。\n"
        for category in ("AI科技动态", "时政要闻", "GitHub Trending"):
            with self.subTest(category=category):
                self.assertEqual([title for title, _ in self.parse(category, markdown)], ["原有条目"])


if __name__ == "__main__":
    unittest.main()
