# P0-A engineering scope and execution plan

Frozen before pilot processing, 2026-10-21 (Asia/Jerusalem). This is an
engineering scope note, **not a scientific amendment**. Owner authority is the
P0-A execution request and G4 clarification in this chat. External spending $0.

Goal: test offline original-10-Q MD&A preparation, traceability, strict structured
output validation and immutable persistence before an authorized alpha pilot.
No returns, performance labels, economic signal, broker, new credentials, SEC
requests, continuous capture, candidate advancement or protected registration edits.

## Reconciliation and sample rule

Trusted foundation: merged PR43, `051c6c2d99f1ef6cfefd082ff646ed1c1cd88a09`.
Reconciled draft PR45: `46737267dac2f15ab45bb032490cefebc79b39ea`, unchanged.
Issue40's final CI supplement supersedes only its pending-CI statement: run
39616292183 succeeded. G4 remains INCOMPLETE: six jobs, seven attempts,
38,592,555 response-body bytes, 24.60776813099983 diagnostic seconds. Physical
clock uncertainty and source acceptance/representation conflicts remain unresolved.

Before content inspection: inventory only already-local original-source objects;
bind original accession, CIK, form, source reference, representation, byte count,
SHA256 and provenance record. Require matching bytes and valid evidence chain
where retained. Sort distinct accessions lexicographically and take first 12.
Primary and embedded/complete submission representations count as **one filing**.
Never select by content or financial outcomes. Exclude amended forms, unavailable
objects, unverified provenance and hash/size failures explicitly. No acquisition.

The initial `/workspace` and `/tmp` directory inventory found no
`runs/issue40-g4/live-20261021`; current checkout has no retained `runs/`.
Committed G4 hashes are comparison anchors, not substitute bytes. No authentic
sample is admitted from a hash alone. Additional local files need their own
verified provenance; a synthetic fixture never becomes an authentic observation.
Coverage target 12 remains incomplete if fewer are available. Synthetic cases are
separately named and sorted; all successes and failures remain in the report.

## Fixed contract and thresholds

Version `p0a-v1`: accession, source_sha256, mda_sha256, schema_version;
management_explanations, operational_changes, liquidity_or_financing_concerns,
margin_or_cost_pressures, demand_or_revenue_drivers, material_uncertainties,
management_outlook, unsupported_claims (arrays); overall_extraction_confidence
(null or uncalibrated qualitative low/medium/high).

Every assertion requires claim, exact passage, chunk_id, span in normalized MD&A,
explicit/inferred status, qualitative uncertainty and observed_fact /
management_interpretation / forward_looking classification. Exact citation
validation proves textual grounding only; entailment and contradictions require
independent review. Unsupported claims fail acceptance. No investment output.

Predeclared engineering targets: authentic identity 100%; complete MD&A >=90%;
material-assertion source traceability 100%; deterministic preparation hashes 100%;
schema-valid **real** inference >=95%; independently supported material assertions
>=95%; silent truncations/unrecorded data loss 0; unexplained integrity failures 0.
Report exact counts; small-sample descriptive median/p95 is not population evidence.
No arbitrary trading-speed threshold. GO requires genuine source, processing,
authorized real inference and sufficient independent validation; mocks cannot qualify.

## Bounded implementation plan

One implementer; fresh read-only Sol High independent review before any merge.
Actual parent serving model/effort and client Plan/Goal switches are not exposed;
record unavailable rather than assert a selection. No Astra escalation absent RED.
Included review is not human validation or qualified cross-provider review.

KEEP_OURS: reuse `audit_text.VisibleText` for visibility policy,
`audit_store` for canonical JSON/hashing/UTC/immutable objects and chain verification.
INTEGRATE: source-mapped adapter only; no collector, audit framework or dependency.

1. Add `agent/p0a_mda.py` and `tests/test_p0a_mda.py`: verify source identity and
   exact bytes, isolate primary TEXT from SGML, retain raw byte spans through nested
   HTML/entities/iXBRL and normalization; separate table content; reject ambiguous,
   missing/truncated boundaries and unsupported markup/encoding. Test first.
2. Add lossless deterministic chunks, frozen inert prompt and strict schema/span
   validator. Reject bad identity, malformed JSON, missing citations, unsupported
   assertions and chunk loss/duplication. Never execute source text or infer truth
   merely from a matching quote. No inference adapter without existing authority.
3. Instrument identity, parsing, MD&A extraction, normalization, chunking,
   inference, validation and persistence separately. Use existing EvidenceStore;
   persist failures and immutable original/derived objects. Real inference remains
   NOT_MEASURED when unavailable. Add deterministic synthetic runner and report.
4. Run focused tests, full unittest discovery and demo; compare protected files
   with the base; commit, obtain fresh independent review, publish a separate draft
   PR based on PR45 (stacked dependency); verify exact-head Ubuntu/Windows CI.
   Do not merge this or G4 as part of P0-A.

Review focus: TOC vs body ambiguity; nested inline tags must not shift table cells;
hidden iXBRL must not leak; Unicode/entity byte offsets must reproduce source;
literal prompt injection is inert or rejected, never obeyed. Fail closed on
unsupported DOM/CSS rather than claim broad HTML qualification.

Failure categories: incorrect identity; missing/ambiguous boundary;
incomplete extraction; unsupported normalization; chunk loss/duplication;
invalid model output; unsupported assertion; missing citation; nondeterministic
preparation; persistence/audit failure. All failure attempts retained.

## P0-B proposal — draft only, not authorized

Before any alpha execution, separately register a development sample genuinely
separate from the confirmatory holdout, with a lawful independently frozen
denominator and original-source availability. Freeze a cheap numerical benchmark,
LLM model/prompt/signal and tuning budget, and fixed decision/holding horizons.
Use independently established observation and full processing latency, executable
quotes/status, costs, slippage and conservative failure/abstention rules. Retain
all failed trials. Predeclare economic kill criteria for nonpositive incremental
net performance, excessive cost/latency and dependence on unavailable information.
Quantify selection/survivorship/model-training leakage limits; historical findings
remain exploratory. Do not resolve the original 2018–2025 denominator or source
clock conflicts by assumption. No returns acquisition/inspection under P0-A.
