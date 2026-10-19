"""Read-only old evidence verification. Never launches a native process."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess
R=Path(__file__).resolve().parent;P=R.parent;REPO=P.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify():
 previous=module('prior_verifier',P/'continuation_021/verify_bindings.py').verify()
 preserved=json.loads((R/'preserved_ee72ca9_sha256.json').read_text())
 tracked=subprocess.check_output(['git','ls-tree','-r','--name-only','ee72ca97c6682e2a2200cc996fc51a26e1c65380',str(P.relative_to(REPO))],cwd=REPO,text=True).splitlines()
 assert set(preserved)=={str(Path(f).relative_to(P.relative_to(REPO))) for f in tracked},'Incomplete preservation manifest'
 for name,h in preserved.items():
  assert sha(P/name)==h,('Prior file changed',name)
  blob=subprocess.check_output(['git','show','ee72ca97c6682e2a2200cc996fc51a26e1c65380:'+str((P/name).relative_to(REPO))],cwd=REPO)
  assert hashlib.sha256(blob).hexdigest()==h,('Preservation hash not original',name)
 compare=module('old_compare',P/'compare.py')
 attempts=json.loads((P/'continuation_021/evidence/attempts.json').read_text())
 groups={}
 info=json.loads((P/'build/manifest.json').read_text())
 binding=dict(build_manifest_sha256=sha(P/'build/manifest.json'),fixture_manifest_sha256=sha(P/'fixtures_v3/manifest.json'),host_source_sha256=sha(P/'host/Program.cs'),image=info['image'],verification_sha256=hashlib.sha256(json.dumps(previous,sort_keys=True,separators=(',',':')).encode()).hexdigest(),runner_sha256=sha(P/'continuation_021/run_gate.py'),comparator_sha256=sha(P/'compare.py'),verifier_sha256=sha(P/'continuation_021/verify_bindings.py'))
 for a in attempts:
  assert a['verdict']=='PASS' and a['binding']==binding,(a['attempt'],'Prior binding changed')
  output=P/'continuation_021/evidence'/a['output'];assert sha(output)==a['output_sha256']
  compare.compare_file(output,P/'fixtures_v3'/(a['case_id']+'.expected.json'),P/'fixtures_v3/input.json')
  groups.setdefault(a['case_id'],[]).append(a['output_sha256'])
 assert len(groups)==54 and len(attempts)==108
 for cid,hashes in groups.items():assert len(hashes)==2 and len(set(hashes))==1,cid
 return dict(prior_pr_head='ee72ca97c6682e2a2200cc996fc51a26e1c65380',preserved_packet_files=len(preserved),old_accepted_processes=114,old_replayed=0,v3_pairs_verified=len(groups),v2_pairs_verified=3,original_prerequisites=previous)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
