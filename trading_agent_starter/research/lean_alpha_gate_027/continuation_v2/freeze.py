"""Reproduce v2 inputs by exact copy of independently frozen v1 bytes; no new oracle."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parent
if (R/'fixtures/manifest.json').exists():raise SystemExit('Frozen v2 fixtures exist; do not overwrite')
shutil.copytree(R.parent/'fixtures',R/'fixtures')
for n,h in json.loads((R/'fixtures/manifest.json').read_text())['sha256'].items():assert hashlib.sha256((R/'fixtures'/n).read_bytes()).hexdigest()==h
