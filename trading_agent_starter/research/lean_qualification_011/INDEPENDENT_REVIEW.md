# Independent review — Issue 11

Reviewer: Codex subagent `qualification_review`, requested model `gpt-6-astra`,
reasoning `high`. This is independent agent review using included Codex usage,
not a cross-provider acceptance or a paid external model API call. The first
attempt stopped at a usage limit before completing; the resumed review reused
the existing packet without new source retrievals or LEAN execution.

Trusted policy loaded from original base
`b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe`. Reviewed design at `c537902`, issue
snapshot, full Q01–Q33 matrix and retained source evidence. Parent also read
the newly accepted operating doctrine on current target `1a9014e` after resume;
its scientific policy addition links operations and changes no research rule.

## Findings and resolution

1. **P2 — sizing used a future executable price.** Q23 now supplies the adverse
   price ceiling100.07001 and fee bound1 as inputs known at D, independent of q1.
   Quantity/reservation freeze at D. A later valid narrow-spread quote ask100.03
   (executable100.080015) exceeds the ceiling and must not fill or resize.
2. **P2 — same-engine-tick ordering lacked adversarial availability/status cases.**
   Q08 now reverses event versus receipt order and tests quote-before-halt and
   halt-before-quote inside100ns. Ordering uses native availability/receipt first,
   with event time preserved as provenance/freshness input.

Reviewer rechecked the bounded delta and confirmed both findings resolved;
the final suggestion to keep Q23's negative quote inside the20bps spread limit
was applied. Design/matrix corrections are committed in `8a0d4f0`.

Final assessment: no further material finding after these corrections.
`LEAN_QUALIFICATION_READY` is defensible **as readiness to test**. Source-level
terminal interception/removal reasoning, arithmetic and qualified commercial
claims are supported; actual terminal retention and runtime compatibility remain
unproved. No change to protected science, source admission or trading authority.

Scope limits: documentation/source review only; no runtime fixture passes,
binary/license entitlement qualification, actual broker behavior or alpha claim.
Hosted CI must validate the final PR head with the current target. No merge is
authorized by this task.
