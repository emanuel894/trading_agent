from pathlib import Path
import json,hashlib,subprocess,sys,datetime,importlib.util
repo=Path('/workspace/trading_agent');packet=repo/'trading_agent_starter/research/lean_terminal_017';work=Path('/workspace/issue-17-lean')
spec=importlib.util.spec_from_file_location('gate_compare',packet/'compare.py');comparator=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparator)
case_ids=sys.argv[1:]
if not case_ids:raise SystemExit('Explicit bounded case selection required')
input=json.loads((packet/'fixtures_v2/input.json').read_text());manifest=json.loads((packet/'fixtures_v2/manifest.json').read_text())
for name,digest in manifest['sha256'].items():assert hashlib.sha256((packet/'fixtures_v2'/name).read_bytes()).hexdigest()==digest
image='mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa'
recordfile=work/'evidence/gate-attempts.json';records=json.loads(recordfile.read_text())if recordfile.exists()else[]
for cid in case_ids:
 build=json.loads((packet/'build/manifest.json').read_text())
 for relative,digest in build['runtime_files_sha256'].items():
  assert hashlib.sha256((work/'host/bin/Release/net10.0'/relative).read_bytes()).hexdigest()==digest,relative
 assert cid in [x['case_id']for x in input['cases']]
 hashes=[]
 # Resume only verified successful runs of the same frozen bundle; preserve failed attempts.
 for prior in records:
  if prior.get('case_id')!=cid or prior.get('verdict') not in ['PASS','CONTRACT_VIOLATION_DETECTED_AS_REQUIRED'] or prior.get('host_dll_sha256')!=build['runtime_files_sha256']['LeanTerminal.dll']:continue
  saved=Path(prior['output'])
  try:
   comparator.compare_files(saved,packet/'fixtures_v2'/(cid+'.expected.json'))
   digest=hashlib.sha256(saved.read_bytes()).hexdigest();assert digest==prior['output_sha256']
   hashes.append(digest)
  except Exception:continue
 for repeat in range(len(hashes)+1,3):
  attempt=len(records)+2 # attempt01 was the preserved invalid initial quote-seed run.
  name=f'issue17-terminal-{attempt:02d}';filename=f'{cid}.attempt{attempt:02d}.json';output=work/'runtime-output'/filename;log=work/'evidence'/(filename+'.log')
  cmd=['docker','run','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--volume',str(work)+':/work:ro','--volume',str(work/'runtime-output')+':/out','--workdir','/work','--env','DOTNET_CLI_HOME=/tmp/dotnet','--env','DOTNET_CLI_TELEMETRY_OPTOUT=1','--env','DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1','--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false','--env','ALPACA_LIVE_TRADE=false',image,'dotnet','/work/host/bin/Release/net10.0/LeanTerminal.dll','/work/fixtures_v2',cid,'/out/'+filename]
  record={'case_id':cid,'repeat':repeat,'attempt':attempt,'container':name,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'output':str(output),'log':str(log),'host_dll_sha256':build['runtime_files_sha256']['LeanTerminal.dll'],'build_manifest_sha256':hashlib.sha256((packet/'build/manifest.json').read_bytes()).hexdigest()}
  with log.open('w')as f:
   try:process=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90);record['exit_code']=process.returncode
   except subprocess.TimeoutExpired:record['timeout_seconds']=90;record['exit_code']=124
  inspect=subprocess.run(['docker','inspect',name,'--format','{{json .HostConfig}}'],text=True,capture_output=True)
  if inspect.returncode==0:
   info=json.loads(inspect.stdout);record['container_controls']={k:info[k]for k in ['NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt']}
  else:record['container_inspect_unavailable']=inspect.stderr
  status=3
  try:
   assert output.exists(),'No output artifact'
   record['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
   result=comparator.compare_files(output,packet/'fixtures_v2'/(cid+'.expected.json'))
   assert record['exit_code']==0,'Nonzero runtime exit'
   record['verdict']=result;hashes.append(record['output_sha256']);status=0
  except comparator.GateMismatch as e:
   record['verdict']='LEAN_BLOCKER_FOUND'if e.blocker else'LEAN_TERMINAL_GATE_INCOMPLETE';record['first_divergence']=str(e);status=2 if e.blocker else 3
  except Exception as e:
   record['verdict']='LEAN_TERMINAL_GATE_INCOMPLETE';record['first_divergence']=repr(e)
  records.append(record);recordfile.write_text(json.dumps(records,indent=2)+'\n')
  subprocess.run(['docker','rm',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  print(json.dumps({'case':cid,'attempt':attempt,'verdict':record['verdict'],'divergence':record.get('first_divergence')}),flush=True)
  if status:raise SystemExit(status)
 if len(set(hashes))!=1:raise SystemExit('LEAN_TERMINAL_GATE_INCOMPLETE: clean-process canonical hashes differ')
 print(cid+' deterministic byte hash '+hashes[0],flush=True)
