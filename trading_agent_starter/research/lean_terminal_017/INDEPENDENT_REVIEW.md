# Independent final Q01–Q03 packet review

**PASS for draft publication. No critical or important findings.**

Reviewed committed head `e733519e949b29f61ec0dfcdae158098862681af`, plus the
report's correction of premature CI wording and refreshed local validation logs.
Instructions were read exclusively from protected base
`e20a1410fe0130b7eddfacf97d1fca7860f25d3c`.

Reviewer: fresh read-only agent `/root/issue17_completion_review`. Requested
configuration: `gpt-6-astra`, `high`, `fork_turns=none`. Actual runtime model
identity is not separately exposed; this is not a cross-provider acceptance claim.
No LEAN execution, dependency installation or provider contact occurred in review.

## Findings and disposition

Two minor limitations do not affect the accepted executions:

1. `run_gate.py:19` selects reusable successful entries by host DLL hash without
   also requiring the prior full build-manifest hash. Future dependency changes
   could reuse stale evidence. All twenty accepted entries were independently
   checked to carry the **current full build-manifest hash**, and all 125 runtime
   hashes match. Reuse under changed dependencies is not qualified; do not use this
   bounded runner for such a future run without fixing that selection condition.
2. `host/Program.cs:295` exports `realized_proceeds` using fixture-mode constants,
   so that field alone is not independent accounting evidence. Actual native cash,
   quantity, realized profit, settlement-event amount and settlement count
   separately match $375/affirmative-zero cases. This exporter is bounded fixture
   observation, not an admitted general settlement-accounting implementation.

Both limits are retained rather than changing the frozen host after acceptance.

## Independent verification

The ordinary AlgorithmManager, transaction handler, SubscriptionSynchronizer,
delisting removal/hourly cleanup and native end callback execute. The pinned
SubscriptionSynchronizer calls hourly cleanup at line105 and HandleDelisting at160.
The public notification seam prevents default liquidation while both universe
branches retain native holdings. Q03 reaches the actual stock liquidation and
finds quantity−10, price100, fee0 and cash10000. No private reflection, core patch or
mocked-away native transaction/removal subject was found.

The v2 callback permutation follows native queued cancellation and the later
AlgorithmManager transaction drain. Issue11 does not require the erroneous v1
ordering. Every original economic field/event multiset is unchanged; stronger
checks were added, failures preserved, and v2 frozen before all accepted runs.

Read-only checks verified all twenty outputs/comparators/journal hashes and
network-none controls, pairwise byte identity, full Q02 preavailability equivalence,
both fixture manifests, host-source hashes, 125 runtime files, thirteen dependency
locks, twenty-eight package versions/content hashes, and unchanged upstream source.

## Exact reviewed bindings

| Artifact | Git identity / SHA256 |
| --- | --- |
| LEAN commit | `d4cac37514427c84d40064cecbf3f0e6be4b0137` |
| LEAN tree | `6bdca864f7be86d7268d46328fd5f099db95b882` |
| host/Program.cs | `28320a742918f28667cf1cac49000432d1c9764cde1d8e5c4209bba9c8a919ab` |
| host/LeanTerminal.csproj | `b1fdb8d0ab49c3c7852f69c9db1c2cc8230b0175c503fd6912f7f32f244f3318` |
| Host DLL | `27846cb9dfe0b565149534b76c2f9a8e39f73cff7e2b5e7efc3432b2f4047f38` |
| compare.py | `89db55dd04205a83ddffe402540e28e3da71fd1d76ea33c0f0d4b094e80a6d9b` |
| run_gate.py | `cf0456966dc4959f709b3447cb949f4d0817ed0a0113fb92ad3e755b948cf476` |
| v1 manifest | `94954ba8333711009c00203c787d7b350c24f31c77b11bd73d2576056053755d` |
| v2 manifest | `fcca84dddad0042b448e611f66e38dfa0f577b2adfd700d372ca06eae706cd49` |
| Build manifest | `10b1e4f20e6f0cea40afefcabddd24865cb03cd07fc68d2070e67498d26e71cb` |
| ORACLE_REVISION.md | `20103cb4c4ffbc7e81e1124fe8deac30c0ab3bba8933a7b460c9bc665f54989a` |
| Issue11 design | `9467bde7ef6698decbcf158e5c0d26a57af54283e9f30d2b7a1938beb382e835` |
| Issue11 matrix | `a002fb8d9ae2add7486a196c4d590a47395428f64a24c1a611b159ea8e4ab076` |

## Review limits

Parent-refreshed suite240/comparator12/demo300 evidence is distinct from this
read-only review. Hosted Ubuntu/Windows checks for the final PR head must be read
from GitHub after publication; review does not attest an uncreated future commit.
Q04–Q33, crash-cut recovery, Windows native LEAN, production security, broker
rights/connectivity, real data and alpha remain unqualified. Dependency audit
warnings remain disclosed. Draft publication does not clear merge or wider use.
