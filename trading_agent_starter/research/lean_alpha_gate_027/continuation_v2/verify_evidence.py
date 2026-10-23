"""Verify combined original-bound Q21 reuse and new v2 pairs; never run LEAN."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parent;P=R.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stage(root,required):
 s=importlib.util.spec_from_file_location('exact_'+root.name,root/'compare.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
 cases={x['case_id']:x for x in json.loads((root/'fixtures/input.json').read_text())['cases']};approval=json.loads((root/'ORACLE_REVIEW.json').read_text());assert approval['approved'] is True
 for n,h in approval['binding'].items():assert sha(root/n)==h,n
 records=json.loads((root/'evidence/attempts.json').read_text());pairs={};native=0;failures=[]
 for a in records:
  assert a['verdict']!='LAUNCH_PENDING';assert sha(root/'evidence'/a['output'])==a['output_sha256'];assert sha(root/'evidence'/(a['output']+'.log'))==a['log_sha256']
  assert a['paid_provider_calls']==0 and a['purchases']==0
  if a['verdict']!='PASS':failures.append(dict(stage=root.name,attempt=a['attempt'],case_id=a['case_id'],divergence=a['first_divergence']));continue
  assert a['binding']==approval['binding'];assert a['case_id'] in required
  assert a['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges']) and a['container_user']=='65534:65534'
  c.compare_file(root/'evidence'/a['output'],root/'fixtures'/(a['case_id']+'.expected.json'),root/'fixtures/input.json')
  pairs.setdefault(a['case_id'],[]).append(a['output_sha256']);raw=json.loads((root/'evidence'/a['output']).read_text())
  if raw['execution_complete']:native+=4 if cases[a['case_id']]['fixture']=='Q33' else 1
 assert set(pairs)==required,'Unrun/extra cases: '+str(required^set(pairs))
 assert all(len(v)==2 and len(set(v))==1 for v in pairs.values()),'Nonidentical pair'
 return records,pairs,native,failures
def verify():
 for n,h in json.loads((R/'parent-preserved.json').read_text()).items():assert sha(P/n)==h,n
 legacy=json.loads((R/'reuse-proof.json').read_text())
 for n,h in legacy['preserved_sha256'].items():assert sha(R.parents[1]/n)==h,n
 for n,h in json.loads((R/'fixtures/manifest.json').read_text())['sha256'].items():assert sha(R/'fixtures'/n)==h and sha(P/'fixtures'/n)==h,n
 assert (R/'host/ResearchAlgorithm.cs').read_bytes()==(P/'host/ResearchAlgorithm.cs').read_bytes()
 cases={x['case_id']:x for x in json.loads((R/'fixtures/input.json').read_text())['cases']}
 reused=json.loads((R/'reuse-v1.json').read_text());q21=set(reused['reused']);assert len(q21)==8 and all(cases[x]['fixture']=='Q21' for x in q21)
 a,p,n,f=stage(P,q21);b,q,m,g=stage(R,set(cases)-q21)
 all_records=a+b;assert sorted(x['attempt'] for x in all_records)==list(range(1,len(all_records)+1)),'Global attempt lineage reset/duplicated'
 for cid,pair in reused['reused'].items():
  assert [x['output_sha256'] for x in pair]==p[cid]
 return dict(case_pairs=len(p)+len(q),accepted_processes=sum(map(len,p.values()))+sum(map(len,q.values())),original_q21_pairs=len(p),new_v2_pairs=len(q),native_algorithm_runs=n+m,preserved_failures=f+g,prior_files_preserved=len(legacy['preserved_sha256']),prior_native_reruns=0,q21_native_reruns=0,rows={row:sum(c['fixture']==row for c in cases.values()) for row in sorted({c['fixture'] for c in cases.values()})},elapsed_attempt_seconds=sum(x['elapsed_seconds'] for x in all_records),paid_provider_calls=0,purchases=0,resource_cost=None)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
