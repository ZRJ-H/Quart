import unittest
from datetime import date, datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.render import _markdown_url, render_digest
from scripts.daily_digest.summarize import DigestSummary, ItemSummary, TrendSummary


class DailyRenderingSecurityTests(unittest.TestCase):
    def test_untrusted_feed_and_model_fields_cannot_emit_active_html_or_unsafe_links(self):
        article = Article(
            "malicious",
            "<img src=x onerror=alert(1)>",
            "https://example.com/x)[owned](javascript:alert(1))",
            "<script>alert(1)</script>",
            datetime(2026, 9, 14, tzinfo=timezone.utc),
            "source evidence",
            discussion_url="https://example.com/y)[owned](javascript:alert(2))",
            extra={
                "authors": ["<svg onload=alert(3)>"] ,
                "categories": ["cs.AI"],
            },
        )
        item = ItemSummary(
            0,
            "safe](javascript:alert(4))",
            "<iframe srcdoc='<script>alert(5)</script>'></iframe>",
            background="<details open ontoggle=alert(6)>",
            impact="<img src=x onerror=alert(7)>",
            watch="<svg onload=alert(8)>",
            value="<a href=javascript:alert(9)>click</a>",
            discussion_focus="<video onerror=alert(10)>",
        )
        summary = DigestSummary(
            (item,),
            (
                TrendSummary("<script>alert(11)</script>", "<img src=x onerror=alert(12)>"),
            ),
            "model",
        )

        markdown = render_digest("Hacker News", date(2026, 9, 14), [article], summary)

        self.assertNotRegex(markdown, r"(?i)<(?:script|img|svg|iframe|details|a|video)\b")
        self.assertNotIn("](javascript:", markdown.lower())
        self.assertIn("&lt;script&gt;", markdown)
        self.assertIn(r"\]\(javascript:alert\(1\)\)", markdown)
        self.assertEqual(_markdown_url("javascript:alert(1)"), "about:blank")
        self.assertEqual(
            _markdown_url('https://example.com\"><img src=x onerror=alert(13)>'),
            "about:blank",
        )

    def test_safe_http_links_and_readable_text_are_preserved(self):
        article = Article(
            "safe",
            "Safe [bracket] title",
            "https://example.com/articles/a_(b)?x=1&y=2",
            "Safe & Trusted",
            datetime(2026, 9, 14, tzinfo=timezone.utc),
            "source evidence",
        )
        item = ItemSummary(
            0,
            "Readable [summary]",
            "Plain summary.",
            background="Plain background.",
            impact="Plain impact.",
            watch="Plain watch.",
            value="Plain value.",
        )
        summary = DigestSummary(
            (item,),
            (TrendSummary("Plain fact.", "Plain inference."),),
            "model",
        )

        markdown = render_digest("AI科技动态", date(2026, 9, 14), [article], summary)

        self.assertIn("Readable \\[summary\\]", markdown)
        self.assertIn("Safe \\[bracket\\] title", markdown)
        self.assertIn(r"https://example.com/articles/a_\(b\)?x=1&y=2", markdown)
        self.assertIn("Safe &amp; Trusted", markdown)


if __name__ == "__main__":
    unittest.main()
