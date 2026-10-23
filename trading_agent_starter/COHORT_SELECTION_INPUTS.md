# Source-backed inputs to amendment 002

`agent.cohort_selector` is an offline constructor, not an acquisition audit or an
automatic security-master generator. It accepts only registration
`6d930c58a921bd771ba7a7a43fa767ce0d8fde746bbc88adab73dde3a2d60091`.
Source classification and completeness need documented review. A hash validates
bytes; it cannot prove that a population is complete or a classification is true.

The input JSON has exactly these top-level fields:

| Field | Contract |
| --- | --- |
| `version` | `adr001-universe-inputs-v1` |
| `sources` | Records with `id`, relative `path`, SHA-256, `source_url`, `owner`, and timezone-aware `available_at`. Raw evidence must exist beneath `--root` and hash correctly. Availability describes the underlying historical information, never a fabricated historical download time. Preserve actual retrieval times in the evidence store. |
| `population_by_month` | Keys `2025-01` through `2025-12`. Each contains `complete`, `reviewed_by`, `rationale`, `evidence_ids`, `instrument_ids`. The reviewer must establish a complete dated candidate population, including changes/delistings; current or successful-download-only rosters are insufficient. |
| `identities` | Dated nonoverlapping class intervals, described below. |
| `calendar` | `complete`, `reviewed_by`, `rationale`, `evidence_ids`, `sessions`. Each session has `date`, timezone-aware `open`/`close`. Cover all prior 60-session windows and subsequent action opportunities through early January 2026. Explicitly include holidays, early closes and January 9, 2025 closure. |
| `bars` | One record per research instrument and required session: `date`, `instrument_id`, historically bound `ticker`, Decimal-string `close` and integer Decimal-string `volume`, `feed: sip`, `session: RTH`, `adjustment: raw`, and `evidence_ids`. All 60 immediately prior sessions are needed. No IEX, missing-day fill or implicit symbol-history joining. |
| `filing_inventory` | `complete`, `reviewed_by`, `rationale`, `evidence_ids`, `indexed_originals`, `events`. Indexes cover full calendar 2025; each original index row has `cik` and `accession`. Acceptance metadata is required for every indexed original of every issuer appearing in the monthly top-500 universe, before the 25-issuer sample. Metadata for other filers is optional. |

Each identity row contains exactly:

`instrument_id`, `cik`, `issuer`, `lineage_id`, `share_class`, `ticker`, `exchange`,
`valid_from`, `valid_to`, `known_at`, `security_type`, `domestic_operating`, `shell`,
`fund`, `adr`, `listed_since`, `evidence_ids`.

CIKs have ten digits. IDs start with `research:` and are internal identifiers.
Intervals are half-open `[valid_from, valid_to)`; their endpoints and `known_at`
must be supported by dated sources. Do not set a future interval endpoint using
an announcement that was unknown at that decision time. Boolean classification
fields must be explicit; null is unresolved. Most-liquid-class selection is per
issuer, with one qualifying class per month. An actual recent listing can be
ineligible for insufficient history; a missing historical bar cannot be treated
as proof of a recent listing.

Each event has exactly `cik`, `accession`, `form: 10-Q`, `accepted_at`, `report_date`
and `evidence_ids`. Amendments are excluded. No MD&A, prior-disclosure result,
acquisition-success flag, return, signal or manual-priority field is accepted.
All events used must reconcile to the original SEC index inventory. Incomplete
metadata stops construction; it never selects the next convenient issuer.

With a **completed and source-reviewed** input file, from `trading_agent_starter`:

```powershell
.venv\Scripts\python.exe -m agent.cohort_selector --inputs runs/cohort_correction_002/selection_inputs_complete.json --root . --store runs/cohort_correction_002 --output research/cohort_2025_corrected_frozen.json
```

That complete input file does not currently exist. The preserved
`selection_inputs_incomplete.json` is an inventory of actual missing evidence,
not a fill-in assertion template that may be marked complete without sources.
Keep raw market data and private evidence outside public Git. No credentials
belong in any input file or evidence record.

On success the constructor freezes an immutable `historical-cohort-v2` manifest
and records the active scope. It does not call `evidence_audit` or the dated gate.
The later scoped packet supplies `selection_inputs: {path, sha256}` and its
`frozen_manifest` reference. The dynamic gate rebuilds selection against those
inputs, checks the active registry, then evaluates the existing historical
requirements. Scoped review hashes must refer to this new scope.

The registry plus evidence store refuse a second freeze for this registration,
including a different output filename/store. A failed write is a recoverable
administrative failure, never authorization to resample. Preserve the store and
resolve the partial write explicitly. Any substantive input/universe/scope change
requires a documented amendment and new scoped reviews.
