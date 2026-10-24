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


def verify_bindings(runtime, config_root, manifest, expected_manifest_sha):
    if sha(manifest.read_bytes())!=expected_manifest_sha:raise RuntimeError('ACCEPTED_MANIFEST_CHANGED')
    binding=json.loads(manifest.read_text())
    for mapping,root in ((binding['runtime_files_sha256'],runtime),(binding['config_sha256'],config_root)):
        for name,digest in mapping.items():
            if sha((root/name).read_bytes())!=digest:raise RuntimeError('RUNTIME_OR_CONFIG_BINDING_CHANGED')
    return binding


def check_output(output, prepared, failure=None, expected_initialized=False):
    if failure:
        if (failure not in output.get('error','') or output['initialized'] is not expected_initialized
            or (expected_initialized and not output['ended']) or output['orders']!=0):raise RuntimeError('NEGATIVE_ORACLE')
    elif (output.get('error') or not output['initialized'] or not output['ended']
          or output['on_data_batches']!=len(prepared['batches']) or output['events']!=prepared['events']
          or output['trace_sha256']!=prepared['expected_trace_sha256'] or output['provider_calls']!=0
          or output['orders']!=0 or output['execution_admitted']):raise RuntimeError('POSITIVE_ORACLE')


def build(work):
    parent=HERE.parent.parent/'lean_alpha_gate_027/continuation_v2/build.json'
    verify_bindings(RUNTIME,Path('/workspace/issue-27-lean'),parent,
                    'dbf0134509f550f9333548c59c12fa1d556bdf54f42ce70c2da74ba05c251ebb')
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


def execute(work, app, name, prepared, repeat, failure=None, expected_initialized=False):
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
        if result.returncode!=(3 if failure else 0):raise RuntimeError('EXIT_ORACLE')
        check_output(output,prepared,failure,expected_initialized)
        receipt['status']='PASS';return receipt
    except BaseException as error:
        receipt['status']='FAILED';receipt['failure']=repr(error)
        subprocess.run(DOCKER+['stop','--time','1',container],capture_output=True)
        raise
    finally:
        write(directory/'receipt.json',receipt)
        subprocess.run(DOCKER+['rm',container],capture_output=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',required=True);parser.add_argument('--projection',required=True);parser.add_argument('--resume',action='store_true');parser.add_argument('--cases',nargs='+')
    args=parser.parse_args();work=Path(args.work).resolve();repo=HERE.parents[3]
    if work==repo or repo in work.parents:raise RuntimeError('PRIVATE_WORK_OUTSIDE_CHECKOUT_REQUIRED')
    if not args.resume:work.mkdir(mode=0o700,exist_ok=False)
    elif not (work/'summary.json').is_file():raise RuntimeError('EXISTING_CHECKPOINT_REQUIRED')
    projection=Path(args.projection).read_bytes()
    if sha(projection)!='5097fa90a3080a60d20db230cc90849317654a37a3f5ce2ee6968dff7482f969':raise RuntimeError('PROJECTION_BINDING_CHANGED')
    real=p.prepare(json.loads(projection),[p.session('2025-01-15T14:30:00Z','2025-01-15T21:00:00Z','existing-2025-calendar-observation-premise')])
    names=('EngineReplay.cs','prepare.py','run.py','build-local.sh','CONTRACT.md',
           'fixtures/synthetic-positive.json','fixtures/synthetic-gap.json','fixtures/synthetic-session-reject.json')
    code={n:sha((HERE/n).read_bytes()) for n in names}
    if args.resume:
        summary=json.loads((work/'summary.json').read_text());app=work/'build/app'
        if summary['code_sha256']!=code or summary['source_projection_sha256']!=sha(projection) or summary['compiled_sha256']!=sha((app/'SipEngine.dll').read_bytes()):raise RuntimeError('RESUME_BINDING_CHANGED')
        verify_bindings(RUNTIME,Path('/workspace/issue-27-lean'),HERE.parent.parent/'lean_alpha_gate_027/continuation_v2/build.json',
                        'dbf0134509f550f9333548c59c12fa1d556bdf54f42ce70c2da74ba05c251ebb')
    else:
        app=build(work);summary={'source_projection_sha256':sha(projection),'compiled_sha256':sha((app/'SipEngine.dll').read_bytes()),
                                'code_sha256':code,'attempts':[],'status':'RUNNING'}
        write(work/'summary.json',summary)
    cases=[('synthetic-positive',json.loads((HERE/'fixtures/synthetic-positive.json').read_text()),None),
           ('synthetic-gap',json.loads((HERE/'fixtures/synthetic-gap.json').read_text()),None),
           ('synthetic-session-reject',json.loads((HERE/'fixtures/synthetic-session-reject.json').read_text()),None)]
    bad=json.loads(p.encode(cases[0][1]));bad['mode']='EXECUTABLE';cases.append(('synthetic-execution-denied',bad,'OBSERVATION_SCOPE'))
    bad=json.loads(p.encode(cases[0][1]));bad['sessions']=[];cases.append(('synthetic-no-session',bad,'SESSION_BOUNDARY'))
    bad=json.loads(p.encode(cases[0][1]));bad['expected_trace_sha256']='0'*64;cases.append(('synthetic-post-end-failure',bad,'DELIVERY_ORACLE'))
    cases.append(('real-observations',real,None))
    selected=args.cases or (summary.get('selected_cases') if args.resume else None) or [c[0] for c in cases]
    if len(selected)!=len(set(selected)) or set(selected)-{c[0] for c in cases}:raise RuntimeError('INVALID_CASE_SELECTION')
    if args.resume and summary['selected_cases']!=selected:raise RuntimeError('RESUME_SCOPE_CHANGED')
    cases=[c for c in cases if c[0] in selected];summary['selected_cases']=selected
    completed={(a['case'],a['repeat']):a for a in summary['attempts']}
    if len(completed)!=len(summary['attempts']):raise RuntimeError('DUPLICATE_ATTEMPT_IDENTITY')
    executed=False
    for name,data,failure in cases:
        pair=[]
        for repeat in (1,2):
            expected_init=name=='synthetic-post-end-failure'
            if (name,repeat) in completed:
                receipt=completed[(name,repeat)];raw=(work/f'{name}-{repeat}/artifacts/output.json').read_bytes()
                if receipt['status']!='PASS' or receipt['input_sha256']!=sha(p.encode(data)) or receipt['output_sha256']!=sha(raw):raise RuntimeError('RESUME_RECEIPT_CHANGED')
                check_output(json.loads(raw),data,failure,expected_init)
                pair.append(receipt['output_sha256']);continue
            if (work/f'{name}-{repeat}').exists():raise RuntimeError('RECONCILE_EXISTING_ATTEMPT_BEFORE_RESUME')
            executed=True
            receipt=execute(work,app,name,data,repeat,failure,expected_init);summary['attempts'].append(receipt);write(work/'summary.json',summary)
            pair.append(receipt['output_sha256']);print(name,repeat,'PASS',flush=True)
        if pair[0]!=pair[1]:raise RuntimeError('NONDETERMINISTIC_PAIR')
    if executed or summary['status']!='NATIVE_ENGINE_DIAGNOSTIC_PASS':
        summary['status']='NATIVE_ENGINE_DIAGNOSTIC_PASS';write(work/'summary.json',summary)
    else:print('Existing completion verified; zero native launches and no checkpoint writes',flush=True)


if __name__=='__main__':main()
