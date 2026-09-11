from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeedSource:
    name: str
    url: str
    kind: str = "feed"


AI_SOURCES = (
    FeedSource("OpenAI", "https://openai.com/news/rss.xml"),
    FeedSource("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    FeedSource("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    FeedSource("Microsoft Research", "https://www.microsoft.com/en-us/research/feed/"),
    FeedSource("Google Research", "https://research.google/blog/rss/"),
)

DOMESTIC_NEWS_SOURCES = (
    FeedSource("新华网时政", "https://www.news.cn/politics/", "xinhua-politics"),
)

INTERNATIONAL_NEWS_SOURCES = (
    FeedSource("联合国新闻", "https://news.un.org/feed/subscribe/zh/news/all/rss.xml"),
    FeedSource("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    FeedSource("NPR World", "https://feeds.npr.org/1004/rss.xml"),
)
