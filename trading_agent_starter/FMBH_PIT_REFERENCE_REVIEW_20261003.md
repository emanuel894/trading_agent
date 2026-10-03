# FMBH external point-in-time reference-source review

**NARROW_EFFECTIVE_TIME_AMENDMENT_REQUIRED**

This is a source-resolution finding and a proposed wording correction, not an
amendment or eligibility decision. Candidate #1 remains **UNRESOLVED**. The
recommendation is necessary to admit retrospective valid-state evidence without
also proving historical knowledge time under the current contract. It does not
mean every possible source fails the existing contract: timestamped exchange
records may satisfy its stronger requirement.

Scope: First Mid Bancshares, Inc., CIK `0000700565`, observed FMBH common stock,
XNAS; priority rank 1 and digest
`00004f5851fcd2d7cd1ba3e1dfe1e225fa7d8b4fd50a675cc1bc44a552c0f2e6`.
No new issuer facts or eligibility claims were inferred from documentation examples.

## Controlling registration and the three clocks

Amendment 003, `research/cohort_selection_registration_003.json`,
`universe.identity`, says exactly:

> Dated research-class lineage and listing intervals; interval/source evidence predates the membership/event cutoff, historical retrieval time may be later

Amendment 004 incorporates that sentence unchanged in
`eligibility.inherited_universe_contract.identity`. Its exception waives only
the global population/top-500 requirement. Its event rule also states:

> Same issuer CIK and dated research share-class lineage at monthly cutoff, acceptance and simulated action; no parent/subsidiary ticker inheritance, debt ticker substitution or new-class substitution within month.

The distinction is therefore **not local possession in 2025 versus 2026**.
Later retrieval is expressly permitted. There is nevertheless an additional
source-availability/knowledge requirement beyond historical validity:

- `agent/cohort_selector.py:identity_at` requires both interval coverage and
  `known_at <= required instant`; `refs` requires source `available_at <= cutoff`.
- `agent/acquisition_registration.py:validate_issuer_class_binding` separately
  enforces `known_at <= instant`.
- `COHORT_SELECTION_INPUTS.md` requires source-backed interval endpoints and
  knowledge timestamps; it disallows future endpoints inferred from an
  announcement unknown at the decision time. Its source availability describes
  underlying information, not a fabricated historical download time.

| Clock | Meaning | Admissible treatment |
| --- | --- | --- |
| A: effective/valid time | When the issuer/class/symbol/listing fact held | Must cover the required historical date/instant at the source's actual resolution. |
| B: source publication/capture/revision | When a source published, captured or revised the fact | Preserve each separately where supplied. Unknown is unknown; an update field is not automatically first publication. |
| C: our retrieval | When we acquired these bytes in 2026 | Preserve the actual timestamp. Later retrieval alone cannot invalidate genuine historical evidence. |

The existing rule cannot silently accept A as proof of B. Nor may a later
record about a May 12 charter change be backdated to May 1 or May 9.

## Massive: promising date-level reference, insufficient knowledge-time contract

[All Tickers](https://massive.com/docs/rest/stocks/tickers/all-tickers)
documents a historical `date` query and date-relative `active` filter. It exposes
CIK, symbol, asset type, primary-listing MIC and optional share-class FIGI.
`active=false` denotes delisting; `active=true` does not prove uninterrupted
tradability or absence of a halt. `last_updated_utc` describes information
currency, without a documented first-publication or immutable-vintage guarantee.

[Ticker Types](https://massive.com/docs/rest/stocks/tickers/ticker-types)
maps `CS` to common stock. Missing optional identifiers remain unresolved; a
FIGI alone does not establish charter continuity or a complete issuer-class set.

The reference endpoint is included in Stocks Basic, whose documented history is
two years; total provider history starts September 10, 2003. All requested
February–May 2025 dates are inside two years as of October 3, 2026.
[Basic limits](https://massive.com/knowledge-base/article/what-is-the-request-limit-for-massives-restful-apis)
are five requests per minute for stocks. Actual account access has not been tested.

[Ticker Overview](https://massive.com/docs/rest/stocks/tickers/ticker-overview)
explicitly aligns SEC-derived details to reporting-period dates, even where the
filing arrives later. Consequently its historical response cannot be treated
as a knowledge-time snapshot. This warning is not proof that every All Tickers
identity field has the same sourcing algorithm; field-level provenance is
undocumented in the reviewed material.
[The update description](https://www.massive.com/blog/announcing-our-new-point-in-time-company-details-api)
describes nightly SEC-driven changes. It does not supply a reference-data
revision ledger or an as-known-vintage parameter.

Neither endpoint's reviewed documentation defines the timezone/day boundary
or an intraday effective interval for `date`. No midnight-to-midnight validity,
exact May 9 intraday state, or continuity between sparse requests is certified.
The API can address all 60 registered dates; four successful pilot dates would
not establish the other 56, interval continuity or historical public availability.

## Conditional fallback: Databento XNAS.ITCH definitions

Evaluated because Massive does not document the current contract's publication
and exact-instant semantics. [Databento's XNAS normalization](https://databento.com/docs/venues-and-datasets/xnas-itch)
sources definitions from Nasdaq Stock Directory messages. `exchange` maps the
listing market to MIC, including XNAS; `security_type` and `secsubtype` preserve
Nasdaq issue classifications. Merely appearing in XNAS.ITCH is insufficient:
the execution venue also handles non-Nasdaq-listed issues.

[Nasdaq's specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf)
defines a daily directory, historical symbol, listing categories Q/G/S for
Nasdaq, and issue classification C for common stock. The directory timestamp
is message-generation time. A daily stock-locate code is not a permanent
share-class identifier, and a directory message is not a halt clearance.

[Databento definitions](https://databento.com/docs/schemas-and-data-formats/instrument-definitions)
provide a timestamped series and capture time `ts_recv`; distinguish replay or
synthetic snapshots from original messages. These records can potentially bind
symbol/type/listing to a historically bounded state. They do not themselves
provide CIK, a permanent share-class FIGI, complete legal lineage, or an
unconditional interval extending from a morning message back to midnight.
Existing SEC bindings would still be required. Carry-in and complete relevant
definition changes must be established before inferring an interval.

No FMBH definition records, authenticated coverage result or price quote were
obtained. This is a credible fallback, not a demonstrated need to buy data.
A future cost-only check would use `metadata.get_cost` for `XNAS.ITCH`,
`schema=definition`, `symbols=FMBH`, after confirming range availability.
No trade or order-book schemas are needed. Exact price remains unquoted.

## Exact remaining scope

| Instrument / dates | Unresolved evidence |
| --- | --- |
| FMBH / 60 registered sessions, 2025-02-04 through 2025-04-30 | Actual historical class/CIK/symbol/XNAS records for each required date; documented valid-time resolution and lineage; source knowledge time under the unchanged rule. |
| FMBH / 2025-05-01 00:00 EDT | Valid listing/class state at the cutoff, including day-boundary/carry-in semantics; source knowledge time under the unchanged rule. |
| FMBH / 2025-05-09 09:52:26 and 10:03 EDT | Same class/listing at acceptance and simulated action; date-only data must not be promoted to intraday evidence. |

## Minimal proposed wording — not registered or implemented

Replace only the structural identity temporal requirement for the
acquisition/provenance audit with:

> Identity and listing facts must be source-backed as valid at each required
> historical date or instant. Retrospective point-in-time reference records may
> be retrieved or revised later. Preserve valid time, source publication/capture
> and revision time where available, and actual retrieval time separately.
> Unknown source knowledge time does not alone disqualify historical structural
> reconstruction. Date-only evidence retains date-only resolution; unresolved
> intraday or boundary validity remains UNRESOLVED. This exception does not
> establish decision-time availability of disclosures or predictive features,
> and does not authorize prospective actionability.

This removes the A/B conflation for retrospective structural reconstruction
without changing issuer priority, economics, class completeness or the event
rule. It would require explicit authorization and a separately versioned
contract before changing the current guards. It does not automatically admit
Massive or FMBH, infer missing intervals, or authorize candidate #2.

## Smallest conditional owner-local probe

`MASSIVE_API_KEY` was unavailable in the runtime/environment check. No account
was created and no authenticated reference request was made. Once the temporal
contract is resolved, the smallest access/schema pilot is four GETs to
`https://api.massive.com/v3/reference/tickers`, with `ticker=FMBH`,
`market=stocks`, `active=true`, `limit=10`, and dates **2025-02-04,
2025-04-30, 2025-05-01, 2025-05-09**. Do not prefilter CIK/type/exchange:
inspect returned values so disagreement cannot be hidden by filtering.

Use an existing owner-local `MASSIVE_API_KEY` through an authorization header,
never a printed URL or persisted credential. Preserve response bytes, request
parameters, request ID, actual retrieval time and hashes in the existing store;
never assign a query date to `known_at` or `available_at`. Stop on unexpected
pagination, ambiguous/missing rows or mismatched identifiers. HTTP success
proves access only. No probe has been implemented or run in this milestone.

Estimated burden: four small reference responses, one Basic rate-limit window,
$0 on documented Basic access; response size is unmeasured. A later complete
date-level check would require at least 62 date queries (60 sessions plus the
two May dates), about 13 five-request windows, plus any separately justified
issuer-class completeness queries. It is not authorized here. No paid product
is recommended and no purchase occurred.

## Preservation and stop

The companion JSON binds source captures, the unchanged registrations/priority/
ledger and all 60 dates. Documentation was captured through the web retrieval
service; hashes authenticate the preserved returned text/metadata, **not raw
origin HTTP bodies or a historical documentation version**. Origin download
was unavailable in the shell. The captures make no FMBH factual assertion.

Only this report and its evidence inventory are new repository artifacts.
No amendment, selector, ledger or executable pipeline was changed; no new SEC
cover, market bar, reference data, cohort, audit or strategy was acquired/run.
Next permissible step is review of the proposed temporal wording. Candidate #1
remains UNRESOLVED; candidate #2 remains blocked.

Verification: Amendment 004 returned `REGISTRATION_VERIFIED` with its accepted
SHA-256 `c4dfc00f202ef93a3b87cfb8928f75c4a7e152db6a3253260187bdb9b0173409`.
The new evidence store returned `VERIFIED` for nine records (eight documentation
captures and one review), chain head
`5461e63ea8cbfed49929588c54cc8a63b4900060ca1563a7f630f07dd1d354e7`.
The preserved evidence ZIP is 49,127 bytes, SHA-256
`f2763914b15d25217e027f44d07b50fb5016e8cd828a8a67cd4e0bf36d9e05fe`.
No code tests or new CI result are claimed for this documentation-only review.
