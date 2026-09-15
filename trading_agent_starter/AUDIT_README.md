# Read-only 10-Q evidence and actionability audit

This implements ADR 001's acquisition milestone. It does not run an LLM, calculate
returns, fit forecasts, allocate capital or submit orders. All existing Alpaca,
30-minute, risk, ledger, CLI and replay modules remain unchanged.

**The 50-filing audit is BLOCKED by the dated-source validation packet.** Read
`DATED_SOURCE_VALIDATION_PACKET.md` before registering a cohort. The dynamic gate
requires historical evidence only; prospective readiness is separate. Run the
offline `agent.dated_source_gate` to evaluate current evidence without repeating
the warm benchmark or spending the cohort budget. Historical SIP bars and
quotes are locally confirmed sufficient for backfill; real-time SIP remains
not entitled, and status subscription was not reached. The mini-gate records
these owner-reported observations without claiming an independent account run.

To repeat the two-issuer evidence-path measurement from existing archives:

```powershell
.venv\Scripts\python.exe -m agent.access_fastpath --source-store runs/audit_access_probe --source-store runs/audit_msft_probe --store runs/access_fastpath_gate --refresh-current
```

The source directories must contain the earlier complete evidence archives.
Optional `--sip-store <local_probe_directory>` reviews captured SIP quality;
it does not probe credentials, require audit context or change entitlement.
The gate persists a unique report and intentionally exits 2 while its dated-source
and real-sample policy blockers remain. Cached historical preparation cannot pass
the prospective cutoff check. This command does not run the 50-filing audit.

## Run a small acquisition probe

From `trading_agent_starter`, using the existing environment:

```powershell
.venv\Scripts\python.exe -m agent.evidence_audit --store runs/10q_audit run --ciks 0000320193,0000789019 --start 2025-01-01 --end 2025-06-30 --max-requests 60
```

The two CIKs are an acquisition smoke sample, not a point-in-time investment
universe. The 50-filing gate needs a registered 25-issuer list, two target filings
per issuer, and sourced context. Selection is the earliest original 10-Qs by
acceptance/accession within the stated window; amendments are prior evidence.
Register the cohort before inspecting results. Do not substitute successful
issuers for failed issuers.

Set `SEC_USER_AGENT` locally to your identifying organization/contact string.
The default identifies this repository without inventing an email address. Keep
existing `.env` flags disabled. The audit can use existing local Alpaca credentials
for explicit SIP requests while leaving `ALPACA_DATA_FEED=iex` unchanged for the
validated foundation. It does not purchase a data subscription.

An initial run without a context file is useful: SEC acquisition proceeds and
missing mappings/reviews become explicit abstentions. Supply a populated
`--context config/evidence_audit.local.json` for the complete gate. Copy the empty
example first; empty evidence never passes.

## Independent historical SIP entitlement probe

Run this small probe before the 50-filing audit. It requires only the local
Alpaca credentials and read-only execution flags; it does not load the evidence
audit context, security master or status inputs. It requests AAPL and SPY
historical `1Min` bars and quotes from the same completed UTC window, with
`feed=sip`, and never falls back to IEX. The default is the reproducible
ordinary-session window 2025-01-15 15:00–15:05 UTC; `--start` and `--end` can
pin another completed window.

The report records the exact window, request URLs/IDs, HTTP statuses, receipt
and elapsed-time metadata, row counts, immutable response hashes and one of
`SUCCEEDED_WITH_ROWS`, `SUCCEEDED_PARTIAL_ROWS`, `SUCCEEDED_EMPTY`,
`DELAYED_LIMITED`,
`PROVIDER_RESTRICTION`, `AUTHENTICATION_FAILED` or `FAILED`. Empty data is not
treated as sufficient backfill access. The supplied real-time websocket result
is recorded separately as `REALTIME_SIP = NOT_ENTITLED`; this probe does not
open a websocket, purchase a subscription, run a model, or send an order.

Historical entitlement and market-data quality are separate report sections.
Successful HTTP 200 SIP access remains successful even when a quote is locked,
crossed, zero-sized, uses a non-`R` condition, or fails the later strict
execution-quality policy. The `data_quality` section counts rows for every
symbol, quote/tape/exchange frequencies, locked/crossed/zero values, malformed
rows, strict-policy passes and rejection reasons. Historical freshness is not
claimed because reception time at the original market timestamp cannot be
reconstructed.

The probe exits `0` only when both endpoints return rows for both symbols. It
exits `2` for missing credentials, empty windows, provider restrictions,
malformed data or any other failed gate, while preserving the failure record.
Run it from `trading_agent_starter`:

```powershell
.venv\Scripts\python.exe -m agent.entitlement_probe
```

Exit codes: `0` means the command completed (for `run`, the software research count
gate passed); `2` means stopped or the gate did not pass. A readable report is not
itself a successful acquisition gate. Manual quality review remains separate.

## What is persisted

`evidence.sqlite` contains append-only records with update/delete guards, prior
version references and a hash chain. `objects/<sha256>` holds immutable raw HTTP
responses, individual SEC document bytes and normalized text views. Every report
has a unique name and an immutable database counterpart. New versions append;
prior versions remain queryable. Code-file hashes are registered before a run.

Preserve the entire directory, not just the report. Close writers before copying
or use SQLite's backup API. Verify a restored copy with:

```powershell
.venv\Scripts\python.exe -m agent.evidence_audit --store runs/10q_audit verify
```

These checks detect accidental alteration; they are not independent publication
proof or protection against an administrator rewriting the whole archive. Raw
runtime evidence stays outside Git. Imported-source receipt times are declared
metadata; actual import time is recorded separately and is not backdated.

## Context file contract

The top-level keys must exactly match `config/evidence_audit.example.json`.
All input context is versioned. Source files must be beneath the manifest's
directory; absolute paths/traversal are rejected. No external URL is fetched from
the manifest or from document content.

| Collection | Required record fields |
|---|---|
| `sources` | `id`, relative `path`, exact `sha256`, `url`, `published_at` or null, `reported_observed_at` or null, `rights_ref`. Files: JSON, CSV, text or inert HTML. Unknown times stay null. |
| `instruments` | `cik` as a 10-digit string, `symbol`, permanent `instrument_id`, UTC-aware `valid_from`/`valid_to`, `round_lot_shares`, `source_id`, `reviewed_by`. Intervals are half-open and cannot overlap at action. A current ticker file is insufficient. |
| `status_intervals` | `symbol`, UTC-aware `valid_from`/`valid_to`, `state` (`TRADING` required for eligibility), `source_id`, `reviewed_by`. Include the issuer and SPY. Unknown status is not inferred from available quotes. |
| `company_disclosures` | `cik`, `source_id`. Publication comes from the referenced captured source; documents at or after target acceptance cannot enter the prior map. |
| `prior_reviews` | `accession`, exact report `text_sha256` and `inventory_sha256`, `reviewed_by`, `external_search_source_ids`, and one `paragraph_reviews` entry per changed paragraph. Each entry needs `paragraph_id`, `relation` (`equivalent` or `distinct_within_captured_sources`), `rationale`, and `source_ids`. The source files must contain the reviewer's evidence. Unreviewed or stale reviews abstain. |
| `clock` | null, or `source_id`, `uncertainty_ms`, `measured_at`. Prospective admission requires sourced absolute clock uncertainty ≤1 second, measured within the preceding day. Local wall/monotonic agreement alone cannot establish UTC accuracy. |

Context assertions are reviewed input, not independent verification by the
software. Hashes establish which evidence was used, not whether a supplied
vendor history or reviewer conclusion is correct. Raw source spans and the review
sources allow a person to assess that conclusion before research admission.

## Prior-disclosure map

The source adapter follows SEC submissions-history pages and downloads complete
submissions. It preserves the primary document and EX-99 exhibits. Acceptance,
accession, form and issuer are cross-checked against the SEC envelope; New York
header time must agree with the API's UTC time. Same fiscal quarter/year pairing
requires matching source-tagged fiscal period and adjacent fiscal years.

Normalized text is a separate immutable object. Paragraph references identify
that object and Unicode character offsets; raw-parent byte spans also link each
SEC child document to its original submission. Token overlap is deliberately
conservative about numeric changes and negation. It generates review candidates,
not semantic truth. There is no automatic `new_to_public=true` path.

Issuer releases outside SEC are explicit imports in this milestone, not an
unbounded web crawler. The map records incomplete coverage and requires external
search evidence before eligibility. This limitation can kill the event family if
reliable earlier-publication evidence cannot be acquired economically.

## Market context and prospective capture

The separate adapter requests raw `1Min`, `feed=sip`, `asof=-` data, following
pagination without an IEX fallback. Admission reconstruction retrieves completed
minutes from the prior regular close up to action, and SIP quotes at/before
action for the issuer and SPY. Optional action-to-+30-minute collection requires
an already persisted audit record via `SIPSource.post_decision_context`; its
quality results never modify admission. RTH minute gaps, missing symbols, bad OHLC,
crossed/locked/stale/future quotes, ambiguous quote ordering and unsupported quote
conditions fail. Extended-hours bars are context only; sparse intervals are not
filled. Quote timestamps retain native nanoseconds and sizes retain round-lot
units. No execution/fill is simulated.

Calendar access is GET-only on the Paper endpoint. It handles New York DST and
early closes. The provisional action is the first whole minute inside 09:35 to
close minus 30 minutes after the selected delay; otherwise the next eligible
session. Historical action uses **simulated availability after acceptance**.
Historical corrected bars/quotes cannot prove reception at that time.

For a bounded real-time pilot, run a separate capture process **before** the
filing/action window, using the same store and including SPY:

```powershell
.venv\Scripts\python.exe -m agent.evidence_audit --store runs/10q_audit capture-sip --symbols AAPL,SPY --seconds 900
```

Then a bounded SEC observation run, with actual current dates:

```powershell
.venv\Scripts\python.exe -m agent.evidence_audit --store runs/10q_audit run --ciks 0000320193 --start YYYY-MM-DD --end YYYY-MM-DD --mode prospective --polls 15 --poll-seconds 60 --context config/evidence_audit.local.json
```

Capture subscribes only to SIP quotes, minute/updated bars and statuses. It logs
receipt times, subscription denial, discontinuities and termination. Status
channels may require additional access. Absence of a halt message is **not** an
initial tradable-status snapshot. A bounded pilot may correctly abstain throughout
if status evidence is unavailable. No restart/reconnect is hidden as continuous
coverage. Historical REST responses received after action cannot substitute for
prospective quote receipts. Stream bars are retained for subsequent as-of review;
this audit does not certify a complete prospective feature dataset or simulator.

The observation loop is intentionally single-worker and finite; slow acquisition
can delay later polls and will be visible. It is an audit, not a production scanner.
The context window must have completed before historical retrieval; early runs
abstain and can be rerun against the same immutable first-observation record.

## Bounds and interpretation

- At most 25 issuers × two targets per run; eight history pages per issuer;
  64 prior filings and 20 admitted documents per submission. A cap causes failure,
  never silent truncation. Prior downloads are cached only within one poll, with
  explicit cache-hit records; subsequent polls re-observe possible revisions.
- SEC/HTTP requests: at most four starts/second per process, 20-second timeout,
  three attempts for transient failures, no retry on 403, 2,000 default requests
  (maximum 5,000), 2 GB aggregate raw-response budget, 40 MB per response.
- SIP pagination: at most 50 pages/window; capture ≤30 minutes, ≤10 symbols,
  ≤100,000 frames. No fallback feed, order endpoint or arbitrary redirect.
- Parsing: ≤15 MB/document, ≤2 million visible characters, bounded paragraphs and
  comparisons; suspicious content and ambiguous MD&A boundaries abstain.

Do not compare cached prior-document timings with fresh current-filing downloads
as if they were equivalent. Automatic review validation is not human review
latency. The initial 600-second setting remains provisional. Freeze an operationally
achievable deadline before later performance tests; no return-based deadline
selection or alpha metric exists in this implementation.

Read the actual measured report separately from unit tests. A test fixture can
exercise the eligible path but can never pass the real research gate. No small
probe, extraction precision result or short shadow period is final alpha proof.
