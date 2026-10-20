import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.summarize import (
    EvidenceBoundaryError,
    _parse_content,
    _prompt,
    summarize,
)


# Real empty RSS evidence and offending Oct20 output, with no network/model use.
TORCH = Article(
    "https://huggingface.co/blog/hf-torchneuron",
    "TorchNeuron: running HF models on AWS Trainium is easier than ever",
    "https://huggingface.co/blog/hf-torchneuron",
    "Hugging Face", datetime(2026, 10, 19, tzinfo=timezone.utc), "",
)
BAD = "文章标题强调降低部署门槛，但摘要信息有限，未披露具体支持的模型范围、性能数据或使用步骤，因此其实际适配能力仍需参考原文与后续实践。"
GOOD = "Hugging Face 介绍 TorchNeuron 在 AWS Trainium 上运行模型。"


def payload(text=GOOD, **fields):
    return {
        "items": [{"index": 0, "title_zh": "TorchNeuron 模型运行工具", "summary": text, **fields}],
        "trends": [{"fact": "Hugging Face 介绍了 TorchNeuron。", "inference": ""} for _ in range(3)],
    }


class EvidenceBoundaryTests(unittest.TestCase):
    def test_oct20_empty_feed_does_not_prove_source_omission(self):
        with self.assertRaises(EvidenceBoundaryError):
            _parse_content(json.dumps(payload(BAD)), "AI科技动态", [TORCH])

    def test_oct19_itau_disclosure_claim_is_rejected(self):
        with self.assertRaises(EvidenceBoundaryError):
            _parse_content(json.dumps(payload("案例未披露使用规模或效果指标。")), "AI科技动态", [TORCH])

    def test_published_benchmark_should_not_be_framed_as_waiting(self):
        with self.assertRaises(EvidenceBoundaryError):
            _parse_content(json.dumps(payload(watch="后续可观察 OpenAI 是否公开评测细节与基线结果。")), "AI科技动态", [TORCH])

    def test_scoped_collector_uncertainty_is_preserved(self):
        text = "本次采集的摘要未给出支持模型的清单。"
        result = _parse_content(json.dumps(payload(text)), "AI科技动态", [TORCH])
        self.assertEqual(result.items[0].summary, text)
        self.assertEqual(result.mode, "model")

    def test_scoped_clause_does_not_license_unscoped_next_clause(self):
        with self.assertRaises(EvidenceBoundaryError):
            _parse_content(json.dumps(payload("本次采集的摘要未给出细节，但官方未公布性能数据。")), "AI科技动态", [TORCH])

    def test_scoped_phrase_does_not_license_second_claim_without_comma(self):
        with self.assertRaises(EvidenceBoundaryError):
            _parse_content(json.dumps(payload("本次采集的摘要未给出细节且官方未公布性能数据。")), "AI科技动态", [TORCH])

    def test_real_source_negative_statement_remains_supported(self):
        text = "作者明确表示尚未公布完整代码。"
        article = replace(TORCH, summary=text)
        result = _parse_content(json.dumps(payload(text)), "AI科技动态", [article])
        self.assertEqual(result.items[0].summary, text)

    def test_actual_uncertainty_is_not_mechanically_banned(self):
        text = "作者称实验只覆盖 Linux，Windows 兼容性尚未验证。"
        result = _parse_content(json.dumps(payload(text)), "AI科技动态", [TORCH])
        self.assertEqual(result.items[0].summary, text)

    def test_guard_covers_all_item_text_fields(self):
        for name in ("title_zh", "summary", "background", "impact", "watch", "value",
                     "research_problem", "method", "results", "limitations",
                     "engineering_value", "discussion_focus"):
            with self.subTest(name=name):
                data = payload()
                data["items"][0][name] = "原文未披露细节。"
                with self.assertRaises(EvidenceBoundaryError):
                    _parse_content(json.dumps(data), "AI科技动态", [TORCH])

    def test_guard_covers_observation_fact_and_inference(self):
        for name in ("fact", "inference"):
            with self.subTest(name=name):
                data = payload()
                data["trends"][0][name] = "原文未披露性能。"
                with self.assertRaises(EvidenceBoundaryError):
                    _parse_content(json.dumps(data), "AI科技动态", [TORCH])

    def test_retry_can_repair_without_extra_provider(self):
        calls = []
        def request(url, headers, body):
            calls.append(body["messages"])
            data = payload(BAD if len(calls) == 1 else GOOD)
            return {"choices": [{"message": {"content": json.dumps(data)}}]}
        result = summarize("AI科技动态", [TORCH], "stub", None, require_model=True, request=request)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.mode, "model")
        self.assertIn("删除或限定", calls[1][-1]["content"])

    def test_exhausted_boundary_retry_falls_back_not_whole_feed_failure(self):
        calls = []
        def request(url, headers, body):
            calls.append(url)
            data = payload(BAD)
            data["items"].append({"index": 1, "title_zh": "安全条目", "summary": GOOD})
            data["trends"][0]["fact"] = "原文未披露性能。"
            return {"choices": [{"message": {"content": json.dumps(data)}}]}
        result = summarize("AI科技动态", [TORCH, TORCH], "stub", "unused-stub",
                           require_model=True, request=request)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result.mode, "model-with-evidence-fallback")
        self.assertEqual(result.items[0].summary, TORCH.title)
        self.assertEqual(result.items[1].summary, GOOD)
        self.assertNotIn("未披露", result.trends[0].fact)
        self.assertEqual(result.trends[1].fact, "Hugging Face 介绍了 TorchNeuron。")

    def test_non_boundary_failure_still_respects_require_model(self):
        def request(url, headers, body):
            return {"choices": [{"message": {"content": "{}"}}]}
        with self.assertRaises(RuntimeError):
            summarize("AI科技动态", [TORCH], "stub", None, require_model=True, request=request)

    def test_prompt_explains_partial_evidence(self):
        prompt = _prompt("AI科技动态", [TORCH])
        self.assertIn("不代表完整原文", prompt)
        self.assertIn("摘要为空或只含分类标签时", prompt)


if __name__ == "__main__":
    unittest.main()
