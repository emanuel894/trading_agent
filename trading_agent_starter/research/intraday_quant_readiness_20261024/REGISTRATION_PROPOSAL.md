# IQ-P1 — separate exploratory intraday Quant proposal v0.1

**UNAPPROVED / NOT REGISTERED / NOT EXECUTED.** Independent of ADR001's original
10-Q N/A/B/C experiment, its universe and amendments. SPY is a named study object,
not a sampled representative of surviving US stocks. No FMBH screening, issuer
replacement or alteration of original registrations. Numbers below are proposed
fixed research choices, not existing source facts, proven realistic costs or alpha.

## One hypothesis, two arms, one finite trial

On regular-session SPY trust units in2025, does a positive first30-minute raw-price
move identify intraday long opportunities that outperform cheap market exposure
net of explicit costs? Candidate M: buy only if close of09:59–10:00 minute exceeds
open of09:30–09:31 minute; otherwise cash. Control C: unconditional intraday SPY
long over the same permitted entry/exit times. This low-turnover market control
is a stronger practical hurdle than cash; cash is a descriptive reference only.
No LLM, indicator search, thresholds, short selling, universe selection or tuning.

Train Jan1–Mar31; validation Apr1–Jun30; untouched test Jul1–Dec31,2025, by
America/New_York session date. Quality-only review of predeclared source samples
may precede freezing; no P&L/features of held-out days. Training estimates the
single exposure diagnostic below and checks implementation; validation is a
one-time go/no-go, never parameter selection. Only one candidate/primary run,
one cost stress and one delay stress; all failures/results retained. No restart,
new dates, symbol substitution or holdout reopening to rescue failure. Any needed
change requires a new owner-approved proposal/trial before dependent evaluation.

Each day resets its feature window; no cross-day price feature/warmup or overnight
position is intended. Thus labels do not overlap across sessions. No cross-split
feature fitting or outcome leakage; unresolved overnight exposure invalidates the
complete outcome panel rather than crossing a split unnoticed. Existing knowledge
of SPY's survival limits external generalization; this is not historical stock
selection or confirmatory population alpha.

## Causal clocks, inputs and equal risk budget

Use provider-native1Min SIP raw bars, historical literal symbol asof=-, complete
RTH calendar and reviewed identity/status/actions. Thirty consecutive bars
required; no gap filling or revised-bar backdating. Freeze actual retrieval/vintage
and raw hashes. Original receipt/revision-availability stays null if unknown.
Primary simulated feature availability is bar end+60s; decision D=10:01:01 NY,
strictly after all modeled completions. This delay is an assumption, not measured
historical receipt. A fixed120s delay stress uses D=10:02:01. No timestamp alone
certifies historical knowledge. Corrected-vintage findings are exploratory and
conditional on this model; no live-actionability/PIT alpha claim is allowed.

Both arms start with separate virtual$10,000 ledgers. Same long-only rules:
position/gross cap10% own pre-entry NAV (one instrument), no leverage/shorts,
daily loss entry halt2%, running drawdown entry halt8%; exits continue. Each uses
integer quantity floor((0.10*NAV-1)/reserved_entry_price), further capped by
10% of correctly converted displayed side shares; quantity≤0 abstains. Identical
cash/fee reservations, source eligibility and entry/exit rules. Equal ex-ante
limits do not imply equal realized volatility/exposure; report both, do not
rescale using final-test outcomes. No parameter or position-size optimization.

At D require a known eligible historical state/session, no unresolved action,
and latest valid quote at/before D with source age≤2s. Reuse R-only-v1 numeric
rules after explicit extension review for2025H2; preserve native nanoseconds,
quote versions/exchange/tape and evidenced size units. Conflicting same-time
ordering abstains. Entry is the first eligible quote from D+1s through D+5s;
no retroactive bar-open fill. Buy at ask×1.0005, bounded by a reservation frozen
from D's ask×1.0005; do not raise it using later data. No qualifying full-size
capacity means no fill, logged cancellation after the5s window; no assumed partial
fill or invented broker acknowledgement. These are simulator events only.

Exit due at official close−5min (12:55 on a13:00 early close); earliest eligible
execution due+1s, sell at bid×0.9995. Retain original exposure until an evidenced
valid exit; never force fill at close/last price or delete halted/missing outcomes.
A missing exit or unresolved position blocks complete performance inference and
requires explicit outcome accounting, not an automatic overnight strategy.
Cash dividends create no credit if flat before ex-date; splits/class changes need
actual units/effective-time handling, even with raw prices. Session-reset features
avoid mechanically using overnight ex-dividend moves as momentum.

## Costs, metrics and falsification

Spread paid through ask/bid, additional5bp adverse slippage per side, $1 per
executed order as a conservative modeled fee, including any higher evidenced
mandatory charges (never double count). Final fee schedule/rights must be pinned
before replay; if incompatible with these assumptions stop for approval, not a
post-result replacement. This is not an Alpaca fee quote or guaranteed live fill.
Primary stress doubles adverse slippage to10bp and modeled fees to$2, without
retuning. Allocate any actual research execution costs equally across eligible
sessions; report unavailable accounting as unknown, not demonstrated zero cost.
External acquisitions/subscriptions/spend remain unauthorized.

Mark daily portfolios using completed raw minute bars after modeled availability
and execution cash; log unknown NAV, block entries and keep exits pending.
Report minute-observed and end-of-session drawdown; neither is tick-continuous
worst drawdown. No zero-valued mark or fabricated liquidation. Daily returns use
start-day NAV; compound net daily returns for period return. Report paired M−C
net daily returns on ALL calendar-defined sessions, return/volatility, max
observed drawdown, gross/net exposure and time invested, notional turnover
(sum absolute traded notional / start-day NAV), per-side fees/spread/slippage,
order/abstention/rejection counts by reason and unresolved terminal exposure.
Verified flat abstentions earn zero trading return and retain allocated costs;
unknown held-position outcomes cannot be set to zero or dropped. Common source
failures remain in coverage denominators; no arm-specific successful-day sample.

Primary hurdle: positive mean paired net M−C daily return with95% lower bound>0;
M cumulative net return must also be positive, with observed drawdown≤8%, no risk
violations, and positive mean paired improvement under doubled costs AND120s
feature-delay stress separately. To avoid claiming alpha from lower beta alone,
freeze beta=cov_train(rM,rC)/var_train(rC) using primary net daily returns; zero
control variance blocks. Also require positive mean(rM−beta*rC) and95% lower
bound>0 in test; this residual is a diagnostic, not an executed hedge. Both raw
and exposure-adjusted hurdles must pass. No test-fitted normalization.

Use paired daily stationary-series inference via moving blocks of5 consecutive
sessions,10,000 bootstrap samples, seed894, percentile95% mean intervals; resample
whole paired/residual days in blocks, not trades as independent observations.
At least100 completely accounted test sessions, ≥95% source-admissible test
sessions and ≥30 completed M round trips are proposed minimum information gates,
not a power guarantee. Failure means INCOMPLETE/REJECT, never expand the endpoint.
Reject on nonpositive validation improvement, any accepted future join, unresolved
outcomes, risk violations or any failed final economic hurdle. No final holdout
access before owner-approved frozen manifests, software/version hashes, ledger
of prior data exposure and independent input/implementation review. Passing only
permits a new replication proposal; it cannot establish production alpha, grant
trading permission or modify the10-Q experiment.

## Owner decisions and remaining executable gap

Approve or reject this entire separate protocol, the retrospective-vintage
limitation, named object/date partitions, conservative cost/risk conventions,
coverage/information thresholds and final-test custodian before registration.
Then separately authorize a source-only qualification with explicit limits and
private approved evidence storage. After that, a bounded real-data manifest→LEAN
mapping and one-shot paired evaluation need their own mandate; PR51 is a fixed
synthetic one-decision adapter, not an already implemented year-long strategy.
No implementation, acquisition, return inspection, science amendment or activation
is authorized by this document. Current decision remains **DATA_BLOCKED**.
