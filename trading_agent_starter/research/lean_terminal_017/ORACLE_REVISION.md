# Versioned callback-order correction — before v2 execution

The original `fixtures/` and failed attempts01/02 remain immutable. Neither is a
qualification pass. A fresh independent review, requested `gpt-6-astra`/High with
fresh context, supports this narrowly source-grounded correction. Runtime model
identity is not separately exposed; no cross-provider acceptance is claimed.

At LEAN pin `d4cac37514427c84d40064cecbf3f0e6be4b0137`:

- `Engine/TransactionHandlers/BacktestingTransactionHandler.cs` lines70–87 drains
  pending requests before calling brokerage `ProcessDelistings`.
- `Brokerages/Backtesting/BacktestingBrokerage.cs` lines669–702 emits notification,
  removes universe membership and calls `CancelOpenOrders`.
- `Engine/TransactionHandlers/BrokerageTransactionHandler.cs` lines551–564 emits
  CancelPending and dispatches the cancellation request to the synchronous queue.
- `Engine/AlgorithmManager.cs` calls `OnDelistings` at543; the second transaction
  drain at601 produces the final Canceled callbacks. The delisting liquidation
  control is synchronous inside `HandleDelistingNotification` at1689–1737, before
  `OnDelistings` (order-event dispatch at1469–1485).

Thus notification → Delisted/UnresolvedTerminal → canceled callbacks is the native
same-frame order. The initial oracle incorrectly assumed acknowledgments occurred
inside `CancelOpenOrders`. The merged Q01 requires exact cancellation once and
reservation retention until acknowledgment; it does not require cancellation
acknowledgments before the algorithm's delisting callback. The review found no
mocked-away lifecycle or observed immediate-stop scientific blocker.

`fixtures_v2/` appends only that event-order permutation to existing expectations;
every original economic/identity/outcome/count/denominator/settlement field is
unchanged. Machine checks compare v1/v2 fields and event multisets before launch.
New exact event-time/identity/native-event/phase checks strengthen acceptance.
An executable Q01 NAV-dependent intent probe now calls the actual narrow admission
guard with an unresolved NAV; the destination delegate must remain uncalled and
native order count unchanged. A known-NAV positive control prevents an always-deny
implementation from passing. This is a terminal-qualification guard, not a general
risk engine or a new registration.

All v2 bytes/hashes are frozen before any v2 run. No sorting events, alternate-order
tolerance, economic relaxation or relabeling of prior failures is permitted. If
these additions cannot be completed in the bounded spike, result stays INCOMPLETE;
any actual Issue17 immediate-stop condition means BLOCKER and no further fixtures.
