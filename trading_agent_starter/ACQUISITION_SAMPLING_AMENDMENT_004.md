# ADR001-ACQUISITION-004 — acquisition-only SEC filing-frame sampling

Status: **REGISTERED; SCREENING NOT STARTED.** This is one sampling amendment,
implemented by `research/acquisition_frame_registration_004.json`, version
`adr001-acquisition-frame-v1`.

Registration SHA-256 (exact file bytes, including final LF):

`c4dfc00f202ef93a3b87cfb8928f75c4a7e152db6a3253260187bdb9b0173409`

The adjacent `.sha256` file and the offline protocol module pin the same digest.
Changing the seed, hash, domain, encoding, version, frame or eligibility contract
invalidates the registration and dependent ledgers/scopes. It requires an explicit
amendment; a new hash alone is not authorization. No real candidate priority has
been calculated or screened in this milestone.

## Scope and preserved contracts

This amendment authorizes a **sampling design for acquisition/provenance
feasibility only**. It replaces the requirement to establish global monthly
top-500 membership for this acquisition sample with the preserved SEC filing
frame. It does not change Amendment 003, selector v3, the eventual ADR economic
universe, or any prior amendment, manifest, review, exception ledger or checksum
index. The superseded cohort remains superseded and unchanged.

The future acquisition sample cannot be described as the full market universe,
the ADR top-500 universe, representative live opportunities, or evidence about
alpha, opportunity frequency or market-wide performance. The filing frame and
two-event requirement condition the sample on filing behavior. A seeded order
prevents discretionary issuer preference; it does not remove that conditioning.

Only the global top-500 membership requirement and its exchange-wide population
reconstruction prerequisite are waived. All issuer-specific dated eligibility
and economic requirements remain. The economic selector continues requiring the
complete dated monthly population, most-liquid eligible class, and top-500 rank.
The new registration is rejected by selector v3 and must not be supplied to it.

## Frozen frame and priority

The frame is the complete **preserved** calendar-2025 SEC original-10-Q index
frame: 17,289 distinct original index pairs and 5,974 distinct CIKs recorded in
the existing inventory. Counts describe filers, not eligible companies. All four
SEC `2025/QTR1` through `QTR4/master.zip` URLs, raw hashes and evidence record IDs
are pinned in the registration. The preserved normalized inventory is bound to
SHA-256 `294c2354af6ca69d8b875088115184c583cc058947643b7ea2a8762f03fcf865`.

Before any future screening, verify the archive objects, normalized inventory,
pair set and CIK set against those bindings. Exact `10-Q` records only; `10-Q/A`
does not qualify. Deduplicate identical `(CIK, accession)` pairs while preserving
source references; conflicting duplicates block. Missing archives, mismatched
sets or counts, or unresolved calendar-year acceptance boundary discrepancies
block. Do not reconstruct a smaller frame from successful metadata downloads.

Priority is frozen now, before real eligibility or source screening:

- Seed, exactly: `ADR001-ACQUISITION-004/calendar-2025/issuer-priority/v1`
- Hash: SHA-256, all 32 bytes.
- Domain, exactly: `adr001-acquisition-cik-priority-v1`
- CIK: positive identifier, zero-padded to exactly ten ASCII decimal digits.
- Message bytes: `ASCII(domain) || 0x00 || UTF-8(seed) || 0x00 || ASCII(cik10)`.
  No BOM, whitespace, newline, trailing delimiter or locale-dependent conversion.
- Ordering: unsigned lexicographic ascending digest bytes, equivalent to sorting
  lowercase 64-character hexadecimal digests. Assign one-based priority ranks.
- A collision between different CIKs blocks; no numeric-CIK or manual fallback.

There is no ascending-CIK sample, seed search or reroll. Acquisition success,
source availability, MD&A, prior disclosures, market reaction, future returns,
post-event prices and manual issuer preference cannot affect priority or passage.

## Eligibility and event selection

For each screened issuer, establish the complete relevant set of its own dated
share classes. Each qualifying class must be common stock of a domestic operating
company with primary XNYS or XNAS listing. Exclude funds, ETFs, ADRs, shells,
debt, preferreds, warrants, rights, units and duplicate issuer classes. Source
evidence must establish issuer CIK, share-class lineage, historical ticker,
listing interval and classification. A subsidiary never inherits a parent's
ticker. One excluded security does not prove the issuer has no eligible class.

Retain the Amendment 003 acceptance-month rule: cutoff at 00:00 New York on the
first calendar day of the month; exactly the immediately preceding 60 completed
session-date bars from the registered calendar. All classes that could affect the
most-liquid eligible class choice must be resolved. The chosen class must remain
valid at SEC acceptance and simulated action; no within-month class substitution.

Use only the unchanged Amendment 003 metric:

`median(previous 60 session-date Alpaca SIP 1Day raw close × Alpaca SIP 1Day raw volume)`

Request `timeframe=1Day`, `feed=sip`, `adjustment=raw`, `asof=-`. Preserve dated
ticker binding and provider-native New York calendar-day semantics. This is not
RTH-only volume, official closing-price dollar volume or actual traded notional.
Daily volume can include trades, including extended-hours conditions, that do
not update daily prices. Use Decimal arithmetic; the median is the mean of the
middle two products. Require median at least $20m and preceding-session daily
close at least $10. Choose the most liquid qualifying class per issuer, breaking
class ties by stable `research:` instrument ID. No class-source convenience rule.

A missing required bar is UNRESOLVED, not illiquid. Proven insufficient listing
history may establish ineligibility; download failure cannot. Invalid IEX,
adjusted, mapped-symbol or RTH-relabeled inputs cannot justify replacement.

After issuer/class/month eligibility, require at least two eligible original
10-Q events with SEC acceptance in calendar 2025, America/New_York. Resolve the
candidate's complete original-event metadata and select the earliest two by SEC
acceptance instant, then accession. An unresolved event that could precede or
change the chosen pair blocks. No amendment filings, content filters or outcomes.
Retain the registered provisional 600-second action offset and `choose_action`
session rule; neither represents a frozen economic latency deadline. A future
manifest must include SPY context for every distinct simulated action timestamp.

## Ledger and stopping rules

Process only a contiguous prefix of frozen CIK priority. Each decision records:
registration hash, priority rank/digest, CIK, eligibility status, exact reason
code and exclusion fact or unresolved field, and evidence record IDs/hashes.
The initial empty ledger registration is preserved separately; future decisions
belong in the append-only evidence store, with prior versions retained.

An issuer may be passed only with source-backed proof of ineligibility. Proof
must exclude other possible classes/events where they could change the decision.
An unresolved higher-priority issuer **blocks completion**. Conflicts or false
claims also block. A claimed eligible or ineligible row without evidence is
invalid; source failure is never an exclusion fact. Stop once exactly 25 issuers
and their earliest two eligible events are established. No extra candidates for
subsequent success-based replacements.

The small offline helper checks registration integrity, hash priority, dated
issuer/class binding and ledger protocol. It does **not** verify the truth of
linked evidence, establish eligibility, build/freeze a cohort or authorize an
audit. Its synthetic “protocol complete” state explicitly requires source
validation. Source review must verify object bytes, provenance, factual grounding,
class completeness, session-date bars and event ordering before using a decision.

## Exact next bounded workflow — not started

The only CLI added now is a local registration check. From
`trading_agent_starter`, including on Windows:

```text
python -m agent.acquisition_registration --verify-only
```

It uses no credentials or network and verifies the registration and protected
prior artifact hashes. It neither derives real CIK priorities nor screens issuers.

On later authorization, the bounded candidate-screening workflow is:

1. Run that verification; verify the four preserved SEC objects and normalized
   inventory. Reconcile the complete original-pair/CIK set. Missing or inconsistent
   inputs stop the workflow before screening.
2. Derive the full CIK hash order offline using `priority_order(ciks, raw)` after
   frame verification. Preserve its canonical JSON bytes and SHA-256 together
   with the frame and registration hashes. No real priorities are frozen now.
3. Review **one candidate maximum**: the first undecided CIK in that order. Use
   captured official evidence first. Resolve original acceptance metadata and
   dated issuer/class/listing facts; only where needed collect the relevant
   Amendment 003 class/month daily inputs. No whole-universe download or MD&A.
4. Verify the source-backed review and append one exact ledger decision. An
   unresolved field stops immediately; document instrument/date/field/source.
   A proven exclusion is retained, but this bounded run still stops after one
   candidate. Future authorized continuation resumes at the next permissible
   priority; there is no fixed total candidate budget that permits skipping.
5. Validate the ledger prefix with `check_ledger_prefix(ciks, entries, raw)`.
   Preserve source review and result separately. Do not treat that protocol
   check as substantive evidence approval. No cohort freeze or audit execution.

There is intentionally no automatic screening command in this registration-only
milestone. The workflow above specifies the later bounded evidence work without
shipping or running an unreviewed acquisition pipeline. Liquidity research,
membership research, returns, forecasting, LLM research, optimization, allocation,
orders and live trading are outside this amendment's execution scope.
