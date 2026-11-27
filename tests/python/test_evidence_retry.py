"""Real Oct30 source snapshot, simulated model replies; never replay a live model."""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from scripts.daily_digest.models import Article
from scripts.daily_digest.summarize import EvidenceBoundaryError, _parse_content, summarize


def articles():
    path = Path(__file__).parent / "fixtures" / "hn-20261030-source.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["articles"]
    return [Article(**dict(row, published_at=datetime.fromisoformat(row["published_at"]))) for row in rows]


def payload():
    # Deliberately minimal fixture text: this is NOT recovered model output.
    titles = ["帕特里克·斯图尔特去世", "帖子称币安被盗56亿美元", "LLM文风",
              "H.264很神奇（2016）", "在Minecraft和Mindustry运行AI智能体群",
              "在Raspberry Pi Pico 2 W上运行游戏的小型世界模型",
              "自动关闭macOS本地网络权限弹窗", "Herdr发布原生应用"]
    return {"items": [{"index": i, "title_zh": title, "summary": "条目标题：" + title + "。"}
                      for i, title in enumerate(titles)],
            "trends": [{"fact": "本次收录包含LLM文风条目。", "inference": ""} for _ in range(3)]}


class EvidenceRetryTests(unittest.TestCase):
    def run_summary(self, reply):
        calls = []
        def request(url, headers, body):
            calls.append((url, copy.deepcopy(body)))
            data = reply(len(calls), body)
            return {"choices": [{"message": {"content": json.dumps(data, ensure_ascii=False)}}]}
        with redirect_stdout(io.StringIO()):
            result = summarize("Hacker News", articles(), "stub", "unused-stub",
                               require_model=True, request=request)
        return result, calls

    def test_five_item_repair_receives_exact_locations_without_evidence_as_instructions(self):
        bad = payload()
        indexes = (1, 2, 4, 5, 7)  # Matches observed fallback positions, not known causes.
        for i in indexes:
            bad["items"][i]["value"] = "原文未披露细节。private-model-marker"
        def reply(attempt, body):
            if attempt == 1:
                return bad
            guidance = body["messages"][-1]["content"]
            for i in indexes:
                self.assertIn(f'"index": {i}', guidance)
            self.assertIn('"field": "value"', guidance)
            self.assertIn('"rule_id": "unsupported_disclosure_claim"', guidance)
            self.assertIn("零基", guidance)
            self.assertIn("空字符串", guidance)
            self.assertNotIn("private-model-marker", guidance)
            for article in articles():
                self.assertNotIn(article.url, guidance)
            return payload()
        result, calls = self.run_summary(reply)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.mode, "model")
        self.assertEqual([x.title_zh for x in result.items], [x["title_zh"] for x in payload()["items"]])
        self.assertTrue(all(body["max_tokens"] == 9000 for _, body in calls))
        self.assertEqual({url for url, _ in calls}, {"https://api.deepseek.com/chat/completions"})

    def test_exhausted_retry_keeps_exact_original_fallback_and_budget(self):
        bad = payload()
        for i in (1, 2, 4, 5, 7):
            bad["items"][i]["summary"] = "法院已裁定败诉。"
        with self.assertRaises(EvidenceBoundaryError) as caught:
            _parse_content(json.dumps(bad), "Hacker News", articles())
        result, calls = self.run_summary(lambda *_: bad)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result, caught.exception.safe_digest)
        self.assertEqual(result.mode, "model-with-evidence-fallback")
        self.assertIn('"rule_id": "unsupported_hn_judicial_outcome"', calls[1][1]["messages"][-1]["content"])
        self.assertEqual(len({url for url, _ in calls}), 1)

    def test_trend_locations_and_required_field_repair(self):
        bad = payload()
        bad["items"][0]["summary"] = "原文未披露细节。"
        bad["trends"][2]["inference"] = "法院裁定败诉。"
        result, calls = self.run_summary(lambda attempt, _: bad if attempt == 1 else payload())
        guidance = calls[1][1]["messages"][-1]["content"]
        self.assertIn('"scope": "trend", "index": 2, "field": "inference"', guidance)
        self.assertIn('"scope": "item", "index": 0, "field": "summary"', guidance)
        self.assertIn("title_zh、summary 和 trend.fact", guidance)
        self.assertIn("中文", guidance)
        self.assertEqual(result.mode, "model")

    def test_structural_errors_do_not_get_evidence_locations(self):
        result, calls = self.run_summary(lambda attempt, _: {} if attempt == 1 else payload())
        guidance = calls[1][1]["messages"][-1]["content"]
        self.assertNotIn("rule_id", guidance)
        self.assertIn("Model item count", guidance)
        self.assertEqual(result.mode, "model")


if __name__ == "__main__":
    unittest.main()
