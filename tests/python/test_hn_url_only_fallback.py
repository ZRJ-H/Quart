import json
import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

from scripts.daily_digest.models import Article
from scripts.daily_digest.collectors import collect_hacker_news
from scripts.daily_digest.pipeline import _fingerprint, _load_cached_articles
from scripts.daily_digest.render import _markdown_text, render_digest
from scripts.daily_digest.summarize import _clip, _parse_content, summarize
from scripts.daily_digest.weekly import generate_weekly_report


RUN_DATE = date(2026, 11, 8)
# Frozen Nov8 collected record from main 187960189ff91095bc7281c8692c0e244315e108.
# The fixture is source evidence, not a reconstruction of the unavailable model reply.
SOURCE = json.loads(
    (Path(__file__).parent / "fixtures" / "hn-url-only-50406563.json").read_text(encoding="utf-8")
)
LEGACY_ARTICLE = Article(**{**SOURCE, "published_at": datetime.fromisoformat(SOURCE["published_at"])})
# Simulate the new collector's verified-link marker separately from the frozen
# legacy record. The original HTML and original model reply are unavailable.
ARTICLE = replace(LEGACY_ARTICLE, extra={**LEGACY_ARTICLE.extra, "hn_summary_is_link_only": True})


def with_source_text(text):
    collected = collect_story(text)
    extra = dict(LEGACY_ARTICLE.extra)
    if collected.extra.get("hn_summary_is_link_only") is True:
        extra["hn_summary_is_link_only"] = True
    return replace(LEGACY_ARTICLE, summary=collected.summary, extra=extra)


def collect_story(text):
    story = dict(type="story", title=ARTICLE.title, url=ARTICLE.url,
                 time=int(ARTICLE.published_at.timestamp()), text=text, kids=[2])

    def fetch_json(url):
        if url.endswith("/topstories.json"):
            return [1]
        if url.endswith("/item/1.json"):
            return story
        if url.endswith("/item/2.json"):
            return dict(text="Comment-only claim.")
        raise AssertionError(url)

    return collect_hacker_news(ARTICLE.published_at + timedelta(hours=1), limit=1, fetch_json=fetch_json)[0]


def payload(count):
    return {
        "items": [
            dict(index=index, title_zh="微软研究院 AI Frontiers 团队的终结", summary="标题谈到微软研究院 AI Frontiers 团队的终结。")
            for index in range(count)
        ],
        "trends": [dict(fact="本条来源标题涉及微软研究院。", inference="") for _ in range(3)],
    }


class HNURLOnlyFallbackTests(unittest.TestCase):
    def assert_title_only(self, article, item):
        self.assertEqual(item.summary, " ".join(article.title.split()))
        self.assertEqual(item.title_zh, article.title)
        self.assertTrue(item.is_source_excerpt)
        for field in ("background", "impact", "watch", "value", "research_problem", "method", "results"):
            self.assertEqual(getattr(item, field), "", field)

    def test_nov8_links_with_verified_collector_marker_use_source_title(self):
        digest = summarize("Hacker News", [ARTICLE], None, None)
        self.assertEqual(digest.mode, "evidence-only")
        self.assert_title_only(ARTICLE, digest.items[0])
        expected_focus = _clip("；".join(ARTICLE.extra["top_comments"]), 180)
        self.assertEqual(digest.items[0].discussion_focus, expected_focus)
        markdown = render_digest("Hacker News", RUN_DATE, [ARTICLE], digest)
        self.assertIn("- **来源标题**：" + _markdown_text(ARTICLE.title), markdown)
        self.assertNotIn("**核心摘要**", markdown)
        self.assertNotIn(ARTICLE.summary, markdown)
        self.assertIn(ARTICLE.url, markdown)
        self.assertIn(ARTICLE.discussion_url, markdown)

    def test_url_only_blank_and_title_only_sources_use_full_title(self):
        examples = (
            "https://example.com/a", "http://example.com/a?x=1&y=2#part",
            "HTTPS://example.com/a", "https://example.com/a https://example.net/b",
            " \nhttps://example.com/a\t\nhttps://example.net/b  ",
            ARTICLE.summary, "", " \n\t", ARTICLE.title,
        )
        for source in examples:
            with self.subTest(source=source):
                article = with_source_text(source)
                self.assert_title_only(article, summarize("Hacker News", [article], None, None).items[0])
        article = replace(ARTICLE, title="First title sentence. " + "Long title " * 30, summary=ARTICLE.summary)
        self.assert_title_only(article, summarize("Hacker News", [article], None, None).items[0])

    def test_real_source_prose_with_urls_is_not_discarded(self):
        for source in (
            "Read https://example.com/a for the source.",
            "https://example.com/a is the project URL.",
            "More details: https://example.com/a https://example.net/b",
            "The author describes the project.",
            "说明见 https://example.com/a 。",
        ):
            with self.subTest(source=source):
                article = with_source_text(source)
                item = summarize("Hacker News", [article], None, None).items[0]
                self.assertEqual(item.summary, source)
                self.assertFalse(item.is_source_excerpt)

    def test_partial_evidence_fallback_marks_deep_and_quick_titles_only(self):
        articles = [ARTICLE] * 5
        data = payload(len(articles))
        # Synthetic, deliberately unsupported output exercises the real guard.
        for index in (0, 4):
            data["items"][index]["summary"] = "原文未披露团队的后续安排。"
        calls = []

        def request(url, headers, body):
            calls.append((url, body["max_tokens"]))
            return {"choices": [{"message": {"content": json.dumps(data)}}]}

        digest = summarize("Hacker News", articles, "stub", "unused", require_model=True, request=request)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(url == "https://api.deepseek.com/chat/completions" and limit == 9000 for url, limit in calls))
        self.assertEqual(digest.mode, "model-with-evidence-fallback")
        for index in (0, 4):
            self.assert_title_only(ARTICLE, digest.items[index])
        for index in (1, 2, 3):
            self.assertEqual(digest.items[index].summary, data["items"][index]["summary"])
            self.assertFalse(digest.items[index].is_source_excerpt)
        self.assertEqual(digest.trends[0].fact, data["trends"][0]["fact"])
        markdown = render_digest("Hacker News", RUN_DATE, articles, digest)
        self.assertEqual(markdown.count("**来源标题**"), 2)
        self.assertEqual(markdown.count("**核心摘要**"), 3)
        self.assertNotIn(ARTICLE.summary, markdown)

    def test_model_cannot_set_internal_source_marker(self):
        data = payload(1)
        data["items"][0]["is_source_excerpt"] = True
        digest = _parse_content(json.dumps(data), "Hacker News", [ARTICLE])
        self.assertEqual(digest.mode, "model")
        self.assertFalse(digest.items[0].is_source_excerpt)
        markdown = render_digest("Hacker News", RUN_DATE, [ARTICLE], digest)
        self.assertIn("**核心摘要**", markdown)
        self.assertNotIn("**来源标题**", markdown)

    def test_title_rendering_escapes_untrusted_markup_and_keeps_comments_separate(self):
        article = replace(ARTICLE, title="<script>unsafe</script> [Title](https://example.net)\nNext", extra={"top_comments": ["Comment-only claim."], "hn_summary_is_link_only": True})
        digest = summarize("Hacker News", [article], None, None)
        self.assert_title_only(article, digest.items[0])
        self.assertNotIn("Comment-only claim", digest.items[0].summary)
        markdown = render_digest("Hacker News", RUN_DATE, [article], digest)
        self.assertIn("- **来源标题**：" + _markdown_text(" ".join(article.title.split())), markdown)
        self.assertNotIn("<script>", markdown)

    def test_no_comments_does_not_invent_discussion(self):
        article = replace(ARTICLE, extra={"hn_summary_is_link_only": True})
        item = summarize("Hacker News", [article], None, None).items[0]
        self.assert_title_only(article, item)
        self.assertEqual(item.discussion_focus, "本次未采集到评论。")

    def test_collector_preserves_prose_next_to_links_before_fallback(self):
        for text, prose in (
            ('<a href="https://example.com/a">https://example.com/a</a><p>Retracted.</p>', "Retracted."),
            ('<a href="https://example.com/a">https://example.com/a</a><p>作者撤回了此前结论。</p>', "作者撤回了此前结论。"),
            ('<a>https://example.com/a</a>Retracted.', "Retracted."),
            ('https://example.com/a<i>Retracted.</i>', "Retracted."),
            ('<p>https://example.com/a</p><p>Retracted.</p>', "Retracted."),
        ):
            with self.subTest(text=text):
                article = collect_story(text)
                self.assertIn(prose, article.summary)
                self.assertNotIn("hn_summary_is_link_only", article.extra)
                item = summarize("Hacker News", [article], None, None).items[0]
                self.assertEqual(item.summary, article.summary)
                self.assertFalse(item.is_source_excerpt)
                self.assertEqual(item.discussion_focus, "Comment-only claim.")

    def test_collector_marks_only_pure_link_fragments(self):
        # Synthetic HTML carrying the two exact URLs from the Nov8 record.
        first = "https://archive.is/AaY5O"
        second = "https://businessexaminer.ca/victoria-articles/item/microsoft..."
        article = collect_story(f'<a href="{first}">{first}</a><p><a href="{second}">{second}</a></p>')
        self.assertEqual(article.summary, first + " " + second)
        self.assertIs(article.extra["hn_summary_is_link_only"], True)
        item = summarize("Hacker News", [article], None, None).items[0]
        self.assert_title_only(article, item)
        self.assertEqual(item.discussion_focus, "Comment-only claim.")

    def test_legacy_flattened_summaries_are_not_guessed_to_be_link_only(self):
        for source in (LEGACY_ARTICLE.summary, "https://example.com/aRetracted.",
                       "https://example.com/a作者撤回了此前结论。", "https://example.com/a"):
            with self.subTest(source=source):
                article = replace(LEGACY_ARTICLE, summary=source)
                item = summarize("Hacker News", [article], None, None).items[0]
                self.assertEqual(item.summary, source)
                self.assertFalse(item.is_source_excerpt)

    def test_collector_retains_non_ascii_url_ambiguity(self):
        for text in ("https://example.com/作者撤回了此前结论。", "https://例子.测试/路径"):
            with self.subTest(text=text):
                article = collect_story(text)
                self.assertEqual(article.summary, text)
                self.assertNotIn("hn_summary_is_link_only", article.extra)
                self.assertEqual(summarize("Hacker News", [article], None, None).items[0].summary, text)

    def test_collector_does_not_split_words_at_inline_markup(self):
        article = collect_story("<p>Re<i>tract</i>ed.</p><p>Details follow.</p>")
        self.assertEqual(article.summary, "Retracted. Details follow.")
        self.assertNotIn("hn_summary_is_link_only", article.extra)

    def test_link_provenance_changes_fingerprint_and_survives_cache(self):
        self.assertNotEqual(_fingerprint([ARTICLE]), _fingerprint([LEGACY_ARTICLE]))
        cached_at = ARTICLE.published_at + timedelta(hours=1)
        cached = {"cached_at": cached_at.isoformat(), "articles": [{**SOURCE, "extra": ARTICLE.extra}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Hacker-News.json").write_text(json.dumps(cached), encoding="utf-8")
            articles = _load_cached_articles(root, "Hacker News", cached_at)
        self.assertEqual(len(articles), 1)
        self.assertIs(articles[0].extra["hn_summary_is_link_only"], True)
        self.assert_title_only(articles[0], summarize("Hacker News", articles, None, None).items[0])

    def test_weekly_summary_reads_source_title(self):
        digest = summarize("Hacker News", [ARTICLE], None, None)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            daily = root / "Hacker News" / f"{RUN_DATE}.md"
            daily.parent.mkdir()
            daily.write_text(render_digest("Hacker News", RUN_DATE, [ARTICLE], digest), encoding="utf-8")
            text = generate_weekly_report(root, RUN_DATE).read_text(encoding="utf-8")
        self.assertIn("摘要：" + _markdown_text(ARTICLE.title), text)
        self.assertNotIn(ARTICLE.summary, text)

    def test_other_categories_keep_existing_fallback_contract(self):
        for category in ("AI科技动态", "时政要闻", "AI论文日报"):
            with self.subTest(category=category):
                item = summarize(category, [ARTICLE], None, None).items[0]
                self.assertEqual(item.summary, ARTICLE.summary)
                self.assertEqual(item.is_source_excerpt, category == "AI论文日报")


if __name__ == "__main__":
    unittest.main()
