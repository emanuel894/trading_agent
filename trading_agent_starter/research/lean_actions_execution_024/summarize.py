"""Read-only revalidation of staged outputs; emit auditable combined evidence."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parent;V=R/'continuation_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('stage',R/'compare.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def collect(root):
 records=json.loads((root/'evidence/attempts.json').read_text());groups={};failures=[]
 for a in records:
  output=root/'evidence'/a['output'];assert sha(output)==a['output_sha256']
  for n,h in a['binding'].items():assert sha(root/n)==h,n
  if a['verdict']!='PASS':
   assert a['attempt']==33 and a['first_divergence']=="$.fills[0].price: '99.9' != '99.90'",a
   try:m.compare_file(output,root/'fixtures'/(a['case_id']+'.expected.json'),root/'fixtures/input.json')
   except m.Mismatch:pass
   else:raise AssertionError('Historical mismatch no longer reproduced')
   failures.append({k:a[k] for k in ['attempt','case_id','verdict','first_divergence','output_sha256']});continue
  m.compare_file(output,root/'fixtures'/(a['case_id']+'.expected.json'),root/'fixtures/input.json')
  groups.setdefault(a['case_id'],[]).append(a)
 pairs={}
 for cid,pair in groups.items():
  assert len(pair)==2 and pair[0]['binding']==pair[1]['binding'] and pair[0]['output_sha256']==pair[1]['output_sha256']
  pairs[cid]=dict(attempts=[a['attempt'] for a in pair],output_sha256=pair[0]['output_sha256'],binding=pair[0]['binding'])
 return records,pairs,failures
if __name__=='__main__':
 a,p,f=collect(R);b,q,g=collect(V)
 assert len(a)==33 and len(b)==26 and len(p)==16 and len(q)==13 and len(f)==1 and not g
 assert not (p.keys()&q.keys())
 assert set(q)==set(json.loads((V/'reuse-v1.json').read_text())['remaining_ids'])
 combined={**p,**q};assert len(combined)==29
 result=dict(decision='LEAN_Q12_Q20_GATE_PASS',scope='Q12-Q20 only; no Q21-Q33 qualification',foundation='ba213d8d775c20db7a299932a9ea3319c9bc8a59',source_pin='d4cac37514427c84d40064cecbf3f0e6be4b0137',new_launches=59,new_accepted_processes=58,new_paired_cases=29,accepted_v1_processes_repeated=0,Q01_Q11_native_reruns=0,original_reused_pairs=json.loads((R/'reuse-proof.json').read_text()),failures_preserved=f,pairs={k:dict(evidence_root='.' if k in p else 'continuation_v2',**v) for k,v in combined.items()},caveat='Staged bindings:16pairs original v1;13pairs v2; original accepted processes are never relabeled as v2. Final PASS also requires independent review and final-head checks/CI reported in the PR.')
 out=R/'NATIVE_RESULT.json';assert not out.exists(),'Never overwrite result';out.write_text(json.dumps(result,indent=2)+'\n');print('29 exact deterministic pairs;58 accepted new processes;one preserved failure;4 prior accepted processes reused')
