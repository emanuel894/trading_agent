# Independent pre-execution oracle review

Read-only subagent oracle_review; requested route gpt-6-astra/high, included usage. Reviewer reports Codex/GPT-6 family only; exact served API ID/reasoning support not observable. Independent context, not cross-provider acceptance. Trusted base67317e573624529e247d98a4964f946421b571e7. No fixture runtime had executed.

The original56 variants were rejected for qualification. Findings and disposition, all before first native launch:

1. Q04 at/after used I1 decision quote for I2; valid rows lacked all3quotes and malformed mappings were labels. Corrected decision-quote identity, supplied all3quotes, encoded actual missing/overlapping intervals, added per-instrument holdings and comparator crosswalk/native-SID assertions. Before-boundary intent remains I1 but no fill after its validity ends.
2. Same-key conflicting Q08payloads used physical order to choose an authoritative fill. Corrected to reject the entire ambiguous key before either quote can fill; added reversed-file-order run and subsequent must-not-consume quote. Explicit ABORTED_CONFLICT distinguishes admission abort from native Completed run loop.
3. Q11 has no Q12split execution, so it cannot prove no double split or full Q11completion. Accepted limit: raw ingress subchecks only; explicit split accounting remains unrun. This prevents overall GATE_PASS; no scope expansion.
4. Missing evidence/precision/clock fields and impossible tie availability. Added fill evidence/source/tape/native-nanosecond precision/per-fill mode; receipt remains null where unknown. Ties now available at/after both event times. Comparator validates every consumed envelope byte hash, ordered native availability/sequence/event ID, dispatch ceilings, and identity bindings.

Final fixture manifest has57variants and was committed before native execution. Fresh final whole-packet review remains mandatory.
