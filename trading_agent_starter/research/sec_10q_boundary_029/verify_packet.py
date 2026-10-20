"""Offline assertions for this frozen source packet, not an admission/ingestion API.

P01 is only decompressed for byte length and hashing; never decode/render its text.
No network, clocks invented from dates, or performance inputs.
"""
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import copy
import gzip
import hashlib
import json
import re
import subprocess

R = Path(__file__).resolve().parent
REPO = R.parents[2]
BASE = "d90f13035cf47e4d96ac8a33aed25d784dc589fe"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

captures = json.loads((R / "sources/captures.json").read_text())
assert len(captures) == 9 and len({c['id'] for c in captures}) == 9
bodies = {}
for c in captures:
    assert c['historical_receipt_at'] is None
    assert c['historical_first_machine_observable_at'] is None
    if c.get('outcome') == 'ABORTED_SIZE_CAP':
        assert c['id'] == 'T01' and c['retained_body_bytes'] == 0
        assert c['raw_sha256'] is None and c['completed_utc'] is None
        continue
    archive = (R / c['path']).read_bytes()
    body = gzip.decompress(archive)
    assert sha(archive) == c['archive_sha256']
    assert sha(body) == c['raw_sha256'] and len(body) == c['raw_bytes']
    assert c['status'] == 200
    times = [datetime.fromisoformat(c[k]) for k in
             ['started_utc', 'headers_received_utc', 'completed_utc']]
    assert all(t.utcoffset() == timedelta(0) for t in times) and times == sorted(times)
    bodies[c['id']] = body
assert len(bodies) == 8

for name, expected in json.loads((R / 'reuse_manifest.json').read_text()).items():
    assert sha((REPO / name).read_bytes()) == expected, name
assert sha(gzip.decompress((REPO / 'docs/event-evidence/sources/S01.raw.gz').read_bytes())) == \
    'a43713b1f7b26bd0e95eb4b5cb4e08b4947a4a86166efe9bb9ae4fadc49b5e19'

s = json.loads((R / 'sample.json').read_text())
root = json.loads(bodies['M01'])
assert str(root['cik']).zfill(10) == s['event_key']['cik']
recent = root['filings']['recent']
ix = recent['accessionNumber'].index(s['event_key']['accession'])
assert ix == s['submissions']['row_index']
row = {k: recent[k][ix] for k in s['submissions']['fields']}
assert row == s['submissions']['fields']

class IndexText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
    def handle_data(self, data):
        if data.strip():
            self.items.append(data.strip())

index = IndexText()
index.feed(bodies['I01'].decode('utf-8'))
t = index.items
assert t[t.index('Accepted') + 1] == s['index']['accepted_native']
assert t[t.index('Period of Report') + 1] == row['reportDate']
j = t.index(row['primaryDocument'])
assert t[j + 2] == '10-Q'
assert int(t[j + 3]) == s['index']['primary_listed_bytes']
for tag, key in [('ACCESSION-NUMBER', 'accession'), ('CIK', 'cik'),
                 ('TYPE', 'type'), ('PERIOD', 'period'),
                 ('ACCEPTANCE-DATETIME', 'acceptance_native'),
                 ('FILING-DATE', 'filing_date'),
                 ('DATE-OF-FILING-DATE-CHANGE', 'date_of_filing_date_change')]:
    value = re.findall(rb'<' + tag.encode() + rb'>([^\r\n<]+)', bodies['H01'])
    assert len(value) == 1 and value[0].decode() == s['header'][key], tag

# A conversion hypothesis is tested, not assigned as the unresolved source zone.
naive = datetime.strptime(s['header']['acceptance_native'], '%Y%m%d%H%M%S')
ny_candidate = naive.replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
est_candidate = naive.replace(tzinfo=timezone(timedelta(hours=-5))).astimezone(timezone.utc)
api_assertion = datetime.fromisoformat(row['acceptanceDateTime'].replace('Z', '+00:00'))
assert ny_candidate.isoformat() == '2025-05-09T13:52:26+00:00'
assert est_candidate.isoformat() == '2025-05-09T14:52:26+00:00'
assert api_assertion not in [ny_candidate, est_candidate]
assert s['header']['acceptance_source_timezone'] is None
assert s['index']['accepted_source_timezone'] is None
for k in ['sec_acceptance_utc', 'official_public_dissemination_utc',
          'historical_first_machine_observable_utc', 'historical_first_receipt_utc',
          'source_revision_instant_utc']:
    assert s['resolved_clocks'][k] is None, k
assert len(bodies['P01']) == s['primary_retrieval']['actual_bytes']
assert len(bodies['P01']) - int(t[j + 3]) == 106
assert not s['primary_retrieval']['original_2025_bytes_guaranteed']

# Explicit original-identity counterexamples; no amendment/body acquisition.
target_identity = {k: row[k] for k in ['accessionNumber', 'form', 'reportDate', 'primaryDocument']}
amended = copy.deepcopy(target_identity)
amended['form'] = '10-Q/A'
assert amended != target_identity and amended['form'] != '10-Q'
later_index = recent['accessionNumber'].index('0000950170-25-105507')
later = {k: recent[k][later_index] for k in target_identity}
assert later != target_identity and later['form'] == '10-Q'
assert later['accessionNumber'] != target_identity['accessionNumber']
missing_acceptance = {k: v for k, v in row.items() if k != 'acceptanceDateTime'}
assert 'acceptanceDateTime' not in missing_acceptance
assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', missing_acceptance['filingDate'])
assert sha(bodies['P01'] + b'\x00') != sha(bodies['P01'])  # synthetic hash mutation only

decision = json.loads((R / 'decision.json').read_text())
assert decision['state'] == 'SEC_10Q_SOURCE_BOUNDARY_INCOMPLETE'
assert decision['reason_codes'] == s['reason_codes']
assert not decision['provenance_clock_dependency_closed']
assert not decision['scientific_blocker_proven'] and not decision['scientific_changes_made']
assert s['disposition'] == 'QUARANTINE'
assert all(not s[k] for k in ['historical_acquisition_proxy_admitted',
                              'historical_performance_admitted', 'prospective_observed_admitted'])
assert len(json.loads((R / 'falsifications.json').read_text())['cases']) == 8
changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=REPO, text=True).splitlines()
assert all(n.startswith('trading_agent_starter/research/sec_10q_boundary_029/') for n in changed)
print(json.dumps(dict(state=decision['state'], complete_captures=8,
    preserved_aborted_capture=1, historical_receipt=None, clock_conflict_preserved=True,
    primary_size_conflict_bytes=106, original_amendment_and_later_accession_checks='PASS',
    reused_hashes='PASS', protected_foundation_unchanged=True, network_calls=0), indent=2))
