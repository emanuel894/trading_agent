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

## Executed once — 2026-10-21

**Overall bounded G4 measurement: INCOMPLETE. External spend exactly $0.**
Transport/body preservation completed all six fixed jobs inside every cap; physical
UTC uncertainty and source acceptance/representation contracts remain unqualified.
No continuous capture, G3 registration, scientific admission or trading follows.

Execution head: `c09133fc1b540c00e2e8cc1495b5ec908d5bf6bd`. Independent review found
no remaining findings; [exact-head CI39614990177](https://github.com/emanuel894/trading_agent/actions/runs/39614990177)
passed343 tests and demo on Ubuntu and Windows before the invocation.

| Canonical job | Attempts/statuses | Body bytes, including errors |
|---|---|---:|
| Discovery, start0 | 1:200 | 21,188 |
| Submissions, CIK0000700565 | 1:200 | 158,301 |
| Accession index,0000950170-25-067613 | 2:503 then200 | 7,747 +10,050 |
| Complete submission | 1:200 | 30,606,368 |
| Direct primary,fmbh-20250331.htm | 1:200 | 7,306,025 |
| Daily index,2025-05-09 | 1:200 | 482,876 |

**Six jobs, seven attempts,38,592,555 aggregate response-body bytes; largest
30,606,368 bytes; elapsed24.60776813099983 seconds.** First request
14:16:46.066211UTC (17:16:46.066211 Asia/Jerusalem); last complete body
14:17:10.466069UTC (17:17:10.466069 Asia/Jerusalem). Elapsed includes initialization,
parsing and terminal store verification through closure, sampled before local
receipt serialization. All response bodies, including503, have exact size/hash
and completion evidence. Discovery/index/error used Content-Length; submissions,
complete submission, primary and daily index used verified chunked completion.
No403 or hard cap occurred. No SEC requests were made after this session.

The503 and successful index are separate immutable observations with different
hashes and a version link; the503 has no successful document receipt. It is not a
filing revision assertion. Same-hash live refetch/version stability was not tested;
offline idempotency tests do not establish source immutability.

### Clocks and Issue29

Every attempt preserves request/header/body/end UTC and monotonic samples under
session `3c3c07c08b774794b74195a80c518205`. No sample discontinuity was observed;
offset/uncertainty are null and all seven observations are CLOCK_UNCERTAIN. HTTP
Date and nanosecond clock resolution do not establish UTC accuracy.

The submissions response still asserts `2025-05-09T17:52:26.000Z`. The index says
`2025-05-09 09:52:26`; SGML header says `20250509095226`. The latter strings have
no explicit timezone. No zone, publication instant or missing precision was
invented. Resolved acceptance/publication and historical observation/receipt remain
null. Atom supplies updated strings with explicit-04:00 offset, not a published
field in this response; those are retained without relabeling acceptance.

The index reports7,305,910 bytes. This direct primary is7,306,025 bytes (+115),
where Issue29 previously reported7,306,016 (+9 difference between retrievals).
The exact TEXT-tag-delimited embedded primary span is7,305,926 bytes, with its own
hash and boundary/wrapper semantics. It is not silently equated with the direct
primary or index. No authoritative correction/serialization/version explanation
is established; Issue29 stays INCOMPLETE and eligibility remains unresolved.

Offline processing found the initial index extractor had read the Type cell
`10-Q` as its size because iXBRL adds nested text. A failing regression reproduced
this; the adapter now reads the actual Size cell. The original g4.native assertion
and original receipt remain intact; a new version appends the correction and
reverifies the29-record evidence chain. This involved **zero additional SEC
requests**. The manifest exposes both the initial assertion and corrected value.

### Actual storage and durable evidence

At session closure, the evidence subtree had38,703,148 apparent bytes and
38,723,584 allocated bytes. Unique raw objects:38,592,555 apparent/38,604,800
allocated. SQLite:110,592 apparent/114,688 allocated; writer lock:1/4,096.
Across23 samples, maximum observed allocation was38,735,872; maximum observed
rollback-journal allocation20,480. No spool files remained; spool peaks were not
measured. Free disk recorded31,973,072,896 bytes, above5,180,000,000 required.
Overlay-filesystem st_blocks is an allocation observation, not a media/durability
guarantee. Backup footprint/restore, retention, production volume and exhaustive
transient peaks remain UNMEASURED. No backup copy was created.

[measurement.json](measurement.json) contains exact hashes, per-attempt clocks,
headers, latest native fields, append-only correction references and separately
measured postprocessing footprint. Original exact bytes, SQLite, run intent and
receipt remain under ignored `runs/issue40-g4/live-20261021`; no source bodies are
published in Git. Original28-record chain head:
`c9e9c72f85214acbf11a94a69acf7a13bbdee60a3092474aa708e469ffe84673`.
After offline correction,29-record chain head:
`dce9e60f780b902cb7f157d5abee8c184998cacbcba31aa11714ddfbd3b79806`.

### Final decision record

Critical path is the owner's assessment of measured facts and remaining clock/
source/operations unknowns; no automatic G3 registration or G4 activation follows.
One implementer/one independent reviewer suffices; another collection worker would
duplicate work and violate this session's scope. Reuse the committed measurements,
accepted planner and preserved conflicts. External spend exactly$0; no paid route.

Next three highest-information-value tasks: (1) independently verify the receipt
and offline parser correction; (2) obtain qualified physical-clock/source-contract
evidence if the owner pursues timing qualification; (3) reconsider proposed
operational budgets only within explicit owner decisions. No further SEC request,
capacity extrapolation, science redesign, candidate advancement, alpha run or
trading is authorized by this result. Reusing the receipt avoids repeated source
retrieval and development; six jobs cannot support a seasonal capacity forecast.
