"""Explicit bounded clean-process pairs. This journal never restores business state."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess,sys,time
R=Path(__file__).resolve().parent;W=Path('/workspace/issue-27-lean');P=W/'packet'
spec=importlib.util.spec_from_file_location('research_comparator',R/'compare.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def binding():
 b=json.loads((R/'build.json').read_text())
 for n,h in b['runtime_files_sha256'].items():assert sha(P/'host/bin/Release/net10.0'/n)==h,n
 for n,h in b['config_sha256'].items():assert sha(W/n)==h,n
 for n,h in b['code_sha256'].items():assert sha(R/n)==sha(P/n)==h,n
 for n,h in json.loads((R/'fixtures/manifest.json').read_text())['sha256'].items():assert sha(R/'fixtures'/n)==sha(P/'fixtures'/n)==h,n
 prior=json.loads((R/'reuse-proof.json').read_text())
 for n,h in prior['preserved_sha256'].items():assert sha(R.parent/n)==h,n
 names=['build.json','fixtures/manifest.json','compare.py','evaluate.py','run_gate.py','reuse-proof.json','host/Program.cs','host/ResearchAlgorithm.cs','host/LeanResearch.csproj']
 return {n:sha(R/n) for n in names}
def main(ids):
 cases={c['case_id']:c for c in json.loads((R/'fixtures/input.json').read_text())['cases']}
 assert ids and len(ids)==len(set(ids)) and set(ids)<=set(cases),'Explicit unique new case IDs required'
 assert all(c['fixture'] in ['Q21','Q22','Q23','Q24','Q25','Q26','Q32','Q33'] for c in cases.values())
 bound=binding();approval=json.loads((R/'ORACLE_REVIEW.json').read_text());assert approval['approved'] is True and approval['binding']==bound,'Independent review does not bind current oracles/code/build'
 build=json.loads((R/'build.json').read_text());journal=R/'evidence/attempts.json';records=json.loads(journal.read_text()) if journal.exists() else []
 assert not any(a['verdict']=='LAUNCH_PENDING' for a in records),'Reconcile pending container/output before retry'
 for cid in ids:
  accepted=[]
  for a in records:
   if a['case_id']==cid and a['verdict']=='PASS' and a['binding']==bound:
    p=R/'evidence'/a['output'];assert sha(p)==a['output_sha256'];C.compare_file(p,R/'fixtures'/(cid+'.expected.json'),R/'fixtures/input.json');accepted.append(a['output_sha256'])
  assert len(accepted)<=2
  for repeat in range(len(accepted)+1,3):
   number=len(records)+1;name=f'issue27-case-{number:03d}';filename=f'{cid}.attempt{number:03d}.json';raw=W/'runtime-output'/filename;dest=R/'evidence'/filename;log=R/'evidence'/(filename+'.log')
   mode=cases[cid].get('ingress','complete');store='/inputs/'+mode
   cmd=['docker','--host=unix:///var/run/docker.sock','run','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--volume',str(W)+':/work:ro','--volume',str(P)+':/packet:ro','--volume',str(W/'stores')+':/inputs:ro','--volume',str(R.parent)+':/prior:ro','--volume',str(W/'runtime-output')+':/out','--workdir','/work','--env','DOTNET_CLI_HOME=/tmp/dotnet','--env','DOTNET_CLI_TELEMETRY_OPTOUT=1','--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false','--env','ALPACA_LIVE_TRADE=false',build['image'],'dotnet','/packet/host/bin/Release/net10.0/LeanResearch.dll','/packet/fixtures',cid,'/out/'+filename,store]
   a=dict(case_id=cid,repeat=repeat,attempt=number,output=filename,binding=bound,command=cmd,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict='LAUNCH_PENDING',paid_provider_calls=0,purchases=0,model_tokens=None,resource_cost=None,resource_cost_status='unavailable; elapsed resource use retained')
   records.append(a);save(journal,records);start=time.monotonic()
   try:
    with log.open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
    a['exit_code']=result.returncode
   except subprocess.TimeoutExpired:
    a['exit_code']=124;subprocess.run(['docker','--host=unix:///var/run/docker.sock','stop','--time','1',name],capture_output=True)
   a['elapsed_seconds']=round(time.monotonic()-start,6)
   inspect=subprocess.run(['docker','--host=unix:///var/run/docker.sock','inspect',name],capture_output=True,text=True)
   if inspect.returncode==0:
    data=json.loads(inspect.stdout)[0];a['container_controls']={k:data['HostConfig'][k] for k in ['NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt']};a['container_user']=data['Config']['User'];a['container_state']={k:data['State'][k] for k in ['Status','ExitCode','OOMKilled','Error']}
   try:
    assert raw.exists() and not dest.exists(),'Missing output or overwrite attempt';dest.write_bytes(raw.read_bytes());a['output_sha256']=sha(dest)
    assert a['exit_code']==0,'Nonzero host exit'
    assert a['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges']) and a['container_user']=='65534:65534','Isolation changed'
    C.compare_file(dest,R/'fixtures'/(cid+'.expected.json'),R/'fixtures/input.json');a['verdict']='PASS';accepted.append(a['output_sha256'])
   except Exception as e:a['verdict']='LEAN_ALPHA_RESEARCH_GATE_INCOMPLETE';a['first_divergence']=str(e)
   a['log_sha256']=sha(log);save(journal,records);subprocess.run(['docker','--host=unix:///var/run/docker.sock','rm',name],capture_output=True)
   print(json.dumps({k:a.get(k) for k in ['case_id','attempt','verdict','first_divergence']}),flush=True)
   if a['verdict']!='PASS':raise SystemExit(3)
  assert len(accepted)==2 and len(set(accepted))==1,'Clean-pair mismatch: '+cid
  print(cid+' paired '+accepted[0],flush=True)
if __name__=='__main__':main(sys.argv[1:])
