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

## Checkpoint 3 — independent review and finalization

- Resumed existing branch; no source research repeated. Two review P2 findings
  fixed in `8a0d4f0`: decision-time sizing bounds and adversarial same-tick
  availability/status ordering. Independent reviewer accepted those fixes;
  see `INDEPENDENT_REVIEW.md` for scope/model/limits.
- Packet checks passed: 43 retained source hashes, four metadata pins, 53
  verbatim excerpts, 19 evidence sections, 33 fixture groups, prose file links,
  decimal oracles and issue-only changed-path allowlist. LEAN fixtures UNRUN.
- During the usage pause, PR #10 was merged externally at final head
  `13c691e0adbd9ed743f389c09515d134bcee2069`; current target is
  `1a9014ef47accbea82fd086866bce114621a0d1f`. This task made no PR #10 writes.
  Original base remains b5b06af; target is its descendant. Three-dot PR diff
  contains only Issue #11 additions. No rebase, merge or other-branch work.
- Final evidence commit/publication and both hosted OS jobs are the remaining
  side effects. Retain final local test logs and record exact PR head/CI state
  in final delivery. No publication retry until live PR existence is checked.
- Final design status: **LEAN_QUALIFICATION_READY**. Final Linux Python3.13.5
  rerun passed240 tests in8.691s and the300-bar synthetic demo passed. Logs,
  artifact hashes, source-limited/unrun distinctions and review are retained in
  this packet. All original-base tracked files remain unchanged. Design work
  is complete; only its evidence commit, draft publication and CI observation
  remain at this checkpoint. Stop after that delivery; do not implement LEAN.

### Milestone decision record

1. Critical path: complete final evidence and draft PR/CI; future LEAN acceptance
   depends on separately authorized terminal-first spike, not Databento.
2. Workers: one owner plus one bounded independent reviewer; no duplicate source
   worker. Review is complete, and further delegation would waste usage.
3. Adopt/build: configured LEAN extension seams; retain independent scientific
   manifests/evaluator. No generic engine/OMS or integration implementation.
4. Waste avoided: reused all completed source captures; PR #10 untouched; other
   workstreams excluded. No LEAN installation or runtime falsification probe.
5. Usage/API ROI: included Codex usage only; first review/publication check halted
   at usage limit and resumed. Zero paid provider/model API calls, purchases,
   subscriptions or broker calls. No paid fallback or automation activation.
6. Next three information-value tasks (future work, not executed here): (a)
   authorized Q01–Q03 terminal spike, stop on fork/holding loss, can precede any
   data answer; (b) adjudicate an actual source reply/sample under Issue #7's
   ownership before data admission, waits for owner evidence; (c) if synthetic
   spike passes, separately qualify exact runtime/plugin entitlement and broker
   boundary, stop before credentials/spend/orders absent their explicit gates.

## Resume

1. Verify branch/status and read this checkpoint and the issue snapshot.
2. Read design, fixture matrix and source evidence; do not reimplement the spike.
3. Review is complete; inspect validation.json and final local logs, then check
   whether final evidence commit/draft PR already exists before retrying writes.
4. Push only this branch and publish draft PR if still missing, targeting the
   named base. Attach PR to the chat and inspect exact-head Ubuntu/Windows CI.
   Never merge or change PR #10. Stop when design delivery is complete.

Constraints remain: no Databento, purchases, paid provider/model calls, alpha,
FMBH/Amendment 005/candidate changes, broker credentials, Paper/Live orders,
generic backtester/OMS or qualification implementation.
