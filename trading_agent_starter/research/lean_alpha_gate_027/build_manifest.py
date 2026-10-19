"""Freeze restored source/build/config provenance; never execute a fixture."""
from pathlib import Path
import hashlib,json,shutil,subprocess,gzip
R=Path(__file__).resolve().parent;W=Path('/workspace/issue-27-lean');P=W/'packet'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=Path('/workspace/audit-upstreams/framework-audit-20261018/execution/lean');pin='d4cac37514427c84d40064cecbf3f0e6be4b0137'
 assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==pin
 entries=subprocess.check_output(['git','-C',str(source),'ls-tree','-r','-z',pin]).split(b'\0');tracked=[]
 for entry in entries:
  if not entry:continue
  meta,raw_name=entry.split(b'\t',1);name=raw_name.decode();tracked.append(name);data=(W/'source'/name).read_bytes()
  blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  assert blob==meta.decode().split()[2],'Source changed: '+name
 for file in ['host/Program.cs','host/ResearchAlgorithm.cs','host/LeanResearch.csproj']:
  assert sha(R/file)==sha(W/file),'Compile current source before freezing: '+file
 for directory in ['host','fixtures']:
  if (P/directory).exists():shutil.rmtree(P/directory)
  shutil.copytree(W/'host' if directory=='host' else R/'fixtures',P/directory)
 code=['host/Program.cs','host/ResearchAlgorithm.cs','host/LeanResearch.csproj','compare.py','evaluate.py','run_gate.py','freeze.py','build_manifest.py','source_refs.json']
 for file in code:
  target=P/file;target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(R/file,target)
 runtime=P/'host/bin/Release/net10.0';old=json.loads((R.parent/'lean_actions_execution_024/build.json').read_text())
 shared={f.name:sha(f) for f in runtime.iterdir() if f.is_file() and f.name in old['runtime_files_sha256']}
 assert all(h==old['runtime_files_sha256'][n] for n,h in shared.items()),'Shared binary binding changed'
 config={n:sha(W/n) for n in old['config_sha256']}
 assert config==old['config_sha256'],'Engine config binding changed'
 locks={str(p.relative_to(W)):sha(p) for p in (W/'source').rglob('packages.lock.json') if 'obj/' not in str(p)}
 locks['host/packages.lock.json']=sha(W/'host/packages.lock.json')
 for name in ['complete','empty','missing','tampered','config_tampered','download','history']:
  target=W/'stores'/name
  if target.exists():shutil.rmtree(target)
  if name=='empty':target.mkdir(parents=True)
  else:
   shutil.copytree(R/'fixtures',target)
   if name=='missing':(target/'input.json').unlink()
   if name=='tampered':(target/'input.json').write_bytes((target/'input.json').read_bytes()+b' ')
   if name=='config_tampered':(target/'config.json').write_bytes((target/'config.json').read_bytes()+b' ')
 b=dict(source_pin=pin,source_tree=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD^{tree}'],text=True).strip(),tracked_source_files_verified=len(tracked),image=old['image'],sdk='10.0.402',runtime='10.0.13',code_sha256={n:sha(R/n) for n in code},runtime_files_sha256={f.name:sha(f) for f in sorted(runtime.iterdir()) if f.is_file()},config_sha256=config,original_identical_shared_files=shared,locks_sha256=locks)
 (R/'build.json').write_text(json.dumps(b,indent=2)+'\n')
 for n in ['source-build.log','host-build01.log','host-build02.log','host-build03.log','host-build04.log','host-build05.log','host-build06.log','host-build07.log','comparator-red.log']:
  if (W/n).exists():(R/'evidence'/(n+'.gz')).write_bytes(gzip.compress((W/n).read_bytes(),mtime=0))
 print(len(shared),'runtime files byte-identical to accepted evidence;',len(tracked),'tracked source files verified unchanged')
if __name__=='__main__':main()
