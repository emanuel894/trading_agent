# CP1 — source-to-native-engine diagnostic contract v1

Parent: PR56@fc3b6a8b7e5f070e6602487637d5e9b714023b7f; pinned LEAN
source d4cac37514427c84d40064cecbf3f0e6be4b0137. Owner authorized this next
no-order native replay. Archive/observation verification remains accepted; reuse
private projection SHA5097fa90a3080a60d20db230cc90849317654a37a3f5ce2ee6968dff7482f969.
No new archive/probe/codec qualification or agreement search. Rights UNRESOLVED.

## Admission is purpose-specific

Real rows are admitted only as **retrospective observations** to a custom-data
subscription in LEAN's actual datafeed/synchronizer/AlgorithmManager/QCAlgorithm
lifecycle. ObservationBatch carries original payload and clocks; Value=0 is a
non-price diagnostic sentinel. It is NOT a Quote/Tick for a tradable Security.
No historical SPY class/listing/state or actual receipt is inferred. Fixed alias
SIPOBS represents this archive stream, not a ticker mapping or investment universe.
Every event has execution_admitted=false. No algorithm signal/order or portfolio
metric is permitted. Broker admission denies all requests; final order count0.
Missing historical identity/state/units prevents executable data, not observation
of retained source bytes. A future tradable subscription needs separate admission.

## Time/session/order rules

- Preserve original nanoseconds and source-row lineage hash. Quotes emit at source
  timestamp as a retrospective observation clock, NEVER historical receipt.
- Bars emit at source interval end (start+60s), not at interval start. Actual
  publication/receipt availability stays null. An observation of a completed bar
  does not establish its historical predictive availability. No60s assumption
  becomes a source fact. Incomplete endpoint bar remains excluded by prior bridge.
- Require an explicit session record: UTC open/close and provenance label. For the
  retained Jan15 sample, declare14:30–21:00Z from existing2025 calendar references;
  this is an observation-window premise, not halt/tradability evidence. Missing
  session => block. Half-open quote interval[open,close); completed bar may emit
  at close iff its full interval is within session. Out-of-session events reject.
  No holiday/day-gap repair, weekend interpolation or current calendar substitution.
- Round delivery upward to native100ns precision. Group ALL observations mapping
  to the same native slot into one atomic custom-data batch. Preserve raw ns in
  payload. Content sort within a batch is deterministic serialization only, not
  execution order, including source ties and distinct ns collapsed into one slot.
  LEAN receives no arbitrary ordering decisions from collapsed source clocks.
- Preserve all distinct tied quote states and explicit tie-group size; never
  choose a best/latest state. Source-invalid quotes remain rejected/counted by the
  accepted bridge. Unknown state and provider size units remain explicit. Size
  values may be observed, never interpreted as executable shares/capacity.
- Freeze a source projection/version hash. Corrections are separate versions;
  never overwrite an earlier trace or assign a revision's later bytes to an old
  knowledge clock. Reproduction uses the SAME hash, not a new provider response.
  Missing intervals are missing coverage, not zero volume or a continuous session.

## Engine/oracle and finite bounds

Reuse accepted public integration seams: IDataFeed→SubscriptionData,
DataManager/UniverseSelection→SubscriptionSynchronizer→TimeSliceFactory→
AlgorithmManager.Run→QCAlgorithm.OnData/OnEndOfAlgorithm. Existing OfflineData,
OfflineApi and LocalResults from accepted host assembly deny provider/API/history
and disable result sampling. Custom feed only supplies frozen ObservationBatch
objects; AddData fillForward=false. No engine core patch/private/reflection APIs.
Standard backtest transaction lifecycle exists but no order is submitted.

OnData recomputes EVERY delivered batch payload hash, compares native time/index,
counts rows and updates a deterministic trace digest. Parent compares all planned
batch counts/row counts/digest; initialized/end observed, provider calls0,
submitted/open/native orders0. Two fresh processes must produce identical output.
Clock warmup/universe pulses are native lifecycle events, not source observations.

Limits:≤50,000 events,≤50MiB prepared input,120s per process,2GiB container memory,
512MiB tmpfs,≤64pids,2CPUs; networknone/read-only root/capdropALL/
no-new-privileges/UID65534. Failures/attempts retained, no retry-until-green.
Report wall/container peak separately from source latency; never infer production
latency from five minutes. No P&L, alpha, hypothetical fills or return statistics.

Synthetic-only cases add missing session, bad bounds, timezone/DST/early-close,
future/incomplete bar, invalid state/quote, source ties and native clock collapse.
Positive and negative native cases use this contract, not old qualification rows.
CP4 preserves complete2025 SPY IQ-P1 scope and existing proposed Q1/Q2/H2 splits;
no shrinking the study to this sample or changing registrations.

NEXT_ACTION: implement/test this frozen diagnostic contract, then independent
review and exact-head CI. RESUME_PROMPT: reconcile latest PR56 engine checkpoint;
reuse original archive/codec evidence; continue the first incomplete engine step,
with unchanged no-data/no-performance/no-trading/no-spend/no-merge boundaries.
