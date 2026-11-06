# Retained Fed format adapter — bounded engineering checkpoint

Base: `feat/alpaca-paper-foundation@5f8b850548e2f7786814086d5350a72a19d87459`.
Branch: `feat/fed-retained-format-adapter-20261106`. The resulting commit is recorded
in the draft PR and final review receipt; this document does not self-hash.

## Existing evidence and new result

Reused merged PR16's event contract and PR36's synthetic demonstration, existing
storage/adoption decisions and the retained `sources/M02.raw.gz` plus
`sources/captures.json`. No source was reacquired. The new module is a small
template-specific offline adapter; it leaves existing synthetic/shared code alone.
It reuses standard-library Decimal, gzip, regex and immutable values, rather than
adding an ingestion, parser or version-store framework.

Trusted source bindings:

- URL: `https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm`.
- Retrieved: `2026-10-18T08:00:10.273966+00:00`, preserved verbatim from the capture.
- Raw: 81,576 bytes; SHA256 `af7d78c3516a12e6fc03a4db92d9fe610a5bbbdf9619e880df28fdc92aa882fd`.
- Archive SHA256 `cc3456f0801b0ea1203c76dacf25de88bd2a2d1bfaf1c25549f5ef294f8c538f`.
- Manifest SHA256 `8475f374d6192540bfd8581749487eae736a1f6365c3d326092bd18d100c2798`.

The adapter extracts target bounds **4.75 and 5 percent**, with raw UTF-8 byte
spans, and occurrences of three fixed policy phrases: `continue reducing its
holdings`, `somewhat elevated`, and `maximum employment`. Inflation objectives
and dissenting preferences do not supply decision-rate bounds. Release date/time
labels carry raw spans, retain minute precision, and have no inferred UTC instant.

**Stop at missing independent comparator:** no independently admissible prior
setting/statement was found in the retained packet. `rate_change_pp` and
`statement_diff` are null with `ABSTAIN_MISSING_INDEPENDENT_PRIOR`. The current
document's asserted half-point cut is not used to backsolve a prior setting.
There is no new comparator API or fabricated successful historical comparison.

## Admission and revision limits

All successful outputs are `CATALOG_FACTS_ONLY`, `catalog_only`, predictively
`quarantined`, with `original_edition_proven=false`. Historical first observation,
receipt, effective time, revision and processing clocks remain unknown. A cutoff
at/before actual retrieval yields no facts; later catalog visibility is **not**
predictive availability or a registered historical publication proxy.

Archive and manifest pins must both match. Missing files, changed source bytes,
self-certified manifests and unsupported formats stop without fallback. Tests
on modified payloads are explicitly synthetic parser/corruption probes, not
additional authentic samples. A frozen loaded document retains its exact bytes
and earlier views after a disk replacement; reloading the replacement fails
verification. This is not qualification of a real revision chain or a guarantee
of unseen historical versions. New editions/manifests need separately reviewed
evidence and implementation, not an automatic pin update.

The regex parser supports this retained template's plain policy paragraphs only;
it neither sanitizes arbitrary HTML nor certifies general visibility, attachments,
original editions, source completeness or usage rights. No market or model data
is consumed. No existing experiment, holdout, eligibility or broker flags changed.

## Reproduce offline

From `trading_agent_starter`, with repository requirements in an isolated venv:

```text
python -m unittest discover -s tests -p test_fed_statement_offline.py -v
python -m agent.fed_statement_offline --cutoff 2026-10-19T00:00:00Z
python -m unittest discover -s tests -v
python -m agent demo --output <new-ignored-or-temporary-directory>
```

Local verification: Python3.12.14/Linux; 12 focused tests PASS; full suite
344 tests PASS, no failures/errors/skips; required 300-bar demo PASS. The generated
performance artifact was not opened. Existing requirements were installed into
`/tmp/fed-adapter-venv`; no dependency files changed. An initial full-suite wrapper
could not launch because `/usr/bin/time` was absent (exit127, tests NOT_RUN in
that invocation); the actual suite then ran under a standard-library measurement
wrapper. No fixture assertion or gate was weakened.

Full-suite measurements: wall12.1621s, child user CPU11.7846s/system0.5693s,
Linux child peak RSS117,292KiB. These describe the suite, not adapter production
throughput. Included tool/model usage has no exposed metering; external spend$0.
Initial TDD evidence:11 tests failed because the module was absent. The first
implementation exposed an overly broad range-anchor check that also matched
dissent text; it was narrowed to the Committee's decision sentence. Release-label
span coverage was also observed failing before adding spans. Logs are retained
locally under `/tmp/fed-adapter-*`; hosted exact-head Ubuntu/Windows CI and fresh
independent review are required before integration, and are recorded in the PR.

## Decision record

Critical path: review and CI for bounded current-document extraction; independent
prior evidence remains the source dependency for comparisons. One adapter author,
one final independent reviewer; separate read-only workers handled SEC diagnosis
and IQ-P1 source planning. No repeated audits, native LEAN replay, sample
restoration, entitlement probes or generic licensing search. Owner attestation of
existing Alpaca use is recorded separately in the IQ-P1 source plan and does not
invent provider terms or coverage.

Next three actions: (1) exact-head independent review and both CI jobs;
(2) retain the comparator abstention until independently grounded evidence is
supplied; (3) only under a later mandate, qualify that evidence before implementing
comparisons. No source acquisition, inference, strategy, returns, trading or merge
is authorized by this checkpoint. Reusable raw spans and honest abstentions reduce
later integration work without suggesting alpha.

NEXT_ACTION: Publish the draft, bind independent review/CI to its exact head, and
keep it unmerged. Stop comparison development at the missing independent prior.

RESUME_PROMPT: Read this checkpoint, canonical policy/project skill and the draft
PR's exact-head review/CI. Reuse the unchanged M02 archive/manifest; do not reacquire
it. Preserve catalog-only quarantine, unknown historical clocks and the unproved
2024 edition. Advance rate-change/statement-diff work only when an independently
admissible prior setting/statement and its source/clock proof are supplied under
a separate bounded mandate. Do not backsolve from the current cut, substitute
synthetic context, update pins casually or change scientific/trading protocols.
