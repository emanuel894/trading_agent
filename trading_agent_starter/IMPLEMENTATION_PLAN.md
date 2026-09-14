# Implementation plan — agreed destination and current boundary

As of 2026-09-14. User scope: Israeli resident, personal account, US market, IBKR, autonomous decisions and execution; broker Paper first, Live only after separate approval.

## V1 scope recommendation

Start with 10–20 liquid, unleveraged US-listed ETFs and/or stocks, 30-minute decisions (configurable to 15–60 minutes), low turnover, and holding periods of hours to a few days. Selection must consider inception dates, spreads, underlying exposures and correlated holdings. This is a research scope, not an investment recommendation. Overnight holdings require explicit gap-risk modeling. No leverage, short selling, options, online self-modification or LLM order authority.

First compare cash, passive holdings, fixed trend/momentum rules, and a regularized linear or gradient-boosting model. Evaluate a temporal model such as PatchTST only if it improves held-out results after costs. No assumption that adding ML produces alpha.

## Work packages and acceptance

| Work package | Deliverable | Exit condition | Indicative effort |
|---|---|---|---|
| A — local foundation | This package, reproducible tests, read-only adapter | Local tests pass; actual TWS handshake and exact Paper account verified on user's machine | Prepared now; account onboarding timing outside our control |
| B — data and research | Licensed history, corporate actions, frozen universe rules, benchmark, cost ledger, walk-forward runner and experiment log | All features/labels use available-at-time data; untouched final holdout; alternative assumptions and parameter sensitivity reported | 2–4 weeks |
| C — broker Paper execution | Single writer, durable outbox, target-to-order conversion, order lifecycle, reconciliation and session calendar | Partial fill/cancel races, ambiguous submit timeout and restart faults tested through broker Paper; no duplicate orders or unexplained mismatches | 2–4 weeks, partly parallel with B |
| D — autonomous operation | IB Gateway on dedicated host, service supervision, backups, metrics, user-facing alerts, recovery runbook | At least 30 trading sessions of unattended routine operation, including reconnect/restart drills and weekly authentication handling | 6–8 calendar weeks minimum, not proof of alpha |
| E — strategy review | Frozen model/version, net performance report, confidence ranges, stress analysis, expense coverage | Statistical and economic evidence under the predeclared risk budget; no automatic approval from an elapsed number of weeks | Evidence-dependent |
| F — future Live canary | Separate Live build/config/credentials and small capital allocation | User explicitly approves this transition; professional tax/account issues addressed; actual execution-cost review | Only after all relevant gates |

These are planning ranges, not promises. Reliable broker Paper MVP may take around 6–10 weeks after access and data are ready; validation continues after delivery. Profitability may never be demonstrated. If the strategy fails, reject it or stop the project rather than relax risk controls or retune on the final test set.

The complete V1 specification and the comparison with Foundation 0.1 are in `TECHNICAL_SPEC_V1_HE.md` and `GAP_ANALYSIS_V1_HE.md`.

## Research protocol

- Freeze the research question, universe policy, benchmark, fee model and trial budget before optimization.
- Prefer several years spanning different conditions; require only assets existing in each historical window. Corporate actions and price adjustment conventions must be consistent with execution prices.
- Use chronological train/validation/test windows, purge overlapping labels and fit scalers only on training data. Include a final holdout untouched by candidate selection. Log every experiment, including failed trials.
- Report excess performance versus suitable benchmarks at comparable exposure/risk, net of commissions, spread, impact assumptions and expected recurring operating costs; include cash interest and turnover. Track pre-tax strategy economics separately from personal after-tax outcomes.
- Compare cost scenarios and parameter neighbors; use time-dependent uncertainty estimates such as block bootstrap, rather than assuming each bar is independent.
- Paper validates behavior against current market data. Its fills do not reveal true queue position, adverse selection or live market impact. Only a later small Live canary can measure those directly.

## Broker execution contract to implement in C

1. Resolve and allowlist exact account and contract identifiers; read the actual account type, currency, permissions and applicable trading restrictions.
2. At boot/reconnect, reconcile cash/settled funds, all positions, all open orders and recent executions. Persist a fresh snapshot only after all streams complete. Data uncertainty blocks risk-increasing actions.
3. Keep one account writer. Atomically reserve an intent and risk budget before submission. Persist strategy/version/symbol/decision timestamp, broker client ID, order ID, permId and execId mapping. Broker timeouts are ambiguous outcomes: query before retrying. Local deduplication alone does not provide broker exactly-once execution.
4. Include pending buys, reserved sells, commissions and currency balances in capacity calculations. Deduplicate fills by execId, process corrections, and handle partial fills and cancel/replace races.
5. Use price-bounded orders with exchange tick-size validation and expiry policy. Do not silently replace unfilled orders with unlimited-price orders. Record the reason for every decision, rejection and cancellation.
6. Use an exchange-aware calendar with UTC storage and America/New_York scheduling, holidays, early closes and halts. Extended hours disabled for this V1.
7. Persist halt reason across restarts. Separate disabling new risk, selective cancellation of entry orders, reduce-only exits and emergency liquidation. Preserve valid protective orders unless the selected policy explicitly replaces them. A disconnected broker cannot be assumed to have canceled anything.
8. Require an operator-reviewed reset after a hard stop; routine accepted trades require no human approval. Model updates and Live transitions are separate controlled releases.

## Risk budget before broker orders

The user still needs to set intended future capital, maximum tolerable loss and monthly operating budget. Match Paper capital to that planned scale instead of the broker's large default balance. Until then, the code's $10,000 virtual balance and numeric limits are test fixtures only.

The production budget must include single-instrument and underlying sector overlap, aggregate exposure, order/turnover caps, daily and peak-to-trough losses, liquidity, overnight gaps and USD/ILS exposure. A stop threshold triggers a response; it is not a guarantee of the maximum possible loss.

## Continuous operation

Use an existing computer for setup and a dedicated host for sustained testing. Later deploy a pinned Python environment and IB Gateway on a maintained host with encrypted storage, restricted network access and a service supervisor. Keep API traffic local. No public TWS port, no credentials in prompts, no bypassing MFA. Add heartbeat, stale-data, order-reject and state-mismatch alerts. Define who handles weekly reauthentication and exceptional failures. There is no permanent trading runtime inside this chat.

## Historical status — Foundation 0.1

- 21 local tests passed on Python 3.12.14 / Linux.
- Synthetic 300-bar demonstration completed.
- No real historical dataset analyzed; no profitability result.
- SDK/TWS connection, API data entitlements and broker Paper executions untested.
- Windows scripts authored; not executed on Windows.
- Risk and ledger modules are standalone foundations; integration into a broker execution engine remains work package C.

Primary sources and exact user-facing setup steps are in Trading_Agent_Setup_HE.html.

## Current continuation — Alpaca Paper and Phase A

The project intentionally moved development to Alpaca Paper. The owner reported
the real read-only probe passed. Broker portability and the original foundation
are preserved. Phase A now adds a multi-asset 30-minute historical data provider,
strict contract, quality gate and reproducible export; see MARKET_DATA_CONTRACT.md
for commands, acceptance tests, scientific limitations and the next real-data gate.
The new historical download still needs validation with local Paper credentials.
The active sequence is data → Quant baseline → multi-asset simulator → Paper order
manager → autonomous loop → AI → controlled A/B experiment. Earlier roadmap labels
in this document describe the original IBKR plan. No execution gate has passed.
