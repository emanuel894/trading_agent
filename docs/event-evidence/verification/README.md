# Verification evidence

These are completed engineering checks, not an alpha experiment or source
qualification. The compressed logs preserve the actual command output.

- `tests.log.gz`: `python -m unittest discover -s tests -v` from
  `trading_agent_starter`, Python 3.13.5/Linux: 240 tests, no failures/errors/skips.
- `demo.log.gz`: `python -m agent demo` from the same directory: 300 synthetic
  bars, no broker orders, no model training/promotion.
- `install.log.gz`: disposable verification environment dependencies. Production
  requirements and dependency files are unchanged. `jsonschema==4.26.0` is used
  only to validate this design packet offline.

To reproduce the artifact checks with an existing disposable environment:

```bash
python docs/event-evidence/verify_artifacts.py
git diff --check
```

The environment needs Python 3.13 and `jsonschema==4.26.0`. The original checks
used `/tmp/issue12-py313` created with `uv venv --python /usr/bin/python3.13`
and installed `trading_agent_starter/requirements.txt` plus `jsonschema`. No
source credentials, data/provider/model APIs or broker connection are needed.

The [final verification record](../verification.json) contains the command
results, content hashes, review scope and material limits. Source capture
integrity is checked against [the existing manifest](../sources/captures.json),
without repeating any capture. Hosted Ubuntu/Windows CI runs on the draft PR;
local test success is separate evidence.
