# FMBH — verified pilot and substantive Amendment 005 review

**GENUINE_UNRESOLVED_BLOCKER.** The supplied pilot is independently verified.
Massive is admissible as date-level structural reference evidence for the four
queried dates. This finding does not establish candidate eligibility, continuous
lineage, class completeness or exact-instant validity. No provider request was
repeated, and no new candidate-ledger decision was appended.

Candidate: priority 1, CIK `0000700565`, First Mid Bancshares, Inc., FMBH;
priority digest `00004f5851fcd2d7cd1ba3e1dfe1e225fa7d8b4fd50a675cc1bc44a552c0f2e6`.
Amendment 005: `26eeca3bc843f0de0dab53b61fa2008773e1616d888bb165111fabe8a2c38cc5`.

## Independent archive verification

The uploaded ZIP has SHA-256
`dc8fd3f18c3d28a9e25c8203996a2043a3b1610736bfb623ad993376c061d24f`.
It contains one SQLite database and five content-addressed objects, with no
`.env`. Every object filename matches its bytes. All four supplied response
record IDs and hashes match. The existing evidence-store verifier independently
returns five records, VERIFIED, and head:

`7a5f0dafddee5e17dc24dc13e82157be98d14b57d716d9590574f047971c7705`

All six materialized files remain byte-identical to the uploaded archive.
Each response binds the exact registered GET parameters, CIK, priority digest
and amendment; HTTP 200, provider request ID, one result and no pagination were
checked. Chain verification establishes internal integrity, not an independent
provider signature or proof of account entitlements beyond these captures.

| Requested historical date | Preserved provider `last_updated_utc` |
| --- | --- |
| 2025-02-04 | 2025-08-13T15:21:34.283298Z |
| 2025-04-30 | 2025-05-01T06:03:37.059139972Z |
| 2025-05-01 | 2025-08-13T17:22:03.324807Z |
| 2025-05-09 | 2025-05-10T06:06:38.775815022Z |

Actual owner retrieval was October 7, 2026, 11:04:10–11:04:49 UTC. Source
first-publication, capture, historical knowledge and effective timestamps remain
unknown. Update strings are retained exactly, including nanosecond precision;
none becomes `known_at`, `available_at` or the beginning of a validity interval.
The August updates do not alone disqualify retrospective structural reconstruction.
They do prevent describing these bytes as an immutable May information vintage.

## Field-by-field source finding

The preserved [All Tickers documentation](https://massive.com/docs/rest/stocks/tickers/all-tickers)
describes date-relative historical ticker availability and active-state filtering.
This is a documented historical-reference purpose, beyond a date parameter alone.
Its schema identifies the listing MIC and issuer/class identifiers. The preserved
[type documentation](https://massive.com/docs/rest/stocks/tickers/ticker-types)
maps CS to common stock. The following are reviewed source assertions, not an
automatic PASS from the stricter complete-identity validator.

| Field | Four observed values | Admissible use and limit |
| --- | --- | --- |
| Issuer / CIK | First Mid Bancshares, Inc. Common Stock / 0000700565 | Date-level provider binding, corroborated by cached SEC issuer anchors; no parent ticker substitution. |
| Ticker | FMBH | Symbol at the queried dates; no interpolation. |
| Type | CS | Common-stock classification; does not prove domestic operating-company status by itself. |
| Primary exchange | XNAS | Provider primary-listing assertion; no exact effective timestamp. |
| Active | true | Date-level active/listed classification; no halt clearance or executable-market assertion. |
| Share-class FIGI | BBG001S704Q4 | Consistent identifier at four dates; contributes to lineage, but cannot prove continuity or absence of other classes. |

Field-specific revision provenance and an as-known vintage are not documented
in the preserved material. The [Overview endpoint's SEC-period behavior](https://massive.com/docs/rest/stocks/tickers/ticker-overview)
is not used to backdate a later filing, and is not assumed to describe the
different All Tickers endpoint. No current-only row was substituted.

The documentation captures were retrieved October 3, 2026. Their store verifies
nine records and head `5461e63ea8cbfed49929588c54cc8a63b4900060ca1563a7f630f07dd1d354e7`.
They preserve web extraction, not origin HTTP bytes or historical documentation
versions. The JSON inventory binds each capture and the actual response bytes.

## Concrete remaining evidence

| Instrument / date | Required field | Missing source evidence |
| --- | --- | --- |
| FMBH / registered sessions February 4–April 30, 2025 | Historical class/CIK/ticker/type/listing | **58 remaining session-date records**, or a genuinely documented interval. Only February 4 and April 30 of the pilot fall inside the 60-session window. The JSON enumerates all 58 dates. |
| CIK 0000700565 / May 1, 2025 cutoff | Complete qualifying-class set and legal lineage | Issuer-wide historical class enumeration reconciled with authoritative class evidence. A ticker-filtered result does not exclude another class. |
| FMBH / May 1, 2025 00:00 EDT | Class/listing validity at the boundary | Source-grounded carry-in/effective interval. Massive's undocumented date cutover cannot be converted to midnight. |
| FMBH / May 9, 2025 09:52:26 and 10:03 EDT | Same class/listing at acceptance and simulated action | Independently grounded exact-validity evidence. Cached SEC covers give issuer assertions at filing anchors; they do not supply the missing interval through action. |
| FMBH / February 4–April 30, 2025 | Amendment 003 liquidity and prior close | Exact 60-session Alpaca SIP 1Day raw/asof=- capture; Decimal median and April 30 close are not yet measured. |

The cached April 30 and May 6 8-K covers, May 9 10-Q cover, and SEC acceptance
metadata were reused. No additional SEC cover was acquired. Reporting-period
contexts were not converted into listing intervals. Later May 12 charter changes
are not evidence of historical knowledge on May 1/9. Amendment 005 could admit
later evidence of earlier *valid* facts when it actually states them; no such
interval was established by this review.

Neither `MASSIVE_API_KEY` nor usable Alpaca credentials is available in this
runtime. No secret was printed, persisted or requested for upload. The missing
58 records are an acquisition gap, not adverse evidence about FMBH. Exact-time
semantics and issuer-class completeness are separate source-evidence gaps; more
identical date probes alone cannot close them.

## Bounded continuation and stop

The next scientific determination is whether independently documented structural
validity and class completeness can cover the registered May cutoff/action
instants. No further sampling amendment or relaxation is proposed. Resolve that
source question before spending 58 calls on date completion. A dated issuer-wide
reference query (CIK, market stocks, active true, date May 1; no ticker/type/exchange
prefilter) is the smallest additional class-discovery capture, but its response
alone must not be called authoritative class completeness.

Conditional remaining capture burden: 58 nonduplicate Massive daily queries,
at least one issuer-wide query, and ordinarily one Alpaca daily-bar page for the
May window. Pagination and source-completeness needs remain explicit. These are
estimates, not executed calls or approval of intraday semantics. The existing
four-date pilot command must not be rerun. No new local capture implementation
is claimed in this source-review milestone.

Databento XNAS.ITCH definitions remain a documented possible interval source,
not proven coverage for these instants. A directory-message timestamp is not
automatically an effective interval extending backwards to midnight. No paid
data need or minimum purchase price has been established; no purchase is
recommended. The review does not claim every possible public source is exhausted.

Candidate counts remain 0 eligible / 0 ineligible / 1 unresolved. Candidate #2,
Amendment 006, August/November capture, cohort construction and the audit were
not started. Original registrations, priority, ledger and executable code remain
unchanged. All new data-provider and documentation requests: **0**; four existing
owner requests reused; spending **$0**. Trading flags remain unchanged and disabled.

Canonical review: `research/fmbh_massive_source_review_20261007.json`, SHA-256
`7775d0fc47bfb899d59222b25f247f40fb71fd4c82a1606a7b3714a8ace0a293`.
This is an additional source review, not a replacement of the original ledger
snapshot or a new eligibility decision. Substantive candidate evidence is still
incomplete, so the mandate's conditional batch phase is not authorized to start.
