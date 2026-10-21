# P0-A evidence report

Decision: **P0A_INCOMPLETE**. External spend **$0**. No SEC, model, market or
broker requests; no credentials, protected science edits, alpha inspection or
continuous capture. Registration and P0-B proposal: [REGISTRATION.md](REGISTRATION.md).

## Sources and inherited G4 evidence

Reconciled live [Issue40](https://github.com/emanuel894/trading_agent/issues/40),
draft [PR45](https://github.com/emanuel894/trading_agent/pull/45) at
`46737267dac2f15ab45bb032490cefebc79b39ea`, and merged
[PR43](https://github.com/emanuel894/trading_agent/pull/43), foundation
`051c6c2d99f1ef6cfefd082ff646ed1c1cd88a09`. Also read Issues29/32/35/38/44,
canonical policy/operating skill, ADR001 and Amendments003/004/005.
[G4 final CI39616292183](https://github.com/emanuel894/trading_agent/actions/runs/39616292183)
is completed/success; the final Issue40 supplement supersedes only pending CI.
The completed six-job/seven-attempt measurement is **not repeated**.

The directory `runs/issue40-g4/live-20261021` is unavailable in this workspace.
Directory searches under `/workspace` and `/tmp` and exact object-filename searches
found neither retained original object. Both remain excluded:

| Representation, same accession 0000950170-25-067613 | Expected bytes | Expected SHA256 |
|---|---:|---|
| Complete submission | 30,606,368 | `306a47c1a8a325f173ef8a63b6669a0ff48a8dad2053aa00c4d7a9262f8d17a3` |
| Direct primary | 7,306,025 | `7813247ab8b09da0683ca568373aef17da4881984b9488f2eb8bd10e2edf8d56` |

These anchors come from committed G4 evidence; **their raw integrity cannot be
reverified here**. No replacement bytes were downloaded. Authentic provenance-
verified sample coverage: **0/12**. Two representations would count as one filing.
No authentic boundary/manual assertion review was possible. The runner first
verifies the retained receipt, existing append-only chain and each bound object
if that exact local store is later restored; it opens G4 storage read-only.
This verification mechanism is fixture-tested, not a successful genuine replay.

G4's **24.60776813099983 seconds** measures that diagnostic acquisition session,
not document-to-LLM completion. Unqualified physical clock uncertainty, JSON
acceptance versus unzoned index/SGML acceptance, direct/index/embedded size and
historical version/receipt conflicts remain unresolved. P0-A qualifies none of them.

## Implemented and bounded

`agent/p0a_mda.py` extends the existing VisibleText visibility policy with UTF-8
byte mapping, strict nesting, cell boundaries and entity handling. It separates
original primary TEXT from submission exhibits; removes hidden iXBRL while
retaining visible facts; marks tables separately from prose; excludes unrelated
text outside the unique Item2→Item3/4 boundary. It preserves every original source
byte and immutable derived view in the existing EvidenceStore. Whitespace-only
normalization preserves case, numbers, punctuation and Unicode. Generated
separators have null raw spans. Chunk IDs and text hashes are deterministic;
concatenating all chunks exactly reconstructs normalized MD&A.

The `p0a-v1` strict contract requires source-bound identity, exact passages,
chunk-relative containment and explicitness/uncertainty/statement type. The
validator rejects extra/missing fields, invalid identities/JSON/quotes/spans,
unsupported assertions and numerical confidence. A matching quote establishes
citation grounding, **not semantic support**. The frozen prompt is inert and has
never been sent to a model. No inference adapter or paid route was added.

Limits: conservative allowlisted HTML and CSS subset; strict nesting can reject valid HTML with
omitted end tags. CSS stylesheets, active markup, unqualified CSS (including opacity/font size/colors) and inert template content are rejected. Only exact qualified visibility rules and four narrow cosmetic property/value sets are accepted. Heading
variants, TOCs and complex tables may abstain; no universal SEC parser claim.
The section's minimum length and explicit closing heading do not independently
prove authentic document completeness. Boilerplate *inside* MD&A is retained
as source text; semantic boilerplate classification is NOT_MEASURED. Authentic preparation requires an explicit source EvidenceStore resolver: verified chain, existing successful observation, original bytes/hash/size, URI and representation must agree. An SEC-looking URL or arbitrary provenance string cannot admit a source. Primary
accession is provenance-bound; conflicting native DEI form/CIK is rejected,
but missing native identity is not invented. No human or population qualification.

## Measured fixture results

Fixed selection: [fixture_selection.json](fixture_selection.json), frozen before
processing; all six named synthetic fixtures, sorted lexicographically. No issuer
selection or financial outcomes. [measurement.json](measurement.json) is the
final post-review v2 run; [measurement-review-v2.json](measurement-review-v2.json) retains the first v2 run; [measurement-accounting.json](measurement-accounting.json) retains the intermediate accounting run; [measurement-initial.json](measurement-initial.json)
retains the first six-attempt run. All four ran the same selected cases, not additional
independent observations. All attempts and three intended rejections per run are
preserved. No per-attempt retries or manual repair of fixture source contents.

| Fixture | Result |
|---|---|
| Simple nested heading | PREPARED_NO_INFERENCE |
| Long nested HTML/iXBRL, entities and table cells | PREPARED_NO_INFERENCE |
| SGML original with unrelated exhibit | PREPARED_NO_INFERENCE |
| Duplicate/ambiguous sections | Rejected: MDA_BOUNDARY_MISSING_OR_AMBIGUOUS |
| Missing end heading | Rejected: MDA_BOUNDARY_MISSING_OR_AMBIGUOUS |
| Prompt injection | Rejected: SUSPICIOUS_DOCUMENT_CONTENT |

Expected outcomes **6/6**, valid-case preparation **3/3**, exact chunk
reconstruction/hash reproduction **3/3**, unexpected failures **0**, preserved
deliberate failures **3/6**. These are synthetic engineering counts, not authentic
extraction or model-quality estimates. Material assertion support and manual
intervention on authentic filings are NOT_MEASURED, not zero-error rates.

Corrected run, Python3.12.14 on Ubuntu with tracemalloc enabled: valid fixture
median **0.045153s**, maximum/nearest-rank descriptive p95 **0.113064s** (n=3).
These durations include durable source/derived writes and chain verification,
exclude the final timing-receipt append and reproduce neither source delivery nor
LLM processing. Cold/warm, disk-cache and host-load effects are uncontrolled;
the initial median0.084961s/max0.417196s and intermediate median0.068189s/max0.180863s are preserved, not hidden. The first v2 run (median0.111108s/max0.965288s) overlapped full-suite verification; the final code-bound run ran before full-suite checks. CPU and wall measurements are separate. All four sessions are preserved; no favorable timing is selected from a fixed-code repeat.

Each attempt records identity, parsing, MD&A boundary extraction, normalization,
chunking, validation and persistence separately. Unreached stages are NOT_RUN;
LLM inference is NOT_MEASURED with null duration. CPU time and unclassified
overhead are separate. Persistence includes serialization, original/derived/failure
writes and integrity verification. The initial report omitted an explicit overhead
field and mislabeled a wall-time projection as CPU; the corrected runner accounts
for overhead and labels wall time accurately. Initial data is retained as-is.


Mean stage durations for the final three valid **synthetic** preparations (seconds):

| Stage | Mean seconds |
|---|---:|
| Identity verification | 0.000210 |
| Parsing | 0.017737 |
| MD&A boundary extraction | 0.002378 |
| Normalization | 0.001496 |
| Chunking | 0.000123 |
| Inference | NOT_MEASURED |
| Preparation validation | 0.000096 |
| Persistence/serialization/integrity | 0.040451 |

Unattributed overhead is explicitly recorded per attempt; these stage means do
not include the final timing-receipt append. Real LLM validation is NOT_MEASURED.

The final local store verifies **19 records**, chain head
`e304679c25e59036a7db8dca4a425962f09b4c05c6bcf09f2d786bfb6d6ab061`.
Derived preparation hashes reproduce within each session; review repairs intentionally versioned the algorithm from v1 to v2, changing preparation/chunk hashes. Earlier hashes and measurements remain preserved. Original and derived
objects are under ignored `runs/p0a-20261021-{a,b,c,d}/evidence`; the Git packet retains
reports and fixtures, **not a durable hosted copy of those SQLite stores**.
The reports alone cannot reconstruct an identical timestamped evidence chain.

## Cost, resources and scaling

New external cost **$0**. Actual model input/output tokens, model price/cost,
inference quality/agreement/retry/schema/support rates, inference latency and
end-to-end LLM latency: **NOT_MEASURED**. No mock results count as inference;
empty-output integration tests exercise the validator only. No authorized usable
inference path exists in repository routing (actual model IDs/caps null, activation
disabled) or the managed environment's credential/capability inventory. Completing
that stage needs separate owner approval of one exact usable zero-spend route,
model/version, data destination, bounded calls/tokens and permitted configuration.
Paid calls/new credentials remain outside this mandate.

Traced Python allocation peak **1,431,707 bytes** (whole runner); RSS/OS peak,
physical storage durability, backup footprint and production capacity unmeasured.
Before final report output: **232,821 apparent /270,336 allocated bytes**, 13 files
in the run directory on overlay storage. Average successful fixture source+derived
payload **61,282.67 bytes**. Per-case source/derived sizes and CPU/wall stage timing
are in measurement.json. Allocation tracing adds overhead; these tiny documents
do not approximate the unavailable 7.3MB/30.6MB originals.

Linear **fixture-only projections**, no inference, metadata/backup expansion or
concurrency: 100/1,000/10,000 cases → **6.27/62.73/627.33 seconds** and
**6.13/61.28/612.83MB** source+derived payload. These are arithmetic estimates,
not production forecasts or evidence of scalability. Per-codepoint span storage,
repeated chain verification and serialization dominate scale; benchmark authentic
sizes before choosing compressed span runs or incremental validation. No architecture
redesign is justified by these fixtures alone.

## Validation, review and continuation

Baseline Python3.12.14:344 tests,335 pass/9 Alpaca-SDK skips. Existing dependency
environment `/workspace/audit-upstreams/test-venv`: **377/377 tests passed**, no
skips; `python -m agent demo` exited0. No dependency installation or upgrades.
Focused21 tests, then24, and final33 tests cover nested Size-cell-like structures, hidden tags,
entities, SGML/exhibits, conflicting form/CIK, truncation, schema/citations,
chunk loss/duplication, failures, idempotency and read-only provenance verification.
RED evidence is retained in `/tmp/p0a-red-{2,3}.log`; full output
`/tmp/p0a-full-1.log` (368 tests) and `/tmp/p0a-full-2.log` (375 tests), and `/tmp/p0a-full-final.log` (377 tests). Review defect RED reproductions are `/tmp/p0a-review-red.log` and `/tmp/p0a-css-red.log`. Protected-artifact comparison against46737267 is empty.

Fresh independent Sol High review of7f85636 found four defects: unsupported hidden CSS/DOM text, self-asserted authentic provenance, table-heading silent truncation, and recoverable SQLite/identity errors escaping receipts. Each reproduced RED and was repaired with regressions; v2 requires resolved source evidence, rejects unqualified markup/styles/legacy presentation attributes, uses table-aware and unambiguous end boundaries, and preserves recoverable failures. Re-review of8442d57 confirmed the original four repairs, found a legacy font-color/bgcolor attribute bypass, and passed31 focused tests. A second repair reproduced that bypass RED, added a small inert-attribute allowlist and passed33 focused tests. Exact final-head re-review and hosted Ubuntu/Windows CI are pending at this checkpoint; the PR conversation records their final receipts. Earlier-head CI39622179853 and39623026348 passed; neither qualifies the final head. Actual parent serving model/effort is not exposed. Requested
route Sol High; reviewer requested `gpt-6.1-sol/high`, actual serving identity/effort unavailable. No Astra escalation. New code and runner SHA256 bindings are in measurement.json; earlier runs explicitly predate that binding. No human validation or qualified cross-provider
review is claimed. G4's completed review is reused only for G4 and not duplicated.

Critical path: restore genuine source bytes with provenance, then separately
authorize usable inference and obtain source-grounded human review. One runnable
implementer plus one final reviewer is sufficient; another collector duplicates
completed work and violates scope. Reuse existing evidence store and included
usage; no paid automation ROI is demonstrated. Next three actions: finish fresh
code review/CI; restore retained bytes offline without SEC requests; qualify the
smallest zero-spend inference and independent source-review mandate. P0-B remains
a proposal only. This pipeline does not resolve source admission or the historical
denominator, and successful extraction would not establish alpha.

**P0A_INCOMPLETE**
