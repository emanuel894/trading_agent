"""Run final-head checks once; write logs outside git to avoid self-referential claims."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;PROJECT=R.parents[1];REPO=PROJECT.parent
OUT=Path('/workspace/issue27-final-validation');OUT.mkdir(exist_ok=True)
def main():
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True),'Commit final packet before checks'
 record_path=OUT/(head+'.json');assert not record_path.exists(),'Final checks already recorded for this head; inspect before repeating'
 checks=[('repository',[sys.executable,'-m','unittest','discover','-s','tests','-v'])]
 for name,p in [('terminal','lean_terminal_017/test_comparator.py'),('identity','lean_identity_time_019/test_comparator.py'),('identity-gap','lean_identity_time_019/continuation_023/test_gap.py'),('amendment','lean_identity_time_019/continuation_021/test_amendment.py'),('actions','lean_actions_execution_024/test_comparator.py'),('actions-lineage','lean_actions_execution_024/continuation_v2/test_lineage.py'),('research-adversarial','lean_alpha_gate_027/test_gate.py'),('research-evidence','lean_alpha_gate_027/verify_evidence.py')]:checks.append((name,[sys.executable,str(PROJECT/'research'/p)]))
 checks.append(('demo',[sys.executable,'-m','agent','demo']))
 result=dict(head_sha=head,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,checks=[])
 for name,cmd in checks:
  log=OUT/(head+'-'+name+'.txt')
  with log.open('x') as f:p=subprocess.run(cmd,cwd=PROJECT,stdout=f,stderr=subprocess.STDOUT)
  tail=log.read_text()[-1800:];item=dict(name=name,command=cmd,exit_code=p.returncode,log=str(log),sha256=hashlib.sha256(log.read_bytes()).hexdigest(),tail=tail);result['checks'].append(item)
  record_path.write_text(json.dumps(result,indent=2)+'\n');print(name,p.returncode,tail[-300:],flush=True)
  if p.returncode:raise SystemExit(3)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==head
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True),'Checks modified tracked state'
 result['all_passed']=True;result['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record_path.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
