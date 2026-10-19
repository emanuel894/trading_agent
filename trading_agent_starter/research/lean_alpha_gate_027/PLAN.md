# Pre-alpha LEAN research gate implementation plan

Spec: issue_snapshot.json and ../lean_qualification_011/FIXTURE_MATRIX.md.
Foundation: 7fc2e91b01194a01cdc59f05fbd9d9f778cceebc.
Branch: research/issue-27-alpha-research-gate.

Goal: exact Q21–Q26/Q32/Q33 synthetic research qualification, with new clean pairs.
Architecture: reuse pinned public AlgorithmManager/data synchronizer/transaction/portfolio seams. One thin policy gate owns admission and cash/share reservations before native submission. Independent frozen expected records compare native observations and evaluator exports; no engine performance metrics decide outcomes.
Tech: pinned C# .NET10/LEAN d4cac37514427c84d40064cecbf3f0e6be4b0137, Python3.13 standard-library comparator.

Constraints: new packet only; old accepted evidence/bindings immutable; no scientific amendment, paid services, broker plugins, Paper/Live, Q27 recovery, or Q28–Q31 implementation. Full Q27 stays unqualified. Failed/interrupted runs remain recorded; restart empty, no mutable continuation.

## Tasks / files / interfaces

- [x] Reconcile issue, protected base and project instructions; create dedicated branch from exact base.
- [ ] Source-first delta and evidence reuse: SOURCE_COVERAGE.md, reuse-proof.json, source_refs.json. Consume old packet decisions/manifests/oracles and pinned public source; produce precise original-bound evidence references, preserved-file hashes and minimum case map. Never run old native cases.
- [ ] Freeze fixture inputs/expected records under fixtures/ with manifest.json before native execution. Freeze numerical values from matrix, per-variant separate runs except explicit sequences. Independent read-only oracle review must bind exact inputs/comparator/host/build before execution.
- [ ] Write failing adversarial comparator/coverage tests in test_gate.py (wrong cash/share reservation, extra/missing cases, changed native outputs, future-price sizing, cross-arm leakage, missing completion, missing binding). Observe rejection before implementing compare.py. Green focused checks; do not repeat full suite until final head.
- [ ] host/Program.cs: strict manifest ingress/network sentinel plus native host and canonical export. host/ResearchAlgorithm.cs: ordinary LEAN initialization, immutable envelope admission, policy and quote-only fill hooks. host/Policy.cs: SubmitIntent(intent) gate, cash/share reservations, sizing/ranking, halts and scheduled exits; native order/accounting is sole trade accounting owner. Public scripted callbacks only for explicitly adversarial local reservation lifecycle.
- [ ] fixtures/ -> host -> canonical business/native observations -> compare.py. Freeze build.json and reviewed binding. run_gate.py validates all bindings, journals each launch before side effects, runs fresh network-none read-only unprivileged containers, preserves failure/log/control/cost metadata, stops at first divergence, and reuses only already accepted exact-bound outputs. Pair every new accepted case, no crash recovery.
- [ ] Commit at oracle freeze, reviewed build, accepted runtime stage(s), and final evidence. Each checkpoint states exact remaining action, counts, failures and pending side effects.
- [ ] Final committed head: full repository tests/demo, original/stage adversarial comparators and preservation checks once; fresh independent review; push dedicated branch and draft PR to feat/alpaca-paper-foundation; exact-head Ubuntu/Windows Foundation success. No merge.
- [ ] Report exact gate PASS/BLOCKER/INCOMPLETE and stop.

Review focus: direct-order bypass; pending sells freeing capacity early; late price changing earlier quantity; halts blocking exits; duplicate sell overshooting holdings; offline guards that merely inspect configuration; evaluator copying engine metrics; partial output accepted after interruption.

Reuse is original-bound evidence, not a claim prior binaries ran against this new host. A changed source/runtime semantic dependency triggers targeted adjudication before rerun; setup restoration is not a fixture rerun.

