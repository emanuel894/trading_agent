"""Read-only verification of exact new clean pairs, failures and immutable reuse."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 s=importlib.util.spec_from_file_location('new_exact',R/'compare.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
 cases={x['case_id']:x for x in json.loads((R/'fixtures/input.json').read_text())['cases']}
 assert {x['fixture'] for x in cases.values()}=={'Q21','Q22','Q23','Q24','Q25','Q26','Q32','Q33'}
 approval=json.loads((R/'ORACLE_REVIEW.json').read_text());assert approval['approved'] is True
 for n,h in approval['binding'].items():assert sha(R/n)==h,n
 for n,h in json.loads((R/'fixtures/manifest.json').read_text())['sha256'].items():assert sha(R/'fixtures'/n)==h,n
 prior=json.loads((R/'reuse-proof.json').read_text())
 for n,h in prior['preserved_sha256'].items():assert sha(R.parent/n)==h,n
 records=json.loads((R/'evidence/attempts.json').read_text());pairs={};failures=[];native=0
 for a in records:
  assert a['verdict']!='LAUNCH_PENDING','Unreconciled launch'
  assert sha(R/'evidence'/a['output'])==a['output_sha256']
  assert sha(R/'evidence'/(a['output']+'.log'))==a['log_sha256']
  assert a['paid_provider_calls']==0 and a['purchases']==0
  if a['verdict']!='PASS':failures.append(dict(attempt=a['attempt'],case_id=a['case_id'],divergence=a['first_divergence']));continue
  assert a['binding']==approval['binding'],'Accepted output bound to a different stage'
  assert a['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges']) and a['container_user']=='65534:65534'
  c.compare_file(R/'evidence'/a['output'],R/'fixtures'/(a['case_id']+'.expected.json'),R/'fixtures/input.json')
  pairs.setdefault(a['case_id'],[]).append(a['output_sha256'])
  raw=json.loads((R/'evidence'/a['output']).read_text())
  if raw['execution_complete']:native+=4 if cases[a['case_id']]['fixture']=='Q33' else 1
 assert set(pairs)==set(cases),'Unrun required cases: '+str(sorted(set(cases)-set(pairs)))
 assert all(len(v)==2 and len(set(v))==1 for v in pairs.values()),'Nonidentical/incomplete clean pair'
 return dict(case_pairs=len(pairs),accepted_processes=sum(map(len,pairs.values())),native_algorithm_runs=native,preserved_failures=failures,prior_files_preserved=len(prior['preserved_sha256']),prior_native_reruns=0,rows={row:sum(x['fixture']==row for x in cases.values()) for row in sorted({x['fixture'] for x in cases.values()})},elapsed_attempt_seconds=sum(a['elapsed_seconds'] for a in records),paid_provider_calls=0,purchases=0,resource_cost=None)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
