# LEAN identity/time spike implementation plan

Goal: falsify Q04–Q11 exactly under merged Issue11 design; stop at Issue19 decision.
Architecture: isolated C# host reuses pinned native algorithm/transaction/accounting path; frozen int64-nanosecond envelopes retain external identity/availability ordering. Python3.13 exact independent comparator; network-none clean processes.
Spec: ../lean_qualification_011/FIXTURE_MATRIX.md Q04–Q11 and ../../LEAN_CONTRACT_QUALIFICATION_20261018.md; Issue19 stop rules.

## Constraints
Only this packet changes. No Q12–Q33, policy/science/registration/runtime/credentials/paid/broker/alpha changes. Exact fixtures precede execution. Preserve failed attempts; never relax an oracle.

## Review focus
Same-tick causal availability, historical SID collisions/carried holdings, decision/fill boundary distinction, append-only future revisions, raw/adjusted substitution and share-unit proof.

## Task 1: frozen inputs and independent expected records
- [ ] Restore pinned SDK/source/locked dependencies without changing tracked upstream files.
- [ ] Enumerate every Q04–Q11 variant; serialize fixtures plus exact oracles and hash manifest.
- [ ] Comparator adversarial tests first: reject field/order/precision/cash/identity changes. Observe failure before implementation, then pass exact comparator.
- [ ] Commit/push checkpoint and immutable fixture bundle before engine execution.

## Task 2: minimal native host and runtime gate
- [ ] Reuse Issue17 supported AlgorithmManager/transaction setup; replace only ingress and fixture algorithm.
- [ ] Implement explicit SID crosswalk, int64 availability queue, raw quote-only fill/fee model, native cash/holding observations.
- [ ] Build against exact source/locked packages; record source/config/runtime hashes.
- [ ] Run explicit cases in matrix order, twice in fresh network-none processes, compare every canonical field and byte hash; stop immediately at blocker or bounded uncertainty.

## Task 3: decision and publication
- [ ] Record passed/failed/unrun variants and exact technical or contract reason.
- [ ] Run repository240/comparator/demo and protected-file comparison.
- [ ] Fresh independent review, fix evidenced defects within bound; preserve attempts.
- [ ] Draft PR to verified foundation; final native Ubuntu/Windows CI on final PR head. No merge.
