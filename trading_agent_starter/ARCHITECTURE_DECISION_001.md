# ADR 001 — Event research, data gates and experiment registration

**Decision date:** 2026-09-14. **Baseline commit:** `885ebf1`.
**Status:** architecture accepted; first research candidate selected; acquisition gate NOT PASSED.
**Scope:** documentation only; order execution remains disabled. This decision supersedes the old baseline → LLM → six-agent roadmap.

The Quant strategy is a control. Preserve the validated Alpaca foundation and
regular-session 30-minute contract unchanged. The proposed intelligence path is
versioned evidence → deterministic detection/features → selective extraction →
statistical policies → deterministic allocation/risk → simulation → evaluation.

## 1. First event: original 10-Q filings, focusing on MD&A changes

Test whether **MD&A changes add predictive information beyond numerical facts
and the market response already visible when we can act**. Compare Part I Item 2
with the same fiscal quarter a year earlier, retaining intervening reports as
context. Detect original `10-Q` accessions deterministically; do not select events
with an LLM. The comparisons below are engineering judgments, not measured alpha
rankings; archive completeness and incorporation speeds require measurement.

| Event family | History, prospective capture and provenance | Frequency / eligible universe | Actionability and language/control tradeoff | Cost / complexity; verdict |
|---|---|---|---|---|
| Earnings releases, 8-K Item 2.02 | Archived exhibits; earlier issuer/wire releases require their own historical and prospective timestamps. | Roughly quarterly; broad liquid universe. | Fast headline response; numeric control needs point-in-time expectations. Language may explain mixed results. | Reliable release/consensus archives may be paid; medium–high complexity. Runner-up. |
| Guidance revisions | Partial SEC/issuer history; no universal event flag or standardized prior-guidance archive. | Unknown subset; many firms do not guide. | Strong semantic question, but event selection requires parsing; revision is not consensus surprise. Prior disclosure and speed matter. | Medium–high archive/parsing cost; uncertain sample. Do not select first. |
| **Original 10-Q MD&A** | Identifiable accession and prior reports; public historical/prospective SEC access. Acceptance is not first-disclosure proof. | Three regular filings/year; broad domestic operating-company universe. | Possible slower interpretation; clean numeric/text controls and fixed event detection. Short-horizon edge unproven. | No SEC subscription fee; medium section-parsing complexity. **Selected.** |
| Repurchases / dividend changes | Releases/exhibits; link announcements and amendments. | Irregular, broad but uneven. | Cheap numeric extraction is strong; authorization is not actual buying. | Low–medium processing; weak LLM case. |
| Executive changes, Item 5.02 | Archived filings; mixed with routine compensation/appointments. | Meaningful departures sparse. | Language could distinguish adverse departures; difficult labels/confounding. | Medium parsing, low effective sample. Defer. |
| Agreements / M&A, Items 1.01/2.01 | Archived contracts/amendments; earlier announcements possible. | Heterogeneous, repeated deal records. | Contract interpretation useful; potentially rapid repricing, long horizons/hedges needed. | High complexity; poor first long-only study. |
| Insider purchases, Form 4 | Structured archival/prospective filings; transaction time differs from disclosure. | Numerous but clustered records. | Strong cheap structured control; little incremental language beyond footnotes. | Low–medium complexity; better non-LLM candidate. |

Filing structures and reporting requirements: [Form 10-Q](https://www.sec.gov/files/form10-q.pdf),
[Form 8-K](https://www.sec.gov/files/form8-k.pdf).

**Guidance loses** on enumeration, comparable sample size and timestamp ambiguity.
**10-Q can still fail:** earnings releases may already contain the information;
remaining value may require months or short selling. Neither justifies changing
the registered five-session, long-only hypothesis after results.

## 2. Minimum additional data and what it can establish

| Dataset | Exact minimum and use | Historical versus prospective |
|---|---|---|
| Filing evidence | CIK, accession, form, reporting period, acceptance timestamp with its semantics/timezone, primary document, submission metadata and prior comparable document. Capture 10-Q/A separately. | Archives and company submissions history support backfill. Prospectively archive discovery responses and downloaded bytes. Original reception times cannot be reconstructed. |
| Security master / eligibility | Permanent instrument ID, dated CIK/ticker/share-class/listing mappings, issuer type, listing/delisting and corporate actions; trailing daily prices/volume. | A historical membership source must be verified; today's ticker list is insufficient. Prospectively retain every eligibility snapshot and input version. |
| **1-minute SIP OHLCV** | UTC start/end, raw OHLCV, feed, session, original provider message/version, received/available timestamps and corrections. Cover 04:00–20:00 New York for event-context windows; RTH for holding-period marks. | Historical bars may contain later corrections. Prospectively retain original and updated bars; never replace silently. |
| **Timestamped SIP consolidated quotes / NBBO** | Bid/ask, sizes and size units, quote conditions, exchange/tape, provider event timestamp at native precision, local receipt time, sequence/gap flags and source hash. Obtain event/action/exit windows, plus SPY. | Historical quote API exists; actual account entitlements/completeness need a probe. Prospective real-time SIP access is distinct from IEX or delayed SIP. |
| Session/status data | Exchange calendar, early closes, instrument trading status, halts and corporate-action treatment. Unknown executable status blocks a simulated fill. | Historical halt/delist coverage is an explicit acquisition gate; prospective status must be observed and logged. |
| Existing 30-minute contract | Controls, slower numerical features and integration checks. | Reuse unchanged; do not generalize its RTH or completion rules to the new contract. |

Minute context runs from the preceding regular-session close through action +30
minutes; holding marks cover entry through exit. Capture quote windows from
60 seconds before to 60 seconds after each reference, decision and scheduled exit,
including SPY. Retry halted exits with status evidence. No separate 5-minute feed,
order book or raw trade-print archive; no extended-hours execution. Minute bars
alone cannot establish an executable price.

Preserve supplied timestamp precision. Features use only observations received
by decision time; historical availability is simulated, never claimed as reception.

Record spread/midpoint and the pre-filing/prior-close price response relative to
SPY. This measures **response already observed**, not the unknowable fraction of
information priced. Outside-hours bars are context, not executable NBBO. Do not
forward-fill missing/closed intervals.

Alpaca publishes historical quotes and extended-hours minute-bar updates. Basic
is free; Algo Trader Plus is listed at $99/month with different real-time coverage.
Verify this account's historical and real-time SIP entitlements: the successful
IEX probe does not establish them. No subscription purchased.
[Plans](https://docs.alpaca.markets/us/docs/about-market-data-api),
[historical quotes](https://docs.alpaca.markets/us/reference/stockquotes-1),
[stream schemas](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data).

Record document/market-data usage rights; keep licensed raw data out of Git.
Historical security-master/status costs remain unquoted. Proposed audit budget:
$0 new subscriptions and $0 model calls; full data cost is unresolved.

## 3. Immutable evidence design: objects plus append-only records

Use content-addressed raw-byte blobs plus transactional SQLite metadata, separate
from the ledger. Persist bytes before ingestion completes. Corrections append;
update/delete guards prevent accidental overwrite. Hashes and backed-up manifests
detect alteration; they do not prove publication time or provide tamper-proof WORM.

| Record | Required fields |
|---|---|
| Source/document version | Source and URL, rights reference, CIK/company, dated instrument mapping ID, accession/source document ID, form/period, source publication timestamp or null, acceptance timestamp separately, original timestamp text/timezone/precision, first-observed and ingestion-complete times, capture mode (`prospective`, `historical_backfill`, `fixture`), raw-byte hash/content type/size, previous version and prior comparable document references. |
| Processing run | Unique run ID, input version IDs, parsing/extraction code version, model provider/name/exact version or null, prompt/schema versions and hashes, model start/end, verification end, extracted facts with source spans, verifier version/status, errors/abstention reason, token/API cost. Unused model fields are null, not fabricated. |
| Decision evidence | Experiment/arm/version, feature and model-artifact hashes, numerical evaluation start/end, portfolio/risk completion, market snapshots available at decision, quote/status IDs, actual decision timestamp, common deadline, intended executable window, abstention/failure code. Actual later fill observations are separate records. |
| Capture/registry log | Discovery checkpoints, successful/failed polls, disconnects, clock offset estimate, process/version IDs; experiment registration, amendment reason, trial count, model/data freeze and access log. |

Keep **source time** separate from **knowledge time**. As-of queries follow immutable
inputs and completed verification runs, excluding later corrections and outcomes.
A 2022 filing backfilled today has today's observation time; its original served
bytes are not guaranteed merely because an accession exists. Historical latency
assumptions stay separate. Historical LLM results are exploratory because weights
may contain later knowledge; confirmation requires prospective frozen evaluation.

## 4. Latency, actionable-time rule and costs

The complete observed chain is public/source availability (possibly unknown) →
first observation → ingestion → extraction → verification → numerical evaluation
→ portfolio/risk check → decision → first executable opportunity. Record wall
clock UTC and monotonic durations; clock-offset uncertainty above one second
causes abstention from timing-sensitive evaluation.

**Registered information-value experiment:** all A/B/C arms share a ten-minute
processing deadline after first observation. Schedule the decision on the first
whole-minute boundary at or after that deadline inside 09:35 to session-close
minus 30 minutes. Otherwise use 09:35 of the next trading session. Overnight and
holiday waits follow the calendar. Extraction/verification must finish within ten
minutes even overnight. Freeze market features at the scheduled minute; numerical
evaluation and risk checks must complete within one additional second. That common
second is the decision timestamp; record actual stage completions separately.
A late arm abstains; it cannot delay its rivals.

Observe a filing within five minutes of recorded SEC acceptance; otherwise mark
it late and exclude it from actionable candidates while retaining it in coverage
counts. This tests **SEC-observed disclosure**, not speed relative to an earlier
issuer release. New knowledge discovered after the initial decision cannot enter
that decision's evidence. Missing the first eligible slot by over 60 seconds
causes abstention; do not retry the same event days later.

At decision, require a valid, uncrossed positive RTH quote received within the
previous two seconds, spread ≤20 bps, a versioned valid-condition allowlist and
known tradable status. A simulated buy
uses the first valid quote at or after decision +1 second, available within five
seconds, at ask plus 5 bps; sell at bid minus 5 bps. Limit simulated size to 10%
of displayed same-side shares after verified unit conversion; otherwise reject
the fill. No guaranteed execution, queue or impact claim follows from NBBO.

Charge the greater of $1 per filled side or verified applicable commissions/fees.
This avoids double counting the fee allowance. Stress the adverse
slippage at 10 bps/side with spread still charged through bid/ask. Charge all
compute/data costs at portfolio level, including failed runs. These are frozen
research assumptions, not a broker fee schedule.

Primary holding horizon: exit at close minus five minutes of the fifth trading
session counting the entry session as session one. One-session exit is a secondary
diagnostic. Halted exits stay open until executable; delisting/corporate-action
outcomes require actual treatment, never deletion or a convenient last-price fill.

On validation only, examine 1/5/10/30-minute availability delays and the proposed
RTH restriction. If benefit disappears before ten minutes or before the next
permitted open, the registered implementation is a no-go. Do not rescue it with
an impossible earlier fill. Once a model exists, an ex-ante expected net return
below 20 bps also produces abstention; this estimate is not LLM self-confidence.

C uses one extractor plus at most one schema-repair call, capped at 24,000 input
and 2,000 output tokens total and $0.10/event at the frozen model price. A fixed B
procedure selects changed passages within this budget; all arms receive those
same passages and filing numbers. Verification initially checks schemas, source
spans, entities, periods and units deterministically. Overflow/uncertainty abstains.
Model names/prices freeze before calibration; stronger models and conversational
agents are separate future trials. An offline research assistant cannot alter
frozen test decisions.

## 5. Experiment registration v1 — before performance access

These rules are registered by the Git commit. There has been no performance test.
Dataset manifests, actual instrument membership and model hashes do not yet exist:
the execution-ready registration remains blocked until they are frozen. Any
change creates a new version/trial; it does not amend an evaluated test silently.

| Design item | Frozen rule / remaining artifact |
|---|---|
| Universe | Domestic NYSE/Nasdaq operating-company common shares with original 10-Qs; exclude funds, ADRs, shells and duplicate share classes. Monthly select up to 500 issuers by preceding 60-session median dollar volume, minimum $20m/day and prior close ≥$10; require 60 valid prior sessions. Use the most liquid class per issuer and dated membership. Realized count is an audit result, not assumed to be 500. |
| Event definition | Original 10-Q with comparable prior-year fiscal-quarter MD&A known at observation. Preserve no-change reports. Missing comparison or ambiguous section boundary causes logged abstention. No selection using future returns. |
| A / B / C | A: event timing, calendar, pre-action price/volume/volatility/market response and structurally tagged numbers available in the filing. B: A plus deterministic section differences, term/negation counts and numeric-text changes. C: B plus bounded LLM facts about operations, demand, margins and liquidity, each source-grounded. All use the same documents, deadlines, forecasting family and tuning budget. |
| Numerical challenger | N uses price/volume/volatility features on identical event opportunities for attribution, plus a separate daily 09:35 all-universe portfolio for practical competition. EMA remains a reference. Event scheduling itself is information; N on event opportunities is not an unconditional numerical strategy. |
| Forecast | Predict five-session SPY-relative return before additional fees/slippage; SPY is a benchmark, not a hedge. Training-only scaling. Ridge standardized-feature penalties {0.1, 1, 10}; squared-loss boosted trees with depth 2, learning rate 0.05, minimum leaf 50 and {50, 100, 200} trees. Fix implementation/version/seed before fitting. No online adaptation. |
| Risk / allocation | Long-only, virtual $10,000 research capital; size `min(10% NAV, 0.25% NAV / sigma5)` using the volatility below. At most five positions, gross ≤60%, daily loss halt 2%, drawdown halt 8%; halts block entries, scheduled exits continue. Rank by predicted net return/volatility; instrument ID breaks ties. Identical cash/fee reservations; missing/zero volatility abstains. Actual owner capital is unspecified. |
| Primary metric | Mean paired C-minus-validation-selected-best-non-LLM net event return. Apply common ex-ante scale `min(2, 0.02 / sigma5)` to each hypothetical $1,000 position return after execution fees/slippage and allocated run costs; `sigma5` is trailing 60-session daily return SD × √5. Abstentions have zero trading return but still incur run costs. Denominator includes all common eligible opportunities. Portfolio survival is a separate gate. |
| Portfolio gate | Positive net P&L after full running costs, no limit violations, and positive paired improvement over the chosen non-LLM portfolio using a training/validation-frozen exposure/volatility normalization. Report unmatched actual portfolio returns too; never scale with future realized volatility. Lower exposure alone is not an alpha claim. |
| Historical periods | Train 2018-01-01–2023-12-31; validation 2024-01-01–2025-12-31; 2026-01-01–2026-09-14 reserved for data-quality audits without inspecting strategy returns. Backfill original versions and dated membership; otherwise no historical performance claim. LLM historical results remain exploratory. |
| Prospective periods | Proposed capture/calibration 2026-10-01–2027-09-30. Freeze production artifacts by 2027-09-30; untouched confirmatory test 2027-10-01–2029-09-30. If capture does not start on time, register new dates before collecting performance data. No automatic extension or early success declaration. |
| Overlap / missing outcomes | One open position per issuer; later filings are captured but cannot create another entry while it is open. Do not delete an event because later news occurred. Group related accessions/amendments and issuer episodes for evaluation. Unresolved terminal prices remain failures, not dropped winners/losers. |
| Uncertainty / trial registry | Two-way clustering by issuer and filing week; portfolio block bootstrap with four-week blocks, 10,000 resamples, fixed seed 894. Use the wider applicable 95% interval. Purge five trading sessions around train/validation boundaries and overlapping labels. Log all feature/prompt/model/data/timing variants; at most six forecasting settings per A/B/C/N plus two extraction-model candidates. No prompt tuning on test. Secondary horizons are descriptive; any promotion requires a new trial. |

Run every arm on every admitted event; allocate actual fixed costs equally across
those events and variable costs to the generating event, including failed runs.
Report N→A→B→C paired ablations for detection/numbers, cheap text and LLM facts,
then portfolio results for economic survival. Feature ablations identify the
component's contribution within this frozen simulator; they cannot prove that
the corporate disclosure caused market returns. All arms receive the same documents.

## 6. Sample size and explicit go/no-go rules

Counts below are planning arithmetic, not a retrieved dataset. Original 10-Qs
give approximately three opportunities per issuer/year. At 70% usable coverage:
12 issuers → 25 usable/year; 100 → 210; 500 → 1,050. Abstentions, unavailable prior
reports and simultaneous earnings may lower these further. Correlated issuers
and filing seasons reduce effective sample size. Daily bars are not independent
new filing events. These are opportunity counts, not executed trades: five-position
limits and filing-season bunching can reduce portfolio trades substantially.

For illustration, paired-event standard deviation 2%, 80% power and a two-sided
5% test imply about 126 independent events for a 50 bp effect, or 784 for 20 bp.
A hypothetical clustering design effect of two raises raw counts to about 251
or 1,568. These are sensitivity calculations, not proof of adequate power for
the primary statistic. Estimate its variance and clustering from validation,
freeze the power calculation, and do not inspect the final test to choose N.

| Gate | Pass condition | Failure action |
|---|---|---|
| Acquisition — currently OPEN | Audit 50 original filings across at least 25 issuers with prior comparisons; ≥95% retrievable/comparable, 100% admitted records have hashes, timestamp semantics and complete lineage. Verify SIP quote/bar/status access and dated-universe source/rights on the actual account; no silent IEX substitution. | No event forecasting implementation until resolved. |
| Prospective feasibility | Observe at least 50 filings and one filing-season peak; ≥95% discovered within five minutes of acceptance, ≥95% admissible market snapshots, zero known future joins. Project ≥1,568 usable events, 200 issuers and 80 represented filing weeks in the fixed two-year test. | If deficient after a capped 12-week audit, park the event track. This does not test alpha. |
| Extraction | Blindly annotate 100 calibration documents; ≥95% accuracy on declared factual fields and source grounding, zero accepted wrong-issuer/period/unit cases, 100% schema validity. Unverifiable fields abstain. At least 95% of attempted runs complete within ten minutes. | Reject C or simplify it; B/N may continue. Empirical accuracy is not a guaranteed error rate. |
| Economic confirmation | Primary improvement ≥20 bps per registered event opportunity and 95% clustered lower bound >0; at least 1,568 usable events, 200 issuers and 80 distinct filing weeks. Portfolio gate also passes, and net benefit remains positive under doubled adverse slippage. Validation power must support the test length. | If complete test excludes a meaningful effect or is inconclusive at the fixed endpoint, do not promote C. Do not move thresholds. |
| Event versus fallback | A/B/C event portfolios must also beat the validation-selected N challenger after comparable risk and all operating costs. | If B wins, retain event statistics/cheap text without C. If N wins, deploy/research N. If none survive costs, promote none. |

If two-year confirmation or broad coverage is impractical, choose the statistical
fallback now. More numerical observations do not automatically establish
independence or alpha either.

## 7. Exactly one next implementation milestone

**A read-only, versioned 10-Q evidence-and-actionability audit.** One bounded
workflow should discover a filing and prior comparator, persist immutable raw
versions and receipt times, join 1-minute/SIP quote context at the registered
actionable time, and emit an auditable eligibility/abstention record. No LLM,
return forecasting, portfolio optimization, order submission or trade committee.
Its purpose is to falsify acquisition, provenance and latency feasibility before
we spend money or research trials on intelligence. The later A/B/C experiment
falsifies economic value; this milestone cannot claim to do that.

**What is new:** evidence store/registry, SEC discovery/download adapters with
checkpoints and failures, separate minute/quote contract and adapter, dated
universe/status inputs, clock/latency records and an as-of replay audit.
**What is reused unchanged:** Alpaca Paper configuration/probe, broker abstraction,
30-minute request/normalization/export, risk and intent-ledger foundations,
daily replay control, existing tests and Python 3.13 CI. Existing risk/ledger
modules still need later integration; reuse is not production certification.

**Disposition:** document the decision and refresh its checksum; no trading code
changes. The candidate passes design comparison, but data readiness is unproven:
no verified account SIP access or historical membership/status source. Once access
is established, the one audit above should measure capture latency and provenance;
those measurements are its deliverable, not prerequisites to writing the collector.
Published API capabilities or offline fixtures cannot certify the acquisition gate.

SEC discovery/archives and fair-access limits are documented, but a production
collector needs an identifying user agent, bounded retries and capture-gap logs.
No collector has been started here.
[SEC developer resources](https://www.sec.gov/about/developer-resources),
[SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
