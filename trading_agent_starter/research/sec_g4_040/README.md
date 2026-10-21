# Issue40 bounded SEC qualification

This is technical source/transport measurement for the same ADR001 experiment:
incremental net alpha of original SEC10-Q MD&A textual information over quantitative
controls. It does not register prospective capture or modify science.

Authority: [owner instruction recorded in Issue40](https://github.com/emanuel894/trading_agent/issues/40#issuecomment-6317975636).
Trusted base: `051c6c2d99f1ef6cfefd082ff646ed1c1cd88a09`, merged PR43.

## Scope and controls

Reuse the existing canonical planner, OfflinePreserver queue/reservations/retries,
and EvidenceStore immutable objects/version chains. Only the new diagnostic
adapter accepts the fixed six real URLs. Synthetic fixtures remain synthetic.
No original foundation code, registrations or protected research artifacts change.

Fixed manifest: one discovery page at start0; submissions CIK0000700565; accession
0000950170-25-067613 index, complete submission and primary fmbh-20250331.htm; daily
index2025-05-09. This reuses the known Issue29 source example without selecting or
admitting a scientific event. No pagination, history, quarterly indexes or refetches.

Hard ceilings: six jobs,18 attempts,100,000,000 aggregate response-body bytes,
40,000,000 bytes/response,900 seconds,$0 external spend. The engine's counted
oversize byte is included in the40MB ceiling: usable response limit39,999,999 plus
one counted byte. Full per-request reservations can conservatively stop earlier
than the aggregate ceiling. No counter resets or automatic cap increases.

Single writer, two seconds after completion between requests,20-second transport
timeout bounded by remaining session time, maximum three attempts/job, bounded
retry backoff. Numeric Retry-After is respected globally; unsupported values stop.
No redirects, mirrors, credentials or content decompression. urllib retains its
configured proxy and verified TLS. Strict stdlib response hooks verify chunk
delimiters and trailer termination; framing bytes never become entity bytes.
403, malformed/partial/ambiguous responses, disk/accounting/storage failures and
deadline exhaustion stop the session. Queue counters are reconciled with immutable
records before dispatch and at summary. Minimum verified free reserve is5GB plus
180MB conservative working allowance. This is a diagnostic reserve, not capacity
approval for a future capture window.

`run_once.py` is an explicit Linux operator invocation, with a900-second alarm and
an exclusive persistent run-intent marker. It never runs on import or in ordinary
CI. Its fixed output is the ignored local directory
`runs/issue40-g4/live-20261021`; the same invocation cannot reset/reuse that run.
Do not invoke it again to work around an incomplete measurement. Any future run
requires reconciliation of Issue40 and separate authority, not a new output name.

Clocks preserve UTC wall samples, monotonic samples/session and native SEC values.
UTC offset/uncertainty remain null without qualified host evidence; HTTP Date is
not an offset measurement. Unknown/contradictory acceptance and historical receipt
remain null. Current matching bytes cannot resolve Issue29's historical conflicts.
Objects, metadata, SQLite/journal and spool allocation are sampled where the host
exposes st_blocks; sampled peaks are not exhaustive peaks. No backup, retention or
power-loss guarantee follows. Exact bodies stay in the local evidence store;
public reports contain hashes, sizes, bounded native fields and limitations.

## Checkpoint before live requests

One implementer plus one read-only independent included-usage reviewer. Initial
review of40f6e0a reproduced chunk-delimiter contamination, permissive trailer EOF
and duplicate content-encoding defects. Failing regressions preceded repairs;
strict chunk checks, duplicate validation and cumulative queue reconciliation were
added. The operator alarm now remains through final accounting/receipt creation.
Fresh exact-head independent review and both hosted OS jobs are required before
the single live invocation. Python3.13.5; alpaca-py0.42.2, python-dotenv1.1.1,
pytz2026.5. Actual serving model/effort IDs are unavailable; included review is not
qualified cross-provider acceptance. No paid API tools are used.

Critical path: reviewed transport plus CI -> one bounded measurement -> owner
assessment of remaining G3/G4 unknowns. No independent runnable implementation
benefits from another worker; the reviewer has a separate read-only output.
Reuse the accepted source and foundation work; defer generic collector, scheduler,
capacity forecasting and all scientific/market admission. Next three tasks are:
validate fixes; execute once if checks pass and stops permit; publish exact
measurement/unknowns in Issue40. Existing components reduce duplicate maintenance;
six diagnostic responses cannot establish seasonal volume or economic alpha.

Live receipt and final validation links will be appended after execution. External
spend so far exactly $0; no SEC request at this preflight checkpoint.
