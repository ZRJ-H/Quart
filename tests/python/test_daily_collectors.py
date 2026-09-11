import json
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from scripts.daily_digest.collectors import (
    collect_arxiv,
    collect_feed_category,
    collect_hacker_news,
    collect_news_category,
    collect_xinhua_politics,
)
from scripts.daily_digest.sources import FeedSource


NOW = datetime(2026, 9, 11, 12, tzinfo=ZoneInfo("Asia/Shanghai"))

ARXIV_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2609.00001v1</id>
    <title>Reliable Agents</title>
    <link rel="alternate" href="https://arxiv.org/abs/2609.00001" />
    <link rel="related" href="https://arxiv.org/pdf/2609.00001v1" />
    <published>2026-09-11T01:00:00Z</published>
    <updated>2026-09-11T01:00:00Z</updated>
    <summary>We evaluate reliable agents on 12 tasks.</summary>
    <author><name>Alice Example</name></author>
    <category term="cs.AI" />
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2609.00002v1</id>
    <title>Efficient Language Models</title>
    <link rel="alternate" href="https://arxiv.org/abs/2609.00002" />
    <published>2026-09-10T02:00:00Z</published>
    <updated>2026-09-10T02:00:00Z</updated>
    <summary>A compression method reduces memory by 30 percent.</summary>
    <author><name>Bob Example</name></author>
    <category term="cs.CL" />
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2609.00001v2</id>
    <title>Reliable Agents revised</title>
    <link rel="alternate" href="https://arxiv.org/abs/2609.00001" />
    <published>2026-09-11T00:30:00Z</published>
    <updated>2026-09-11T00:30:00Z</updated>
    <summary>Duplicate version.</summary>
  </entry>
</feed>
"""

RSS_FIXTURE = """<?xml version="1.0"?><rss version="2.0"><channel>
  <item><guid>one</guid><title>Official update</title><link>https://example.com/update</link>
  <pubDate>Thu, 11 Sep 2026 00:15:00 GMT</pubDate><description>Verified source detail.</description></item>
</channel></rss>"""


class DailyCollectorTests(unittest.TestCase):
    def test_news_category_keeps_five_domestic_items_in_an_eight_item_digest(self):
        domestic = (FeedSource("国内来源", "https://domestic.example/feed"),)
        international = (FeedSource("国际来源", "https://international.example/feed"),)

        def rss(prefix, count, minute_offset):
            items = "".join(
                f"<item><guid>{prefix}-{index}</guid><title>{prefix} {index}</title>"
                f"<link>https://example.com/{prefix}/{index}</link>"
                f"<pubDate>Fri, 11 Sep 2026 0{(index + minute_offset) % 8}:00:00 GMT</pubDate>"
                f"<description>{prefix} evidence {index}</description></item>"
                for index in range(count)
            )
            return f'<?xml version="1.0"?><rss version="2.0"><channel>{items}</channel></rss>'

        def fake_fetch(url):
            return rss("国内", 7, 0) if "domestic" in url else rss("国际", 7, 1)

        items = collect_news_category(domestic, international, NOW, limit=8, domestic_minimum=5, fetch_text=fake_fetch)

        self.assertEqual(len(items), 8)
        self.assertEqual(sum(item.source == "国内来源" for item in items), 5)
        self.assertTrue(all(item.source == "国内来源" for item in items[:5]))

    def test_xinhua_page_collector_reads_current_links_and_article_descriptions(self):
        source = FeedSource("新华网时政", "https://www.news.cn/politics/", "xinhua-politics")
        listing = """
        <div id="recommendDepth">
          <a href='https://www.news.cn/politics/20260911/first/c.html'>国内政策新进展</a>
          <a href='https://www.news.cn/politics/20260910/second/c.html'>民生保障新措施</a>
          <a href='https://www.news.cn/politics/20260901/old/c.html'>过期内容</a>
        </div>
        """
        details = {
            "https://www.news.cn/politics/20260911/first/c.html":
                '<meta name="description" content="有关部门公布政策执行范围、关键措施和后续安排。">'
                '<p>发布会介绍了政策覆盖对象、执行部门和正式实施时间，并披露了首批工作安排。</p>'
                '<p>有关部门表示将继续公布配套细则，并根据执行情况开展后续评估。</p>',
            "https://www.news.cn/politics/20260910/second/c.html":
                '<meta name="description" content="报道介绍民生保障措施及其适用对象。">',
        }

        def fake_fetch(url):
            return listing if url.endswith("/politics/") else details[url]

        items = collect_xinhua_politics(source, NOW, limit=5, fetch_text=fake_fetch)

        self.assertEqual([item.title for item in items], ["国内政策新进展", "民生保障新措施"])
        self.assertIn("有关部门公布政策执行范围、关键措施和后续安排。", items[0].summary)
        self.assertIn("发布会介绍了政策覆盖对象、执行部门和正式实施时间", items[0].summary)
        self.assertIn("有关部门表示将继续公布配套细则", items[0].summary)
        self.assertEqual(items[0].published_at.date().isoformat(), "2026-09-11")

    def test_feed_category_survives_one_broken_source(self):
        sources = (
            FeedSource("Broken", "https://broken.example/feed"),
            FeedSource("Working", "https://working.example/feed"),
        )

        def fake_fetch(url):
            if "broken" in url:
                raise OSError("source unavailable")
            return RSS_FIXTURE

        items = collect_feed_category(sources, NOW, limit=8, fetch_text=fake_fetch)

        self.assertEqual([item.id for item in items], ["one"])
        self.assertEqual(items[0].source, "Working")

    def test_arxiv_combines_categories_and_removes_duplicate_papers(self):
        seen_urls = []

        def fake_fetch(url):
            seen_urls.append(url)
            return ARXIV_FIXTURE

        papers = collect_arxiv(NOW, limit=5, fetch_text=fake_fetch)

        self.assertEqual([paper.id for paper in papers], ["2609.00001", "2609.00002"])
        self.assertEqual(papers[0].extra["authors"], ["Alice Example"])
        self.assertEqual(papers[0].extra["categories"], ["cs.AI"])
        self.assertIn("cat%3Acs.AI", seen_urls[0])

    def test_arxiv_falls_back_to_official_rss_when_api_is_unavailable(self):
        seen_urls = []

        def fake_fetch(url):
            seen_urls.append(url)
            if "api/query" in url:
                raise OSError("API unavailable")
            return ARXIV_FIXTURE

        papers = collect_arxiv(NOW, limit=5, fetch_text=fake_fetch)

        self.assertEqual([paper.id for paper in papers], ["2609.00001", "2609.00002"])
        self.assertTrue(any("rss.arxiv.org/rss/cs.AI" in url for url in seen_urls))

    def test_hacker_news_collects_ranked_stories_and_discussion_evidence(self):
        story_time = int(datetime(2026, 9, 11, 1, tzinfo=timezone.utc).timestamp())
        payloads = {
            "topstories.json": [101, 102, 103],
            "item/101.json": {
                "id": 101,
                "type": "story",
                "title": "First story",
                "url": "https://example.com/first",
                "time": story_time,
                "score": 420,
                "descendants": 88,
                "kids": [201],
            },
            "item/102.json": {
                "id": 102,
                "type": "story",
                "title": "Second story",
                "url": "https://example.com/second",
                "time": story_time - 60,
                "score": 200,
                "descendants": 30,
                "kids": [],
            },
            "item/201.json": {"id": 201, "type": "comment", "text": "<p>First discussion point</p>"},
            "item/103.json": {
                "id": 103,
                "type": "story",
                "title": "Low ranked story",
                "url": "https://example.com/low",
                "time": story_time - 120,
                "score": 1,
                "descendants": 1,
                "kids": [203],
            },
            "item/203.json": {"id": 203, "type": "comment", "text": "This should not be fetched."},
        }
        requested = []

        def fake_fetch(url):
            key = url.split("/v0/")[1]
            requested.append(key)
            return json.loads(json.dumps(payloads[key]))

        items = collect_hacker_news(NOW, limit=2, fetch_json=fake_fetch)

        self.assertEqual([(item.score, item.comments) for item in items], [(420, 88), (200, 30)])
        self.assertEqual(items[0].discussion_url, "https://news.ycombinator.com/item?id=101")
        self.assertEqual(items[0].extra["top_comments"], ["First discussion point"])
        self.assertNotIn("item/203.json", requested)


if __name__ == "__main__":
    unittest.main()
