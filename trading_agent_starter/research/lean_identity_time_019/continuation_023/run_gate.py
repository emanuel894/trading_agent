"""Only six Issue23 cases. Launch intent is persisted before each side effect."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess,sys
R=Path(__file__).resolve().parent;WORK=Path('/workspace/issue-23-lean');OLD=Path('/workspace/issue-19-lean')
s=importlib.util.spec_from_file_location('gap_oracle',R/'compare.py');compare=importlib.util.module_from_spec(s);s.loader.exec_module(compare)
s=importlib.util.spec_from_file_location('reuse_verifier',R/'verify_reuse.py');reuse=importlib.util.module_from_spec(s);s.loader.exec_module(reuse)
ALLOWED=['Q09_typed_historical','Q09_typed_prospective','Q11_ingress_raw','Q11_ingress_future_factor','Q11_ingress_wrong_metadata','Q11_integral_coupling']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 temp=p.with_suffix('.json.tmp');temp.write_text(json.dumps(x,indent=2)+'\n');temp.replace(p)
def bindings():
 build=json.loads((R/'build.json').read_text())
 for n,h in build['runtime_files_sha256'].items():assert sha(WORK/'host/bin/Release/net10.0'/n)==h,n
 for n,h in build['code_sha256'].items():assert sha(R/n)==sha(WORK/n)==h,n
 for n,h in json.loads((R/'fixtures/manifest.json').read_text())['sha256'].items():assert sha(R/'fixtures'/n)==sha(WORK/'fixtures'/n)==h,n
 proof=reuse.verify();save(R/'evidence/pre-run-reuse-proof.json',proof)
 names=['build.json','fixtures/manifest.json','compare.py','verify_reuse.py','run_gate.py','host/Program.cs','host/Gap.cs','host/LeanGap.csproj']
 return {n:sha(R/n) for n in names}
def main(ids):
 assert ids and len(ids)==len(set(ids)) and set(ids)<=set(ALLOWED),'Explicit unique bounded IDs required'
 binding=bindings();approval=json.loads((R/'ORACLE_REVIEW.json').read_text());assert approval['approved'] is True and approval['binding']==binding,'Approval does not bind current code/build/oracles'
 build=json.loads((R/'build.json').read_text());journal=R/'evidence/attempts.json';records=json.loads(journal.read_text()) if journal.exists() else []
 assert not any(r['verdict']=='LAUNCH_PENDING' for r in records),'Reconcile outstanding launch first'
 for cid in ids:
  accepted=[]
  for a in records:
   if a['case_id']==cid and a['verdict']=='PASS' and a['binding']==binding:
    output=R/'evidence'/a['output'];assert sha(output)==a['output_sha256'];compare.compare_file(output,R/'fixtures'/(cid+'.expected.json'),R/'fixtures/input.json');accepted.append(a['output_sha256'])
  assert len(accepted)<=2
  for repeat in range(len(accepted)+1,3):
   number=121+len(records);name=f'issue23-gap-{number:03d}';filename=f'{cid}.attempt{number:03d}.json';raw=WORK/'runtime-output'/filename;output=R/'evidence'/filename;log=R/'evidence'/(filename+'.log')
   cmd=['docker','--host=unix:///var/run/docker.sock','run','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--volume',str(OLD)+':/work:ro','--volume',str(WORK)+':/continuation:ro','--volume',str(WORK/'runtime-output')+':/out','--workdir','/work','--env','DOTNET_CLI_HOME=/tmp/dotnet','--env','DOTNET_CLI_TELEMETRY_OPTOUT=1','--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false','--env','ALPACA_LIVE_TRADE=false',build['image'],'dotnet','/continuation/host/bin/Release/net10.0/LeanGap.dll','/continuation/fixtures',cid,'/out/'+filename]
   a=dict(case_id=cid,repeat=repeat,attempt=number,output=filename,binding=binding,command=cmd,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict='LAUNCH_PENDING');records.append(a);save(journal,records)
   try:
    with log.open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
    a['exit_code']=result.returncode
   except subprocess.TimeoutExpired:
    a['exit_code']=124;subprocess.run(['docker','--host=unix:///var/run/docker.sock','stop','--time','1',name],capture_output=True)
   inspect=subprocess.run(['docker','--host=unix:///var/run/docker.sock','inspect',name],capture_output=True,text=True)
   if inspect.returncode==0:
    data=json.loads(inspect.stdout)[0];a['container_controls']={k:data['HostConfig'][k] for k in ['NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt']};a['container_user']=data['Config']['User'];a['container_state']={k:data['State'][k] for k in ['Status','ExitCode','OOMKilled','Error']}
   try:
    assert raw.exists() and not output.exists(),'Missing native output or overwrite attempt'
    output.write_bytes(raw.read_bytes());a['output_sha256']=sha(output)
    assert a['exit_code']==0,'Nonzero native exit'
    assert a['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges']) and a['container_user']=='65534:65534','Container isolation changed'
    compare.compare_file(output,R/'fixtures'/(cid+'.expected.json'),R/'fixtures/input.json')
    a['verdict']='PASS';accepted.append(a['output_sha256'])
   except Exception as e:a['verdict']='LEAN_IDENTITY_TIME_GATE_INCOMPLETE';a['first_divergence']=str(e)
   save(journal,records);subprocess.run(['docker','--host=unix:///var/run/docker.sock','rm',name],capture_output=True)
   print(json.dumps({k:a.get(k) for k in ['case_id','attempt','verdict','first_divergence']}),flush=True)
   if a['verdict']!='PASS':raise SystemExit(3)
  assert len(accepted)==2 and len(set(accepted))==1,'Deterministic replay mismatch: '+cid
  print(cid+' deterministic '+accepted[0],flush=True)
if __name__=='__main__':main(sys.argv[1:])
