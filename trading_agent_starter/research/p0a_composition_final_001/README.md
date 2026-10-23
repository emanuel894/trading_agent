# Final composition decision: reproducibility and boundary

Read DECISION.md, then PROCEDURES.md and ORACLES.md. This is the final bounded
design-only adjudication of five gaps, not a parser implementation plan.

`bindings.json` freezes accepted PR48 head/contract files, all nine existing V2
inventory artifacts, protected policy/registration and application-parser hashes.
PR48 was independently read live as open/draft/unmerged at that exact head.
No source inventory script was rerun. Existing source evidence stays read-only.

Reproduce only the JSON analysis, with the already retained V2 packet available:

```
python evaluate_inventory.py /workspace/p0a-v2-20261023 OUTPUT_DIRECTORY
```

This stdlib analysis tool verifies inventory hashes, examines the frozen node and
declaration graph, checks table grids/empty collapsed rows/zero positioning and
performs ten supplied-premise scalar oracle assertions. It never imports or
invokes the application, HTML parser, CSS layout/renderer, extraction processor,
network or inference. Its code is an audit recipe, not a newly supported parser.
No runtime test purporting to qualify new production CSS behavior was added.

EVALUATION.json is the compact committed result. The evidence packet retains the
full evaluation.json (all81 per-table grid facts) and deterministic
instances.jsonl.gz:52,976 records with gap, node, original source span, context,
local result and reason. The compressed/uncompressed hashes are in EVALUATION.json.
The counts are overlapping obligations, not filings, extracted passages or measured
hidden text. LOCAL_CLOSED is a local predicate result; NEEDS_CERTIFICATE is a
missing proof premise. Neither is an authentic VISIBLE/HIDDEN classification.

Source-span values are copied from the already independently reviewed inventory;
this analysis does not newly verify tokenization/entity maps against raw HTML.
The transfer snapshot check independently rehashes all15 immutable files and modes,
without opening SQLite for writes, reexecuting G4 or qualifying its clocks.

Independent review must recompute memberships, inspect all five procedures and
countermodel scope, check accepted-contract/protected-source bindings, and review
the final B/NO-GO conclusion. Review files and exact-head repository CI receipts
live in the evidence packet/PR conversation, avoiding a self-referential commit.
Existing Ubuntu/Windows tests/demo validate repository regressions only; they do
not execute the proposed CSS/DOM/security oracle matrix or qualify authentic text.

All earlier PRs/evidence are preserved. External spend$0, new SEC/source requests0,
authentic processor replays0, research model inference0, render/layout invocations0,
protected science changes0, merges0. P0A_INCOMPLETE.
