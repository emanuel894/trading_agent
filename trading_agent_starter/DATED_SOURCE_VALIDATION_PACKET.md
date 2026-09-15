# Dated source + historical tradability validation packet

2026-09-15. Scope: source feasibility, six deliberately selected fiscal documents,
three historical halt-day responses, and an offline evidence gate. **No 50-filing
cohort, alpha research or order execution was run.**

**Current recommendation: `BLOCK_HISTORICAL_AUDIT`.** Independently,
`PROSPECTIVE_ACTIONABILITY_BLOCKED`. Historical SIP access is accepted from the
owner's successful local probe. Missing live SIP is **not** a historical blocker.
The historical blockers are incomplete dated identity/lifecycle/action coverage,
unresolved scoped halt coverage and usage rights, and the unavailable local SIP
sample needed for quote-policy review. A paid dataset is not yet demonstrated to
be necessary. The preferred cheapest path is **official SEC evidence + public
Nasdaq halt RSS + the existing historical Alpaca SIP access**, with manual,
source-linked reviews limited to the registered research scope.

This packet supersedes the fixed recommendation logic and source requirements in
the earlier Access + Fast-Path report. Its two warm timings remain two observations,
not a latency distribution, economic deadline, or alpha evidence.

| Gate | Current result | Evidence or missing requirement |
|---|---|---|
| Historical SIP access | PASS | Owner reports bars and quotes `SUCCEEDED_WITH_ROWS`, `SUFFICIENT_FOR_BACKFILL`; SIP only. |
| Instrument identity | UNRESOLVED | Real COST/UAA/UA cover anchors captured; continuous dated class/listing intervals for the proposed scope and SPY are not verified. |
| Lifecycle | UNRESOLVED | No scoped listing, delisting and symbol/name-change inventory. |
| Corporate actions | UNRESOLVED | No complete scoped event inventory or announcement/effective-date review. |
| Historical halt/tradability | UNRESOLVED | Historical RSS works, including non-Nasdaq securities; carry-in and negative-coverage review remain missing. |
| Source rights | UNRESOLVED | Terms hashes captured; internal retention/use and applicable account agreements need scoped review. |
| Quote-policy review | UNRESOLVED | Successful raw local SIP archive not supplied; no measured sample-quality result here. |
| Fiscal comparator review | PASS | Real 53-week/week-based and transition samples reviewed; retain filter and fiscal verification. |
| Prospective readiness | FAIL | Real-time SIP `NOT_ENTITLED`; status subscription was never reached. |

PASS for fiscal review is scoped to completing this diagnostic and rule decision,
not proving every fiscal calendar works. Raw source objects must accompany a
reproduction: if absent or corrupt, the evaluator downgrades affected gates.

**Dated identity and lifecycle contract**

Use our own `research:<stable-id>` for the actual share-class lineage, with
`id_authority=INTERNAL_RESEARCH`. Keep that ID across a ticker/name change when
the underlying class is demonstrably continuous. Different simultaneous classes
get different IDs. A merger/conversion may close one lineage and open another;
record the predecessor/successor edge and terms rather than silently merging IDs.
CIK identifies a filer/issuer, not uniquely a listed class. A recycled ticker must
never reuse an unrelated class ID.

Each immutable interval records: instrument ID, issuer identity/CIK, class name and
rights, lineage anchor, ticker, exchange name plus reviewed MIC mapping,
`valid_from` inclusive / `valid_to` exclusive, date precision/time zone, boundary
source, source URL/document ID/hash and tag/context or source span, publication
and actual receipt/verification times, reviewer, conflicts and superseded-record
reference. Interval boundaries are effective dates, not download or filing dates.
Unknown boundaries remain unknown; no automatic interpolation from two matching
cover pages. A bounded verified research interval need not assert the issuer's
entire life. Record IPO/delisting dates separately, including left/right-censored
or unresolved values; do not convert an unknown delisting date into infinity.

Real source anchors are in `research/dated_source_findings_20260915.json`:

| SEC source anchor | Observed class/ticker/exchange relationship | What it does not establish |
|---|---|---|
| Costco, 0000909832-23-000065, accepted 2023-12-20 | Common Stock, $.005 par → COST → Nasdaq Global Select Market | Original listing date or uninterrupted active interval. |
| Under Armour, 0001336917-22-000029, accepted 2022-08-04 | Class A → UAA → NYSE; separate Class C → UA → NYSE | That one issuer ID can represent both classes, or that the XBRL financial-period interval is a listing interval. |

The extractor retains each cover tag's `contextRef`; it never joins security
tags solely by their order in the document. These are historical anchors, not
approved tradability intervals. The packet deliberately contains no fabricated
active intervals.

| Required field/event | Cheapest official evidence path | Exact remaining limitation |
|---|---|---|
| Listing / first trading date | SEC registration/8-A plus dated exchange admission or issuer announcement filed as an exhibit | Registration alone is not first trading; cover pages provide anchors only. |
| Delisting / last trading date | Form 25 and attached exchange determination; suspension/delisting notices | Filing, effective delisting, registration withdrawal and last executable trade are different times. |
| Name/ticker change | Before/after dated covers, 8-K/charter and effective exchange/issuer notice | Must prove class continuity and effective boundary, not infer from today's list. |
| Split / reverse split | Corporate-action announcement, effective/ex dates, class/ratio and charter evidence | Event-date completeness is not proven by adjusted prices or financial footnotes alone. |
| Merger/reorganization | Agreement plus closing 8-K, class conversion/cash terms, successor filing | Announcement is not consummation; withdrawn deals and amendments must remain visible. |
| Distributions/class changes | Relevant filed announcement/exhibit, declaration/record/ex/payment dates, amended class rights | Ex-date and eligibility mechanics may need exchange confirmation; include SPY distributions in scope. |

Form 25's instructions explicitly distinguish removal from listing and withdrawal
of registration; retain the dated notice and applicable instructions rather than
treating the submission date as the last tradable date.
[Official Form 25](https://www.sec.gov/files/form25.pdf)

For every action record store `announced_at`, `source_publication_at`,
`effective_at`, any ex/record/payment dates, affected old/new class IDs,
ratio/consideration, source spans, actual observation time and uncertainty.
Date-only effective evidence cannot establish an intraday boundary; abstain for
that ambiguous day. Record positive actions and a reviewer-signed scoped inventory
of sources checked; “no event found” without coverage is unresolved.

The existing acquisition parser retains primary documents and EX-99 exhibits.
Charters/merger agreements in EX-3/EX-2 and Forms 8-A/25 are not yet supported as
complete lifecycle ingestion. Capture/review those specifically where the scope
needs them; do not claim current 10-Q discovery is a security master. Transition
Forms 10-QT/10-KT and amendments are now included as prior-disclosure evidence;
target and comparator selection remain original 10-Q only.

**Historical halt tests and reconstruction rule**

The actual captured RSS responses, all HTTP 200 with checked XML/item counts:

| Halt-start query | Records | Raw market-code frequencies |
|---|---:|---|
| 2010-10-11 | 7 | Q:6, C:1 |
| 2024-06-03 | 91 | Q:33, N:36, A:16, P:5, Z:1 |
| 2025-01-31 | 53 | Q:27, A:26 |

The June sample includes NYSE-listed BRK.A: halt 09:50:52 ET and reported
resumption 11:35:54 ET. Non-Nasdaq coverage is therefore observed, not merely
assumed. The raw market letters above are **halt-feed fields, not SIP tape codes**;
retain their source-era meanings rather than applying today's exchange naming
blindly. Full request URLs, receipt times, response hashes and counts are saved.

The public search page advertises the last year; the history menu displayed 20
recent business dates. Neither bounds the observed RSS history: older responses
were available. Conversely, three successful dates do not establish a continuous
2010–2026 archive, its earliest date, or a retention guarantee. The search form
was submitted for `*`, 01/31/2025–01/31/2025; its last observed display was a working
message, followed by a browser evaluation timeout. **Search result unverified**,
not “zero halts.” The static RPC bootstrap returned “Request is not valid.” with
HTTP 200; that is not a successful search either.
[Search](https://www.nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch),
[history](https://www.nasdaqtrader.com/trader.aspx?id=TradingHaltHistory)

The RSS documentation supports automated readers, with at most one request per
minute. Run the bounded probe serially against one archive; it enforces a local
per-archive interval and request/byte caps, not a distributed polling service.
Halt-date queries select starts on that date; resume-date queries select
resumptions; using both is a union, not a complete interval-intersection query.
An earlier halt still open during the queried day can therefore be absent.
[RSS documentation](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS),
[query examples](https://www.nasdaqtrader.com/snippets/tradehaltaccordion.html)

Interpret halt times in America/New_York and convert with historical DST rules;
ambiguous/invalid local timestamps fail. Halt time denotes the initial halt;
quotation and trading resumptions are distinct, and the field definitions call
resumptions scheduled. RSS item `pubDate` at midnight and the retrieval-time
channel timestamp are not reliable first-publication times for the halt.
Scheduled resumption alone cannot close a covering halt in the new rule.
[Halt field definitions](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes)

`HISTORICAL_TRADABILITY_RECONSTRUCTION` is a defensible **conditional research
rule**, without a reconstructed full live stream. For issuer and SPY, require:

1. A source-reviewed active class/listing interval covering the proposed action.
2. A dated regular-session calendar, including holidays/early closes.
3. Scoped halt/suspension evidence with resolved carry-in, matching historical
   aliases/classes and relevant markets. Any authoritative covering halt fails.
4. A contemporaneous SIP/NBBO quote at/before action passing the strict policy.
5. No unresolved lifecycle/action conflict at that time.

The coverage review must describe the exact dates/markets queried, retained
responses, omissions/corrections, carry-in basis, SEC suspension-order review,
and any authoritative resumption evidence. Reconcile ambiguous cases against
listing-exchange/issuer notices. For a known halt with only a scheduled resume,
abstain unless actual resumption is corroborated; a quote cannot supply that
corroboration. A conservative halt-day exclusion may be registered if adequate
actual resumption evidence is unavailable, before admission/performance testing.
Do not require certainty about every exchange message, but do require a reasoned,
source-supported coverage assertion for this scope. An empty day query alone
never supplies it. This assertion has not yet been established here.

The official SEC suspension index was captured as a supplemental route. Its
first page is not a full historical enumeration; amendments and longer exchange
restrictions still need review. Remaining blind spots include carry-in outside
the query range, delayed/corrected records, market-wide/system interruptions,
symbol reuse, and venue-specific restrictions. Quotes show a market state, not
uninterrupted trading or guaranteed fills.
[SEC suspension index](https://www.sec.gov/enforcement-litigation/trading-suspensions)

The helper reports `live_status=false`, `original_receipt_proven=false`, and
`decision_time_eligibility=NOT_EVALUATED`. Backfilled effective-time evidence can
describe historical physical tradability; it cannot prove what our system knew
then. Genuine prospective admission still needs pre-decision receipt, verification,
clock and continuity records. Later bars, later halts and outcome audits cannot
rewrite a sealed admission. The existing audit's post-decision separation remains
unchanged. Wiring approved reconstruction records into audit context is deliberately
not activated while coverage/policy gates are unresolved; no TRADING interval is
fabricated to satisfy the old context format.

**Rights, real quotes and fiscal review**

`research/source_rights_20260915.json` is the rights ledger: source/product/owner,
actual retrieved terms URL/hash/time, research use, automation, retention,
redistribution, date coverage and unresolved question for each proposed source.
The captured documents do not identify every account agreement/version or give a
blanket long-term research archive grant. SEC download guidance permits programmatic
access under fair-access rules; company exhibits are not presumed public domain.
Nasdaq describes free RSS use but retains ownership and disclaims completeness.
Its captured terms do not clearly settle long-term internal archival analysis.
Alpaca website terms do not substitute for the owner's accepted subscriber/data
agreements. Review those scopes before promoting the rights gate; absence of an
explicit retention clause is unresolved, not proof that retention is prohibited.
[SEC access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
[Nasdaq RSS terms](https://www.nasdaqtrader.com/content/administrationsupport/agreementstrading/THRSSFeedTermsCond.pdf),
[Alpaca terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)

The successful **local** SIP archive is not in this shared workspace. Available
probe stores contain no Alpaca HTTP responses. Therefore total rows, condition,
tape and exchange frequencies, locked/crossed/zero-price/zero-size/malformed counts
and strict-policy pass rates are all **unknown**, not zero. The earlier reported
13,088 AAPL rows are a partial owner observation, not a substitute for the corrected
complete archive or an SPY count. Historical entitlement stays PASS independently.

An offline review command now reads every captured SIP response and reports these
counts and per-symbol/overall pass rates without credentials or requests. Counts
are captured rows, including repeated requests if present; they are not guaranteed
unique market observations. The row-policy pass rate evaluates freshness at the
row timestamp; it is not the pass rate at a later action time. Invalid quality
cannot revoke entitlement, and AAPL rejection cannot prevent SPY counting.

**No frozen quote policy is recommended yet.** The unchanged provisional policy
requires positive finite bid/ask and size, unlocked/uncrossed prices, exactly `R`,
recognized tape, exchange fields, spread at most 20 bps and age at most 2 seconds
at action. Preserve it while reviewing real captures against tape-specific
condition/round-lot/exchange definitions. A documentation sample containing `R`
does not establish an exhaustive approved condition set. Missing/unknown codes
abstain; do not loosen the rule to increase admission.
[Alpaca quote/status schema](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)

Six real SEC complete submissions were downloaded and acceptance-crosschecked;
raw hashes, inert text hashes, fiscal tags, cover contexts and review spans are
in the findings file. No MD&A performance or novelty score was computed.

| Deliberate case | Measured result | Rule decision |
|---|---|---|
| Costco FY2023 53-week year, supported by its FY2023 10-K and Q1 report; FY2024 Q1 vs FY2023 Q1 | Period ends 2023-11-26 vs 2022-11-20: **371 days**, same quarter/adjacent fiscal year | Legitimate comparator accepted by existing prefilter. |
| Under Armour year-end transition December → March; actual 2022-03-31 10-QT retained | 2022-06-30 vs 2021-06-30: **365 days**, but FY2023 Q1 vs FY2021 Q2 | Day candidate correctly fails fiscal verification. The short transition's FY2022/Q1 tag cannot make it an ordinary year comparator. |

There are **0 false day-prefilter abstentions among 1 supported comparable pair**;
the transition is a separate exception case, not another legitimate annual pair.
This tiny chosen sample cannot estimate a population rejection rate. Keep 350–380
plus source-tag verification. Register abstention/manual fiscal-period review for
transition reports and affected comparisons lacking an ordinary equivalent period;
do not infer duration/seasonality from tags alone. Transition discovery is fixed
for background disclosures; it does not admit transition filings as target 10-Qs.

**Dynamic gate, reproduction and closure**

`agent.dated_source_gate` consumes `config/dated_source_packet.json`; it validates
evidence hashes, review references, scope hashes and class intervals. Each criterion
is true/false/unknown and produces PASS/FAIL/UNRESOLVED. A true claim without a
reviewer, timestamp, rationale or available evidence stays unresolved. Hashes prove
byte identity, not source completeness or legal truth. Those remain explicit reviews.

All eight historical gates must PASS to return `RUN_50_HISTORICAL_AUDIT`; otherwise
it returns `BLOCK_HISTORICAL_AUDIT`. Prospective readiness is computed separately.
There is no force/pass override and no automatic cohort execution. The proposed
scope must identify 50 filings across at least 25 issuers and SPY context at the
relevant action times; changing it invalidates scoped reviews. This is a coverage
manifest, not permission to select winners from acquisition results. The current
manifest is deliberately unfilled, consistent with the unfrozen cohort.

From `trading_agent_starter`, evaluate offline:

```powershell
.venv\Scripts\python.exe -m agent.dated_source_gate --store runs/dated_source_gate
```

Exit 2 currently means the historical gate is blocked. Source objects are private
runtime evidence, not copied into Git. Restore the preserved source archive to its
recorded paths for exact reproduction. To review the already successful local
entitlement archive, replace the source path with its actual directory:

```powershell
.venv\Scripts\python.exe -m agent.dated_source_review --kind sip --source-store runs/ACTUAL_SUCCESSFUL_PROBE --store runs/sip_sample_review
```

To close this packet, supply that successful archive (`evidence.sqlite` and
`objects`, no credentials), document the proposed dated issuer/SPY scope and
complete the source-linked identity/action/halt/rights reviews. Freeze the quote
policy only after sample/definition review. If public evidence cannot resolve a
particular boundary, name that instrument/date/field: e.g. actual listing/last
trading effective time, an unreported class conversion or ex-date, or missing
halt/resumption/carry-in coverage. Only then compare a narrowly scoped vendor
history or official written clarification against that exact gap. Neither a paid
permanent identifier nor real-time SIP is inherently required for historical
acquisition; a live subscription would not fix historical identity or rights gaps.

The final result is a source-readiness block, not rejection of 10-Q alpha and not
proof that public sources are unusable. Keep the 50-filing budget unspent. The
validated Alpaca and 30-minute pipeline, simulator, hard risk and order flags are
unchanged. The bounded additions are source diagnostics, offline sample review,
dated research gate and transition-disclosure discovery; no trading agents exist.

Verification: **124 tests passed, zero skips** using Python 3.12 and the existing
dependencies. New checks cover historical PASS with prospective FAIL, missing or
corrupt evidence, scope changes, overlapping/reused class identities, carry-in and
scheduled-resumption uncertainty, future-event isolation, SIP-only enforcement,
RSS parsing/rate caps and transition discovery. These fixtures are not market
measurements. The measured gate exited 2 and is saved in
`research/dated_source_gate_20260915.json`, result record
`7d43c0876fc541d4a76ce582afc531f2`. The public-source archive verified 41 records,
head `52763e9e6ce7d32382cfe61e24ee5807e29c2c24e17be05c4b8bd40c9cfe6b7d`.
