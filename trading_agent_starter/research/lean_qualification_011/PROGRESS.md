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

## Resume

1. Verify branch/status and read this checkpoint and the issue snapshot.
2. Finish pinned LEAN/official plugin inspection; persist evidence and exact
   synthetic fixture matrix with pass/fail rules and adapter seams.
3. Validate documentation, protected-file invariance, required existing tests
   and demo. Obtain independent review under the trusted base policy.
4. Commit and push only this branch; open draft PR targeting the named base.
   Attach PR to the chat. Never merge or change PR #10.

Constraints remain: no Databento, purchases, paid provider/model calls, alpha,
FMBH/Amendment 005/candidate changes, broker credentials, Paper/Live orders,
generic backtester/OMS or qualification implementation.
