# Issue 17 checkpoint

Base `e20a1410fe0130b7eddfacf97d1fca7860f25d3c`; branch `research/issue-17-lean-terminal-spike`.
Read `checkpoint.json` and live GitHub state on resume. Do not re-fetch/build completed dependencies. Host workspace `/workspace/issue-17-lean`, source pin `d4cac37514427c84d40064cecbf3f0e6be4b0137`, image/SDK/dependencies in `build/manifest.json`.

**Current: LEAN_TERMINAL_GATE_INCOMPLETE, not a final result.** Only Q01 user-defined attempted. Both unknown holding/cash persist, but first attempt lacked mandatory orders (host quote-seed HasData issue, preserved). Repair1 uses native TradeBar seed; attempt02 has admitted/canceled orders but its callback order differs from our initial oracle. Native callbacks emit Delisted/claim before cancellation callbacks in the same frame. No economic discrepancy, forced fill or lost exposure observed. Independent boundary review is pending before any oracle correction or additional fixture.

## Milestone decision record

1. Critical path: determine whether a versioned source-grounded callback-order correction (not economic-rule relaxation) is admissible under fixture freeze. Owner: current worker + independent reviewer. No other case can run meanwhile.
2. Workers: one implementation owner plus one bounded independent review; shared host/state precludes parallel implementations.
3. Adopt/build: real LEAN AlgorithmManager, SubscriptionSynchronizer, DataManager/UniverseSelection and BacktestingTransactionHandler. Custom code is fixture ingress/export, public brokerage interception and a bounded settlement journal; no generic engine/OMS or core patch.
4. Reuse/stop: merged Issue11 design, pinned source packet and existing build. Do not repeat broad audits, touch Q04–Q33 or patch native lifecycle to fit the contract.
5. Usage/API ROI: included usage only, $0 paid model/provider calls/purchases; two fixture process attempts, one host repair. No scheduler tool or quota reset time is exposed; no scheduled resume/heartbeat claimed.
6. Next three bounded actions: (a) independent oracle-boundary ruling, stop INCOMPLETE if inadmissible; (b) only if admissible, freeze corrected ordering and run remaining terminal cases/replays, stop on first Issue17 blocker; (c) repository regression tests, exact-head Ubuntu/Windows CI and draft PR with the allowed result. All are independent of Databento; none authorizes broader science.
7. Scale/leverage: maintained native lifecycle must replace bespoke engine work only if gate passes. A passing holding snapshot without required admitted orders is not accepted; correction provenance matters more than convenient green tests.

No Databento/FMBH/registration/paid-provider/credential/Paper/Live/alpha work. No Q02/Q03 runtime or Q04–Q33 work yet. Exact next action and preserved attempts are in `checkpoint.json`.
