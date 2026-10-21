import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from scripts.daily_digest.models import Article
from scripts.daily_digest.summarize import (
    EvidenceBoundaryError, _parse_content, _prompt, summarize,
)

# Oct21 production evidence: primary summary is only the title, while the
# comment quotes a general court principle, not a ruling against Ofcom.
ARTICLE = Article(
    '50167028', 'Ofcom concedes defeat in 4chan case',
    'https://prestonbyrne.com/2026/10/20/ofcom-concedes-defeat/',
    'Hacker News', datetime(2026, 10, 20, tzinfo=timezone.utc),
    'Ofcom concedes defeat in 4chan case',
    extra={'top_comments': [
        'This quote from the court is amazing: American courts generally decline '
        'to enforce foreign judgments that violate the United States Constitution. '
        'Was the defeat a planned showing to justify future action?',
    ]},
)
BAD = 'Hacker News 讨论 Ofcom 在 4chan 相关案件中败诉一事。'
GOOD = 'Hacker News 讨论一篇把 Ofcom 的表态称为认输的文章。'


def payload(summary=GOOD, **fields):
    return {'items': [dict(index=0, title_zh='Ofcom 与 4chan 执法争议', summary=summary, **fields)],
            'trends': [dict(fact='Hacker News 讨论跨境执法。', inference='') for _ in range(3)]}


def parse(data, article=ARTICLE):
    return _parse_content(json.dumps(data), 'Hacker News', [article])


class HNJudicialEvidenceTests(unittest.TestCase):
    def test_actual_oct21_rhetorical_defeat_cannot_become_court_loss(self):
        with self.assertRaises(EvidenceBoundaryError):
            parse(payload(BAD))

    def test_comment_court_and_judgment_words_are_not_primary_support(self):
        article = replace(ARTICLE, extra={'top_comments': ['The court ruled against Ofcom.']})
        with self.assertRaises(EvidenceBoundaryError):
            parse(payload(BAD), article)

    def test_explicit_primary_decision_preserves_summary(self):
        for title in ('Court ruled against Ofcom in the case', 'Ofcom loses legal challenge'):
            article = replace(ARTICLE, title=title, summary='')
            self.assertEqual(parse(payload(BAD), article).items[0].summary, BAD)

    def test_explicit_primary_chinese_decision_preserves_summary(self):
        article = replace(ARTICLE, summary='法院裁定 Ofcom 败诉。')
        self.assertEqual(parse(payload(BAD), article).mode, 'model')

    def test_negated_or_hypothetical_primary_cannot_license_outcome(self):
        for title in ('Court has not ruled on the Ofcom case',
                      'What if Ofcom lost the case?', 'Ofcom 并非败诉',
                      'Ofcom has not lost the case', '并非法院裁定 Ofcom 败诉。',
                      '法院未裁定 Ofcom 败诉', "Ofcom hasn't lost the case",
                      'Has Ofcom lost the case?'):
            with self.subTest(title=title):
                with self.assertRaises(EvidenceBoundaryError):
                    parse(payload(BAD), replace(ARTICLE, title=title, summary=''))

    def test_trends_cannot_borrow_a_primary_outcome_without_provenance(self):
        for name in ('fact', 'inference'):
            data = payload()
            data['trends'][0][name] = BAD
            with self.subTest(name=name), self.assertRaises(EvidenceBoundaryError):
                parse(data)

    def test_ordinary_rhetorical_defeat_and_other_stories_are_preserved(self):
        self.assertEqual(parse(payload(GOOD)).items[0].summary, GOOD)
        self.assertEqual(parse(payload('Mistral 发布 Voxtral 3。')).mode, 'model')

    def test_uncertainty_and_negation_are_preserved(self):
        for text in ('Ofcom 可能败诉。', 'Ofcom 是否败诉仍有争议。', 'Ofcom 并非败诉。', '如果 Ofcom 败诉，可能有影响。', '不能认定 Ofcom 已经败诉。', 'Ofcom has not lost the case.', '并非法院裁定 Ofcom 败诉。', '法院未裁定 Ofcom 败诉', "Ofcom hasn't lost the case", 'Has Ofcom lost the case?'):
            with self.subTest(text=text):
                self.assertEqual(parse(payload(text)).items[0].summary, text)

    def test_uncertainty_does_not_license_later_assertion(self):
        for text in ('Ofcom 可能败诉但4chan已经胜诉。',
                     'Ofcom may appeal and 4chan won the case.',
                     'Ofcom not only lost the case but must also pay costs.'):
            with self.subTest(text=text), self.assertRaises(EvidenceBoundaryError):
                parse(payload(text))

    def test_commentary_stays_in_explicit_discussion_field(self):
        focus = '评论者猜测 Ofcom 败诉是否是策略。'
        self.assertEqual(parse(payload(discussion_focus=focus)).items[0].discussion_focus, focus)
        with self.assertRaises(EvidenceBoundaryError):
            parse(payload(BAD, discussion_focus=focus))

    def test_source_fields_cannot_hide_outcome_in_title_or_impact(self):
        for field in ('title_zh', 'background', 'impact', 'watch', 'value'):
            with self.subTest(field=field):
                data = payload()
                data['items'][0][field] = '法院裁定 Ofcom 败诉。'
                with self.assertRaises(EvidenceBoundaryError):
                    parse(data)

    def test_existing_retry_repairs_claim_without_extra_call_budget(self):
        calls = []
        def request(url, headers, body):
            calls.append(body['messages'])
            return {'choices': [{'message': {'content': json.dumps(payload(BAD if len(calls)==1 else GOOD))}}]}
        result = summarize('Hacker News', [ARTICLE], 'stub', None, request=request)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.mode, 'model')
        self.assertIn('judicial outcomes', calls[1][-1]['content'])

    def test_exhausted_retry_reuses_partial_fallback(self):
        calls = []
        def request(url, headers, body):
            calls.append(url)
            data = payload(BAD)
            data['items'].append(dict(index=1, title_zh='正常条目', summary=GOOD))
            return {'choices': [{'message': {'content': json.dumps(data)}}]}
        result = summarize('Hacker News', [ARTICLE, ARTICLE], 'stub', 'unused', require_model=True, request=request)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result.mode, 'model-with-evidence-fallback')
        self.assertEqual(result.items[0].summary, ARTICLE.title)
        self.assertEqual(result.items[1].summary, GOOD)

    def test_malformed_payload_keeps_structural_validation(self):
        data = payload()
        data['items'] = []
        with self.assertRaisesRegex(ValueError, 'item count'):
            parse(data)

    def test_prompt_separates_primary_evidence_from_community(self):
        prompt = _prompt('Hacker News', [ARTICLE])
        self.assertIn('top_comments 仅是社区发言', prompt)
        self.assertIn('不等于法院判决', prompt)


if __name__ == '__main__':
    unittest.main()
