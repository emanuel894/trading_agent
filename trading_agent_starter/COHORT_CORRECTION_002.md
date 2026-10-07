# Cohort construction amendment 002

**Historical decision: `BLOCK_HISTORICAL_AUDIT`.**
**Prospective status: `PROSPECTIVE_ACTIONABILITY_BLOCKED`.**

The selection bug is corrected in code and the replacement algorithm is registered.
**A replacement cohort has not been constructed or frozen.** The available evidence
does not establish the dated monthly candidate population or its liquidity ranking.
No target-specific source review or corrected-scope dynamic gate is represented as
completed. No 50-filing audit or performance analysis was run.

## Supersession without rewriting history

The rejected H1 manifest, reviews, hashes and exception ledger are unchanged.
Their scope is marked `SUPERSEDED_SELECTION_ALGORITHM_DEFECT` in
`research/cohort_scope_amendment_002.json` and `config/cohort_scope_registry.json`.
The current gate rejects that superseded scope even if someone fills its old
exception ledger. The legacy selector remains available to reproduce the failed
attempt; it is not the current cohort constructor.

The defect was sampling raw SEC filers before applying ADR 001's universe. The H1
two-filing condition also favored non-calendar fiscal years. Amendment 002 covers
calendar 2025 and reconstructs the whole sample; no individual old issuer is
replaced for convenience. This correction preceded replacement selection and any
performance analysis.

The new registration was recorded at **2026-09-16T15:11:17.642949+00:00**.
Its file SHA-256 is:

`6d930c58a921bd771ba7a7a43fa767ce0d8fde746bbc88adab73dde3a2d60091`

The superseded scope remains:

`34af6e2c1d930d89eb956e77ee2aca43ba39daaf8b1276befc2243120e92faca`

## Registered replacement rule

1. At each 2025 month-start, establish a complete, dated candidate population.
   Source-ground each issuer and class: domestic operating company, common stock,
   primary XNYS/XNAS listing; exclude funds, ETFs, ADRs, shells, debt and other
   non-common instruments. An issuer cannot inherit a parent's class or ticker.
2. Use exactly the preceding 60 completed valid sessions. Require median raw SIP
   regular-session close × volume of at least $20m/day and prior close of at least
   $10. Use Decimal arithmetic. Missing sessions are unresolved, not replaced by
   older days or used to remove inconvenient candidates.
3. Choose each issuer's most liquid qualifying common class; rank the complete
   eligible issuer population by that median, then numeric CIK, then research ID.
   Keep up to 500. This ranking cannot be restricted to issuers whose filings were
   easy to download or who eventually supply two events.
4. Join original 2025 10-Qs to their SEC acceptance month's membership. The chosen
   class must remain qualifying at acceptance and simulated actionable time.
   Keep issuers with at least two eligible events. Only now take the 25 lowest
   numeric CIKs and each issuer's earliest two events, ordered by acceptance and
   accession. No content, comparator, acquisition-success or outcome filter.
5. Freeze a completely new 50-filing, 25-issuer manifest, including source/input,
   monthly-membership, registration and selector hashes, qualified class lineage,
   acceptance/action timestamps and SPY context for each distinct action time.
   Action remains the existing provisional acceptance + 600 seconds scenario,
   rounded into an allowed session; this is not a frozen performance deadline.
6. Only then finish scoped identity/lifecycle/actions/halts/rights/SIP-window
   review and run the dynamic gate once. A successful freeze alone never
   authorizes or executes the acquisition audit.

Both the immutable store and active scope registry reject another freeze under
the same registration. Changing universe evidence invalidates the scope even when
the selected 50 happen to stay the same. An explicit amendment and new scoped
reviews are required; changing the output filename or store is not a replacement
mechanism.

## Source work completed

All four 2025 SEC quarter indexes are preserved. Q1/Q2 bytes were reused unchanged;
Q3/Q4 were retrieved with HTTP 200 after registration. They contain **17,289
original 10-Q index pairs across 5,974 CIKs**, before any universe eligibility.
Quarter counts are 1,033 / 5,399 / 5,419 / 5,438. These counts are not an eligible
issuer list or a replacement cohort.

The current Nasdaq symbol-directory definitions describe files updated during
the day and their file-creation timestamp. A current directory therefore does not
establish the requested 2025 dated population. The tested Daily List description
route returned a redirect rejected by the bounded probe; this does not establish
historical coverage, entitlement or a need to purchase it.
[Nasdaq definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs).

Alpaca's FAQ says its default historical `asof` behavior links renamed symbols.
It also shows extended-hours trades updating daily volume. Native `1Day` volume
therefore cannot silently be labeled regular-session-only. The registered input
contract requires `feed=sip`, raw prices, dated ticker binding and explicit RTH
session provenance; use `asof=-` and a verified session aggregation when obtaining
these inputs. [Alpaca market-data definitions](https://docs.alpaca.markets/us/docs/market-data-faq).

The supplied SIP archive covers AAPL/SPY on **2025-01-15 15:00–15:05 UTC**. It does
not contain a 60-session history or a dated exchange universe. This workspace has
no configured Alpaca credentials; no account request or entitlement failure was
invented. Historical SIP remains **PASS**. No purchase is recommended.

## Exact outstanding construction inputs

At each cutoff below, the missing identity field is the **dated candidate-class
population with CIK, issuer, lineage, common-stock type, domestic-operating status,
primary exchange and ticker interval**. The missing source evidence is a dated
exchange population tied to official issuer/class disclosures. A current ticker
list or the raw 5,974 SEC filers cannot substitute for it.

For every structurally eligible class in that population, the missing market
fields are **raw SIP regular-session close and volume for all 60 listed sessions,
plus the last prior close**. The intended source is the already-entitled Alpaca
historical account. No such archive was supplied for these windows.

| Month-start cutoff (00:00 New York) | First required session | Last required session |
| --- | --- | --- |
| 2025-01-01 | 2024-10-07 | 2024-12-31 |
| 2025-02-01 | 2024-11-04 | 2025-01-31 |
| 2025-03-01 | 2024-12-02 | 2025-02-28 |
| 2025-04-01 | 2025-01-02 | 2025-03-31 |
| 2025-05-01 | 2025-02-04 | 2025-04-30 |
| 2025-06-01 | 2025-03-06 | 2025-05-30 |
| 2025-07-01 | 2025-04-03 | 2025-06-30 |
| 2025-08-01 | 2025-05-06 | 2025-07-31 |
| 2025-09-01 | 2025-06-05 | 2025-08-29 |
| 2025-10-01 | 2025-07-08 | 2025-09-30 |
| 2025-11-01 | 2025-08-08 | 2025-10-31 |
| 2025-12-01 | 2025-09-05 | 2025-11-28 |

Windows use the preserved NYSE 2024–2026 calendar and UTP2024-20's January 9
closure. They are input-request dates, not price observations. The machine-readable
24-row field/source ledger is `research/cohort_correction_source_inventory_002.json`.

Exact selected instrument/accession blockers cannot truthfully be named yet:
which 25 issuers qualify is precisely what the missing population and liquidity
inputs determine. Once membership exists, reconcile SEC acceptance metadata for
every issuer appearing in that monthly universe against the preserved complete
quarter indexes, before taking the 25-CIK sample. Do not reuse the old issuer list.

The actual constructor was run against the preserved incomplete input inventory.
It exited **2**, reported twelve dated population gaps, wrote an immutable failure
record and created **no manifest**. The historical BLOCK is a construction block,
not a claim that the corrected cohort has undergone scoped review. There is no
new general research gate and no conclusion against the 10-Q hypothesis.

## Reused work and validation

Historical SIP entitlement, the real AAPL/SPY quality review, conservative frozen
quote policy, fiscal comparator review, evidence store and historical tradability
rule remain accepted. The original 30-minute and Alpaca foundations are unchanged.
Only scope-bound evidence must be reviewed once a genuine corrected scope exists.
Live SIP/status readiness remains separate and cannot block historical selection.

Selector tests cover no listed common class, listed debt, parent/subsidiary CIK
separation, universe-before-sampling, top-500 ranking and class deduplication,
thresholds, missing sessions/evidence, changed membership, and replacement across
filenames/stores. Tests use explicitly synthetic data; test manifests are never
research cohorts. The source-input contract is documented in
`COHORT_SELECTION_INPUTS.md`.

Validation completed: **154 tests passed**; all **14 protected artifacts** match
their pre-amendment hashes. The new private evidence archive is
`cohort_correction_002_evidence.zip` (15,214,796 bytes), SHA-256
`c1c87bc4215d210f87d9525a4fbc62a6fd09ebe59fe60d6154acfa4d93e5b75b`.
Its 18-record evidence chain verifies to
`a2b4bde1b03792f9cae3f7942d871852ab9d744dbdca9ce4c3d23aafa2daa7f9`.
Raw responses remain outside the public repository.
