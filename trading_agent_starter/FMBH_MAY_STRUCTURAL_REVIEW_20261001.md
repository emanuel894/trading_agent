# Candidate #1 — May point-in-time structural review

**UNRESOLVED. The user's structural-failure stop condition was reached.**
The owner-local liquidity tool was not implemented or run. There is no new
Windows capture command or capture-output schema to present as completed.
The existing candidate decision remains unchanged; candidate #2 was not reviewed.

Candidate: rank 1, First Mid Bancshares, Inc., CIK `0000700565`, observed ticker
FMBH. Priority digest:
`00004f5851fcd2d7cd1ba3e1dfe1e225fa7d8b4fd50a675cc1bc44a552c0f2e6`.
Amendments 003/004 and the complete frozen priority order remain unchanged.

## New official evidence

Two issuer-specific SEC responses were acquired, totaling **87,608 bytes**.
Only the cover before the first substantive item was reviewed. No earnings
release exhibit, MD&A, return calculation or market reaction was used.

| SEC filing | Acceptance / knowledge anchor | Findings |
|---|---|---|
| [April 30 8-K, 0001171843-25-002652](https://www.sec.gov/Archives/edgar/data/700565/000117184325002652/f8k_042925.htm) | 2025-04-30 20:30:10 UTC | The cover explicitly binds CIK 0000700565 to First Mid Bancshares, Common Stock, FMBH and Nasdaq Global Market. Available before the May 1 cutoff. |
| [May 6 8-K, 0000950170-25-064109](https://www.sec.gov/Archives/edgar/data/700565/000095017025064109/fmbh-20250506.htm) | 2025-05-06 15:38:53 UTC | Same CIK/common-class/ticker/Nasdaq binding. Available before the May 9 event, but not before the May 1 cutoff. |

The inline-XBRL security fields were grouped by context and matched to the
registrant CIK. Context reporting dates were **not** used as listing intervals.
The April 30 cover prints administrative SEC file number 0-13368 and the May 6
cover prints 001-36434; no separate issuer/class was inferred from that difference.

Raw SHA-256 values:

- April 30 cover: `d8dee3a11109c4ca725785ffe37d88dc0c9e77f531ba4a4fdd0347aa0d627abf`
- May 6 cover: `13e6676f26e4e076c7fdf56afe3c8978a24f7bf385048ceb5d2f87f8e143736f`

Acceptance metadata was reused from the previously preserved official SEC
submissions response. Historical retrieval time is retained separately; SEC
acceptance is the registered historical anchor, not a claim of live receipt.

## What remains unproved

The new covers establish dated issuer assertions of common-stock registration
on Nasdaq. They do not state an explicit validity interval or establish complete
effective listing/class-change coverage through the required later instants.

| Required instant | Admissible evidence | Remaining source requirement |
|---|---|---|
| May 1, 2025, 00:00 EDT / 04:00 UTC | April 30 cover, accepted 7h 29m 50s earlier | Authoritative FMBH common-class / primary-XNAS interval evidence covering the cutoff, known by that cutoff. |
| May 9, 2025, 09:52:26 EDT / 13:52:26 UTC acceptance | May 6 cover; existing May 9 10-Q cover at its acceptance anchor | Source-backed class/listing interval evidence; the May 9 cover must never be backdated to May 1. |
| May 9, 2025, 10:03 EDT / 14:03 UTC simulated action | Existing May 9 10-Q cover, accepted 10m 34s earlier | Evidence carrying the same class/listing validity through the action instant without an invented interval. |

The exact unresolved source is an **authoritative issuer-specific XNAS
issue/membership record, or a baseline plus demonstrably complete issuer-specific
effective-change ledger**, with publication/knowledge bounds no later than each
required instant. It must establish the same FMBH common-stock lineage and
primary XNAS membership at those instants.

No qualifying record closing those intervals was established in this bounded
review. Carrying each cover forward until another filing appears would be an
additional continuity assumption, not a fact stated by the captured sources.
This review does not silently add that assumption to the registered rules.
It also does not claim all possible public sources are exhausted, that FMBH was
actually unlisted, or that a paid dataset is necessary.

## Point-in-time exclusions and stop

The May 16 8-K and its May 12 effective charter change were not used at May 1 or
May 9. The referenced `fmbh-ex3_1.htm` and `fmbh-ex3_2.htm` exhibits were not
downloaded: they cannot close the earlier knowledge gap, and later-event lineage
is outside this bounded May review. Later quarterly filings and today's ticker
directories were not used to manufacture earlier membership.

Because the user explicitly required a stop if May structural evidence could
not be established, work stopped **before liquidity-tool implementation**.
No Alpaca request, August/November capture, liquidity calculation, new ledger
decision, sampling amendment, cohort freeze or audit execution occurred. The
existing daily contract and verified historical SIP entitlement are unchanged.

The new immutable evidence store verifies **12 records, VERIFIED**. The linked
review record is `0ab35d73ec1e46598b25087df1db20e8`; its canonical review hash is
`526b3e49b6998914a4d1af15819e0fa3f79a6132c195482f4cd71a9b1b6c5766`.
Full source references and temporal exclusions are in
`research/acquisition_candidate_001_may_structural_20261001.json`.

**Next permissible action:** obtain the named May structural interval evidence
for candidate #1 only. Once that requirement is satisfied, implement and test
the already specified fixed May-window owner-local capture. Candidate #2 remains
blocked. No continuity claim or source-rule amendment was made here.
