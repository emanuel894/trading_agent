"""Read-only verification of immutable prior evidence and exact reuse prerequisites."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess

ROOT=Path(__file__).resolve().parent
PACKET=ROOT.parent
REPO=PACKET.parents[2]
WORK=Path('/workspace/issue-19-lean')
SOURCE=Path('/workspace/audit-upstreams/framework-audit-20261018/execution/lean')
CODE_COMMIT='a6200ce3aa5cfd916a83be17775b125138e1af70'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def object_hash(x):return hashlib.sha256(json.dumps(x,separators=(',',':'),sort_keys=True).encode()).hexdigest()

def verify():
    preserved=json.loads((ROOT/'preserved_c70aa32_sha256.json').read_text())
    for name,digest in preserved.items():assert sha(PACKET/name)==digest,('Preserved evidence changed',name)
    build=PACKET/'build/manifest.json';info=json.loads(build.read_text())
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()==info['source_pin']
    assert subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=SOURCE,text=True).strip()==info['source_tree']
    files=[]
    for name in filter(None,subprocess.check_output(['git','ls-files','-z'],cwd=SOURCE).decode().split('\0')):
        f=SOURCE/name
        if f.is_file():
            digest=sha(f);assert sha(WORK/'source'/name)==digest,('Upstream copy mismatch',name)
            files.append([name,digest])
    source_hash=hashlib.sha256(json.dumps(files,separators=(',',':')).encode()).hexdigest()
    assert source_hash==info['source_files_manifest_sha256']
    assert len(files)==info['source_files']
    for name,digest in info['runtime_files_sha256'].items():
        assert sha(WORK/'host/bin/Release/net10.0'/name)==digest,('Runtime changed',name)
    config=json.loads((PACKET/'validation.json').read_text())['config_sha256']
    for name,digest in config.items():assert sha(WORK/name)==digest,('Config changed',name)
    code={}
    for name in ['host/Program.cs','host/LeanIdentity.csproj','compare.py','run_gate.py']:
        rel=(PACKET/name).relative_to(REPO)
        prior=subprocess.check_output(['git','show',CODE_COMMIT+':'+str(rel)],cwd=REPO)
        code[name]=sha(PACKET/name)
        assert hashlib.sha256(prior).hexdigest()==code[name],('Pre-run code changed',name)
    assert code['host/Program.cs']==info['host_source_sha256']
    assert code['host/LeanIdentity.csproj']==info['host_project_sha256']
    for version in ['fixtures','fixtures_v2','fixtures_v3']:
        for name,digest in json.loads((PACKET/version/'manifest.json').read_text())['sha256'].items():
            assert sha(PACKET/version/name)==digest,(version,name)
    spec=importlib.util.spec_from_file_location('original_issue19_compare',PACKET/'compare.py')
    compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)
    old=json.loads((PACKET/'fixtures_v2/input.json').read_text())
    new=json.loads((PACKET/'fixtures_v3/input.json').read_text())
    records=json.loads((PACKET/'evidence/attempts.json').read_text())
    reused={}
    expected_binding=dict(build_manifest_sha256=sha(build),fixture_manifest_sha256=sha(PACKET/'fixtures_v2/manifest.json'),host_source_sha256=code['host/Program.cs'],image=info['image'])
    for cid in ['Q04_before','Q04_at','Q04_after']:
        prior_case=next(c for c in old['cases']if c['case_id']==cid)
        assert prior_case==next(c for c in new['cases']if c['case_id']==cid)
        assert (PACKET/'fixtures_v2'/(cid+'.expected.json')).read_bytes()==(PACKET/'fixtures_v3'/(cid+'.expected.json')).read_bytes()
        runs=[r for r in records if r['case_id']==cid and r['verdict']=='PASS']
        assert len(runs)==2 and len({r['output_sha256']for r in runs})==1
        for run in runs:
            assert run['binding']==expected_binding
            output=PACKET/'evidence'/run['output'];assert sha(output)==run['output_sha256']
            compare.compare_file(output,PACKET/'fixtures_v2'/(cid+'.expected.json'),PACKET/'fixtures_v2/input.json')
        reused[cid]=dict(version='fixtures_v2',attempts=[r['attempt']for r in runs],output_sha256=runs[0]['output_sha256'],unchanged_case_sha256=object_hash(prior_case),oracle_sha256=sha(PACKET/'fixtures_v3'/(cid+'.expected.json')))
    return dict(source_pin=info['source_pin'],source_tree=info['source_tree'],source_files=len(files),source_files_manifest_sha256=source_hash,
        build_manifest_sha256=sha(build),runtime_files=len(info['runtime_files_sha256']),config_sha256=config,code_sha256=code,
        code_commit_before_prior_accepted_runs=CODE_COMMIT,preserved_files=len(preserved),reused=reused,
        reuse_rule='Original outputs stay bound to v2. Only unchanged case/oracle evidence is reused after exact code/source/runtime/config verification; corrected cases require fresh v3 runs.')

if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
