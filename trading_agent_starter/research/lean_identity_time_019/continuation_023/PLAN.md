# Issue 23 bounded continuation

Authority: Issue23 explicitly executes the Route B design adjudicated in Issue22.
Starting PR20 head ee72ca97c6682e2a2200cc996fc51a26e1c65380; foundation
67317e573624529e247d98a4964f946421b571e7. Existing branch and draft only.

Preserve every tracked packet byte from the starting head. Verify original
source/runtime/config/code and all114 accepted outputs under their original
bindings; reuse them without native reruns. Build a separate continuation host
against the existing pinned runtime assemblies, leaving the old binary intact.

1. Freeze six new cases and independent exact oracles: Q09 historical typed
   ingress and prospective receipt; Q11 actual factor/decoy ingress, future factor
   revision, wrong normalization; one integral split coupling. Typed records carry
   explicit unknown clocks, immutable source references and append-only versions.
   Compare Q09 business prefix against the preserved baseline. Observe downstream
   as-of knowledge before/after admission, not merely metadata logging.
2. Keep Raw data on the native PriceScaleFactorEnumerator Raw path. Because that
   path deliberately skips factors, prove factor consumption with a quarantined
   nontrading Adjusted control using IFactorFileProvider/CorporateFactorProvider.
   Its outputs must be rejected by quote admission before native market-price use.
   Native daily factor dates do not become intraday availability/effective clocks.
3. Sole split owner is the public action projection, calling Portfolio.ApplySplit
   and BrokerageModel.ApplySplit once per action ID; warnings/duplicates cannot
   apply it again. No automatic split input is also delivered. Order: action,
   native order-update acknowledgment, then raw post-action quote. Seed10@100 and
   pending2 limit100 become20@50 and pending4 limit50; reservation200 and fee bound1
   unchanged; no fill, cash or profit. Q12 overall remains unqualified.
4. Fresh independent oracle/code review precedes native execution. Each of the
   six cases runs twice in isolated fresh processes. Journal before launch; stop
   at first mismatch for diagnosis, preserve all failures. No existing114 reruns.
5. Final: full repository240 tests/demo, old/new comparator adversarial checks,
   terminal regression checks, preservation/reuse proof and fresh independent
   final review. Commit/push, exact-head Ubuntu/Windows Foundation CI, update only
   draftPR20 and stop at Issue23's supported decision. Never merge.

Critical path: actual ingress and action ownership, independent of external
FMBH/Databento waits. One implementation owner; bounded read-only seam/oracle/final
reviewers. Reuse native pipeline/build/evidence; no generic engine or framework
audit. Included usage only, zero paid calls/purchases; exact usage unavailable.
Next three tasks: verify reuse, freeze/review minimal gap oracles, execute paired
new cases. Immutable versioned evidence reduces repeated compute and review work;
it implies no alpha or production readiness. All Issue23 stop conditions apply.
