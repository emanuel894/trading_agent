"""Bind the isolated continuation build to original shared assemblies."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;WORK=Path('/workspace/issue-23-lean')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R.parent/'build/manifest.json').read_text());runtime=WORK/'host/bin/Release/net10.0'
files={str(p.relative_to(runtime)):sha(p) for p in sorted(runtime.rglob('*')) if p.is_file()}
shared={n:h for n,h in files.items() if n in old['runtime_files_sha256']}
assert shared and all(old['runtime_files_sha256'][n]==h for n,h in shared.items()),'Shared assembly changed'
manifest=dict(source_pin=old['source_pin'],source_tree=old['source_tree'],source_files_manifest_sha256=old['source_files_manifest_sha256'],image=old['image'],sdk=old['sdk'],runtime=old['runtime'],original_build_manifest_sha256=sha(R.parent/'build/manifest.json'),shared_files_verified=len(shared),runtime_files_sha256=files,code_sha256={str(p.relative_to(R)):sha(p) for p in sorted((R/'host').iterdir()) if p.is_file()})
(R/'build.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(len(files),'runtime files;',len(shared),'unchanged shared files')
