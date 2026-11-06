"""Offline request contract; no provider calls or live quality claims."""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.summarize import summarize


ARTICLE = Article("fixture", "A source title", "https://example.test/source", "fixture",
                  datetime(2026, 10, 30, tzinfo=timezone.utc), "A source abstract.")
GOOD = {"items": [{"index": 0, "title_zh": "测试标题", "summary": "测试中文摘要。"}],
        "trends": [{"fact": "测试来源事实。", "inference": ""} for _ in range(3)]}
DIRECT = "https://api.deepseek.com/chat/completions"
GO = "https://opencode.ai/zen/go/v1/chat/completions"


class DigestModelContractTests(unittest.TestCase):
    def run_request(self, category="Hacker News", direct="fixture", go="fixture", reply=None):
        calls = []
        def request(url, headers, body):
            calls.append((url, copy.deepcopy(body)))
            data = GOOD if reply is None else reply(url, len(calls))
            return {"choices": [{"message": {"content": json.dumps(data)}}]}
        with redirect_stdout(io.StringIO()):
            result = summarize(category, [ARTICLE], direct, go, request=request)
        return result, calls

    def test_four_categories_use_direct_flash_non_thinking_json_with_original_cap(self):
        for category in ("Hacker News", "AI论文日报", "AI科技动态", "时政要闻"):
            with self.subTest(category=category):
                result, calls = self.run_request(category)
                self.assertEqual(len(calls), 1)
                url, body = calls[0]
                self.assertEqual(url, DIRECT)
                self.assertEqual(body["model"], "deepseek-flash")
                self.assertEqual(body["thinking"], {"type": "disabled"})
                self.assertEqual(body["response_format"], {"type": "json_object"})
                self.assertEqual(body["temperature"], 0.1)
                self.assertEqual(body["max_tokens"], 9000)
                self.assertNotIn("reasoning_effort", body)
                self.assertEqual(result.mode, "model")

    def test_evidence_retries_keep_flash_contract_and_three_attempt_fallback(self):
        bad = copy.deepcopy(GOOD)
        bad["items"][0]["summary"] = "法院裁定败诉。"
        result, calls = self.run_request(reply=lambda *_: bad)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result.mode, "model-with-evidence-fallback")
        for url, body in calls:
            self.assertEqual(url, DIRECT)
            self.assertEqual(body["thinking"], {"type": "disabled"})
            self.assertEqual(body["max_tokens"], 9000)

    def test_invalid_direct_output_still_uses_unchanged_go_pro_backup(self):
        result, calls = self.run_request(reply=lambda url, _: {} if url == DIRECT else GOOD)
        self.assertEqual([url for url, _ in calls], [DIRECT] * 3 + [GO])
        body = calls[-1][1]
        self.assertEqual(body["model"], "deepseek-v4-pro")
        self.assertNotIn("thinking", body)
        self.assertEqual(body["max_tokens"], 9000)
        self.assertEqual(result.mode, "model")

    def test_go_only_keeps_original_request_without_direct_only_options(self):
        _, calls = self.run_request(direct=None)
        self.assertEqual(len(calls), 1)
        url, body = calls[0]
        self.assertEqual(url, GO)
        self.assertEqual(body["model"], "deepseek-v4-pro")
        self.assertNotIn("thinking", body)

    def test_provider_exhaustion_and_no_key_do_not_add_requests(self):
        result, calls = self.run_request(reply=lambda *_: {})
        self.assertEqual([url for url, _ in calls], [DIRECT] * 3 + [GO] * 3)
        self.assertEqual(result.mode, "evidence-only")
        result, calls = self.run_request(direct=None, go=None)
        self.assertEqual(calls, [])
        self.assertEqual(result.mode, "evidence-only")


if __name__ == "__main__":
    unittest.main()
