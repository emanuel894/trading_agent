# Bounded synthetic intraday integration

Owner mandate: resume the qualified executor, verify original hashes/permissions,
then test only synthetic feature-to-LEAN integration, causality, execution costs,
determinism and incremental latency/memory. No alpha or source qualification.
Base: feat/alpaca-paper-foundation@051c6c2d99f1ef6cfefd082ff646ed1c1cd88a09.

Reuse PR28's unchanged continuation_v2 binary and PR36's chart_snapshot and
statement_snapshot. No rebuild, core fork, production module, new dependency,
registration, source request or accepted qualification rerun. The new packet
uses the accepted Q23 input grammar for NEW integration scenarios; it does not
reclassify them as new qualification rows. All signals are fixture wiring only.

- [ ] Freeze six one-minute synthetic bars, two synthetic policy releases and a
  single 2025-01-06 15:00 UTC decision. Fixed illustrative condition: SMA3>SMA5
  and the lower target-range value decreased. Missing inputs abstain. This is
  not a fitted or proposed scientific strategy.
- [ ] Unit-test hand-computable features, strict completion boundaries, future
  revision invariance, gaps, no-signal paths and exact native cost accounting.
- [ ] Execute baseline, future-revision, missing-bar and equal-clock scenarios
  twice each in fresh network-disabled read-only unprivileged containers.
  Compare complete outputs byte-for-byte. Never run the old gate runner.
- [ ] Verify native nine-share buy at 100.07001 (100.02 ask +5bp slippage),
  one-dollar fee and 9098.36991 cash. Negative cases submit zero orders.
  Measure Python feature/prepared-input overhead separately from container
  wall time and cgroup peak memory; no source/market latency claim.
- [ ] Preserve logs, inputs, hashes, measurements, failures and source pin in
  this new packet. Verify all tracked existing files/accepted evidence unchanged.
  Run full tests/demo, independent bounded review; retain a durable checkpoint.

The fixture contains no real source, ticker, model call or returns evaluation.
Existing cash/risk/fill rules remain authoritative. Runtime image must match
PR28's digest. Failure of original bindings, isolation or the new oracle stops
native execution; do not silently rebuild or repair accepted artifacts.
