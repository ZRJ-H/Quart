from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeedSource:
    name: str
    url: str


AI_SOURCES = (
    FeedSource("OpenAI", "https://openai.com/news/rss.xml"),
    FeedSource("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    FeedSource("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    FeedSource("Microsoft Research", "https://www.microsoft.com/en-us/research/feed/"),
    FeedSource("Google Research", "https://research.google/blog/rss/"),
)

NEWS_SOURCES = (
    FeedSource("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    FeedSource("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    FeedSource("NPR World", "https://feeds.npr.org/1004/rss.xml"),
)
