`BLOCK_HISTORICAL_AUDIT`

`PROSPECTIVE_ACTIONABILITY_BLOCKED`

The supplied archive establishes historical SIP access independently of quote quality. The unchanged quote screen and fiscal-comparator review pass. The frozen scope cannot yet meet historical identity/tradability requirements. No 50-filing acquisition audit, MD&A comparison, return analysis, model, optimization, allocation or order was run. This closes the requested preparation step with a block; it does not start another research gate.

The exact instrument/date/field/source exceptions are in [COHORT_CLOSURE_EXCEPTIONS.md](COHORT_CLOSURE_EXCEPTIONS.md) and its [machine-readable ledger](research/cohort_closure_exceptions_20260916.json). The evaluated result is [dated_source_gate_20260916.json](research/dated_source_gate_20260916.json).

| Historical requirement | Result | Evidence |
|---|---|---|
| Historical SIP access | PASS | Hash-verified owner archive; both endpoints and both symbols returned rows |
| Instrument identity | UNRESOLVED | Partial cover/class bindings retained; no invented effective intervals |
| Lifecycle | FAIL | Six selected filings concern issuers without an eligible listed common class |
| Corporate actions | UNRESOLVED | Dated findings and exact remaining fields recorded below and in ledger |
| Historical halt/tradability | UNRESOLVED | Action-window SIP and authoritative carry-in/suspension coverage missing |
| Source rights | UNRESOLVED | Applicable account data agreement and historical RSS retention applicability unresolved |
| Quote-policy review | PASS | Actual sample and provider definitions; original rule frozen unchanged |
| Fiscal-comparator review | PASS | Previously captured real 53-week/transition cases; no rule change |
| Prospective readiness | FAIL, separately | Real-time SIP NOT_ENTITLED; live status/receipt sealing not validated |

The account result remains `SUFFICIENT_FOR_BACKFILL`. It is not changed by locked/crossed quotes or by missing market context for other dates. Real-time access is not a historical approval requirement.

**Measured SIP sample.** Window: 2025-01-15 15:00:00–15:05:00 UTC. One bars response (6 rows per symbol, inclusive endpoint) and seven paginated quote responses, all HTTP 200 with explicit SIP. Original supplied database SHA-256: `4ac083a8c23c2c24c4bd0d4bb08467f43d626d5dd959bab4b2e8561a9272f7c7`. Evidence chain: 9 records, head `e5555e519fc1ac02eef41627227de15cdcc56a016da0045d0a4c025eac72f737`.

| Symbol | Quotes | Locked | Crossed | Zero price | Zero size | Malformed | Strict pass | Pass rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 13,088 | 103 | 0 | 0 | 0 | 0 | 12,985 | 99.2130% |
| SPY | 47,807 | 332 | 22 | 0 | 0 | 0 | 47,453 | 99.2595% |
| Total | 60,895 | 435 | 22 | 0 | 0 | 0 | 60,438 | 99.2495% |

Every quote has condition R. Tape C: 13,088; tape B: 47,807; tape A: not sampled. Full condition, tape, bid/ask exchange-code frequencies and per-symbol zero-field diagnostics are preserved in [sip_quote_review_20260916.json](research/sip_quote_review_20260916.json). Exchange codes are retained as supplied rather than assigned unverified venue names.

The [frozen historical quote policy](research/historical_quote_policy_v1.json) keeps positive finite prices/sizes, bid below ask, exactly R, tapes A/B/C, exchange identifiers, spread at most 20 bps and a quote timestamp no more than two seconds before action. All 457 observed rejections are locked/crossed quotes. This measurement applies freshness at each row's own timestamp; it does not measure pass rates at the cohort action times or guarantee a fill. The numerical thresholds were not fitted to the sample or returns. Tape A has CTA definition support but no empirical sample here. R is a regular quote condition, not sufficient halt/trading-status evidence. See the captured [UTP 2015 specification](https://www.utpplan.com/DOC/uqdfspecification.pdf), [CTA 2015 specification](https://www.nyse.com/publicdocs/ctaplan/notifications/trader-update/cqs_output_spec_v62_11062015.pdf), and [Alpaca historical quote definition](https://docs.alpaca.markets/us/reference/stockquotes-1). Raw exchange participant codes inside SIP do not constitute a fallback feed.

**Frozen scope.** [cohort_2025h1_frozen.json](research/cohort_2025h1_frozen.json) contains exactly 50 original 10-Qs, two for each of 25 CIKs, and SPY at all 43 distinct action times. All internal identifiers use `research:` and explicitly reserve a class binding pending source review. They are not vendor or exchange permanent identifiers.

- File SHA-256: `978370a61119b34ca5a37cdd65ea25c217d813519590bb5a07d0bc8222abb39a`.
- Canonical scope SHA-256: `34af6e2c1d930d89eb956e77ee2aca43ba39daaf8b1276befc2243120e92faca`.
- Immutable freeze record: `9e765dcdb397418c88a4ab82aa5152c0`.
- Registration precedes index retrieval; the freeze precedes selected document-body acquisition. No issuer was replaced after source review.

ADR 001 specifies earliest two filings per issuer but supplies neither a 25-CIK list nor an acquisition window. The [recorded completion of those parameters](research/cohort_selection_registration_20260916.json) uses January–June 2025 and the 25 lowest numeric CIKs with at least two original 10-Qs in the official quarterly indexes. This is an implementation-supplied, metadata-only acquisition sampling detail, not an issuer-ranking rule already written in the ADR. It does **not** establish the ADR's dated liquid-common-share trading universe. The two-filings-in-H1 rule also favors non-calendar fiscal years. No market returns or acquisition outcomes were used in selection. Consequently this sample cannot establish opportunity frequency or refute alpha in the qualified trading universe.

Action times use SEC acceptance plus the existing provisional 600-second scenario, ceiling to a minute, and the first regular-session slot from 09:35 through 30 minutes before close. The [official calendar](https://s2.q4cdn.com/154085107/files/doc_news/NYSE-Group-Announces-2024-2025-and-2026-Holiday-and-Early-Closings-Calendar-2023.pdf) and [January 9 closure notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=UTP2024-20) are pinned. These are simulated historical action times, not original receipt records or a newly validated processing deadline. The earlier two warm-path timings remain two measurements, not a distribution or alpha evidence.

The gate verifies the manifest's file hash, canonical scope and agreement with the packet. Changing any target, date, SPY context, selection or clock rule invalidates scoped reviews. Refreezing the same file fails. A later scope change requires a new explicit documented amendment referencing this frozen scope and new scoped reviews; editing review hashes alone cannot authorize a changed scope. Quote-policy reviews also bind to the validator code hash.

**Concrete findings in the frozen scope.** Fifty selected filing sources were captured for cover identity only, plus 13 item-filtered 8-K action sources and two SPY identity sources. This was source validation, not execution of the 50-filing MD&A/comparator/prior-disclosure audit. The findings and hashes are in [identity anchors](research/cohort_identity_anchors_20260916.json), [action review](research/cohort_action_review_20260916.json), and [SPY identity review](research/cohort_spy_identity_20260916.json).

| Instrument / CIK | Action times (UTC) | Field and concrete evidence |
|---|---|---|
| Spire Alabama / 0000003146 | Feb 5 15:41; Apr 30 14:51, 2025 | Its common shares are wholly owned. The combined filing's SR listing belongs to parent CIK 0001126956. No lawful source join turns SR into the subsidiary's class. |
| Chase General / 0000015357 | Feb 5 15:49; May 9 15:52, 2025 | Both selected covers explicitly report no Section 12(b) class/exchange. No eligible listed-common mapping is available. |
| John Deere Capital / 0000027673 | Feb 27 15:36; May 29 18:14, 2025 | JDCC 31 is senior debt. All common shares are owned by John Deere Financial Services. Parent DE is a different lineage. |
| BRN / 0000010048 | Feb 18 14:35; May 16 13:35, 2025 | January 26 rights agreement and February 7 record date captured; separation/exercise/termination and exchange ex-date evidence remain unresolved. |
| CALM / 0000016160 | Apr 9 13:35, 2025 | February 25 conversion agreement and March 27 charter effectiveness captured; these do not establish actual Class A conversion completion at action. |
| CMTL / 0000023197 | Jan 13 14:35; Mar 13 13:35, 2025 | December 18 Nasdaq late-filing deficiency expressly had no immediate trading effect; dated disposition is missing. March 3 preferred/warrant terms need complete common-class impact review. |
| CPB / 0000016732 | Mar 5 14:35; Jun 2 13:35, 2025 | Name change to The Campbell's Company effective November 19, 2024 is captured. It does not create a new issuer/class ID. |

The existing downloader rejects Spire's combined envelope because it checks the first header CIK. That failure is preserved. A separate offline identity review verified the target among the envelope's multiple filers and checked each cover fact's XBRL entity. The accepted acquisition downloader was not loosened, and the parent's stock was not assigned to the subsidiary.

For every remaining target and SPY date, the exception ledger specifies the absent interval, effective-action coverage, action-window SIP request, halt/carry-in/suspension evidence and source-use agreement. Point-in-time cover tags are preserved as partial evidence: missing bounds do not become FAIL. Known contradictory lineage claims still fail, even if another field is missing. No fiscal reporting-period date is repurposed as a listing date.

The supplied SIP window covers none of the frozen action slots, and no Alpaca credentials exist in this workspace. That is missing target-date evidence, not an entitlement failure. A scoped January 6 Nasdaq RSS probe returned 50 halts (49 Q, 1 P); it does not establish negative coverage. Nasdaq's [documented query semantics](https://www.nasdaqtrader.com/snippets/tradehaltaccordion.html) select starts or resumptions on specified dates and cannot by themselves exclude a halt carried into a session. No quote is used to infer uninterrupted trading. The separately registered historical reconstruction rule needs evidence of these conditions, not a fictional live-status stream.

**Cheapest source path and exact rights limit.** Use the already captured official SEC sources, public exchange notices and the already entitled historical Alpaca feed. No purchase is recommended. The [scoped rights ledger](research/source_rights_20260916.json) pins actual reference/terms documents, owners, use/automation/retention questions and redistribution limits. The missing Alpaca item is the applicable account/subscriber agreement covering automated internal use and immutable retention; the public [general terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf) do not identify the owner's accepted account-specific version. Nasdaq historical RSS retention applicability and authoritative carry-in coverage remain separate questions. A paid dataset's necessity has not been established, and no purchase would turn the three unlisted selected classes into eligible listed shares.

Raw filings and account market data remain outside Git. The private evidence archive preserves response bodies, document hashes, append-only SQLite chains and provenance. The existing Alpaca execution foundation, strict 30-minute contract, minute quote validator and audit execution path are unchanged.

Validation: 135 unit tests passed locally, including partial identity coverage → UNRESOLVED, incompatible overlap/reused lineage → FAIL, missing bounds cannot hide a known lineage conflict, combined-filer parent isolation, no-replacement selection, calendar closures, manifest tampering/scope amendment protection, and quote-code freeze invalidation. These are software checks, not performance evidence. GitHub CI status is reported separately.
