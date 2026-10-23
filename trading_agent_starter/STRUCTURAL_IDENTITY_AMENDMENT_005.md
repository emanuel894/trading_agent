# ADR 001 Amendment 005 — retrospective structural valid state

Scope: `ACQUISITION_PROVENANCE_FEASIBILITY_ONLY`. This single amendment changes
only the structural identity temporal evidence rule inherited from 003 by 004.
It does not edit either original registration, the economic selector, economic
thresholds, monthly top-500 universe, seed, priority, ledger ordering, event
ordering, no-replacement rule, or current candidate decision.

Three clocks must remain separate:

1. **A — valid/effective time:** when the issuer/share-class/ticker/listing fact
   actually held historically, at the source's documented resolution.
2. **B — source publication/capture/revision:** when the source published,
   captured or revised the fact, whenever such metadata is supplied. Preserve
   revisions; unknown first-publication time remains unknown.
3. **C — retrieval:** when our system actually acquired the evidence. Later
   retrieval is allowed. Never use C as historical knowledge time or derive
   `known_at`/`available_at` from a request's historical date.

For this acquisition purpose, a source-backed retrospective reference record
may establish historical structural valid state even when historical first
publication/knowledge time is unknown. This requires documented provider/source
semantics explicitly representing historical valid/effective state, historical
membership, historical symbol/class state, or point-in-time reference state.
A historical date parameter alone is insufficient. Current-only data and a
later SEC-derived retrofill without documented historical-valid-state semantics
cannot establish earlier structural state.

The exception covers only issuer identity, CIK/share-class lineage, historical
ticker, security type, primary listing/exchange and structural listing state/
interval. It never establishes historical availability of disclosures, MD&A,
predictive features, quotes, trades or market data; halt/status knowledge;
live actionability; or prospective readiness. Their decision-time availability
guards remain intact. Later updates do not rewrite earlier evidence versions.

Date-only evidence stays date-only. Daily state cannot become exact intraday
state by assigning midnight timestamps. Unresolved day-boundary, carry-in or
intraday transitions, lineage, and issuer-class completeness remain UNRESOLVED.
Exact-instant requirements need independently source-grounded exact validity;
corroboration must bind the same issuer, class and field value.

Implementation is a separate acquisition structural validation helper. It
verifies registration/protected hashes, evidence references and source-grounded
review spans. A reviewer must still establish the truth and completeness of
the source's semantics and facts. Hashes and checked review fields are not
independent proof. It does not call the economic selector, create an eligible
ledger row, select events, or authorize an audit. Nonstructural evidence has
no retrospective exception. The existing 004 ledger protocol remains binding.

The registered pilot is owner-local only: four GET requests to
`https://api.massive.com/v3/reference/tickers`, dates 2025-02-04, 2025-04-30,
2025-05-01 and 2025-05-09, with ticker FMBH, market stocks, active true and
limit 10. No CIK/type/exchange/FIGI prefilter. `MASSIVE_API_KEY` is sent only
in an Authorization header. No retries, redirects, pagination following,
automatic source admission or eligibility decision. The pilot cannot resolve
all 60 sessions, complete class lineage, or exact intraday validity.

Candidate #1 remains rank 1 / CIK 0000700565 / priority digest
`00004f5851fcd2d7cd1ba3e1dfe1e225fa7d8b4fd50a675cc1bc44a552c0f2e6`.
Its ledger decision remains UNRESOLVED. Candidate #2 is outside this milestone.

Canonical registration: `research/structural_identity_registration_005.json`.
Its SHA-256 is pinned by the validation module and companion `.sha256` file.
Any change to this amendment/registration requires an explicit new version;
all prior artifacts remain reproducible and unchanged.
