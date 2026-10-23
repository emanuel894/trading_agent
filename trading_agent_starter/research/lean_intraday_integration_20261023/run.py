"""One explicit bounded run of NEW integration cases; refuses an existing output.

Run from trading_agent_starter: python -m research.lean_intraday_integration_20261023.run
Requires the preserved PR28 executor; never rebuilds, downloads or reruns Q cases.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

from . import integration as m

HERE=Path(__file__).resolve().parent
STARTER=HERE.parents[1]
WORK=Path('/workspace/issue-27-lean')
OUTPUT=WORK/'intraday-20261023-v2'
DOCKER=['docker','--host=unix:///var/run/docker.sock']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,default=str)+'\n')


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    accepted=STARTER/'research/lean_alpha_gate_027/continuation_v2'
    build=json.loads((accepted/'build.json').read_text())
    assert sha(accepted/'build.json') == 'dbf0134509f550f9333548c59c12fa1d556bdf54f42ce70c2da74ba05c251ebb', 'Trusted PR28 build manifest changed'
    for names,root in ((build['runtime_files_sha256'],WORK/'packet/host/bin/Release/net10.0'),
                       (build['config_sha256'],WORK),(build['code_sha256'],WORK/'packet'),
                       (build['locks_sha256'],WORK)):
        for name,digest in names.items():
            assert sha(root/name)==digest, 'Original binding changed: '+name
    image=build['image']
    inspected=json.loads(subprocess.check_output(DOCKER+['image','inspect',image]))[0]
    assert image in inspected['RepoDigests']
    OUTPUT.mkdir(mode=0o755,exist_ok=False)
    OUTPUT.chmod(0o755)  # Only this NEW public-synthetic packet; never system/accepted paths.
    inputs=OUTPUT/'inputs'; inputs.mkdir(mode=0o755);inputs.chmod(0o755)
    outputs=OUTPUT/'outputs'; outputs.mkdir(mode=0o777); outputs.chmod(0o777)
    data=m.scenarios(); decisions={name:m.decide(*args) for name,args in data.items()}
    assert decisions['baseline']==decisions['future_revision']
    assert [d['signal'] for d in decisions.values()]==[True,True,False,False]
    cases=[m.native_case(name,d) for name,d in decisions.items()]
    write(inputs/'input.json',{'source_pin':build['source_pin'],'capture_mode':'fixture','cases':cases})
    write(inputs/'config.json',dict(trading_enabled=False,allow_paper_orders=False,alpaca_live_trade=False))
    write(inputs/'manifest.json',{'sha256':{n:sha(inputs/n) for n in ('input.json','config.json')}})
    for path in inputs.iterdir():path.chmod(0o644)
    write(OUTPUT/'synthetic-inputs.json',{name:args for name,args in ((n,{'sessions':s,'bars':[asdict(b) for b in bs],'releases':[asdict(r) for r in rs]}) for n,(s,bs,rs) in data.items())})
    write(OUTPUT/'decisions.json',decisions)
    write(OUTPUT/'python-measurement.json',m.measure())
    receipt={'base_sha':'051c6c2d99f1ef6cfefd082ff646ed1c1cd88a09',
             'source_pin':build['source_pin'],'build_manifest_sha256':sha(accepted/'build.json'),
             'runtime_verified_files':len(build['runtime_files_sha256']), 'image':image,
             'image_id':inspected['Id'],'python':platform.python_version(),
             'code_sha256':{n:sha(HERE/n) for n in ('integration.py','run.py')},
             'pr36_code_sha256':sha(STARTER/'agent/offline_chart_gov_demo.py'),
             'fixture_manifest_sha256':sha(inputs/'manifest.json'),'attempts':[],
             'external_spend_usd':0,'status':'RUNNING'}
    write(OUTPUT/'receipt.json',receipt)
    for case in cases:
        pair=[]
        for repeat in (1,2):
            name=case['case_id']+'-'+str(repeat); filename=name+'.json'
            command=DOCKER+['run','--name',name,'--pull=never','--network','none','--read-only',
                           '--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534',
                           '--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
                           '--volume',str(WORK)+':/work:ro','--volume',str(WORK/'packet')+':/packet:ro',
                           '--volume',str(inputs)+':/inputs:ro','--volume',str(outputs)+':/out',
                           '--workdir','/work','--env','DOTNET_CLI_HOME=/tmp/dotnet',
                           '--env','DOTNET_CLI_TELEMETRY_OPTOUT=1',
                           '--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false',
                           '--env','ALPACA_LIVE_TRADE=false',image,'sh','-c',
                           f'dotnet /packet/host/bin/Release/net10.0/LeanResearch.dll /inputs {case["case_id"]} /out/{filename} /inputs; native_exit=$?; cat /sys/fs/cgroup/memory.peak > /out/{name}.memory; exit "$native_exit"']
            record={'case_id':case['case_id'],'repeat':repeat,'command':command,'status':'LAUNCH_PENDING'}
            receipt['attempts'].append(record);write(OUTPUT/'receipt.json',receipt)
            start=time.perf_counter()
            try:
                with (OUTPUT/(name+'.log')).open('x') as log:
                    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=90)
                record['wall_seconds']=time.perf_counter()-start
                record['exit_code']=result.returncode
                inspect=json.loads(subprocess.check_output(DOCKER+['inspect',name]))[0]
                record['controls']={k:inspect['HostConfig'][k] for k in ('NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt')}
                record['user']=inspect['Config']['User']
                assert record['controls']==dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'])
                assert record['user']=='65534:65534' and result.returncode==0
                assert inspect['State']['OOMKilled'] is False
                output=json.loads((outputs/filename).read_text())
                m.check_native(output, decisions[case['case_id'].removeprefix('INTRADAY_')]['signal'])
                record['output_sha256']=sha(outputs/filename);pair.append(record['output_sha256'])
                record['cgroup_peak_bytes']=int((outputs/(name+'.memory')).read_text())
                record['status']='PASS'
            except BaseException as error:
                record['status']='FAILED';record['error']=repr(error);receipt['status']='STOPPED'
                subprocess.run(DOCKER+['stop','--time','1',name],capture_output=True)
                raise
            finally:
                write(OUTPUT/'receipt.json',receipt)
                subprocess.run(DOCKER+['rm',name],capture_output=True)
            print(name,record['status'],flush=True)
        assert len(set(pair))==1, 'New integration clean-pair mismatch'
    receipt['status']='SYNTHETIC_INTRADAY_INTEGRATION_PASS'
    receipt['memory_limits']='cgroup peak includes dotnet, shell and page cache; not isolated engine RSS or incremental feature RAM'
    write(OUTPUT/'receipt.json',receipt)


if __name__=='__main__':
    main()
