"""Final-head checks; outputs stay outside Git and are published on the Issue24 draftPR."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;PROJECT=R.parents[1];REPO=PROJECT.parent
OUT=Path('/workspace/issue-24-final-validation');OUT.mkdir(exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
checks=[('repository-tests',[sys.executable,'-m','unittest','discover','-s','tests','-v']),('packet-comparator',[sys.executable,str(PROJECT/'research/lean_identity_time_019/test_comparator.py')]),('identity-gap-adversarial',[sys.executable,str(PROJECT/'research/lean_identity_time_019/continuation_023/test_gap.py')]),('stage-adversarial',[sys.executable,str(R/'test_comparator.py')]),('terminal-regression',[sys.executable,str(PROJECT/'research/lean_terminal_017/test_comparator.py')]),('amendment-preservation',[sys.executable,str(PROJECT/'research/lean_identity_time_019/continuation_021/test_amendment.py')]),('demo',[sys.executable,'-m','agent','demo'])]
records=[]
for name,cmd in checks:
 p=OUT/(name+'.log');assert not p.exists(),'Refuse to overwrite validation log'
 with p.open('x') as log:result=subprocess.run(cmd,cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,cwd=str(PROJECT),exit_code=result.returncode,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),summary=p.read_text()[-1400:]))
 print(name,result.returncode,p.read_text()[-250:],flush=True)
 if result.returncode:break
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==head,'Head changed during validation'
result=dict(head_sha=head,python=sys.version,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=records,all_passed=len(records)==len(checks) and all(r['exit_code']==0 for r in records),hosted_ci='Must independently verify exact-head Ubuntu and Windows jobs on Issue24 draftPR')
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
raise SystemExit(0 if result['all_passed'] else 3)
