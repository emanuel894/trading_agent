"""Offline documentation checks; not a collector, source qualifier or admission engine.

Run with Python 3.13 and jsonschema (in a disposable environment). No network or
credentials. Checks design schema counterexamples, local links and retained source
integrity. Normative temporal/rights truth still needs qualified human review.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
BASE = 'b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe'


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalize(raw):
    text = raw.decode('utf8', 'replace')
    if '<html' in text[:5000].lower() or '<!doctype html' in text[:5000].lower():
        parser = VisibleText()
        parser.feed(text)
        text = ' '.join(parser.parts)
    return re.sub(r'\s+', ' ', text).strip()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    schema = json.loads((ROOT / 'event-evidence.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    examples = [json.loads(p.read_text()) for p in sorted((ROOT / 'examples').glob('*.json'))]
    assert len(examples) == 2
    for example in examples:
        validator.validate(example)
        assert example['synthetic'] and example['availability']['admission'] == 'quarantined'
    original = next(e for e in examples if e['record_kind'] == 'original')
    correction = next(e for e in examples if e['record_kind'] == 'correction')
    assert original['event_id'] == correction['event_id']
    assert original['evidence_id'] != correction['evidence_id']
    assert correction['relations'][0]['target_evidence_id'] == original['evidence_id']
    assert original['clocks']['first_receipt']['state'] == 'unknown'
    assert original['clocks']['official_publication']['utc'] is None
    assert original['facts'][0]['value'] == '100.1'
    assert correction['facts'][0]['value'] == '100.2'

    counterexamples = []
    def reject(label, change, base=original):
        value = copy.deepcopy(base)
        change(value)
        assert list(validator.iter_errors(value)), label
        counterexamples.append(label)

    reject('date-only clock cannot become midnight UTC', lambda x: x['clocks']['official_publication'].update(utc='2024-09-11T00:00:00Z'))
    reject('unknown receipt cannot carry an invented UTC value', lambda x: x['clocks']['first_receipt'].update(utc='2024-09-11T12:30:00Z'))
    reject('known clock requires source evidence', lambda x: x['clocks']['retrieved'].update(evidence=[]))
    reject('actual retrieval must be a known UTC instant', lambda x: x['clocks']['retrieved'].update(utc=None))
    reject('source facts require spans', lambda x: x['facts'][0].update(evidence=[]))
    reject('primary immutable payload is required', lambda x: x['raw'][0].update(role='derived_text'))
    reject('raw evidence cannot be declared mutable', lambda x: x['raw'][0].update(immutable=False))
    reject('unrecognized clock field rejected', lambda x: x['clocks'].update(known_at='2024-09-11'))
    reject('correction requires target linkage', lambda x: x.update(relations=[]), correction)
    reject('catalog-only cannot admit predictive evidence', lambda x: x['availability'].update(admission='admitted'))
    def invented_admission(x):
        x['availability'].update(mode='historical_publication_proxy', admission='admitted', decision_cutoff_utc='2024-09-12T12:00:00Z', availability_basis_refs=['invented'], registered_policy_ref='invented')
    reject('synthetic and rights-unknown evidence cannot be admitted', invented_admission)

    captures = json.loads((ROOT / 'sources/captures.json').read_text())
    assert len({r['id'] for r in captures}) == len(captures)
    raw_by_id = {}
    failures = []
    for row in captures:
        archive = (ROOT / 'sources' / row['raw_path']).read_bytes()
        raw = gzip.decompress(archive)
        assert digest(archive) == row['archive_sha256'], row['id']
        assert digest(raw) == row['raw_sha256'] and len(raw) == row['raw_bytes'], row['id']
        raw_by_id[row['id']] = raw
        if row['http_status'] != 200:
            failures.append({'source_id': row['id'], 'http_status': row['http_status']})
        if row.get('decoded_text_path'):
            decoded = (ROOT / 'sources' / row['decoded_text_path']).read_bytes()
            assert digest(decoded) == row['decoded_archive_sha256']
            assert digest(gzip.decompress(decoded)) == row['decoded_text_sha256']
    claims = json.loads((ROOT / 'sources/claims.json').read_text())['claims']
    quoted_words = {}
    for claim in claims:
        raw = raw_by_id[claim['source_id']]
        if claim.get('decoded_text_path'):
            raw = gzip.decompress((ROOT / 'sources' / claim['decoded_text_path']).read_bytes())
        text = normalize(raw)
        assert text[claim['normalized_character_start']:claim['normalized_character_end']] == claim['quote'], claim['source_id']
        quoted_words[claim['source_id']] = quoted_words.get(claim['source_id'], 0) + len(claim['quote'].split())
    assert all(n <= 25 for n in quoted_words.values())
    links = 0
    for page in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', page.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            path = target.split('#')[0]
            assert (page.parent / path).exists(), (page, target)
            links += 1
    repo = ROOT.parent.parent
    changed = subprocess.check_output(['git','diff','--name-only',BASE],cwd=repo,text=True).splitlines()
    changed += subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=repo,text=True).splitlines()
    assert changed and all(p.startswith('docs/event-evidence/') for p in changed), changed
    result = {
        'schema_meta_validation': 'PASS', 'valid_synthetic_examples': len(examples),
        'schema_counterexamples_rejected': counterexamples,
        'source_captures_hash_verified': len(captures), 'source_excerpts_verified': len(claims),
        'source_http_failures_preserved': failures, 'local_markdown_links_verified': links,
        'all_changes_under_docs_event_evidence': True,
        'not_verified': ['source truth/completeness','legal rights','causal admission implementation','alpha','provider/broker access'],
    }
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
