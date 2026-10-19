# Issue 27 runtime result and final-gate handoff

All required runtime rows are covered by 52 exact clean pairs: 104 accepted processes, 110 completed native algorithm runs, and 2 preserved failed processes. This document records runtime completion. The final `LEAN_ALPHA_RESEARCH_GATE_PASS` decision requires the independent final review, final-head local checks and both Foundation CI jobs; their exact-head receipts belong in the draft PR/Issue 27 comment so the validation does not create another unvalidated commit. Do not merge.

## Evidence by row

| Row | Reused original evidence | New Issue 27 evidence |
| --- | --- | --- |
| Q01–Q20 | All accepted merged evidence under original bindings; 913 prior files hash-preserved | 0 native reruns |
| Q21 | Q13/Q19 primitives; 8 original v1 pairs remain accepted under their own bindings after reviewed continuation reuse | 8 cases / 16 accepted processes, original v1 |
| Q22 | Q04 identity primitives | 11 cases / 22 accepted processes, v2 |
| Q23 | Q07/Q17/Q20 fill/fee primitives | 6 cases / 12 accepted processes, v2 |
| Q24 | Q16 already-due halt/resume primitives | 6 cases / 12 accepted processes, v2 |
| Q25 | Q01 unknown-NAV primitive | 8 cases / 16 accepted processes, v2 |
| Q26 | Q19 public scripted brokerage-event seam | 3 cases / 6 accepted processes, v2 |
| Q32 | Existing hash/offline/public ingress primitives | 7 cases / 14 accepted processes, v2 |
| Q33 | Original hash-bound Q01 unresolved outcome plus fill/fee primitives | 3 cases / 6 accepted processes, each process runs 4 isolated arms, v2 |

There are 44 v2 pairs plus 8 original-bound v1 Q21 pairs. All 52 were new for Issue 27; Q21 was never rerun or relabeled after the continuation. Every accepted case has two fresh, empty-state, network-disabled processes with identical output bytes. No journal or mutable business state was restored. Global attempts 001–106 remain contiguous.

## Provenance, repairs and cost

The pinned LEAN source is `d4cac37514427c84d40064cecbf3f0e6be4b0137`, foundation `7fc2e91b01194a01cdc59f05fbd9d9f778cceebc`. The source review found no tracked upstream source change; 63 shared runtime assemblies match prior accepted runtime bytes. Code, frozen fixtures/config/oracles, compiled runtime and outputs are bound in the approval/build/journals. Both independent pre-execution receipts precede their affected native runs.

After Q21, source review found that v1 installed API/history deny services only in negative-ingress variants. The versioned v2 continuation installs the same services before initialization for every algorithm. Economics, fixtures/oracles, comparator and evaluator are byte-identical. Independent review accepted Q21 only under its original bindings; 123 parent files remain hash-preserved. Remaining rows ran exclusively under v2.

Two native-process attempts failed before algorithm initialization, with no accepted business output:

- Attempt 001: public source Data directory ancestors lacked traversal permission for container user 65534. Only task-owned fixture directory access changed before the successful pair.
- Attempt 104: the original public synthetic Q01 claim and its three ancestor directories were unreadable by user 65534. Only directory read/traverse and file read permissions changed; bytes, approved bindings and existing accepted evidence stayed unchanged. Independent review confirmed this bounded repair before attempts 105–106 passed.

Every raw output/log and failure remains committed. Build/preparation failures and frozen pre-execution revisions are also retained. Summed measured process-attempt execution time is 977.529665 seconds, including failed attempts; it excludes build/review/publisher overhead. Dollar resource cost and model token accounting are unavailable. Paid provider calls and purchases: 0. Offline denial attempts are synthetic, not authenticated acquisition. No credentials were requested.

The combined verifier checks original approvals/bindings, all pair hashes, actual native order/fill/cash/position reconciliation, parent/prior preservation, isolated container controls and uninterrupted attempt lineage. Run final checks once from the final committed head with `continuation_v2/validate_final.py` using the isolated Python 3.13 environment. Logs are written outside git. Foundation CI covers repository tests/demo on Ubuntu and Windows; native LEAN evidence is Linux-container evidence, not a Windows-native qualification.

## Exact stop boundary

Research reproducibility only is covered from Q27. Full Q27 crash cuts, restoration, journal continuation and ambiguous-command recovery remain unqualified. Q28 broker mapping, Q29 acknowledgement ambiguity, Q30 reconnect snapshots and Q31 destination restart remain unimplemented/unrun here. Q26 uses only a local stale/ambiguous rejection flag, without reconnect machinery.

After final review/checks/CI confirm the research contract, no additional LEAN qualification is on the critical path to the first falsifiable alpha experiment. This synthetic result supplies no source admission, alpha result or Paper/Live authorization. FMBH remains UNRESOLVED. Live Issue 7 records Eric's October 18 response; the old source map's “unsent” snapshot is superseded. The outstanding bounded question is whether the February 28 versus May 9 record changes required structural fields, with independent exact-validity corroboration under Amendment 005.

## Critical path and next three tasks

1. Obtain/adjudicate only that bounded FMBH structural-field delta and independent exact-validity evidence under Amendment 005. Owner/provider evidence is the dependency; stop at UNRESOLVED if the registered exact-instant/class-completeness contract remains unsupported. No paid acquisition, remaining Massive calls or candidate substitution.
2. While Eric/Databento is pending, qualify the narrow official event-source boundary from the accepted Issue 12 design: original 10-Q version/provenance and availability/receipt clocks required by the registered MD&A comparison. A separate bounded source task can establish a defensible contract or specific gap; do not implement broad ingestion or run alpha. Reuse the completed design and source packets.
3. After source/eligibility admission, perform the registered freeze and acquisition/latency audit. A valid immutable audit packet is the prerequisite for separately authorized cheap-control/extraction comparisons. Do not replace this dependency with more LEAN, broker, generic OMS or recovery work.

Staffing is one implementer and one bounded independent reviewer, overlapping code review with isolated execution. No second implementer or duplicate source/framework audit is useful. Reuse maintained LEAN and accepted packets; keep only the demonstrated scientific admission/export/evaluation adapter. Included usage was used; paid automation remains disabled. The economic leverage is avoiding a new OMS/backtester and all unchanged native reruns, then moving the next decision to source sufficiency rather than adding engine scope. No profitability claim is made.
