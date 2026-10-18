# LEAN contract qualification design — Issue 11

**Status: `LEAN_QUALIFICATION_READY`.** A bounded, offline, synthetic spike can
test the contract using configured handlers and public extension points. This
is readiness to **test**, not engine acceptance: terminal retention, action cash
timing and native quote precision remain runtime falsification gates. No LEAN
installation, import, build, execution or compatibility probe was needed here.

Base: `b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe`, branch
`feat/alpaca-paper-foundation`, after merged PR #8. Issue [#11](https://github.com/emanuel894/trading_agent/issues/11)
is the mandate. Draft [PR #10](https://github.com/emanuel894/trading_agent/pull/10)
at `4dd7703f429df01a6f7e67912294ec26e93b4ad0` was read as an audit reference;
this branch has no dependency on its commits. Date: October 18, 2026,
Asia/Jerusalem; source retrieval timestamps are UTC.

The deliverables are the [exact fixture matrix](research/lean_qualification_011/FIXTURE_MATRIX.md),
[numbered source evidence](research/lean_qualification_011/SOURCE_EVIDENCE.md),
[source manifest](research/lean_qualification_011/source_manifest.json), retained
public source ZIP, issue snapshot, validation record and resumable checkpoint.
Fixtures are specifications, **not implemented or passed LEAN tests**.

## Authority and decision

Reuse LEAN's event processing, holdings, orders and model interfaces. Keep frozen
identity/evidence manifests, admission, registered allocation/risk policy and the
evaluator outside the engine. Engine statistics never decide eligibility,
outcome completeness or incremental alpha. Synthetic issuer IDs below are not
population members. FMBH remains UNRESOLVED; Amendment 005, candidate priority,
registrations, existing code and broker-disabled configuration remain unchanged.

Source inspection supports a small testable route, rather than an established
non-negotiable mismatch. The dangerous defaults are replaceable or interceptable
in principle. If the spike cannot retain terminal holdings or needs reflection,
private-member access or a core patch, stop and report `LEAN_BLOCKER_FOUND`.
Do not choose a favorable status by dropping lifecycle events or weakening a
fixture. No experiment, migration, generic OMS or broker adapter is authorized
by this design.

## Source findings that determine the spike

Current public HEADs were read on October 18 and pinned, not inferred from old
release labels: LEAN `d4cac37514427c84d40064cecbf3f0e6be4b0137` (October 16),
IBKR plugin `fb86123c7ea07c3e9d02d56ed7476675e3e4578a` (October 1), Alpaca
plugin `f186471dc3a9b349e516a69fd75a603ffb5e1050` (October 16).

| Question | Finding and qualification consequence |
| --- | --- |
| Can default delisting fills be intercepted? | **Statically yes, runtime unproved.** `BacktestingSetupHandler.CreateBrokerage` is virtual; return a `BacktestingBrokerage` subclass. Its inherited protected virtual `OnDelistingNotification` runs before the private transaction-handler fallback. Override it, record the event, and do not forward unknown treatment to the base notification. `BacktestingTransactionHandler.Initialize` accepts subclasses. Configure the setup handler by assembly-qualified type. [S01–S05] |
| Why not just replace the fill model? | `HandleDelistingNotification` directly creates a full `OrderEvent` at `security.Price` with zero fee, bypassing `IFillModel`. An algorithm `OnDelistings` callback is not the interception guarantee. Keep the entire Warning/Delisted stream and test the transaction-handler path. [S02–S04] |
| Can unresolved holdings survive? | `ProcessDelistings` still removes universe members/subscriptions and cancels orders. `HandleDelisting` marks the security delisted; pending-removal safety checks include `HoldStock`, open orders, targets and unsettled cash. This makes retention plausible, not proven across both removal paths. Q01 requires engine holdings **and** the external unresolved claim to survive hourly cleanup, run end and replay, with no credited cash. A sidecar that silently loses the engine exposure does not pass. [S02, S06–S07] |
| Fill/fee/slippage replacement? | Public `Security.SetFillModel(IFillModel)`, `SetFeeModel(IFeeModel)`, `SetSlippageModel(ISlippageModel)` and their interfaces support replacement. Stock equity fills assume full quantity and best-effort pricing. Use explicit custom quote-only behavior; never inherit bar/trade fallback. Slippage is applied in exactly one layer. [S08–S09] |
| Risk replacement? | `QCAlgorithm.SetRiskManagement(IRiskManagementModel)` and `Security.SetBuyingPowerModel` are public. Framework risk transforms targets; it does not prove an atomic check for direct orders. All qualification intents pass one policy gate before submitting to the engine; pending reservations participate in that gate. Do not extend the existing prototype `risk.py` or ledger. [S08, S10] |
| External frozen identity/evidence? | Configurable data/map/factor providers and explicit SID/Symbol construction provide an ingestion route. `Symbol.Value` is a ticker; SID is engine state, not an issuer/class proof. Use local fixture-only map/factor inputs and an external one-to-one crosswalk. No default download, current universe, automatic historical backfill or remote history. [S11–S12] |
| Corporate actions safe by default? | No. Raw-mode split/dividend support is useful, but fractional splits can cash out at reference/cached prices; dividends credit cash without payable-date modeling. Test integral splits natively; require explicit actual cash-in-lieu/merger/settlement records. Retain dividend receivables separately from spendable cash until supplied payable time, withholding the native early cash credit from buying power. Unknown cash never becomes capacity. If this needs a replacement accounting engine, stop. [S13] |
| Native quote timing? | Tick has decimal prices/sizes but uses `DateTime`; native nanoseconds need a lossless external envelope. Keep int64 UTC ns and original precision, receipt/availability and sequence. Dispatch no earlier than the ceiling to a .NET tick, process same-tick envelopes in native order, and label engine dispatch time separately. Q07/Q08 must prove that no boundary, status or first-quote selection changes. Never silently round two messages into one. [S14] |
| Python 3.13 isolation? | Engine and official plugin projects target .NET 10. Official Python instructions specify 3.11.11 and QuantConnect's Python.NET fork. Use a separate pinned C# qualification host and versioned files; do not import LEAN into research Python 3.13 or change this repository's requirements. Packaging/runtime compatibility remains a later build test. [S15–S17] |

## Minimal adapter boundary

The following are contract shapes for the **future** spike, not code added now.
Use canonical UTF-8 JSON/JSONL, decimal strings, int64 UTC ns and explicit nulls;
hash the input bundle before launch. Research Python 3.13 writes files; the
isolated engine host reads them and writes event records. No pickle, Python.NET
bridge into research, shared mutable database or network service is required.

| Boundary | Minimum records and responsibility |
| --- | --- |
| Frozen evidence input | `run_id, schema_version, base/code/config/model hashes, capture_mode=fixture, rights_ref, raw_sha256, evidence_ref`; append-only source versions, original clock text/precision and separate effective/publication/receipt/retrieval/completion clocks. Manifest hash mismatch aborts before engine creation. |
| Identity projection | `instrument_id, issuer_id, class_id, listing_id, valid_from_ns, valid_to_ns, ticker, venue, evidence_refs, engine_sid`; half-open validity intervals. Export only externally admitted fixture membership. Distinct listings/classes and ticker reuse cannot collapse. Broker mapping fields are excluded. |
| Market/action projection | `event_id, instrument_id, event_ns, available_ns, source_sequence, receipt_ns|null, clock_mode, payload, evidence_refs`; quote bid/ask/size units/conditions/tape/gap flags, calendar/status and actions. Historical simulated availability is labeled assumed, never actual receipt. Predictive/status/action knowledge gets no Amendment 005 exception. |
| Policy-to-engine | `intent_id, opportunity_id, arm_id, instrument_id, side, quantity, decision_ns, eligible_from_ns, deadline_ns, policy_version, evidence_refs`; fixed deterministic test intents only. Policy gate reserves worst-case remaining buy notional/fees and sell shares before engine submission, using engine holdings/orders as the accounting base. State transitions append and reconcile; this is a thin qualification overlay, not another OMS. |
| Engine-to-independent evaluator | `event_id, intent_id, engine_order_id, instrument_id, native_contract_ns, engine_dispatch_ns, status, fill_qty, fill_price, incremental_fee, quote/status/action refs`; also cash/reservations/positions and unresolved claims. Separate `TradeFill`, `ActionSettlement`, `UnresolvedTerminal`, `Abstention`, `ReconciliationObservation`. LEAN marks can be diagnostic only. Unknown terminal return stays null and its opportunity stays in the denominator as a failure. |
| Future execution-only mapping | `destination, account_scope, instrument_id, mapping_valid_interval, broker_symbol/asset_id/conId, engine_order_id, client_intent_id, broker_order_id, execution_id, observed_ns`; append mapping changes without rewriting research IDs. Alpaca/IBKR adapters reuse their maintained broker plugins only in a separately authorized execution host. Acquisition providers, evaluator and evidence store receive no broker credentials. |

Use LEAN's normal fill/accounting pipeline for trades. A small action projection
applies **evidence-backed** cash/share conversions once through public holdings
and cash operations, never disguised market fills. Its journal prevents duplicate
application and explains engine/evaluator differences. Native split/dividend
application and explicit action projection must be mutually exclusive per action
ID. Unknown treatment keeps quantity/exposure encumbered and prevents valuation-
dependent new entries; known reduce-only exits remain possible where executable.
This conservative qualification stop is not a new research valuation convention.

Reconnect is a separate destination state machine: DISCONNECTED → RECONCILING →
READY or BLOCKED. Snapshot open orders, fills, holdings and cash with completeness
watermarks; reconcile to durable intent IDs before resuming. Missing acknowledgement
is UNKNOWN, not REJECTED; never resubmit blindly. Duplicate/out-of-order fills
cannot reverse cumulative fill or release reservations twice. Contradictory
snapshots, foreign orders, missing mappings or stale cash block new submissions;
retain raw observations separately from derived reconciliation. A scheduled exit
remains pending during disconnection; authorization to exit does not establish a
safe channel to send it. Q28–Q31 specify offline fake-destination checks. No stock
plugin is constructed, authenticated or connected in this qualification.

## Pass, fail and stop rules

Run every fixture in [the matrix](research/lean_qualification_011/FIXTURE_MATRIX.md)
against both its independent expected records and the configured LEAN projection.
Compare ordered events, identities, decimal quantities/cash, fees, reservations,
abstention reasons and unresolved outcomes, not an equity-curve tolerance.
No numeric tolerance is allowed for contract assertions; only explicitly labeled
engine diagnostic timestamps may differ from native contract timestamps.

1. **First gate:** Q01–Q03 terminal retention, actual settlement and negative
   default control. Stop the spike immediately on an unpreventable forced fill,
   vanished exposure, invented cash, altered denominator or core patch requirement.
2. **Time/identity gate:** Q04–Q11, Q32–Q33. Reject missing identities/units/clocks,
   hidden normalization, future corrections and precision-changing selections.
   A host may reject unsupported precision explicitly; that is fixture failure,
   not qualification success.
3. **Economics/policy gate:** all remaining action, fill, fee, reservation, limit,
   exit and halt cases. Any bypass or unexplained accounting difference fails.
4. **Reproducibility gate:** Q27 runs twice from empty state and replays from the
   immutable input/journal at the specified crash boundaries. Canonical business
   outputs must hash identically. Strip only declared diagnostic run IDs/wall times.
5. All fixtures, negative controls and clean-process offline runs must pass before
   reporting a **qualified synthetic contract**. That does not admit real data,
   authorize alpha/Paper/Live or establish official broker readiness.

The future spike has a 5 engineer-day target, **7-day hard stop**. No broad engine
redesign, custom broker protocol stack, durable core fork or requirement waiver.
Dependency downloads/build setup must be separate from network-denied test runs;
any implicit paid-data/license/broker connection fails the offline test. If a
commercial/runtime term blocks the contemplated deployment, record it explicitly;
do not remove entitlement checks. Runtime failure yields `LEAN_BLOCKER_FOUND`
when the mismatch is non-negotiable; ordinary repairable fixture failures remain
failed/unqualified until fixed within the bound.

## Synthetic now versus admitted data later

**Synthetic only:** every Q01–Q33 contract fixture, native clock boundaries,
corporate-action conservation arithmetic, adversarial identities, delayed quotes,
duplicate/reordered broker observations, deterministic intent/order/risk behavior,
replay, and network-denial/manifest tamper checks. These test implementation
semantics without any historical population or provider admission. No returns,
model training, parameter search or framework performance benchmark is needed.

**Must wait:** complete issuer/class/listing history and actual effective/action
evidence; FMBH exact intervals and class completeness; quote-condition/size-unit
and SIP coverage evidence, carry-in halts, corrections/availability assumptions,
actual merger/delist recovery/payable dates, licensed retention rights and admitted
historical membership. Historical receipts remain unknown where unavailable.
Real slippage, capacity, queue/impact and fee applicability cannot be established
by synthetic NBBO. Exact broker entitlement, gateway/account/reconnect behavior
requires separately authorized execution-host qualification. No Databento request
or purchase, data admission, cohort freeze or candidate advancement occurs here.

## Exact next implementation spike, if separately authorized

Create a new isolated qualification artifact, leaving the Python research
environment and protected files intact. Pin the three source commits above,
compiler/runtime/container and every resolved dependency; eliminate floating
NuGet resolution from the recorded build. Use one C# test assembly, local synthetic
data/map/factor/calendar files, one configured setup/brokerage subclass, small
fill/fee/slippage/policy models, an action translator and a canonical event exporter.
Do not install official broker plugins for these tests.

1. Implement **only Q01–Q03 first**, with the ordinary backtesting transaction
   handler and real removal/cleanup callbacks; verify no core modifications.
2. If that passes, encode Q04–Q33 as frozen fixture files and independent expected
   JSONL records. Include all table variants and negative controls. C# host tests
   the engine; a Python 3.13 standard-library comparator checks output artifacts.
3. Run twice with network denied, then exercise full-input replay at each Q27
   crash boundary. Emit per-fixture PASS/FAIL and first divergent field plus
   source/build/input/config/output hashes. Stop at 7 engineer-days even if only
   terminal tests are complete. Do not proceed into research integration.

Estimate: 1 day terminal interception/retention, 2–3 days fixture data/model/action
projection, 1–2 days policy/replay/adversarial validation; **5–7 engineer-days**
including setup risk. A later bounded integration is approximately 1–3 additional
weeks, conditional on spike results and admitted inputs. These are engineering
estimates, not runtime results or an authorized implementation plan.

## Official plugin license, service and runtime dependencies

| Component | Publicly established dependency | Unresolved cost or qualification |
| --- | --- | --- |
| LEAN source engine | Apache-2.0; .NET 10. Manual local source build with fixture files is the proposed offline route. Optional Python embedding documents 3.11.11/Python.NET. [S15] | No engine license subscription is established for this manual offline route. Compiler/package availability, exact binary provenance and dependency license review remain build work. Compute/storage/maintenance still cost labor/resources. |
| Official IBKR plugin | Apache-2.0 source license; .NET 10, floating `QuantConnect.Brokerages`/`Lean.Engine` `2.5.*`, `QuantConnect.IBAutomater` 2.0.91, bundled `CSharpAPI.dll`; TWS/IB Gateway/account and authentication/2FA operational requirements. `ValidateSubscription` authenticates QC user/token/org, POSTs `modules/license/read` product **181**, checks valid/expiry/fresh response and exits process on failure. [S16, S18] | A QC license-service dependency is proven; exact module entitlement, recurring price, offline grace/renewal terms and all-in account/data/gateway charges are not publicly resolved here. Bundled IB API redistribution/use rights need exact artifact terms; engine Apache license does not grant them. |
| Official Alpaca plugin | Apache-2.0 headers and README license model (no root LICENSE at captured pin); .NET 10, floating QC `2.5.*`, bundled `Alpaca.Markets.dll`, Polly 8.6.3, MessagePack 3.1.7. QC validation product **347**, same authenticated service/expiry/exit pattern. Broker key/secret and environment are execution-host-only later. [S17–S18] | Exact recurring module entitlement/price and full local deployment minimum unresolved. A commission-free equity statement does not establish free connectivity, data or all fees. Bundled SDK/dependency provenance remains to lock. |
| Official CLI path | Both official local live-broker pages require membership of an organization on a **paid tier**. Captured pricing lists Researcher **Seat $10/month or $96/year**, Researcher **Pack $84/month or $888/year**. [S18] | Seat and Pack are different products, neither is a verified all-in IBKR/Alpaca module price. Current public module-products data supplies neither 181 nor 347 pricing; exact entitlement requires confirmation before execution-host adoption. No license endpoint, account or purchase was used. |

These are distinct source, service and broker/data obligations. A paid CLI route
is not required merely to evaluate the manual source-engine synthetic spike.
Do not promise service-independent official Paper/live deployment or bypass checks.

## LEAN versus the sole challenger

NautilusTrader is the **only fallback**, not an additional audit. Its current
source at `c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1` has a Rust-native 2.x RC,
Python 3.13–3.14 control plane and an IBKR integration; its README distinguishes
PyPI stable 1.x from 2.x APIs. This is a current-source observation, not wheel
qualification. Its `Equity` record does not establish historical issuer/class
completeness or the required corporate-action economics. The inspected integration
list has no Alpaca entry; that is a scoped source gap, not proof no adapter can
exist. [S19] LEAN's existing equity lifecycle and both official plugins make the
small terminal-first test a reasonable first investment. Present evidence does
**not** justify `NAUTILUS_QUALIFICATION_PREFERRED`. Reconsider if LEAN's mandatory
fixtures require a fork, if the action overlay expands into another engine, or
if a later required service-independent broker route is incompatible with plugin
terms. Apply the same fixture contract to the challenger before choosing it.

## Validation of this design

See [validation.json](research/lean_qualification_011/validation.json) for exact
commands, output hashes and limitations. Existing Python tests/demo validate the
unchanged project only. Source/hash/link/fixture coverage checks validate this
design packet. No LEAN or broker runtime test, fixture pass, admitted-data result,
Windows-local result or alpha claim is made. Stop here; the next spike requires
separate authorization.
