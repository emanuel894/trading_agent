# Audit evidence and reproduction

This directory accompanies `BUILD_VS_ADOPT_20261017.md`. It is architecture-audit
metadata, not scientific acquisition evidence, registered source admission, a
vendor entitlement test or a performance dataset.

* `upstream_sources.json`: public upstream commit references, inspected paths,
  retrieval hashes, package/version evidence and blocked documentation URLs.
* `validation.json`: baseline, platform, full-suite results and checks performed.
* `test-environment-python313.txt`: resolved dependency versions for the recorded
  Python 3.13 run; descriptive evidence, not a new project lockfile.

Source downloads and test environments were kept outside the checkout at
`/workspace/audit-upstreams`. No upstream source was vendored or executed. The
EdgarTools archive exceeded the retrieval size bound; only its individually
retrieved files were inspected. No complete-tree absence claim is made for it.

## Repeat the existing validation

Use the existing checkout at the recorded baseline in a disposable environment;
cloud tasks are already isolated, so do not create a Git worktree unless asked.
Preserve existing changes and do not reset a working tree to reproduce an audit.
From the repository root, with Python 3.13 and its venv support installed:

```bash
python3.13 -m venv /tmp/trading-agent-audit-venv
/tmp/trading-agent-audit-venv/bin/python -m pip install -r trading_agent_starter/requirements.txt
cd trading_agent_starter
PYTHONDONTWRITEBYTECODE=1 /tmp/trading-agent-audit-venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 /tmp/trading-agent-audit-venv/bin/python -m agent demo --output /tmp/trading-agent-audit-demo
PYTHONDONTWRITEBYTECODE=1 /tmp/trading-agent-audit-venv/bin/python -m agent.acquisition_registration --verify-only
PYTHONDONTWRITEBYTECODE=1 /tmp/trading-agent-audit-venv/bin/python -c 'from agent.acquisition_identity import registration; registration()'
/tmp/trading-agent-audit-venv/bin/python -m pip check
```

At the recorded baseline expect 204 tests, no skips/failures/errors, and 300
synthetic demo bars. Tests use fixtures; no authenticated acquisition or broker
calls are needed. Do not run the acquisition probes as a validation substitute.
The host's Python 3.13 lacked `ensurepip`; for this audit Python 3.12's pip was
used with `--python /workspace/audit-upstreams/test-venv313/bin/python` to install,
check and list packages in the isolated 3.13 environment. No system install or
verification bypass was required.

Requirements contain floating transitives, including `pytz>=2024.1`; a future
resolution can differ. The recorded dependency list shows this run's resolution.
Do not overwrite the repository requirements or claim a hash-locked installation.
Windows behavior requires the real Windows CI job; this audit ran Linux only.

## Repeat upstream byte verification

For a listed file, retrieve the **exact** `raw.githubusercontent.com` URL from
the manifest with ordinary TLS verification, hash its bytes with SHA-256 and
compare against `sha256`. Do not substitute branch HEAD and call it the same
audit. A changed/deleted file or blocked URL must be reported as such. For
example, from the repository root:

```python
import hashlib, json, urllib.request
from pathlib import Path

manifest = json.loads(Path('audit/20261017/upstream_sources.json').read_text())
project = next(p for p in manifest['repositories']
               if p['repository'] == 'TauricResearch/TradingAgents')
source = next(f for f in project['files']
              if f['path'] == 'tradingagents/agents/context.py'
              and 'sha256' in f)
with urllib.request.urlopen(source['url'], timeout=30) as response:
    raw = response.read()
assert hashlib.sha256(raw).hexdigest() == source['sha256']
```

`git ls-remote --symref https://github.com/OWNER/REPO.git HEAD 'refs/tags/*'`
rechecks current refs using existing authentication/proxy configuration; it does
not reconstruct an earlier observation, prove tag dates or verify a binary
release. Current package metadata is available at each recorded PyPI URL but can
change; its recorded response hash identifies what this audit read. Retain
artifact attestations and verify wheels separately during actual adoption.

Public vendor sites and GitHub's metadata API were blocked by the runtime proxy.
Do not convert those errors into a feature/license/price conclusion. No network
allowlist or cloud environment configuration was changed for this audit. Exact
baseline source can be read through GitHub at commit
`9ff6aa4c5fcedd1051ee3265a7d7982fa4215f9b`; newer audit files do not modify that
baseline's research claims.
