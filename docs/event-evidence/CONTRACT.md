# Event evidence envelope and scientific rules

Normative design version: `event-evidence/1.0.0-design`. The
[schema](event-evidence.schema.json) defines JSON shape. The rules below also
apply: passing JSON Schema validation never grants admission. A future adapter
must qualify these rules against source-grounded fixtures before use.

## Record boundaries and identifiers

An `event_id` identifies a logical occurrence (for example, the September CPI
release, a particular FOMC decision, or an award announcement). An `evidence_id`
identifies one immutable source version. Assign both deterministically within a
frozen namespace policy, independent of returns and model output. Maintain the
original source identifiers even when internal IDs exist. Never identify a story
solely by title, ticker, content hash or calendar date.

`source` retains publisher versus distributor, document/story/accession/series
identifier, native version identifier if supplied, canonical URI, language,
transport and qualification reference. A missing provider version stays null;
each changed raw payload still gets a new internal evidence version. The full
content manifest is separately hashed at freeze time; do not require a hash to
contain itself. A hash proves byte identity, not historical availability.

One release may have multiple `facts`, each with measure/series ID, decimal string
or text/missing marker, units, frequency, seasonal adjustment, reference period,
vintage, source span and role. Keep `prior_as_printed` (possibly revised in this
release) separate from `prior_previously_known`. Preserve displayed precision;
do not treat rounded percentages, annualized rates, index levels or dollar
amounts as interchangeable. Missing values are never zero. Table/series ID,
base year, definitions and classification changes belong in the measure's
versioned source dictionary referenced by qualification.

## Clocks

Every clock is present as an object, including when unknown. It records native
value, native precision, source timezone/offset, UTC conversion when justified,
clock uncertainty, semantic basis, evidence span and explanation. Preserve the
original string even when normalized UTC exists. An unknown timezone is null;
never default a source date to UTC, Eastern Time or the workstation timezone.

| Clock | Meaning and prohibition |
| --- | --- |
| `economic_effective` | When policy/action legally or economically takes effect. This can precede or follow disclosure. A macro reference month/quarter is instead retained in each fact's `reference_period`; it is not release time. |
| `scheduled_publication` | Announced calendar time, preserved with its own version/announcement evidence. This is a plan, not proof of actual release. |
| `official_publication` | Publisher's release assertion for this version, with channel semantics. Public-inspection filing, website posting, wire transmission and SEC dissemination are different channels; use separate evidence records when they differ. |
| `first_machine_observable` | Earliest **evidenced** machine observation on a named channel/observer. No claim of globally earliest availability. Provider logs may establish this for their channel, never for ours. Unknown if only a release label exists. |
| `first_receipt` | First actual receipt of this version by our collector; logs identify collector/session and receive stage. Do not copy a provider clock here. Headers arriving before the body cannot establish possession of the complete payload. |
| `source_revision` | Publisher/provider update, correction, revision or withdrawal time for this version. Can be unknown even if changed bytes are discovered. Never substitute an economic period or document retrieval time. |
| `retrieved` | Actual acquisition/backfill time of the retained bytes. Required known UTC instant in any retained evidence record. Later requests append retrieval-log entries, without replacing the first acquisition record. |
| `ingestion_completed` / `verification_completed` | Actual completion of the corresponding processing stage on these bytes, under the recorded software/configuration. Unknown completion is not permission to use unfinished features. |

Date/month/quarter/year values have **no UTC instant**. No midnight assignment,
end-of-day invented timestamp or arbitrary Eastern offset is permitted. A minute
label is minute-precise, even if its UTC representation uses `:00` as a coordinate:
admission must treat the whole possible minute plus uncertainty as its range,
not the coordinate as a measured second. Ambiguous DST folds, missing timezone
and undocumented truncation remain unresolved until independently corroborated.
Use IANA timezone and tzdb version in conversion lineage; retain explicit source
offsets and conflicts. UTC strings end in `Z`; uncertainty is never silently zero.

`native_value` for an effective interval can be a documented native range with
its actual precision. Interval inclusion, endpoints and units are specified by
the source dictionary; do not derive interval continuity from sparse dates.
`not_applicable` needs a reason (for example, no scheduled publication for an
unscheduled story); it is not a substitute for missing evidence.

## Raw evidence and lineage

Retain original response/document bytes and all material attachments, content
type, byte length, SHA-256, immutable private storage URI and rights reference.
Preserve a source transport/receipt log and relevant response headers separately.
HTTP `Date`, `Last-Modified` and ETag are transport metadata, not independently
proven first-publication or receipt clocks. Keep source precision on every clock.

Retain authoritative legal renditions separately from discovery XML/HTML; preserve
both public-inspection and published versions. Parsed text, OCR and translations
are derived artifacts with hashes and software/config lineage. Text normalization
cannot replace original bytes. Source spans bind to a hash and locator (page,
table, paragraph, JSON pointer), optionally raw byte offsets `[start,end)`; offsets
must match their artifact and encoding. A derived span must trace back to the raw
document. Verify numeric units, period and entities against those spans.

Rights state, permitted purposes, retention duration, termination replay and
redistribution restrictions travel with evidence. Null `retention_until` means
unknown/unset, **not** perpetual rights. Immutable here means version-preserving
while lawfully retained. A legal deletion requirement overrides storage; keep a
permitted tombstone/hash/rights record, mark reproducibility lost and exclude the
affected experiment from a reproducible claim. Never put licensed raw news in
Git or provider prompts by convenience. If raw retention or authorized replay is
not permitted, do not admit the feed to this reproducibility contract.

## Admission

There are three explicit modes, each pinned in a later experiment registration:

1. `prospective_observed`: use actual receipt and completed stages. Establish
   clock calibration, collector identity, full-body receipt, monotonic durations,
   outage logs and sequence/reconciliation evidence. Keep provider publication
   and machine-observation clocks separately. A source may lack an exact official
   release label and still support a **receipt-based** prospective study if its
   identity, version and actual receipt are qualified; no publication-speed claim
   follows. Never manufacture an earlier official or provider observation.
2. `historical_publication_proxy`: only a separately registered exploratory study
   may use a qualified original historical version with a corroborated publication
   clock plus a predeclared latency scenario. Receipt stays unknown if unobserved.
   Store the assumption in the registered policy, not as a source clock. This
   cannot certify prospective readiness, exact historical executions or absence
   of historical LLM weight contamination.
3. `catalog_only`: discovery, schedules, date-only vintages, latest-only APIs or
   unresolved rights/version/clock cases can be stored for qualification but
   cannot enter predictive features. Unknown receipt does not itself make a
   calendar an intraday observation.

For a cutoff `t`, the future admission process must:

- Resolve source qualification for the exact family, channel, dataset edition,
  fields, period, rights and declared mode. Require retained raw hashes/spans;
  retrieval success alone is insufficient. Quarantine conflicting timestamps,
  missing versions, unknown rights, unverifiable links and impossible clock
  order; preserve failures and reason codes.
- Compute availability from the **latest required causal completion**, never the
  earliest clock. In observed mode this includes full receipt, ingestion,
  verification and feature/link completions required by that arm. If a relevant
  publisher/provider clock demonstrably occurs later, resolve the conflict or
  use the later bound; a suspected embargo leak cannot be silently admitted.
  Use a conservative upper bound from native precision and clock uncertainty.
  In historical proxy mode use only the registered publication/latency scenario
  and original-version evidence; actual later retrieval/processing stays later
  and is not misrepresented as a historical observation.
- Require every input dependency, including a prior release, consensus snapshot,
  deduplication rule, entity/exposure link and preprocessing fit, to be admissible
  as of `t`. Equal coarse timestamps do not prove ordering: require complete
  availability strictly before the decision cutoff or a documented finer receive
  sequence. Otherwise abstain. Apply the existing ADR's >1-second clock-error
  abstention for any timing-sensitive work governed by that rule; this design
  creates no waiver.
- Freeze one common event/opportunity inventory and input bundle for all arms.
  Deadlines are registered before outcomes. A late/missing extraction is a costed
  abstention; it cannot shift rivals' action times or delete their opportunities.
  Add processing/decision records by reference in a separate experiment manifest;
  the evidence envelope itself never chooses trades or a strategy.
- Choose the latest **admissible** version, not today's version. Save the exact
  evidence/link/feature IDs used. Never mutate earlier admissions when a later
  correction, duplicate cluster or name mapping arrives.
- Reconcile expected calendars/agency document inventories/feed sequence counts
  with successes, failures, withdrawn items, no-change releases, outages and late
  arrivals. Unknown completeness is explicit. A calendar cancellation is a new
  evidenced event; a failed poll or empty query is not evidence of no event.

All current examples are synthetic and quarantined. Schema validation alone
does not implement these causal checks. Each actual admission must reference its
reviewed qualification record and separate registered experiment policy.

## Version history

Append every changed source version, even if a story ID or URL stays constant.
Store observed content hashes and native revision sequence/time, including
unknown revision clocks. An economic reference-period revision is a new
publication of facts about an old period; it never changes the old feature row.
Benchmark, seasonal-adjustment and classification revisions keep their distinct
causes and new definitions. A same-release revision to prior months is available
only with that release, not at those months' original release times.

Use directional relations (`updates`, `corrects`, `supersedes`, `retracts`,
`duplicates`, `republication_of`, `public_inspection_of`, `same_release_as`), with
target evidence ID, time the relation became evidenced, and source spans. Do not
infer a correction from similar text; unknown targets remain quarantined pending
resolution. `record_kind` states the current version's role; relations carry its
specific links. A revision/correction/retraction requires the appropriate target
link and known-as-of relation evidence before affecting an as-of view. Reject
cycles and contradictory predecessor sequences; preserve the raw conflict.

A retraction/withdrawal is a tombstone with its own payload or feed message and
receipt time, not deletion of historical knowledge. Before its admission, the
earlier version remains what was known. Afterward expose the tombstone and prior
lineage; the later experiment must predeclare how features abstain or respond.
Do not retroactively remove losing opportunities. Removal notices with unknown
publication time act only from observed receipt, not original story creation.

Transport repeats with identical source/version/hash are idempotent receptions:
one evidence version, append receive-log entries. Reused source version ID with
different bytes is a conflict/new internal version. Syndicated/reworded/translated
stories preserve publisher and distributor provenance even when clustered. Freeze
deterministic hash/ID/text-similarity deduplication and thresholds on training
only; clustering at cutoff may use only then-known versions and links. Later
reprints cannot move first observation earlier or increase a past event count.
Keep economic-event clusters separate from story duplicates; a story discussing
two actions need not define two independent trading opportunities.

## Entity links

Each mention-to-entity/class/exposure edge is an independently sourced temporal
claim: namespace and stable ID, native mention, relationship, valid interval,
knowledge/availability time, method version, evidence spans and resolution state.
Retain one-to-many/ambiguous candidates. A null entity/class or uncertain link is
unresolved, never evidence of no exposure. Link completion is an input dependency.

As of the historical decision, separately establish issuer, subsidiary/parent,
award-recipient UEI or other agency ID, sanction subject, share class/listing and
ticker validity. A CIK identifies a filer, not a traded class; matching a current
ticker/company name/ISIN alone is insufficient. Preserve identifier changes,
renamings, mergers, spin-offs, ownership percentages and dates. Award obligations,
ceilings, options and consortium shares cannot be mapped automatically to parent
revenue. Sanction-name similarity is not a resolved legal-entity match.

Exposure links (sector/industry/product, tariff HS code, country revenue, supply
chain or contract materiality denominator) require disclosures/classifications
already public at cutoff. Preserve their versions, definitions and uncertainties;
do not use today's profiles, survivor lists or later-reported business segments.
Macro announcements may link to a predeclared broad instrument without inventing
a causal issuer graph. Missing exposure can cause an abstention or a registered
missingness feature, never hindsight assignment to subsequent movers.

Amendment 005's narrow retrospective **structural acquisition** allowance does
not backdate predictive exposure, issuer releases, news, numeric facts, consensus
or actionability. Keep structural valid-state evidence and then-known predictive
links separate. This document neither broadens that exception nor registers an
alternative historical-universe path.

## Design acceptance cases

| Case | Required result |
| --- | --- |
| Date-only ALFRED vintage and current backfill | Retain native date and today's retrieval; unknown receipt; quarantine for intraday observed mode. |
| Unchanged CPI release absent from a vintage-date list | Retain calendar/official-release event; do not silently drop the opportunity. |
| Later seasonal correction to an earlier CPI month | Append correction and linkage; original cutoff view remains unchanged. |
| Rule filed at 08:45, served online later | Separate filing assertion from online availability/our receipt; no trade timestamp derived from filing alone. |
| FOMC meeting followed three weeks later by minutes | Two publications with different event roles; no minutes at decision date. |
| Current article carries old creation and recent update | Old text unknown unless archived; no corrected body at creation time. |
| Duplicate delivered after reconnect | Preserve receptions, count the source version once; bounded replay cannot erase outage gaps. |
| Withdrawal discovered tomorrow | Keep yesterday's admitted version and today's tombstone; no retrospective deletion. |
| Award transaction signed before public announcement | Economic/action date separate from announcement; no announcement at signing date. |
| Old name maps only through today's parent/sector graph | Link unresolved at historical cutoff; do not infer exposure. |
| Feature verification finishes after common deadline | Costed abstention for that arm; unchanged shared opportunity denominator. |
| Unknown source/receipt timezone or same-minute ordering | No exact-instant claim; quarantine until corroborated. |
