# Issue 11 checkpoint

Scope: qualification design only; no LEAN installation, execution or migration.
Branch: `research/issue-11-lean-contract-qualification`.
Base: `b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe`
(`feat/alpaca-paper-foundation`, includes merged PR #8).
Mandate: https://github.com/emanuel894/trading_agent/issues/11.

## Checkpoint 1 — scope and baseline

- Read AGENTS.md, AI_PROJECT_POLICY.md, ADR 001, Amendments 003/005 and
  MARKET_DATA_CONTRACT.md. No research behavior changes authorized.
- Read draft PR #10 audit at `4dd7703f429df01a6f7e67912294ec26e93b4ad0`;
  reference only, no ancestry dependency or modification.
- Dedicated branch created directly from fetched base; initial tree clean.
- Existing source-only audit captures under `/workspace/audit-upstreams/` may
  accelerate inspection, but fresh public source pins must be captured.
- Critical question: terminal forced-fill interception, including subsequent
  holding/removal effects. Do not assume fill-model replacement alone covers it.

## Checkpoint 2 — design and source evidence

- Design: `../../LEAN_CONTRACT_QUALIFICATION_20261018.md`; exact matrix Q01–Q33
  in `FIXTURE_MATRIX.md`. Provisional design status LEAN_QUALIFICATION_READY;
  no LEAN fixture has been implemented or run.
- Fresh public source/docs GET captures: 43 successful files, pinned HEAD metadata
  and ZIP retained. Alpaca root LICENSE path absent; source/README license exists.
- Source seams support terminal-first falsification without a core patch in
  principle. Runtime holding removal, nanosecond envelope ordering, fractional
  action cash and dividend payable cash remain explicit gates.
- Existing baseline: Python 3.13.5, 240 tests passed; synthetic demo passed.
  First installer attempts found no pip and unwritable default uv cache; using
  existing isolated venv with `UV_CACHE_DIR=/tmp/issue11-uv-cache uv pip install
  --python /workspace/audit-upstreams/test-venv313/bin/python -r requirements.txt`
  succeeded. No project dependency changed.
- Next: source packet/links/arithmetic/invariant validation, independent model
  review from trusted base policy, then final push and draft PR. The initial
  scope checkpoint is already pushed for recovery.

## Resume

1. Verify branch/status and read this checkpoint and the issue snapshot.
2. Read design, fixture matrix and source evidence; do not reimplement the spike.
3. Complete packet validation and independent review under trusted base policy;
   retain existing test/demo evidence and clearly mark LEAN fixtures UNRUN.
4. Commit and push only this branch; open draft PR targeting the named base.
   Attach PR to the chat. Never merge or change PR #10.

Constraints remain: no Databento, purchases, paid provider/model calls, alpha,
FMBH/Amendment 005/candidate changes, broker credentials, Paper/Live orders,
generic backtester/OMS or qualification implementation.
