"""Explicit bounded native engine diagnostic. No acquisition or strategy.

python -m research.sip_lean_bridge_20261024.engine.run --work NEW_PRIVATE_DIR \
  --projection /private/sip-projection-01.json
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import time

from . import prepare as p

HERE=Path(__file__).resolve().parent
IMAGE='mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa'
RUNTIME=Path('/workspace/issue-27-lean/packet/host/bin/Release/net10.0')
DOCKER=['docker','--host=unix:///var/run/docker.sock']


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def archive(files):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as tar:
        for name,raw in files:
            item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o600
            tar.addfile(item,io.BytesIO(raw))
    return buffer.getvalue()


def unpack(tarpath, destination):
    with tarfile.open(tarpath) as tar:
        for item in tar:
            name=PurePosixPath(item.name)
            if name.is_absolute() or '..' in name.parts or item.issym() or item.islnk():raise RuntimeError('UNSAFE_ARTIFACT')
            if item.isfile():
                path=destination.joinpath(*name.parts);path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(tar.extractfile(item).read())


def controls(name):
    value=json.loads(subprocess.check_output(DOCKER+['inspect',name]))[0]
    expected=dict(NetworkMode='none',ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'])
    actual={k:value['HostConfig'][k] for k in expected}
    if actual!=expected or value['Config']['User']!='65534:65534':raise RuntimeError('ISOLATION_CHANGED')
    if value['HostConfig']['Memory']!=2*1024**3 or value['HostConfig']['PidsLimit']!=64:raise RuntimeError('RESOURCE_CAP_CHANGED')
    if value['State']['OOMKilled']:raise RuntimeError('OOM_KILLED')
    return actual


def build(work):
    parent=HERE.parent.parent/'lean_alpha_gate_027/continuation_v2/build.json'
    binding=json.loads(parent.read_text())
    for name,digest in binding['runtime_files_sha256'].items():
        if sha((RUNTIME/name).read_bytes())!=digest:raise RuntimeError('RUNTIME_BINDING_CHANGED')
    files=[(n,(HERE/n).read_bytes()) for n in ('EngineReplay.cs','build-local.sh')]
    command=DOCKER+['run','--rm','--interactive','--pull=never','--network','none','--read-only','--cap-drop','ALL',
                    '--security-opt','no-new-privileges','--user','65534:65534','--tmpfs','/tmp:rw,nosuid,nodev,size=256m',
                    '--volume',str(RUNTIME)+':/runtime:ro',IMAGE,'sh','-c',
                    'mkdir /tmp/build; cd /tmp/build; tar xf -; sh build-local.sh >build.log 2>&1; code=$?; tar czf - .; exit "$code"']
    write(work/'build-command.json',command)
    with (work/'build.tar.gz').open('xb') as out,(work/'build-docker.log').open('x') as err:
        result=subprocess.run(command,input=archive(files),stdout=out,stderr=err,timeout=120)
    unpack(work/'build.tar.gz',work/'build')
    if result.returncode:raise RuntimeError('COMPILE_FAILED_SEE_PRIVATE_LOG')
    return work/'build/app'


def execute(work, app, name, prepared, repeat, failure=None):
    directory=work/f'{name}-{repeat}';directory.mkdir()
    data=p.encode(prepared);(directory/'input.json').write_bytes(data)
    container=f'sip-engine-{work.name}-{name}-{repeat}'
    command=DOCKER+['run','--name',container,'--interactive','--pull=never','--network','none','--read-only',
                    '--cap-drop','ALL','--security-opt','no-new-privileges','--user','65534:65534',
                    '--memory','2g','--memory-swap','2g','--cpus','2','--pids-limit','64',
                    '--tmpfs','/tmp:rw,nosuid,nodev,size=512m',
                    '--volume','/workspace/issue-27-lean/source/Data:/runtime-data:ro',
                    '--env','TRADING_ENABLED=false','--env','ALLOW_PAPER_ORDERS=false','--env','ALPACA_LIVE_TRADE=false',
                    IMAGE,'sh','-c',
                    'cd /tmp; tar xf -; dotnet app/SipEngine.dll input.json output.json '+sha(data)+' >native.log 2>&1; code=$?; cat /sys/fs/cgroup/memory.peak >memory.peak; tar czf - native.log memory.peak output.json; exit "$code"']
    receipt={'case':name,'repeat':repeat,'status':'LAUNCH_PENDING','input_sha256':sha(data),'command':command}
    write(directory/'receipt.json',receipt)
    files=[('app/'+f.name,f.read_bytes()) for f in sorted(app.iterdir()) if f.is_file()]+[('input.json',data)]
    start=time.perf_counter()
    try:
        with (directory/'artifacts.tar.gz').open('xb') as out,(directory/'docker.log').open('x') as err:
            result=subprocess.run(command,input=archive(files),stdout=out,stderr=err,timeout=120)
        receipt['wall_seconds']=time.perf_counter()-start;receipt['exit_code']=result.returncode
        receipt['controls']=controls(container)
        unpack(directory/'artifacts.tar.gz',directory/'artifacts')
        raw=(directory/'artifacts/output.json').read_bytes();output=json.loads(raw)
        receipt['output_sha256']=sha(raw);receipt['cgroup_peak_bytes']=int((directory/'artifacts/memory.peak').read_text())
        if failure:
            if result.returncode!=3 or failure not in output.get('error','') or output['initialized'] or output['orders']!=0:raise RuntimeError('NEGATIVE_ORACLE')
        else:
            if (result.returncode or output.get('error') or not output['initialized'] or not output['ended']
                or output['on_data_batches']!=len(prepared['batches']) or output['events']!=prepared['events']
                or output['trace_sha256']!=prepared['expected_trace_sha256'] or output['provider_calls']!=0
                or output['orders']!=0 or output['execution_admitted']):raise RuntimeError('POSITIVE_ORACLE')
        receipt['status']='PASS';return receipt
    except BaseException as error:
        receipt['status']='FAILED';receipt['failure']=repr(error)
        subprocess.run(DOCKER+['stop','--time','1',container],capture_output=True)
        raise
    finally:
        write(directory/'receipt.json',receipt)
        subprocess.run(DOCKER+['rm',container],capture_output=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',required=True);parser.add_argument('--projection',required=True)
    args=parser.parse_args();work=Path(args.work).resolve();repo=HERE.parents[3]
    if work==repo or repo in work.parents:raise RuntimeError('PRIVATE_WORK_OUTSIDE_CHECKOUT_REQUIRED')
    work.mkdir(mode=0o700,exist_ok=False)
    projection=Path(args.projection).read_bytes()
    if sha(projection)!='5097fa90a3080a60d20db230cc90849317654a37a3f5ce2ee6968dff7482f969':raise RuntimeError('PROJECTION_BINDING_CHANGED')
    real=p.prepare(json.loads(projection),[p.session('2025-01-15T14:30:00Z','2025-01-15T21:00:00Z','existing-2025-calendar-observation-premise')])
    app=build(work);summary={'source_projection_sha256':sha(projection),'compiled_sha256':sha((app/'SipEngine.dll').read_bytes()),
                             'code_sha256':{n:sha((HERE/n).read_bytes()) for n in ('EngineReplay.cs','prepare.py','run.py','build-local.sh','CONTRACT.md')},'attempts':[],'status':'RUNNING'}
    write(work/'summary.json',summary)
    cases=[('synthetic-positive',json.loads((HERE/'fixtures/synthetic-positive.json').read_text()),None),
           ('synthetic-gap',json.loads((HERE/'fixtures/synthetic-gap.json').read_text()),None),
           ('synthetic-session-reject',json.loads((HERE/'fixtures/synthetic-session-reject.json').read_text()),None)]
    bad=json.loads(p.encode(cases[0][1]));bad['mode']='EXECUTABLE';cases.append(('synthetic-execution-denied',bad,'OBSERVATION_SCOPE'))
    bad=json.loads(p.encode(cases[0][1]));bad['sessions']=[];cases.append(('synthetic-no-session',bad,'SESSION_BOUNDARY'))
    cases.append(('real-observations',real,None))
    for name,data,failure in cases:
        pair=[]
        for repeat in (1,2):
            receipt=execute(work,app,name,data,repeat,failure);summary['attempts'].append(receipt);write(work/'summary.json',summary)
            pair.append(receipt['output_sha256']);print(name,repeat,'PASS',flush=True)
        if pair[0]!=pair[1]:raise RuntimeError('NONDETERMINISTIC_PAIR')
    summary['status']='NATIVE_ENGINE_DIAGNOSTIC_PASS';write(work/'summary.json',summary)


if __name__=='__main__':main()
