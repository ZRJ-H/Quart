"""Offline diagnostics contract: locations only, unchanged guard and fallback."""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.daily_digest.models import Article
from scripts.daily_digest import summarize as module


ARTICLE = Article('private-id-marker', 'Source title', 'https://example.com/private-url',
                  'fixture', datetime(2026, 10, 28, tzinfo=timezone.utc), 'Source abstract.')
BAD = '原文未披露 secret-response-marker。'


def payload(**fields):
    return {'items': [dict(index=0, title_zh='标题。', summary='安全摘要。', **fields),
                      dict(index=1, title_zh='安全标题。', summary='另一条安全摘要。')],
            'trends': [dict(fact='安全观察。', inference='') for _ in range(3)]}


class EvidenceDiagnosticsTests(unittest.TestCase):
    def reject(self, data, category='AI论文日报'):
        with self.assertRaises(module.EvidenceBoundaryError) as caught:
            module._parse_content(json.dumps(data), category, [ARTICLE, ARTICLE])
        return caught.exception

    def test_paper_locations_all_fields_and_trends(self):
        for field in ('title_zh', 'summary', 'background', 'impact', 'watch', 'value',
                      'research_problem', 'method', 'results', 'limitations',
                      'engineering_value', 'discussion_focus'):
            data = payload()
            data['items'][1][field] = BAD
            error = self.reject(data)
            self.assertEqual([asdict(v) for v in error.violations], [dict(
                scope='item', index=1, field=field, rule_id='unsupported_disclosure_claim')])
            self.assertEqual(error.safe_digest.items[0].summary, '安全摘要。')
            self.assertEqual(error.safe_digest.items[1], module._fallback('AI论文日报', [ARTICLE, ARTICLE]).items[1])
        for field in ('fact', 'inference'):
            data = payload()
            data['trends'][2][field] = BAD
            error = self.reject(data)
            self.assertEqual([asdict(v) for v in error.violations], [dict(
                scope='trend', index=2, field=field, rule_id='unsupported_disclosure_claim')])
            self.assertEqual(error.safe_digest.trends[0].fact, '安全观察。')

    def test_hn_multiple_rules_fields_and_comment_exclusion(self):
        data = payload(watch=BAD, discussion_focus='评论者称法院裁定败诉。')
        data['items'][0]['summary'] = '法院裁定败诉。'
        data['trends'][1]['inference'] = '法院裁定败诉。'
        error = self.reject(data, 'Hacker News')
        self.assertEqual([(v.scope, v.index, v.field, v.rule_id) for v in error.violations], [
            ('item', 0, 'summary', 'unsupported_hn_judicial_outcome'),
            ('item', 0, 'watch', 'unsupported_disclosure_claim'),
            ('trend', 1, 'inference', 'unsupported_hn_judicial_outcome'),
        ])
        data['items'][0]['summary'] = '安全摘要。'
        data['items'][0]['watch'] = ''
        data['trends'][1]['inference'] = ''
        self.assertEqual(module._parse_content(json.dumps(data), 'Hacker News', [ARTICLE, ARTICLE]).mode, 'model')
        # Judicial rule remains HN-only; paper guard is not broadened.
        data['items'][0]['summary'] = '法院裁定败诉。'
        self.assertEqual(module._parse_content(json.dumps(data), 'AI论文日报', [ARTICLE, ARTICLE]).mode, 'model')

    def run_summary(self, data, repair=False, default_http=False):
        calls = []
        def request(url, headers, body):
            calls.append(copy.deepcopy(body))
            answer = payload() if repair and len(calls) > 1 else data
            return {'choices': [{'message': {'content': json.dumps(answer)}}]}
        output = io.StringIO()
        with redirect_stdout(output):
            if default_http:
                # Keep the actual default callable; stub its HTTP helper below it.
                class Response:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def read(self): return json.dumps(request('', {}, {})).encode()
                with patch.object(module.urllib.request, 'urlopen', return_value=Response()):
                    result = module.summarize('AI论文日报', [ARTICLE, ARTICLE], 'private-key-marker', 'unused', require_model=True)
            else:
                result = module.summarize('AI论文日报', [ARTICLE, ARTICLE], 'private-key-marker', 'unused', require_model=True, request=request)
        return result, calls, output.getvalue()

    def test_retry_budget_partial_fallback_and_private_content_absence(self):
        data = payload(limitations=BAD)
        result, calls, logs = self.run_summary(data)
        events = [json.loads(line) for line in logs.splitlines()]
        self.assertEqual(len(calls), 3)
        self.assertEqual(result, self.reject(data).safe_digest)
        self.assertEqual([e['action'] for e in events], ['retry', 'retry', 'fallback'])
        self.assertEqual([e['attempt'] for e in events], [1, 2, 3])
        self.assertTrue(all(e['request_mode'] == 'injected' for e in events))
        self.assertTrue(all(e['schema_version'] == 1 for e in events))
        self.assertEqual(set(events[0]), {'event', 'schema_version', 'category', 'model', 'request_mode', 'attempt', 'action', 'violations'})
        for secret in (BAD, 'secret-response-marker', ARTICLE.id, ARTICLE.url, ARTICLE.title,
                       ARTICLE.summary, 'private-key-marker'):
            self.assertNotIn(secret, logs)
        self.assertIn('"rule_id": "unsupported_disclosure_claim"', calls[1]['messages'][-1]['content'])
        self.assertNotIn('secret-response-marker', calls[1]['messages'][-1]['content'])
        self.assertIn(str(self.reject(data)), calls[1]['messages'][-1]['content'])

    def test_repair_logs_only_actual_rejection(self):
        result, calls, logs = self.run_summary(payload(limitations=BAD), repair=True)
        self.assertEqual(result.mode, 'model')
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(logs.splitlines()), 1)
        self.assertEqual(json.loads(logs)['action'], 'retry')

    def test_default_http_path_has_distinct_label_without_network(self):
        result, calls, logs = self.run_summary(payload(limitations=BAD), default_http=True)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(json.loads(line)['request_mode'] == 'default_http' for line in logs.splitlines()))
        self.assertEqual(result.mode, 'model-with-evidence-fallback')

    def test_untrusted_category_cannot_leak_or_inject_log_lines(self):
        def request(*args):
            return {'choices': [{'message': {'content': json.dumps(payload(watch=BAD))}}]}
        output = io.StringIO()
        with redirect_stdout(output):
            module.summarize('secret-category-marker\nforged-log', [ARTICLE, ARTICLE],
                             'stub', None, request=request)
        self.assertEqual(len(output.getvalue().splitlines()), 3)
        self.assertNotIn('secret-category-marker', output.getvalue())
        self.assertTrue(all(json.loads(line)['category'] == 'unknown'
                            for line in output.getvalue().splitlines()))

    def test_safe_output_has_no_diagnostics(self):
        result, calls, logs = self.run_summary(payload())
        self.assertEqual(result.mode, 'model')
        self.assertEqual(len(calls), 1)
        self.assertEqual(logs, '')


if __name__ == '__main__':
    unittest.main()
