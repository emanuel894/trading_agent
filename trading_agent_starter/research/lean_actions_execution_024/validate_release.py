"""Run final-head repository checks once, plus staged evidence preservation."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;REPO=R.parents[2];OUT=Path('/workspace/issue-24-final-validation')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip(),'Commit final packet first'
r=subprocess.run([sys.executable,str(R/'validate_final.py')],cwd=REPO);assert r.returncode==0,'Base final checks failed'
p=OUT/'continuation-preservation.log';assert not p.exists()
cmd=[sys.executable,str(R/'continuation_v2/test_lineage.py')]
with p.open('x') as f:r=subprocess.run(cmd,cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
result=json.loads((OUT/'validation.json').read_text());assert result['head_sha']==head
result['checks'].append(dict(name='continuation-preservation',command=cmd,exit_code=r.returncode,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),summary=p.read_text()))
result['all_passed']=result['all_passed'] and r.returncode==0
result['final_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==head
assert not subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip(),'Tracked workspace changed during checks'
(OUT/'release-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['all_passed'] else 3)
