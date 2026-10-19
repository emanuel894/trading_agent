# Issue24 source-first decision and minimum runtime plan

Exact foundation ba213d8d775c20db7a299932a9ea3319c9bc8a59, mergedPR20.
Goal: exactly Q12–Q20, then prescribed gate state and draftPR; no merge/Q21–Q33.
Read exact merged matrix before implementation. Two independent read-only source
passes (issue24_actions_source and issue24_execution_source) examined only relevant
public APIs on the existing pinned LEAN source. Consulted-file hashes/pin are in
source_refs.json. No source install, broad audit or Q01–Q11 native rerun.

| Row | Reuse / source-established fact | New runtime necessary |
| --- | --- | --- |
| Q12 | Reuse accepted integral2:1 Q11 coupling attempts132/133 under original build/oracle bindings. Portfolio.ApplySplit824–863 credits fractional cash at cached price; never admit reverse action to that path. | One reverse split sequence: whole1@200 +unresolved0.5 claim, no cash;37 evidence once atD+2h. Warning/duplicates, prepayment encumbrance. |
| Q13 | ApplyDividend789–814 credits native cash immediately, explicitly lacks payable modeling; SecurityCache also reduces cached price. | Payable and missing-payable variants:20 native credit paired with20 encumbrance, no double receivable/payment/price adjustment;9001 request rejected before pay. |
| Q14 | Accepted public holdings/cash action projection is reusable, but no successor/valuation/tax evidence can be inferred. | Documented, missing and conflicting conversion: explicit I1→I2 lineage,70 receivable then actual payment; missing/conflict preserves unresolved claim. Carry known aggregate original1000 book cost; tax allocation remains null. |
| Q15 | Symbol.UpdateMappedSymbol preserves SID; AlgorithmManager321–343 cancels open tickets for native SymbolChangedEvents. | Exact/date-only/overlap variants. External stable-SID interval mapping; no native SymbolChangedEvent. Preserve holdings/order/intent IDs and reject tempting old-symbol quote. |
| Q16 | Reuse qualified quote validity/delay/precision semantics; no general halt/resume integration qualified. | Entry resume+fresh/no-resume/unknown carry-in/resume without fresh, plus separate due-exit track. Halt invalidates executable cache; preserve original deadline; exit waits for valid resumed quote. Public closed-order semantics plus observed original-deadline cancellation prove no entry-window extension. |
| Q17 | Reuse original isolated buy5 at raw q1/5bps/fee1 from Q06_age_exact: same fill-relevant inputs/native pipeline, flat reset, zero stock slippage. Source formula/hook unchanged under original binding, not a claim about a new host binary. | Sell5bps, buy10bps, sell10bps reset cases; prove actual native cash/fees and no double slippage/spread. |
| Q18 | Q10 proves supplied share conversion and per-order10% guard, not shared quote-event consumption. | One compound sequence:3 fills, frozen3 rejects rather than clips, repeated scans leave budget2, independent event supports separately authorized3. |
| Q19 | Native handler1308+ forwards every fill and supplied status; no execution-ID dedup. Default cancellation acknowledges immediately. | Canonical and duplicate/reordered fake-destination streams. Scripted public BacktestingBrokerage subclass delays ack/Scan; adapter dedups/orders known batch before emission, native handler alone accounts fills. Preserve cancel-pending obligation and reservations through late partial. |
| Q20 | Native fee model is not called automatically on partial events. Public OrderFee.ApplyToPortfolio and Holding.AddNewFee support separately journaled post-cancel fee corrections. | Verified totals0/1/1.25; cumulative.40/.80/1.20 partials then cancel and explicit correction; no-fill cancel; missing/unbounded fee admission blocks. Seven variants cover fee evidence that constant-fee accepted cases cannot establish. |

Minimum new cases:27, each paired in fresh processes (54 accepted if all pass).
Every variant is separate except sequences explicitly allowed by its matrix row.
No replay of the accepted Q11 integral case, nor any Q01–Q11 runtime.

Q19's adversarial physical delivery is reordered/duplicated within an explicitly
same-availability synthetic batch. Source sequence orders already-known records;
no unavailable execution is promoted. Logical cumulative cancellation remains
pending across the second partial even if native diagnostic status is partial.
A stale submitted/duplicate callback cannot regress the terminal projection.
This qualifies a fake destination boundary, not native backtest partial-fill defaults.

One implementation owner, bounded independent source/oracle/final reviews. Adopt
native synchronization/order/portfolio/public hooks; retain only explicit evidence
projection, quote-event budget and fee/execution admission. No generic OMS.
Critical path is new adapter semantics, independent of external data gates. Included
usage only/no paid calls. Next3: freeze27 exact oracles, independently review them
and adapter boundaries, run only new cases with persisted launch journals. Reusing
accepted binaries/oracles and source semantics avoids redundant builds/runtime;
no alpha/production readiness claim. All Issue24 immediate stop conditions apply.
