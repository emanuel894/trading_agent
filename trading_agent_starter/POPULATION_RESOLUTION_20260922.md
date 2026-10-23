# Bounded 2025 historical-population resolution

**NARROW_POPULATION_CONTRACT_AMENDMENT_RECOMMENDED**

This is a recommendation for an **acquisition-audit-only sampling amendment**,
not a registered amendment. No selector, liquidity definition, population input,
cohort, or historical gate was changed or executed. The owner-local Amendment 003
smoke PASS is accepted and recorded separately as explicit owner evidence; its
raw archive was not supplied or independently replayed in this milestone.

The bounded review did not establish complete official/public populations at all
twelve registered cutoffs. It also did **not** prove that payment is unavoidable:
Massive documents a free dated ticker API covering these dates. Neither its
documentation nor a successful paginated download would by itself resolve the
remaining exact-time, exchange-completeness and class-evidence questions. Do not
buy a broad exchange subscription on the strength of this review.

## What the official sources establish

| Source | Evidence supplied | Limit for the registered population |
|---|---|---|
| [CTA archive](https://ftp.nyse.com/cta_symbol_files/) and [SIAC specification](https://www.ctaplan.com/publicdocs/ctaplan/CTA_Symbol_File_Specification.pdf) | 167 dated files listed for May 5–December 31, 2025. Symbol, primary-listing participant, test/IPO flags, broad instrument type and other SIP attributes. | Tape A/B, not Tape C. No January–April files or May 1 cutoff snapshot. No CIK, issuer name, common-share class lineage or domestic operating-company classification. |
| [NYSE Symbol Mapping directory](https://ftp.nyse.com/NYSESymbolMapping/) | Visible production/certification files dated September 21, 2026. | Not a 2025 archive. |
| [NYSE public Security Master samples](https://ftp.nyse.com/Reference%20Data%20Samples/NYSE%20GROUP%20SECURITY%20MASTER/) | Individual sample dates and layouts. | Samples do not form the required dated population/change series. |
| [Nasdaq Symbol Lookup](https://www.nasdaqtrader.com/trader.aspx?id=symbollookup) | Explicitly current-trading-day information. | Cannot prove historical membership. |
| [Nasdaq 2025 corporate-action alert index](https://www.nasdaqtrader.com/Trader.aspx?id=archiveheadlines&cat_id=105&year=2025) | Dated notices. The prior successful index capture is reused. | No independently established complete starting roster or exhaustive change ledger. An absent notice is not proof of no change. |
| [Nasdaq historical volume reports](https://www.nasdaqtrader.com/trader.aspx?ID=marketsharedaily) | Nasdaq/non-Nasdaq monthly workbook links exist for 2024 and 2025. | Trading-statistics documentation does not establish a complete legal listing roster or effective membership intervals. Workbooks were not downloaded. |
| [UTP technical material](https://www.utpplan.com/technical) and [Nasdaq ITCH specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf) | Directory messages are defined. ITCH's start-of-day directory covers active symbols in Nasdaq's execution system, with listing category and issue type/subtype. | A feed specification is not an accessible complete 2025 archive. Execution-system population and legal listing population require reconciliation; feed receipt after a cutoff is not evidence known before it. |

The reused May 5 CTA sample has 6,513 rows: 2,887 primary participant `N`
(NYSE/XNYS), 2,349 `P`, 954 `Z`, 320 `A`, and 3 `V`. All rows have instrument
type `0`: CTA-eligible equity, **not** a common-stock classification. Only `N`
can establish XNYS primary-market association here; Tape B is not an additional
eligible exchange under the registered XNYS/XNAS rule. No price columns were
analyzed. Hashes and counts are recorded in the companion JSON.

The SIAC file is an **8 p.m. ET snapshot**, available by midnight, excluding
adjustments after 8 p.m. A file's date or HTTP Last-Modified value does not prove
midnight state or historical first receipt. The formerly reserved prior-symbol
field became effective November 3, 2025; earlier blanks do not prove no rename.
The initial specification is dated May 5, 2025. Later files cannot be rolled
back into missing earlier populations without a complete dated change history.

## Exact unresolved dates and fields

The required state is 00:00 America/New_York on each month start. These are
source-resolution targets, **not population membership assertions**:

| Month cutoff | Last preceding session | CTA preceding-date file listed | XNAS complete public historical roster established |
|---|---|---|---|
| 2025-01-01 | 2024-12-31 | No | No |
| 2025-02-01 | 2025-01-31 | No | No |
| 2025-03-01 | 2025-02-28 | No | No |
| 2025-04-01 | 2025-03-31 | No | No |
| 2025-05-01 | 2025-04-30 | No | No |
| 2025-06-01 | 2025-05-30 | Yes | No |
| 2025-07-01 | 2025-06-30 | Yes | No |
| 2025-08-01 | 2025-07-31 | Yes | No |
| 2025-09-01 | 2025-08-29 | Yes | No |
| 2025-10-01 | 2025-09-30 | Yes | No |
| 2025-11-01 | 2025-10-31 | Yes | No |
| 2025-12-01 | 2025-11-28 | Yes | No |

- **XNYS/Tape A, January–May cutoffs:** complete dated class roster, primary
  listing, security type and effective intervals. Missing source: authoritative
  snapshots at the required cutoffs, or an earlier complete baseline plus all
  relevant additions/deletions/transfers/renames through April 30/May 1.
- **XNYS/Tape A, June–December cutoffs:** the listed CTA snapshots help enumerate
  symbols. Missing source: coverage of changes after their 8 p.m. state through
  the cutoff, including intervening non-trading days, and dated issuer/class
  bindings. Carry-forward cannot silently stand in for that coverage.
- **XNAS/Tape C, all twelve cutoffs:** complete historical roster/baseline plus
  exhaustive relevant changes, including delisted, renamed, suspended and
  non-common classes. Also required: historical primary listing, issue type,
  class identity and effective/publication times.
- **Both exchanges:** SEC evidence can bind CIK, issuer, class and dated
  classifications once candidates are enumerated. A SEC filing index enumerates
  filings; it is not proof of the complete exchange population. Unknown fields
  remain UNRESOLVED rather than causing candidate removal.

## Cheapest alternatives and their actual limits

1. **Free dated vendor source:** [Massive All Tickers](https://massive.com/docs/rest/stocks/tickers/all-tickers)
   supports `date`, dated `active`, primary MIC, type, optional CIK and class FIGI,
   and pagination. Its [point-in-time description](https://www.massive.com/blog/new-point-in-time-tickers-api)
   specifies nightly synchronization; [delisted histories are retained](https://massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers).
   [Basic is $0, five requests/minute and two years of history](https://massive.com/pricing),
   covering the requested dates as of September 22, 2026. This is a credible
   free discovery/corroboration path, not today's survivors relabeled historical.
   Outstanding: exact date boundary/timezone, coverage of listed but suspended
   classes, historical field revisions/availability, and evidence that the
   provider-supported list exhausts the exchange candidate set. No API account
   was created and no authenticated population query was run. Its
   [individual/business terms](https://www.massive.com/legal/terms) must match the
   actual use; no redistribution or commercial-use grant is inferred.
2. **Small exchange-origin archive extract:** [Databento XNAS.ITCH definitions](https://databento.com/docs/knowledge-base/datasets/xnas-itch)
   normalize the official stock-directory MIC, issue type and subtype. Request
   only directory definitions for the necessary dates, including source coverage
   and capture-integrity evidence. No quote/trade feed purchase is needed for
   this proposal. Reconcile Nasdaq-execution-system scope and cutoff timing
   before calling it complete. [Historical usage pricing](https://databento.com/pricing)
   and promotional credits are advertised; the exact request price and license
   eligibility are **not verified**. This is the smallest credible paid-product
   candidate, not a demonstrated paid necessity or a guaranteed complete solution.
3. **Official exchange fallback:** ask for a bounded non-CUSIP extract from
   [NYSE Group Security Master](https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Security_Master_Client_Specification_v4.0.6.pdf)
   and [Nasdaq Daily List](https://www.nasdaqtrader.com/Trader.aspx?id=dailylistpd),
   with a dated baseline and complete changes. Nasdaq documents historical Daily
   List coverage from 1999, but its [Fundamental Data standard access](https://www.nasdaqtrader.com/Trader.aspx?id=FD)
   is current-business-month only. Do not assume a subscription includes the
   needed 2025 baseline. The [2026 rule filing](https://www.sec.gov/files/rules/sro/nasdaq/2026/34-106034.pdf)
   changes free publication arrangements; it does not promise a complete public
   2025 backfill. The former $3,500 monthly fee is not a current extract quote.
   [Current Equity 7](https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/nasdaq-equity-7)
   reflects the August 28, 2026 amendment. No vendor was contacted or paid.

## Sampling amendment: what it can and cannot solve

For **acquisition feasibility only**, use the complete SEC 2025 original-10-Q
index as the declared issuer sampling frame, rather than the entire U.S.
exchange population. Preserve dated domestic XNYS/XNAS operating common-share
eligibility, all class exclusions, the most liquid eligible class per issuer,
Amendment 003's exact 60-session/$20m/$10 rules, and the 25-issuer/two-event size.
Waive the **global monthly top-500 membership requirement for this acquisition
sample only**. That is the specific dependency removal; changing only the CIK
sampling order while retaining global top-500 membership would not solve it.

Pre-register a fixed seeded CIK hash, independent of all source outcomes, before
screening. Select the 25 highest-priority proven eligible issuers with two
eligible originals and their earliest two eligible filings. Evaluating candidates
in hash order is a lazy evaluation of selection from the eligible frame, not
permission to select before eligibility. An unknown higher-priority candidate
blocks closure; only a proved eligibility exclusion permits moving past it.
Preserve an exclusion/unknown ledger and prohibit success-based replacement.
All classes of each evaluated issuer must be examined; no parent ticker or
convenient class substitution is allowed.

This avoids **new survivor-only and acquisition-success filters within that
explicit filing frame**. It is not an unbiased sample of the original global
top-500 population, all listings, or all live events. The retained two-filing
condition also restricts the population and must not be interpreted as a live
eligibility rule. Uniform fixed-seed random priorities give equal issuer
selection probability within the defined eligible frame; two records per issuer
do not give equal event-level weights across all filings. No representativeness,
alpha, opportunity-rate or latency-distribution conclusion follows from this
acquisition sample.

The recommendation is justified by the acquisition question: can the evidence
chain be assembled reliably? It does not change the eventual trading experiment's
universe. Full-market completeness remains required before making claims about
the original monthly top-500 research universe. This proposal is not implemented.

## Burden and one next step

**Next implementation step:** after explicit acceptance, register only the
acquisition-sampling amendment and its no-replacement/unknown rules. Do not
select issuers or acquire population/bar datasets in that registration step.

Current milestone spend: **$0**. No new full symbol snapshots, population API
requests, market bars, filings or return datasets were downloaded. Existing
CTA and SEC index evidence was reused; public documentation was reviewed.

- Seven relevant CTA snapshot files total approximately **2.10 MB** from listed
  sizes, excluding headers and any required change evidence. All 167 files are
  unnecessary for simple monthly snapshot corroboration.
- A future free vendor enumeration, assuming 10,000 combined candidate rows per
  date, would be about **120 pages at 1,000/page**, at least **24 minutes** at five
  calls/minute, roughly **60–120 MB** at 500–1,000 bytes/row. Inactive-history
  queries can be substantially larger. These are estimates, not measured counts.
- A directory-only historical extract at 10,000 definitions × 12 dates × roughly
  400 bytes is about **48 MB uncompressed**, plus source integrity and change
  records. Actual fees require a request-specific quote; no subscription price
  is inferred from data size or promotional credits.
- The SEC acquisition-frame proposal reuses 17,289 original index pairs across
  5,974 CIKs already captured. That is a filing frame, not 5,974 eligible issuers.
  Screening cost depends on proved exclusions and unknowns; no promise that only
  25 companies need review. Registration itself needs **zero data requests**.
