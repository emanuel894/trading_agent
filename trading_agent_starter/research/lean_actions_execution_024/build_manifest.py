"""Bind the separate Issue24 host to immutable accepted public runtime assemblies."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;W=Path('/workspace/issue-24-lean');P=R.parent/'lean_identity_time_019'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((P/'build/manifest.json').read_text());runtime=W/'host/bin/Release/net10.0'
files={str(p.relative_to(runtime)):sha(p) for p in sorted(runtime.rglob('*')) if p.is_file()};shared={n:h for n,h in files.items() if n in old['runtime_files_sha256']}
assert shared and all(old['runtime_files_sha256'][n]==h for n,h in shared.items())
configs=json.loads((P/'validation.json').read_text())['config_sha256']
for name,h in configs.items():assert sha(Path('/workspace/issue-19-lean')/name)==h,name
out=dict(source_pin=old['source_pin'],source_tree=old['source_tree'],image=old['image'],sdk=old['sdk'],runtime=old['runtime'],original_build_manifest_sha256=sha(P/'build/manifest.json'),runtime_files_sha256=files,shared_runtime_files=len(shared),config_sha256=configs,code_sha256={str(p.relative_to(R)):sha(p) for p in sorted((R/'host').iterdir()) if p.is_file()})
(R/'build.json').write_text(json.dumps(out,indent=2)+'\n');print(len(files),'runtimefiles,',len(shared),'unchangedsharedfiles')
