# Access + Fast-Path gate — 2026-09-15

**Decision: BLOCK the 50-filing cohort.** Historical SIP is sufficient for
backfill. The blockers are missing dated security/lifecycle/status evidence and
source rights, unreviewed real quote/status samples, and an unvalidated live
decision boundary. Real-time denial alone does **not** invalidate historical
acquisition. No subscription purchase or recommendation is needed to reach this
decision. The 10-Q remains a falsifiable candidate; there is no alpha result.

## Account access: actual local results, attributed correctly

| Capability | Recorded result | Evidence and limit |
|---|---|---|
| Historical 1-minute SIP bars, AAPL/SPY | `SUCCEEDED_WITH_ROWS` | Owner's completed local authenticated probe; HTTP 200 and both symbols reported. |
| Historical SIP/NBBO quotes, AAPL/SPY | `SUCCEEDED_WITH_ROWS` | Owner's corrected probe; historical status `SUFFICIENT_FOR_BACKFILL`. Earlier quote-policy failure was not an entitlement failure. |
| Real-time `v2/sip` websocket | `NOT_ENTITLED` | Owner's local `SIP_AUTH_OR_ENTITLEMENT_REJECTED`. |
| SIP status subscription | `NOT_TESTED_AUTH_BLOCKED` | Authentication stopped the connection before subscription. Separate status entitlement, initial state and continuity remain unknown. |

These observations are preserved in `config/access_gate_observations.json` and
the gate's immutable account-observation record. The raw local account archive,
exact timestamps and numeric provider error code were not supplied here; they
remain null/unknown. No independent account probe was claimed or made here.
The completed historical window does not test the latest-data delay boundary.
No IEX or delayed-feed substitution occurred.

Alpaca documents subscription-dependent status messages and authentication
failure for unavailable feeds. Its status codes distinguish quotation resumption
from trading resumption. A granted subscription alone would not establish initial
tradability. [Alpaca stream documentation](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)

## Dated sources: explicitly not ready

| Required evidence | Defensible source route | Current readiness |
|---|---|---|
| CIK ↔ ticker ↔ share class/permanent instrument ID | Source spans in dated SEC cover-page disclosures, joined to a dated exchange/vendor security history with reviewed effective intervals. Issuer CIK is not a unique share-class identifier. | **BLOCK:** filing bytes exist; no reviewed historical crosswalk or share-class lifecycle inventory. Today's SEC ticker metadata cannot fill this gap. |
| Listing/delisting, symbol changes, splits, mergers, distributions | Historical exchange corporate-action records plus source-grounded issuer disclosures; retain announcement and effective dates separately. Include inactive/delisted securities. | **BLOCK:** no captured, licensed complete history. Nasdaq Daily List is a documented candidate, not an acquired source or purchase recommendation; it covers Nasdaq and does not establish coverage for SPY or every eligible listing. |
| Halt/status evidence for issuer and SPY | Dated status/halt/resumption messages plus known initial state, tape/session coverage and outage evidence. | **BLOCK:** no qualifying historical status archive, and live SIP authentication failed. An empty halt search or the presence of quotes is not evidence of uninterrupted trading. |
| Source rights | Hash/version of actual terms or grant, permitted internal automated research/retention/derived use, coverage dates and reviewer. | **BLOCK:** public product documentation and successful HTTP access are not a rights grant for every required source. No rights are invented. |

The SEC describes its submissions metadata as current company/ticker information;
its filings and fiscal tags are useful source anchors, not a ready-made historical
security master. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
Nasdaq documents historical Daily List corporate actions and access agreements;
no files or agreements have been obtained for this gate.
[Daily List description](https://www.nasdaqtrader.com/Trader.aspx?id=DailyListPD)
The public halt-history interface is a source candidate requiring coverage and
rights verification, not a complete status certificate.
[Nasdaq halt history](https://www.nasdaqtrader.com/trader.aspx?id=TradingHaltHistory)

## Measured cold and warm evidence paths

Two existing completed acquisitions were reused, one per issuer, with no new
cohort selection. Each warm measurement made **one new successful SEC GET** for
the current complete submission. Current-document hashes matched the cold run.
Prior evidence was prepared from captured SEC documents strictly accepted before
the target, without reading target content to choose background documents.
All 20 prior documents per target and every paragraph's classification matched
the cold result. No prior-document GET occurred on either warm critical path.

| Seconds | Apple: 0000320193-25-000008 | Microsoft: 0000950170-25-010491 |
|---|---:|---:|
| Original cold audit total | 157.151 | 167.310 |
| Original cold current acquisition | 11.000 | 12.683 |
| Original cold prior acquisition | 143.806 | 143.466 |
| Background preparation from saved bytes, measured now | 1.190 | 6.918 |
| Warm current acquisition, including envelope processing/persistence | 9.973 | 11.281 |
| Warm current parsing | 0.112 | 0.781 |
| Warm prior snapshot load + hash checks | 0.019 | 0.051 |
| Warm deterministic linkage | 1.293 | 5.380 |
| **Warm measured evidence path total** | **11.397** | **17.493** |

The cold measurements were recorded earlier on the same date; this is not a
randomized timing comparison. The background line excludes its earlier network
acquisition cost: the approximately 143 seconds move off the critical path, not
out of the system's operating cost. Counts are two, not a reliable p95 estimate.
Full discovery, market/status, external disclosure capture, human semantic
verification and decision sealing are outside the warm measurement. Both cold
audits abstained before complete market evaluation. These numbers must not be
presented as end-to-end actionable latency or evidence of an economically useful
window. The ten-minute deadline remains provisional; no returns were inspected.

Snapshot verification means envelope provenance, raw/text hashes, parser version
and fiscal consistency. It does not mean semantic novelty or complete external
disclosure coverage was verified. Historical SEC acceptance provides the prior
cutoff; it does not establish the first-served historical document version.
Both warm caches correctly fail prospective use with
`SNAPSHOT_NOT_PREPARED_BEFORE_EVENT`: they were built in 2026 for 2025 events.
Nothing was backdated.

The future background process should capture and version issuer histories,
fiscal metadata, prior disclosures, source rights and instrument/status anchors
before events. Pin an immutable prepared snapshot; include only actual source
receipt, ingestion and verification completed before the new event. On event
arrival, download/parse only the current filing, load/check the pinned snapshot,
link disclosures and abstain on missing or stale coverage. A missing warm cache
must not silently trigger an unbounded history download on the critical path.
Refreshing snapshots or adding corrections appends new versions. A prospective
readiness claim also requires polling/coverage evidence, not just a cutoff date.

## Comparator findings before changing the rule

Source-tagged `DocumentFiscalPeriodFocus` and `DocumentFiscalYearFocus` established
three unique same-quarter/adjacent-fiscal-year pairs in the saved documents:
Apple FY2025 Q1/Q2 against FY2024 (364/364 days), and Microsoft FY2025 Q2 against
FY2024 (366 days). **0/3 false abstentions** under the existing 350–380-day
prefilter. Six other captured current/prior filings lacked a captured preceding
matching year; they are unknown coverage, not demonstrated rejections.

The sample includes Apple's week-based calendar but no measured 53-week or
fiscal-transition pair. Synthetic tests cover 364, 371 and an out-of-window
390-day source-tagged pair; these tests are not empirical observations.
Retain the production rule for now. Prefer fiscal-tag matching as the eventual
primary selector, with period-end spans and transition-filing review; do not
infer comparable operating duration from tags alone. Before cohort freeze, use
a small deliberately chosen 53-week/calendar-transition source sample to decide
whether to replace the day filter or register explicit transition exclusions.
Missing/ambiguous tags still abstain. No rule was loosened based on admission.

## Quote/status policies and the decision boundary

Raw local SIP quotes/status messages were not available for this gate. The
existing quote-condition/tape/spread/freshness and status rules remain unchanged
and **unfrozen**. The standalone entitlement probe already reports quote quality
separately. `--sip-store` on the mini-gate can inspect its captured response
archive, preserving source integrity and reporting quote-quality and actual
status-code frequencies. Review these against tape-specific provider definitions;
explain each excluded category and examine source spans/frames before approval.
A historical quote passing the current row policy does not prove live receipt,
initial trading status, executable depth or a fill.

The previous market-context function included action +30-minute bars in its
eligibility checks. This gate narrows that reconstruction to bars completed
before action and quotes at/before action. Optional post-action collection is a
separate `post_decision_context(saved_audit_record)` operation; it appends a
quality record with `affects_admission=false`. Its failures cannot modify the
saved result. Regression tests enforce this separation.

Every audit result now explicitly says `decision_time_eligibility=NOT_EVALUATED`.
Historical reconstructed eligibility is not actual decision-time admission.
Prospective audit attempts additionally abstain with
`PROSPECTIVE_ADMISSION_NOT_IMPLEMENTED`: later REST receipts, context imports or
stream termination cannot certify what was known at the earlier decision.
Before any trading experiment, build a live immutable decision input set using
source timestamps **and** actual receipt/verification cutoffs, completed bars,
known status and a contemporaneous stream-health/clock checkpoint. Keep later
corrections and outcomes in a separately referenced record. This gate adds no
trading admission or execution path.

## Required before cohort freeze

1. Supply and validate dated instrument/lifecycle/status evidence and source
   rights covering the proposed issuer dates and SPY. No current-list substitute.
2. Preserve the already successful local entitlement archive and review real
   quote/status samples. Historical status evidence can support a backfill-only
   audit; live SIP is a separate requirement for prospective actionability.
3. Complete the small fiscal exception review; freeze comparator/exclusion and
   quote/status policies before selecting the 50-filing cohort.
4. Validate genuinely pre-event snapshot preparation, coverage and the live
   decision cutoff, or explicitly register the next audit as historical
   acquisition-only with prospective actionability still blocked. Do not claim
   this replay completed that gate or freeze a deadline from two measurements.

**One next milestone:** close the dated-source and real-sample validation packet
for this mini-gate, using existing access and supplied captures. Keep the
50-filing budget unspent until that packet supports a reviewed scope decision.

## Reproduction and evidence

`python -m agent.access_fastpath` accepts at most two existing source stores and
optionally refreshes only the two current SEC filings. It does not discover or
run a 50-filing cohort. `--refresh-current` measures network acquisition;
without it, current acquisition is explicitly labelled raw-byte replay. Exit
code **2** and `recommendation=BLOCK` are intentional until the unresolved
source/policy gate is reviewed; the current CLI has no success override.

Measured run: `756df330352e4463bae68fd36b2907b0`, 2026-09-15 15:39 UTC;
immutable report record `b59114907ed849638ae128f87bd044d1`, record/chain hash
`ff2df9d64a727c549fb64ac976b67a84ec62d2f42587c482d45ce5c9bc493116`.
The new evidence store verified 172 records, including two early failed local
development attempts (no HTTP calls), retained rather than overwritten. The
successful measurement has no acquisition failures; its research gate is blocked.
The original Apple/Microsoft archives remained unchanged at 142/81 records.
The machine-readable measurement is preserved in `research/access_fastpath_20260915.json`.

Verification: **105 tests passed, zero skips** in the Python 3.12 environment
with the existing project dependencies. Tests include cache/version corruption,
future knowledge, synthetic fiscal exceptions, bounded missing-input failure and
post-decision isolation. The Alpaca foundation and strict 30-minute files remain
unchanged. No LLM, forecast, optimization, portfolio allocation or orders were run.
