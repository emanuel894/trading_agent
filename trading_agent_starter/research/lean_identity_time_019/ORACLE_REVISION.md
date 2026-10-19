# Frozen v2 cancellation oracle correction

All original `fixtures/` bytes/manifests and attempts001–005 are preserved and remain unqualified. No v1 result counts as a pass.

A second read-only independent source review approved only the correction from `[Submitted,Canceled]` to `[Submitted,CancelPending,Canceled]` in admitted/unfilled cancellation cases. Pinned `Engine/TransactionHandlers/BrokerageTransactionHandler.cs:551` sets CancelPending and emits its event before the separate brokerage cancellation request (`:1184`); cancellation can fail. Merged Issue17 already distinguishes CancelPending and Canceled. This is independently grounded in source, not an economic oracle fitted to observed output. Nonadmitted cases remain empty; filled cases retain Submitted/Filled.

`fixtures_v2/` was frozen before v2 execution. Input bytes are identical to v1; only cancellation expected status sequences change. Cash, quantities, identities, source/decision/availability clocks, receipts, fees, selected quotes, abstentions and precision remain byte-identical. No alternative-order acceptance or tolerance is added.

Review also required native event reconciliation: native SID/orderID/status sequence, fill quantity/price/fee/dispatch UTC, zero-fill cancellation events, and no native open orders. Manifest binding is mandatory. Adversarial comparator tests first failed on8contradictions, then passed after the checks were implemented. These assertions strengthen evidence; they do not execute reservation/Q21 scenarios.

Host preparation correction: a flat security remains its default0quantity/0average; positive seeds explicitly set100average. The prior unconditional SetHoldings(100,0) was a host seed bug, not permission to change the frozen flat initial state.

Reviewer requested routegpt-6-astra/high; exact served ID/reasoning not observable. Included independent context; not cross-provider acceptance.
