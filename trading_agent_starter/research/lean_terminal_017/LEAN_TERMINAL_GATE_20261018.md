# LEAN Q01–Q03 terminal-runtime gate — Issue 17

**LEAN_TERMINAL_GATE_PASS. Stop here; Q04–Q33 remain NOT RUN.**

Twenty clean processes passed ten terminal variants on one final host binary.
Each pair produced byte-identical complete canonical JSON, with no numeric or
equity-curve tolerance. The gate passes the documented interception route; it does
not admit LEAN for research, production, real data, broker connectivity or trading.

Base `e20a1410fe0130b7eddfacf97d1fca7860f25d3c`, branch
`research/issue-17-lean-terminal-spike`. Source of authority: current protected
policy/operating skill, merged Issue11 design and its Q01–Q03 definitions.

## What was executed and observed

- **Q01, user-defined and explicit universe:** native engine quantity10 and USD
  cash9000 survive Warning/Delisted, at least two hourly cleanup boundaries, four
  hours, native AlgorithmManager end and fresh full-input replay. Both open orders
  are admitted and canceled exactly once; buy cash reservation3 (2×limit1+fee1)
  and sell share reservation3 remain through CancelPending and release on Canceled.
  Engine security/exposure persists independently of the external unresolved claim.
  Terminal value/proceeds/NAV stay null, denominator1/failures1. A real bounded
  NAV-dependent admission probe rejects an entry without calling its native-order
  submission delegate; a known-NAV positive control proves the guard is not simply
  always-deny. The security itself becomes nontradable.
- **Q02, both universes, known/zero/conflict variants:** prior states match Q01.
  E-SETTLE effective D+90s is admitted only at its D+2h availability. $37.50×10
  credits375 once: cash9375, quantity0, realized loss625. Affirmatively documented
  zero recovery resolves at cash9000/quantity0/loss1000. No TradeFill is created.
  Exact duplicate is a no-op; same-ID/version $38 conflict blocks further fixture
  input without changing the prior applied state. Native `Completed` is diagnostic
  run-loop completion; `conflict_blocked=true` is the authoritative rejection for
  that negative admission variant, not permission to consume the conflicting record.
- **Q03, both universes:** forwarding stock notification detects the genuine native
  `Liquidate from delisting` fill: quantity-10, price100, fee0, cash10000. Each case
  passes only by reporting **CONTRACT_VIOLATION_DETECTED_AS_REQUIRED**. These default
  economics remain rejected. Interception eliminates this fill in Q01/Q02.

The host executes real LEAN AlgorithmManager, SubscriptionSynchronizer,
DataManager/UniverseSelection, brokerage scans, BacktestingTransactionHandler,
portfolio updates and native end callback. Fixture ingress supplies frozen data;
no native transaction/removal/cleanup implementation is mocked. The public
BacktestingSetupHandler.CreateBrokerage/BacktestingBrokerage.OnDelistingNotification
seam is exercised. No reflection/private-member workaround or core patch is used.
Q02 uses a bounded evidence-ID journal and public cash/holdings operations; it
never disguises settlement as a trade or replaces the accounting engine.

## Pins, isolation and exact evidence

LEAN `d4cac37514427c84d40064cecbf3f0e6be4b0137`; source tracked files unchanged.
SDK10.0.402 / runtime10.0.13, Linux x64, pinned official SDK image:
`mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
Final host DLL SHA256: `27846cb9dfe0b565149534b76c2f9a8e39f73cff7e2b5e7efc3432b2f4047f38`.

[Build manifest](build/manifest.json) freezes source/tree, 13 project locks,
28 resolved packages (normalized NuGet and raw archive hashes separately), and
125 runtime files. [Fixture v2 manifest](fixtures_v2/manifest.json) binds all input
and independent expected records. [Machine decision](decision.json) links every
case/output; [attempt journal](evidence/gate-attempts.json) preserves exact commands,
container controls and hashes. Python3.13 research remains isolated.

Every fixture process has Docker network mode `none`, read-only root/runtime,
unprivileged UID65534, dropped capabilities, no-new-privileges and limited tmpfs.
It observes zero non-loopback interfaces and a TEST-NET socket returning
NetworkUnreachable. Dependency acquisition is separate. No provider/broker/model
credential or plugin, paid service, licensed data, Paper/Live or alpha work occurs.
All three trading flags remain false. Canonical JSON contains deterministic
business clocks; diagnostic wall-clock logs are separate and never normalized
into a passing comparison.

| Case | Result | Attempts | Complete canonical JSON SHA256 |
| --- | --- | --- | --- |
| Q01_user_defined_unknown | PASS | 7,8 | `5563172cc21a757077a62d349130f3539cb5c17deb1744d438a152b4fd384ace` |
| Q02_user_defined_known | PASS | 11,12 | `19abdc4de3d44530d7ed34d059e58dd573a8b965b576971ce4819c962aa72477` |
| Q02_user_defined_conflict | PASS | 15,16 | `f7b56754c8d3e54cf8d300c5d8a5ee141680c9fed905b7eba49b07cad8c4b13f` |
| Q02_user_defined_zero | PASS | 13,14 | `e859db07918b5286194643adb9849bb04e221c9a356b44c707fb95f668929276` |
| Q03_user_defined_negative | PASS (violation detected) | 23,24 | `d5277f456b689e8b2932104e327bd839d60675e4dfbac6e51cc0cd1d0d94cd53` |
| Q01_explicit_unknown | PASS | 9,10 | `99d6e84c4439cbe42008122d3ce5879432c535bdf9fb1dc8f6832f2416a17217` |
| Q02_explicit_known | PASS | 17,18 | `dbcfc4efabad27a18587ea0e656247a4f4ab136c51e9beb681e48588ded21915` |
| Q02_explicit_conflict | PASS | 21,22 | `ea88a29785d69d137aa564a26df1b5fab1a3a0b27ce7084d30c7d36f0e6df9e1` |
| Q02_explicit_zero | PASS | 19,20 | `1b3edb7f0502bfc5b34da3918520b9b88cad83a7ea4b7ba7622f47172018eed7` |
| Q03_explicit_negative | PASS (violation detected) | 25,26 | `0ddd04505e81f6dc5cee7a84f44f73dbf718cf90ea096b4e67ef019821fafdd5` |

## Failed attempts and justified corrections

Original `fixtures/` and attempts01/02 are preserved, never relabeled passes.
The initial quote-only seed did not satisfy native equity HasData, so mandatory
orders were absent: fixture preparation failed despite retained holdings/cash.
The next attempt admitted orders but exposed our incorrect callback-order oracle.
Independent RED review grounded a versioned ordering correction in native request
queue/AlgorithmManager source; the merged contract never required cancellation
acknowledgments before OnDelistings. [ORACLE_REVISION.md](ORACLE_REVISION.md)
records the ruling. V2 preserves every original economic/outcome/denominator field
and event multiset, adds stronger time/identity/probe/reservation assertions, and
was frozen before fresh v2 execution. No sorting or alternative-order tolerance.

An explicit synthetic Base universe initially lacked its calendar registration;
attempt06 failed before any lifecycle. The host now uses public SetEntry with the
same pinned NY equity session hours. No core change or fixture economics changed.
Final source changes were rehashed and all twenty accepted replays rerun on the
same final host. Prior-host successes remain separate evidence.

One container launch failed before execution on disk exhaustion. Container controls
were saved; only stopped task containers were removed. The task's NuGet cache was
cold-archived with a verified hash, then restored byte-for-byte when needed. No
source/dependency research was repeated; no failed launch counts as a replay.

## Validation and limits

Repository suite: **240/240 PASS**, zero failures/errors/skips, Python3.13.5/Linux;
synthetic demo300bars/zeroorders/no trained or promoted model. The independent
comparator has **12 adversarial checks PASS**, including lost exposure, invented
cash, denominator changes, time/class substitution, NAV bypass, early reservation
release, missing native orders, sparse cleanup and duplicate settlement. Exact-
head Ubuntu/Windows Foundation CI and fresh final review are mandatory; their
final outcomes are reported in the draft PR. Local evidence/hashes are in
`validation.json`, which does not attest a future PR head. Foundation CI is distinct from
this Linux-only .NET terminal run. Upstream full test suites/Windows LEAN runtime,
production security and Q04–Q33 were not executed.

[Fresh independent review](INDEPENDENT_REVIEW.md) supports draft publication with
no critical/important findings. Two bounded limits remain: reusable journal entries
are selected by DLL hash rather than the full dependency manifest (all twenty
accepted entries were independently verified against the current full manifest),
and exported `realized_proceeds` is a fixture-mode constant (native cash, quantity,
profit, settlement-event amount and count provide the independent accounting
evidence). Neither runner reuse after changed dependencies nor a general settlement
implementation is qualified. The frozen host was not changed after acceptance.

NuGet audit warnings for source-pinned DotNetZip1.16.0 (high) and
System.Drawing.Common4.7.0 (critical) are preserved, not suppressed or patched.
The synthetic trusted-fixture host is isolated; it is not qualified for production
or arbitrary untrusted input. Commercial broker-module rights remain unqualified;
no license checks, accounts or official broker plugins were invoked.

## Milestone decision record

1. Critical path: terminal uncertainty is falsified for this pin/public seam;
   stop this issue at the terminal gate, independent of the external source wait.
2. Workers: one implementation owner; bounded independent oracle-boundary review
   and one fresh final packet review. No parallel writers/shared-state races.
3. Adopt/build: reuse native lifecycle/accounting/cleanup; keep only fixture ingress,
   exact comparator, evidence-backed action journal and project-specific admission
   guard. No generic engine, OMS, risk platform or orchestration service.
4. Waste: reuse the pinned build and evidence; no broad audit, source qualification,
   Q04–Q33 implementation or broker work merely because terminal tests passed.
5. Usage/ROI: included usage; zero paid provider/model calls/purchases. Real API
   automation remains disabled. Checkpoints were pushed throughout; no scheduling
   surface or reset time was exposed, so no speculative resume was scheduled.
6. Next three actions within this mandate only: fresh final review, mandatory exact-
   head CI, then draft PR/report and stop. No follow-on implementation is authorized.
7. Scale: the maintained engine can retain unknown exposure beneath an independent
   scientific boundary without a core fork for these fixtures. This removes one
   migration risk; it establishes neither historical source truth nor net alpha.

Databento/FMBH, Amendment005, registrations, candidate ordering, project runtime,
policy, workflows and trading state remain unchanged from the protected base.
