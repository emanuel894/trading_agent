"""Timing-only, one-shot amendment. Never reads a native output or overwrites v1/v2/v3."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import shutil

PACKET=Path(__file__).resolve().parents[1]
OLD=1736175601000000000
NEW=1736260201000000000

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    original=PACKET/'fixtures_v2'
    target=PACKET/'fixtures_v3'
    if target.exists():raise SystemExit('Refuse to overwrite frozen v3')
    for name,digest in json.loads((original/'manifest.json').read_text())['sha256'].items():
        assert sha(original/name)==digest,name
    before=json.loads((original/'input.json').read_text());after=deepcopy(before)
    changes=[]
    for index,case in enumerate(after['cases']):
        if case['case_id'] not in ['Q04_missing','Q04_overlap']:continue
        assert case['decision_ns']+1_000_000_000==NEW
        assert len(case['events'])==1 and case['events'][0]['instrument']=='I1'
        for field in ['event_ns','available_ns']:
            assert case['events'][0][field]==OLD
            case['events'][0][field]=NEW
            changes.append(dict(case_id=case['case_id'],path=f'/cases/{index}/events/0/{field}',old=OLD,new=NEW,
                reason='Restore decision-relative q1 at Jan7 decision+1s; simulated availability equals event; no receipt invention.'))
    assert len(changes)==4
    shutil.copytree(original,target)
    (target/'input.json').write_text(json.dumps(after,indent=2)+'\n')
    manifest=dict(sha256={f.name:sha(f)for f in sorted(target.glob('*.json')) if f.name!='manifest.json'})
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    record=dict(issue=21,adjudication='authored_fixture_timing_error',changes=changes,
        unchanged='Every expected-record byte and every other input field, including I1 identity and null receipt.',
        rationale='Merged Q04 is Jan7 malformed mapping rejection before order. Shared q1 is decision+1s. Author omitted events override while overriding decision; ordinary Q04 variants explicitly use decision-relative q1.',
        review_required='Fresh independent review of actual v3 bytes before any native execution.',
        hashes={v:dict(input_sha256=sha(PACKET/v/'input.json'),manifest_sha256=sha(PACKET/v/'manifest.json'))for v in ['fixtures','fixtures_v2','fixtures_v3']})
    (PACKET/'continuation_021/V3_AMENDMENT.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
