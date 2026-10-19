"""Explicit Q04–Q11 runner. Every launch is journaled before the side effect."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import compare
from verify_bindings import verify


PACKET=ROOT.parent
WORK=Path('/workspace/issue-19-lean')
IMAGE='mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    temporary=p.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(x,indent=2)+'\n')
    temporary.replace(p)

def main(ids):
    if not ids:raise SystemExit('Explicit bounded case IDs required')
    manifest=PACKET/'fixtures_v3/manifest.json'
    for f,h in json.loads(manifest.read_text())['sha256'].items():
        assert digest(PACKET/'fixtures_v3'/f)==h,f
        assert digest(WORK/'fixtures_v3'/f)==h,f
    build=PACKET/'build/manifest.json'
    build_info=json.loads(build.read_text())
    assert build_info['host_source_sha256']==digest(PACKET/'host/Program.cs')
    assert build_info['host_project_sha256']==digest(PACKET/'host/LeanIdentity.csproj')
    assert build_info['image']==IMAGE
    runtime=WORK/'host/bin/Release/net10.0'
    for f,h in build_info['runtime_files_sha256'].items():assert digest(runtime/f)==h,f
    bundle=json.loads((PACKET/'fixtures_v3/input.json').read_text())
    allowed={x['case_id'] for x in bundle['cases']}
    journal=ROOT/'evidence/attempts.json'
    records=json.loads(journal.read_text()) if journal.exists() else []
    proof=verify()
    # Bind runner/comparator/config/source verification, beyond the original runner's checks.
    proof_digest=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    prior_records=json.loads((PACKET/'evidence/attempts.json').read_text())
    base_attempt=max(r['attempt'] for r in prior_records)
    if any(r['verdict']=='LAUNCH_PENDING' for r in records):
        raise SystemExit('Reconcile the journaled pending container/output before another launch')
    binding=dict(build_manifest_sha256=digest(build),fixture_manifest_sha256=digest(manifest),
                 host_source_sha256=digest(PACKET/'host/Program.cs'),image=IMAGE,
                 verification_sha256=proof_digest,runner_sha256=digest(Path(__file__)),
                 comparator_sha256=digest(PACKET/'compare.py'),verifier_sha256=digest(ROOT/'verify_bindings.py'))
    for cid in ids:
        assert cid in allowed and cid[:3] in ['Q%02d'%i for i in range(4,12)],cid
        oracle=PACKET/'fixtures_v3'/(cid+'.expected.json')
        accepted=[]
        for prior in records:
            if prior.get('case_id')==cid and prior.get('verdict')=='PASS' and prior.get('binding')==binding:
                output=ROOT/'evidence'/prior['output']
                assert digest(output)==prior['output_sha256']
                compare.compare_file(output,oracle,PACKET/'fixtures_v3/input.json')
                accepted.append(prior['output_sha256'])
        for repeat in range(len(accepted)+1,3):
            number=base_attempt+len(records)+1;name=f'issue21-gate-{number:03d}'
            filename=f'{cid}.issue21.attempt{number:03d}.json'
            raw=WORK/'runtime-output'/filename
            output=ROOT/'evidence'/filename
            log=ROOT/'evidence'/(filename+'.log')
            cmd=['docker','--host=unix:///var/run/docker.sock','run','--name',name,
                 '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                 '--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
                 '--volume',str(WORK)+':/work:ro','--volume',str(WORK/'runtime-output')+':/out',
                 '--workdir','/work','--env','DOTNET_CLI_HOME=/tmp/dotnet','--env','DOTNET_CLI_TELEMETRY_OPTOUT=1',
                 '--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false','--env','ALPACA_LIVE_TRADE=false',
                 IMAGE,'dotnet','/work/host/bin/Release/net10.0/LeanIdentity.dll','/work/fixtures_v3',cid,'/out/'+filename]
            record=dict(case_id=cid,repeat=repeat,attempt=number,output=filename,binding=binding,
                        command=cmd,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict='LAUNCH_PENDING')
            records.append(record);save(journal,records)
            try:
                with log.open('x') as f:
                    result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
                record['exit_code']=result.returncode
            except subprocess.TimeoutExpired:
                record['exit_code']=124
                subprocess.run(['docker','--host=unix:///var/run/docker.sock','stop','--time','1',name],capture_output=True)
            inspect=subprocess.run(['docker','--host=unix:///var/run/docker.sock','inspect',name],capture_output=True,text=True)
            if inspect.returncode==0:
                data=json.loads(inspect.stdout)[0]
                record['container_controls']={k:data['HostConfig'][k] for k in ['NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt']}
                record['container_user']=data['Config']['User']
                record['container_state']={k:data['State'][k] for k in ['Status','ExitCode','OOMKilled','Error']}
            try:
                assert raw.exists(),'No native output'
                assert not output.exists(),'Refuse to overwrite output'
                output.write_bytes(raw.read_bytes());record['output_sha256']=digest(output)
                assert record['exit_code']==0,'Nonzero native exit'
                assert record['container_controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'])
                assert record['container_user']=='65534:65534'
                compare.compare_file(output,oracle,PACKET/'fixtures_v3/input.json')
                record['verdict']='PASS';accepted.append(record['output_sha256'])
            except Exception as e:
                # A mismatch requires diagnosis: do not automatically relabel harness defects as LEAN blockers.
                record['verdict']='LEAN_IDENTITY_TIME_GATE_INCOMPLETE';record['first_divergence']=str(e)
            save(journal,records)
            subprocess.run(['docker','--host=unix:///var/run/docker.sock','rm',name],capture_output=True)
            print(json.dumps({k:record.get(k) for k in ['case_id','attempt','verdict','first_divergence']}),flush=True)
            if record['verdict']!='PASS':raise SystemExit(3)
        assert len(set(accepted))==1,'Clean-process replay bytes differ: '+cid
        print(cid+' deterministic '+accepted[0],flush=True)

if __name__=='__main__':
    approval=ROOT/'V3_ORACLE_REVIEW.json'
    assert approval.exists() and json.loads(approval.read_text())['approved'] is True,'Independent v3 approval missing'
    assert json.loads(approval.read_text())['v3_manifest_sha256']==digest(PACKET/'fixtures_v3/manifest.json'),'Approval does not bind this v3'
    main(sys.argv[1:])
