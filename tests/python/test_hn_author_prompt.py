"""Prompt-contract regressions, not proof of model semantic compliance."""
import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.summarize import _prompt

# Nov2 production item 50328251: title-only primary evidence; authorship is
# absent. Comments mention Tao and explicitly ask to identify guest authors.
ARTICLE = Article(
    '50328251', "Mathematics has changed. Let's act like it",
    'https://terrytao.wordpress.com/2026/11/01/mathematics-has-changed-lets-act-like-it/',
    'Hacker News', datetime(2026, 11, 1, 18, 28, 42, tzinfo=timezone.utc),
    "Mathematics has changed. Let's act like it",
    extra={'top_comments': [
        'This is what Terence Tao has been saying about digestion of results for several months now.',
        'Please can we add the name of the guest authors in the titles of these posts?',
    ]},
)


class HNAuthorPromptTests(unittest.TestCase):
    def test_unsigned_primary_cannot_be_attributed_from_comments_or_url(self):
        prompt = _prompt('Hacker News', [ARTICLE])
        self.assertIn('仅当 title/summary 明确署名时才在标题或摘要添加作者', prompt)
        self.assertIn('未提供署名则省略作者，不从 URL、域名、账号名或 top_comments 推断作者', prompt)

    def test_primary_evidence_and_comments_remain_separate_and_unchanged(self):
        evidence = json.loads(_prompt('Hacker News', [ARTICLE]).split('证据 JSON：\n')[1])[0]
        self.assertEqual(evidence['summary'], ARTICLE.title)
        self.assertEqual(evidence['extra'], ARTICLE.extra)
        self.assertEqual(evidence['url'], ARTICLE.url)
        self.assertNotIn('Terence Tao', evidence['summary'])
        self.assertNotIn('Frank Calegari', evidence['summary'])

    def test_explicit_guest_authorship_stays_in_primary_evidence(self):
        # Synthetic positive case, not a claim about the production input.
        signed = replace(ARTICLE, summary='This is a guest post by Frank Calegari.')
        prompt = _prompt('Hacker News', [signed])
        self.assertIn('明确为客座文章时保留客座作者与刊载博客的区别', prompt)
        self.assertEqual(json.loads(prompt.split('证据 JSON：\n')[1])[0]['summary'], signed.summary)


if __name__ == '__main__':
    unittest.main()
