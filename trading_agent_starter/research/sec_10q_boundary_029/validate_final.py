"""Final-head fixture/packet checks; keep receipts outside git, do not inspect reports."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

R = Path(__file__).resolve().parent
PROJECT = R.parents[1]
REPO = PROJECT.parent
OUT = Path('/workspace/issue29-final-validation')
OUT.mkdir(exist_ok=True)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO, text=True)
receipt = OUT / (head + '.json')
assert not receipt.exists(), 'Inspect the existing exact-head receipt before repeating checks'
commands = [
    ('repository', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    ('source-packet', [sys.executable, str(R / 'verify_packet.py')]),
    ('demo', [sys.executable, '-m', 'agent', 'demo']),
]
result = dict(head=head, python=sys.version,
              started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), checks=[])
for name, cmd in commands:
    log = OUT / (head + '-' + name + '.txt')
    with log.open('x') as f:
        p = subprocess.run(cmd, cwd=PROJECT, stdout=f, stderr=subprocess.STDOUT)
    result['checks'].append(dict(name=name, command=cmd, exit_code=p.returncode,
        log=str(log), sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(name, p.returncode, log.read_text()[-500:], flush=True)
    if p.returncode:
        raise SystemExit(3)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() == head
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO, text=True)
result['all_passed'] = True
result['completed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt.write_text(json.dumps(result, indent=2) + '\n')
