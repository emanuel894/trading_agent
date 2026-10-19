"""Assemble final observations without promoting incomplete coverage to qualification."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parent
PACKET=ROOT.parent
sys.path.insert(0,str(PACKET))
import compare
from verify_bindings import verify

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    records=json.loads((ROOT/'evidence/attempts.json').read_text())
    if any(r['verdict']=='LAUNCH_PENDING' for r in records):raise SystemExit('Native driver still active; do not finalize')
    if any(r['verdict']!='PASS' for r in records):raise SystemExit('Diagnose first preserved divergence before final decision')
    bundle=json.loads((PACKET/'fixtures_v3/input.json').read_text())
    proof=verify()
    save(ROOT/'evidence/final-reuse-proof.json',proof)
    fresh={};outputs={}
    for case in bundle['cases']:
        cid=case['case_id']
        if cid in proof['reused']:continue
        runs=[r for r in records if r['case_id']==cid]
        assert len(runs)==2 and {r['repeat']for r in runs}=={1,2},cid
        assert len({r['output_sha256']for r in runs})==1,cid
        for run in runs:
            f=ROOT/'evidence'/run['output'];assert sha(f)==run['output_sha256']
            compare.compare_file(f,PACKET/'fixtures_v3'/(cid+'.expected.json'),PACKET/'fixtures_v3/input.json')
            assert run['binding']['runner_sha256']==sha(ROOT/'run_gate.py')
            assert run['binding']['comparator_sha256']==sha(PACKET/'compare.py')
            assert run['binding']['verifier_sha256']==sha(ROOT/'verify_bindings.py')
            assert run['binding']['fixture_manifest_sha256']==sha(PACKET/'fixtures_v3/manifest.json')
            assert run['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'])
            assert run['container_user']=='65534:65534' and run['exit_code']==0
        outputs[cid]=json.loads((ROOT/'evidence'/runs[0]['output']).read_text())
        fresh[cid]=dict(version='fixtures_v3',attempts=[r['attempt']for r in runs],output_sha256=runs[0]['output_sha256'])
    assert len(fresh)==54 and len(records)==108
    assert [r['attempt']for r in records]==list(range(13,121))
    equivalences=[]
    for left,right,label in [
        ('Q09_baseline','Q09_future_append','Future-quote append business invariance; future_records remain unexercised'),
        ('Q10_five_shares','Q10_round_lot','Verified round-lot conversion business equivalence'),
        ('Q11_raw','Q11_future_factor','Unused future-factor metadata invariance only; no factor-provider acceptance'),
        ('Q08_conflict','Q08_conflict_reversed','Simultaneous conflict business outcome independent of file order')]:
        compare.compare_business(outputs[left]['business'],outputs[right]['business'])
        equivalences.append(dict(left=left,right=right,result='EXACT_BUSINESS_EQUAL',scope=label))
    counts=collections.Counter(c['fixture']for c in bundle['cases'])
    limits=[
        'Q09 corrections/symbol/action/prediction future_records are not consumed; their admission/revision behavior remains unexercised.',
        'Q11 factor and adjusted_decoy metadata are not consumed by native ingress; factor normalization/adjusted-decoy rejection and no-double-action behavior remain unexercised.',
        'Q12-Q33 remain forbidden/unrun. A split-accounting reference cannot authorize scope expansion.',
        'Q10 proves supplied verified units/gap flags through the custom fill adapter, not native depth or source-gap detection.']
    decision=dict(status='LEAN_IDENTITY_TIME_GATE_INCOMPLETE',issue=21,pr=20,
        branch='research/issue-19-lean-identity-time-spike',starting_head='c70aa329c8ebfc993e0048b1142a7db22fbdcf9b',
        foundation_sha='67317e573624529e247d98a4964f946421b571e7',q04_timing_mismatch='Resolved by independently adjudicated/reviewed timing-only v3',
        observed_subchecks=dict(total=57,reused_v2=3,new_v3=54,new_clean_processes=108,total_accepted_clean_processes=114,failed=0,unrun=0,per_group=dict(counts)),
        all_required_behavior_qualified=False,lean_blocker_established=False,coverage_limits=limits,
        accepted_reused_v2=proof['reused'],accepted_fresh_v3=fresh,cross_case_observations=equivalences,
        immutable_original_files=proof['preserved_files'],source_pin=proof['source_pin'],source_tree=proof['source_tree'],
        source_files_manifest_sha256=proof['source_files_manifest_sha256'],config_sha256=proof['config_sha256'],
        hashes=dict(build_manifest=sha(PACKET/'build/manifest.json'),v1_manifest=sha(PACKET/'fixtures/manifest.json'),
            v2_manifest=sha(PACKET/'fixtures_v2/manifest.json'),v3_manifest=sha(PACKET/'fixtures_v3/manifest.json'),
            v3_input=sha(PACKET/'fixtures_v3/input.json'),runner=sha(ROOT/'run_gate.py'),comparator=sha(PACKET/'compare.py'),
            verifier=sha(ROOT/'verify_bindings.py'),attempt_journal=sha(ROOT/'evidence/attempts.json')),
        stop='No further fixture execution or implementation. Preserve coverage limits; final review/validation/CI; update existing draft PR20 only; no merge.')
    save(ROOT/'decision.json',decision)
    validations=[]
    for filename,count in [('repository-tests.log',240),('comparator-final.log',3),('terminal-comparator.log',12),('amendment-final.log',3)]:
        f=ROOT/'evidence'/filename;s=f.read_text();assert f'Ran {count} tests' in s and s.rstrip().endswith('OK'),filename
        validations.append(dict(log=filename,passed=count,sha256=sha(f)))
    demo=ROOT/'evidence/demo.log';s=demo.read_text();assert 'Processed 300 daily bars' in s and 'No broker orders were sent' in s
    save(ROOT/'validation.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        checks=validations,demo=dict(bars=300,orders=0,sha256=sha(demo)),manifests_valid=True,prior_files_preserved=185,
        full_source_runtime_config_reverified=True,reuse_proof_sha256=sha(ROOT/'evidence/final-reuse-proof.json'),
        code_commit_before_native='6d7c8c7',hosted_ci='Final exact-head native checks to be verified on existing PR20; not attested by a self-referencing commit.'))
    print(json.dumps(decision['observed_subchecks'],indent=2))

if __name__=='__main__':main()
