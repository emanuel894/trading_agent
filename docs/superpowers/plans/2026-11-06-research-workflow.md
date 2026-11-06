# Synthetic readiness research workflow implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh independent reviewer for code and research interpretation.

**Goal:** Bind an existing fixture input, deterministic features, fixed readiness hypothesis, independent critique and auditable decision without source/alpha admission.

**Architecture:** Two offline stages reuse PR51 feature functions, PR59 quarantine and EvidenceStore. Prepare persists a fixed hypothesis before evaluation; finalize requires a critique bound to the immutable packet hash. Actual critique comes from a separate reviewer context; JSON identity fields alone do not authenticate independence.

**Tech stack:** Existing Python standard-library code and unittest. No new dependencies, engine process, provider or inference API.

**Spec:** Owner's 2026-11-06 smallest genuine end-to-end research workflow mission; canonical policy/project skill; PR59 f6dc61ad36596718fcd3b773021af5d26b5c5a43 over foundation5f8b850548e2f7786814086d5350a72a19d87459.

## Global constraints

- Dedicated branch stacked on PR59; one focused draft PR, no merges.
- Existing synthetic/native tests and framework audits are reused, not requalified. Required regression suite/CI runs only for the new integration.
- No market data, holdout outcomes, historical receipts, frozen protocol changes, orders or external spend.
- Synthetic fixture evidence is admissible only for this toy readiness question. Four scenarios are related technical cases, not four independent economic events.
- Fixed H1: all four PR51 opportunities have required market and rate-change features strictly before the common cutoff. Primary measure is ready opportunities / all four cases; no dropping missing/late cases, performance or strategy inference.
- Fed input remains catalog-only and blocks the research hypothesis regardless of an approving critique. No synthetic fallback for the real-source mode.
- Independent critique approves/rejects the interpretation, not source admission or trading. Missing/stale/self-declared same-author critique cannot seal a decision.
- Existing audit storage, adapters, feature formulas, LEAN and risk controls remain unchanged. No engine or risk invocation is necessary without orders.

## Review focus

1. All four fixture cases must remain in the denominator, including missing/late inputs.
2. Finalization must require a hash-bound critique and preserve declared reviewer/author separation without claiming authentication from a string.
3. Real-source quarantine must survive every decision branch.
4. Hypothesis/input/feature/critique/decision bytes must resolve through existing store hashes; later tampering must fail.
5. Repeated prepare/finalize must not overwrite prior runs or silently create another decision.

## Task 1: Minimal two-stage adapter

**Files:** agent/research_workflow_offline.py, tests/test_research_workflow_offline.py and one checkpoint/reuse-map document.

**Interfaces:** prepare(root, input_kind='synthetic', author_id='workflow-author') -> packet record; finalize(root, packet_id, critique) -> decision record. CLI prepare/finalize exposes only these offline operations.

- [x] Write integration tests for readiness2/4, common denominator, pending critique, stale/self critique, critique rejection, audited negative decision, source quarantine, tamper detection, non-overwriting resume and repeatable packet bytes.
- [x] Observe initial missing-module failure.
- [x] Implement fixed hypothesis + existing fixture/features + existing EvidenceStore; do not reproduce feature/admission/risk logic.
- [ ] Run new tests and produce a new synthetic packet plus a Fed-quarantine packet for actual independent critique. No historical native or source tests rerun separately.
- [ ] Commit and obtain independent code review and packet critique; seal only after that critique arrives.
- [ ] Run required suite/demo and Ubuntu/Windows CI; retain measurements and actual critique/decision receipts; publish one draft PR and stop.
