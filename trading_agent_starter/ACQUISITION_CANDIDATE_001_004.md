# Amendment 004 — first bounded candidate review

**Decision: UNRESOLVED. Stop at candidate #1.** Exactly one candidate-ledger
decision was appended. Candidate #2 was not screened. No cohort was constructed
or frozen and no acquisition audit was run. Amendments 003/004, their rules and
all prior artifacts remain unchanged.

## Frame verification and priority preservation

All four pinned SEC master-index ZIP objects passed exact byte-hash checks,
record-chain verification and HTTP provenance checks. The reused Q1/Q2 objects
also match their original capture records. Both prior evidence stores were
opened read-only. Quarterly original counts are 1,033 / 5,399 / 5,419 / 5,438.

The rebuilt frame exactly reconciles to the preserved normalized inventory:
**17,289 distinct original `(CIK, accession)` pairs; 5,974 distinct CIKs.**
No missing/extra pairs or conflicting duplicates were found. These counts are
SEC filers, not an eligible market population. The source vintage was retrieved
in September 2026; it is not claimed to be an unrevised 2025 archive vintage.

| Preserved object | SHA-256 |
|---|---|
| Q1 master ZIP | `33b2b44397e789306ee75953280b42ea5ffc07b52ec47bb58667b8881f0bb134` |
| Q2 master ZIP | `7c53326ee24e96cab8df014d76b839b27d205c82c722e809d94a53ff3af48aa8` |
| Q3 master ZIP | `64d34fab6e75310382be00d50dae4f7b2f7e882acb775ff18b6cef0e015dad88` |
| Q4 master ZIP | `c523d0da50cf2c8acc9a94d7dc2dc4015998fad40babc58277fce48493fdf4ca` |
| Preserved input inventory | `294c2354af6ca69d8b875088115184c583cc058947643b7ea2a8762f03fcf865` |
| Rebuilt canonical original-pair array | `de6d154f6ba886f9cb966f0c73d3297a4462f90097ee2d783e9b34782025ae72` |

The complete 5,974-CIK order was derived with the unchanged Amendment 004 seed
and encoding and preserved at **2026-09-22T15:30:21.380098Z**, before the first
issuer-specific HTTP request. `research/acquisition_priority_order_004.json`
contains the exact canonical bytes, without a trailing newline.

Priority-order SHA-256:

`f90430aeb8c92031317e376080142e3513bb648dc64522cec6c0d526fdc59a69`

Candidate #1:

- Rank: **1**
- CIK: **0000700565**
- Issuer: **First Mid Bancshares, Inc.**
- Registered class observed: **FMBH common stock, Nasdaq**
- Priority digest: `00004f5851fcd2d7cd1ba3e1dfe1e225fa7d8b4fd50a675cc1bc44a552c0f2e6`
- Internal research label: `research:sec-0000700565:common-usd4`. This identifies
  the reviewed lineage; it does not assert a vendor ID or an approved interval.

## Exact evidence reviewed

Existing official index evidence was reused first. There was no preserved
issuer-specific metadata or FMBH daily-bar request record in the local stores.
New retrieval was limited to **nine SEC responses, 704,710 bytes**, for this
issuer only. Raw responses, request/receipt times and hashes are preserved in
the evidence packet. No primary 10-Q/10-K body or MD&A was inspected.

| SEC source | Purpose and review boundary |
|---|---|
| `https://data.sec.gov/submissions/CIK0000700565.json` | Issuer identity and filing metadata; recent metadata covers 2017-05-02–2026-08-07; the only historical page ends in 2017 and does not overlap 2025. Current ticker fields were not used as dated listing proof. |
| `700565/000095017024123741/R1.htm` | November 8, 2024 quarterly DEI cover anchor. |
| `700565/000095017025029793/R1.htm` | February 28, 2025 annual DEI cover anchor. |
| `700565/000095017025029793/FilingSummary.xml` | Table-of-contents metadata locating the identity/consolidation note. |
| `700565/000095017025029793/R14.htm` | Annual Note 1: operating parent and its bank, wealth, insurance and captive subsidiaries; reviewed identity/organization paragraphs, not MD&A. |
| `700565/000095017025067613/R1.htm` | May 9, 2025 quarterly DEI cover anchor. |
| `700565/000095017025105507/R1.htm` | August 8, 2025 quarterly DEI cover anchor. |
| `700565/000119312525272249/R1.htm` | November 7, 2025 quarterly DEI cover anchor. |
| `700565/000095017025073121/fmbh-20250516.htm` | May 16, 2025 Form 8-K item 5.03 only: charter amendment/restatement; referenced exhibits were identified but not acquired. |

Archive-relative paths above have prefix
`https://www.sec.gov/Archives/edgar/data/`. Exact full URLs, raw SHA-256 values,
response timestamps and evidence IDs are in
`research/acquisition_candidate_001_004_review.json`.

The five dated cover anchors consistently identify the same registrant CIK,
FMBH common stock, Nasdaq, Delaware incorporation, Illinois address, SEC file
number 001-36434 and `EntityShellCompany=false`. The annual organization note
supports operating-company status rather than relying on incorporation alone.
FMBH belongs to the registrant; no subsidiary inherits a parent ticker. There
is no debt, preferred, ADR, fund, warrant, right or unit substitution.

These establish a common-class identity at filing anchors. They do **not** by
themselves establish complete valid-from/valid-to intervals or rule out all
intervening class/listing changes. That distinction remains unresolved rather
than being promoted to an eligibility PASS.

## Original 2025 10-Q metadata

All three SEC original-event rows match the original master-index pair set.
Acceptance instants are SEC retrospective metadata, not live decision receipts.

| Accession | Report date | SEC acceptance UTC | Eligibility |
|---|---|---|---|
| `0000950170-25-067613` | 2025-03-31 | 2025-05-09 13:52:26 | UNRESOLVED |
| `0000950170-25-105507` | 2025-06-30 | 2025-08-08 14:05:48 | UNRESOLVED |
| `0001193125-25-272249` | 2025-09-30 | 2025-11-07 20:49:03 | UNRESOLVED |

There are at least two originals, but **at least two eligible originals have not
been proved**. No earliest qualifying pair was selected.

## Exact unresolved evidence

| Instrument / date | Field | Missing source evidence |
|---|---|---|
| FMBH / May 1, 2025 monthly cutoff | Median daily close × volume and prior close | Exactly 60 Amendment 003 FMBH bars, February 4–April 30, 2025, including the April 30 close. |
| FMBH / August 1, 2025 monthly cutoff | Same liquidity and price requirements, if needed | Exactly 60 bars, May 6–July 31, 2025, including the July 31 close. |
| FMBH / November 1, 2025 monthly cutoff | Same requirements, only if needed after earlier events | Exactly 60 bars, August 8–October 31, 2025, including the October 31 close. |
| FMBH / those cutoffs and the May 9, August 8 and November 7 acceptance dates and simulated action instants | Complete dated common-class/listing intervals | Issuer-specific listing/class-change evidence closing intervals between the captured anchors. Do not assign an XBRL reporting period as a listing interval. |
| FMBH / May 12, 2025 effective charter change; later August/November events | Charter/share-class lineage closure | Review exhibits `fmbh-ex3_1.htm` and `fmbh-ex3_2.htm` referenced by the captured May 16 8-K, plus any necessary issuer-specific continuity evidence. |

The market-data source is the existing owner account's Alpaca historical SIP
`/v2/stocks/bars`: `timeframe=1Day`, `feed=sip`, `adjustment=raw`, `asof=-`.
There are no preserved FMBH daily rows here and this runtime has no configured
Alpaca credentials. **Zero market-data requests were made.** Historical SIP
entitlement remains accepted; a missing local input is not an entitlement error
or proof of illiquidity. Daily bars are required to resolve economic eligibility,
but were not acquired in this run.

The 8-K says shareholders approved increasing authorized common shares from
30 million to 45 million on April 30; the charter amendment/restatement became
effective May 12 and the notice was accepted May 16. This is not itself a split
or evidence of a new common class. The May 16 notice cannot be used as evidence
known at the May 1 cutoff or May 9 event. Its implications for later events are
not assumed away.

## Ledger, preservation and next permissible action

Exactly one decision record was appended:
`412f9814ade741ada7d80824f22d29a1`, **UNRESOLVED**. Its review is hash-bound to
`f600da6ef8b10a879a328d3c2ea30a0caeee8e2a99dfd7414847d2bd893d566c`.
The Amendment 004 protocol returns `BLOCKED / UNRESOLVED` at rank 1; it does not
skip to rank 2. The evidence store verifies **29 records, VERIFIED**. Substantive
proof and protocol validation remain separate.

The next permissible action is to resolve **this same candidate only**: close
the dated class/charter interval review and acquire owner-local Amendment 003
FMBH bars, starting with the May cutoff's 60 dates. Proceed to later windows
only as needed to establish the earliest two eligible events or a proven
exclusion. Preserve a linked revised decision on new evidence; never overwrite
this decision. Do not screen candidate #2 while candidate #1 is unresolved.

Offline frame replay is available as
`python -m agent.acquisition_frame_replay --output runs/<new-unused-name>`.
It verifies preserved local evidence and writes priority artifacts only; it
does not perform candidate screening. Do not rerun it merely to change the
priority or replace missing source objects.
