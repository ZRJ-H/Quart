import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from scripts.daily_digest.feeds import deduplicate, parse_feed, select_recent
from scripts.daily_digest.models import Article


RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <guid>rss-model</guid>
      <title>Model release</title>
      <link>https://example.com/model</link>
      <pubDate>Thu, 11 Sep 2026 00:15:00 GMT</pubDate>
      <description><![CDATA[<p>Measured result, <b>not HTML</b>.</p>]]></description>
    </item>
  </channel>
</rss>
"""

ATOM_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>2609.00001</id>
    <title>Agent evaluation</title>
    <link rel="alternate" href="https://arxiv.org/abs/2609.00001" />
    <published>2026-09-10T23:30:00Z</published>
    <summary>  A reproducible evaluation.  </summary>
  </entry>
</feed>
"""


class DailyFeedTests(unittest.TestCase):
    def test_parse_feed_normalizes_rss_and_atom(self):
        rss = parse_feed(RSS_FIXTURE, "Fixture RSS")
        atom = parse_feed(ATOM_FIXTURE, "Fixture Atom")

        self.assertEqual(rss[0].title, "Model release")
        self.assertEqual(rss[0].url, "https://example.com/model")
        self.assertEqual(rss[0].published_at.isoformat(), "2026-09-11T00:15:00+00:00")
        self.assertEqual(rss[0].summary, "Measured result, not HTML.")
        self.assertEqual(atom[0].id, "2609.00001")
        self.assertEqual(atom[0].url, "https://arxiv.org/abs/2609.00001")

    def test_select_recent_uses_48_hour_fallback_and_deduplicates(self):
        articles = [
            Article("today", "Today", "https://example.com/today", "Source", datetime(2026, 9, 11, 1, tzinfo=timezone.utc), "Today summary"),
            Article("duplicate", "Today duplicate", "https://example.com/today?utm_source=rss", "Source", datetime(2026, 9, 11, 0, tzinfo=timezone.utc), "Duplicate"),
            Article("yesterday", "Yesterday", "https://example.com/yesterday", "Source", datetime(2026, 9, 10, 1, tzinfo=timezone.utc), "Yesterday summary"),
            Article("old", "Old", "https://example.com/old", "Source", datetime(2026, 9, 8, 1, tzinfo=timezone.utc), "Old summary"),
        ]
        now = datetime(2026, 9, 11, 12, tzinfo=ZoneInfo("Asia/Shanghai"))

        selected = select_recent(deduplicate(articles), now, limit=3)

        self.assertEqual([article.id for article in selected], ["today", "yesterday"])

    def test_article_rejects_non_http_urls(self):
        with self.assertRaisesRegex(ValueError, "HTTP"):
            Article("bad", "Bad", "javascript:alert(1)", "Source", datetime.now(timezone.utc), "Bad")


if __name__ == "__main__":
    unittest.main()
