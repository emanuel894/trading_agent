# Issue 19 identity/time qualification packet

Only Q04–Q11 are in scope. Read checkpoint.json and the final decision/report before resuming. No Q12–Q33 execution, engine integration, broker/provider/paid access or alpha work is authorized. Source/base and policy hashes are in the checkpoint.

## Evidence boundaries

`fixtures/` is the original immutable v1; attempts001–005 are failed preparation/oracle comparisons, never passing evidence. `fixtures_v2/` is the independently reviewed exact cancellation-state correction. Input bytes are unchanged. ORACLE_REVISION.md records the ruling; ORACLE_REVIEW.md records the pre-execution review. The authoring script freeze.py reads no native output; do not regenerate/overwrite a frozen bundle during replay.

The host invokes real LEAN AlgorithmManager, DataManager, SubscriptionSynchronizer, BacktestingTransactionHandler, BacktestingBrokerage, fill/fee models and native portfolio accounting. Only fixture ingress, source-clock/identity projection and quote-only fill policy are custom. Native data includes explicit synthetic TradeBars for pacing/HasData; these cannot supply execution quotes or capacity. No native lifecycle/order/accounting implementation is mocked. Source tracked bytes and resolved dependency archives match the qualified Issue17 pin.

Native precision is100ns. Every source envelope stays int64UTCns with separate event/availability/nullable receipt; availability/sequence/stable ID determine processing. Dispatch ceilings are diagnostic engine times, never substitute contract times. Same-key conflicting payloads abort before either is consumed; native Completed is run-loop completion, distinct from ABORTED_CONFLICT.

Q11 scope is deliberately limited: raw quote ingress, seeded average100, raw pre/post marks, wrong normalization rejection, and future-metadata invariance. No Q12split action executes, no native factor-file provider is exercised, and no double-split/accounting acceptance is claimed. Factors/adjusted decoys/future-record metadata remain frozen external input; these are not evidence that native factor/correction ingestion is qualified. Full Q11/gate acceptance remains incomplete.

## Reproduction

Use a separate `/workspace/issue-19-lean` directory. Source commitd4cac37514427c84d40064cecbf3f0e6be4b0137; SDK10.0.402/runtime10.0.13 in the immutable official SDK image digest recorded in build/manifest.json. Reuse Issue17 project locks and package hashes; copy this packet host beside source. Restore locked dependencies using ordinary public package access and the managed proxy/CA trust, then build `host/LeanIdentity.csproj --no-restore -c Release -p:RunAnalyzers=false`. Never change tracked upstream files. Preserve a newly built manifest separately; it is not automatically the accepted binary. Initial audit warnings remain in restore/source-build logs. A later cache-only offline restore disabled network audit retrieval; it did not change versions or suppress the original warnings.

Copy the frozen fixtures_v2 directory beside host/source. Make source/Data/runtime/fixtures readable by UID65534 and provide a separate writable runtime-output directory. Hash all runtime files and verify the manifest. Run explicit IDs only with `python3.13 run_gate.py Q04_before ...`; runner paths intentionally target this managed workspace. It refuses out-of-scope cases or unreconciled pending launches. It reuses successful pairs only after validating the full build/fixture/source binding and rechecking canonical output hashes and assertions.

Each fixture is a new process: Docker networknone, read-only root/input/runtime, UID65534, all capabilities dropped, no-new-privileges, boundedtmpfs and false trading flags. The host asserts loopback-only interfaces and a TEST-NET socket returning NetworkUnreachable. No Docker socket, broker/provider/model credentials or official plugins enter the fixture. Dependency acquisition is separate. Container commands/controls/exits and partial outputs are preserved in evidence/attempts.json. A failure stops the selected slice; diagnosis determines technical incompleteness versus a contract blocker.

The comparator matches all business fields exactly, directly reconciles native SID/orderID/status/quantity/price/fee/UTC/closed-order observations, validates input/manifest/source/crosswalk bindings and ordered source-envelope hashes. Complete canonical JSON must be byte-identical in both processes. Wall-clock logs are separate and never normalized into a pass.

Run the repository240-test suite/demo with Python3.13 and both packet comparators. Hosted Ubuntu/Windows Foundation CI is separate from this Linux-only .NET runtime exercise. Full LEAN upstream/Windows runtime, native map/factor file ingestion, real security-master/market data, scientific admission, broker adapters, Q12–Q33 and performance remain unqualified.
