# Draft to Databento Reference data specialists — not sent

Subject: Free Reference Security Master qualification — historical FMBH / CIK 0000700565

We are evaluating a maintained historical US equity security master for a
broker-independent research system. We need retrospective structural validity,
not a claim that we possessed today's corrected records in 2025. This request is
for documentation and a free static sample only, without a purchase, subscription,
credit card, API allocation or paid trial. Please identify any terms before
supplying restricted data. Please do not send credentials.

## First: three short feasibility answers

1. Can Reference Security Master enumerate **every potentially qualifying
   NYSE/Nasdaq common share class** of First Mid Bancshares, CIK `0000700565`, at
   May 1, 2025, including historical classes not active today, with the baseline
   and relevant changes through May 9, 2025? Please say which fields/relationships
   are not covered. We do not need the entire private/debt capital structure.
2. For the eventual US research universe, what are the earliest reliable dates
   **by structural field and population**, including delisted securities? Can
   you support the 2017 warm-up for research beginning January 2018, not merely
   prices or an occasional record with an older effective date?
3. Can you provide the following bounded sample and semantics at zero charge,
   without allocating ISIN entitlement, with internal Python/Linux research,
   frozen-evidence retention and broker/engine-independent use permitted? If
   not, state the exact limitation and minimum separate commercial quote.

## Technical questions and acceptable evidence

Please answer with specification sections, schema/codebook links or a written
data-specialist explanation, not only a general “point-in-time” assertion.

1. **Source scope and hierarchy.** What feeds maintain the issuer/security/listing
   population? Define `issuer_id`, `security_id`, `listing_group_id`, `listing_id`,
   CIK associations, `listing_source`, `primary_exchange`, `exchange`, MIC and
   security type/CFI. Which fields distinguish a second listing of one class
   from a genuinely different common class? Are parent/subsidiary and predecessor/
   successor issuers separate? Can historical issuer links change or be deleted?
2. **Effective state.** Does `ts_effective` mean actual historical validity for
   every returned structural field, or source ingestion, normalized daily state
   or mixed-field vintage? Give native precision and timezone/boundary rules for
   issuer/class identity, ticker, type, primary listing and listing status. What
   does a midnight value mean? Which transitions can occur intraday? Daily fields
   are acceptable inputs when independently grounded corroboration establishes
   the required instants; we do not require synthetic second-resolution values.
3. **Carry-in and query completeness.** How do we retrieve the latest valid
   baseline **before** a target plus every applicable subsequent change?
   `get_range` filters on its clock and `get_last` is latest-only. Identify an
   actual supported query/export that does not omit an unchanged earlier record.
   Describe pagination, truncation, retention boundaries and completion markers.
4. **Historical issuer census.** Does an issuer-ID query enumerate the historical
   set or today's associations? How do we find retired IDs, no-CIK rows and
   classes delisted/merged/reassigned after the target date? Provide an independent
   scope/count or reconciliation method that can detect missing qualifying
   classes. A single primary ticker or `active=true` today is insufficient.
5. **Corrections.** Define `ts_record` and `ts_created` against original-source
   publication, source correction and Databento ingestion. Are old versions,
   deletions, ID merges and tombstones retained? How are equal effective times,
   backdated changes and supersession ordered? Can a corrected value overwrite
   earlier history without a revision record? Describe how a downloaded release
   can be frozen and reproduced. Unknown original publication is acceptable for
   this structural feasibility exercise, but must be reported as unknown.
6. **Coverage and omissions.** Identify history starts, known gaps, late additions,
   inactive/delisted coverage and excluded instrument classes/venues. What does
   no row mean: absent, uncovered, unauthorized, filtered, or no change? How can
   a complete issuer export avoid `allocate_isins=False` silently dropping rows
   without creating charges or allocations? Do not ask us to experiment with
   `allocate_isins=True` to discover the cost.
7. **Corporate actions and legal continuity.** Which actions require a new
   security/issuer ID, and how are ticker reuse, new common classes, mergers,
   spin-offs and primary-exchange transfers represented? Which additional
   reference/action product is required? Separate actual validity, announcement,
   ex-date and record-entry date. We are not requesting prices or return data.
8. **Commercial and operational fit.** Quote Reference specifically: smallest
   single-issuer evaluation/export and smallest full-US-history plus update plan;
   one-off/monthly/annual minimums; ISIN allocations; historical/delisted charges;
   identifier fees; required third-party licenses; cancellation and auto-renewal.
   State rights to retain immutable raw bytes after subscription, create derived
   research bindings, use any backtester/broker, run in private cloud/Python/Linux,
   and share only permitted non-data metadata/hashes in a public repository.
   Do not infer Reference access from historical-market-data credits.

## Exact free FMBH sample

Issuer: **First Mid Bancshares, Inc., CIK 0000700565**. FMBH is a discovery hint,
not the enumeration filter. Prior external observations mention common stock,
XNAS, share-class FIGI `BBG001S704Q4`, composite FIGI `BBG000BD8VT0`. Please
independently confirm or contradict these hints; do not filter out discrepancies.

Return a static native JSONL/CSV export and a manifest, with:

- All issuer/security/listing records needed to identify every potentially
  qualifying NYSE/Nasdaq common class at the May 1 cutoff. Include uncertain type
  or CIK associations and relevant retired IDs; show source-backed exclusion
  reasons for returned nonqualifying classes. No current-active, primary-share,
  ticker-only or convenient-security-type filter that can hide another class.
- A provider-grounded baseline preceding **2025-02-04**, plus all structural
  changes relevant through **2025-05-09T14:03:00Z**. Alternatively, supply a
  documented covering historical-valid interval with its supporting sources.
  Include later corrections to those historical facts as of export time and
  preserve available revision metadata. No look-ahead knowledge claim is requested.
- Evidence mapping the same issuer/class/listing to the **60 registered session
  dates from 2025-02-04 through 2025-04-30**, and establishing state at:
  - **2025-05-01T04:00:00Z** — May 1 midnight America/New_York;
  - **2025-05-09T13:52:26Z** — filing acceptance;
  - **2025-05-09T14:03:00Z** — simulated action instant.
- Structural fields: native IDs and historical relationships; issuer/CIK;
  class/security description and type/CFI; ticker/symbol; primary exchange,
  listing exchange and MIC codebook; listing status and listing/delisting dates;
  effective state/interval; available record, revision, publication and creation
  clocks. Preserve nulls, native precision/timezones and per-field limitations.
  An incorporation-country field alone need not establish domestic operating-company
  status; identify which fields require separate SEC/issuer corroboration.
- Manifest: product/schema version, export UTC time, query/filter description,
  baseline/history start, all delivered IDs and row counts, known exclusions,
  completeness/coverage statement, correction-release identifier and source
  specification references. SHA-256 files are helpful for integrity, not truth.

Please explicitly identify which required facts your product **cannot** prove
and which authoritative SEC/exchange evidence would close those gaps. We accept
a multi-source method; we do not require Databento to independently establish
every legal fact. Do not fabricate precision or include prices, quotes, returns,
MD&A, model outputs or any broker/account information.

## Internal acceptance decision — not part of a sales promise

This request has not been sent. The review author has no authority to purchase.
Documentation and actual sample must jointly support a complete qualifying-class
method, correct historical bindings, carry-in/transition semantics and all three
instants under unchanged Amendment 005. Missing facts remain UNRESOLVED.

An empty response or one FMBH row is not a negative class census. A stable sample
is not a universe-wide guarantee. A successful qualification does not authorize
remaining Massive calls, candidate #2, alpha experiments, an eligibility-ledger
change or trading. For later scale acceptance, request existing provider examples
of delisting, ticker reuse, dual class, exchange transfer and correction; do not
start screening another research candidate to test the supplier.
