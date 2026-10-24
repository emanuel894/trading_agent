# SIP observation bridge: technical PASS; research replay remains unapproved

Owner's complete ZIP SHA25677423e560263b56129849b120e22f0d7be695647e949390f90c4e0cdf0037d4c
matches. Original database4ac083a8… matches, SQLite integrity/9-record chain and all
8 raw-object hashes verify. Original DB unchanged. Private input location is
`/workspace/sip-private-evidence-checkpoint/owner-sip-77423e56/owner_sip_24351e17`.
Only hashes/counts/code are committed, never licensed rows, agreements or keys.
Rights remain **UNRESOLVED**; owner authorized offline technical work and stopped
agreement searches. None occurred. No new acquisition or source requests.

## Implemented boundary

`bridge.py` opens the existing database using mode=ro; it reuses EvidenceStore's
verifier without its initializing constructor. It pins the original DB and
source window/feed/raw/asof contract, follows complete pagination across symbols,
rejects cycles/>50pages, malformed sources, missing/tampered objects and conflicting
bars. No empty/missing store is created. Existing SIP validators are reused.

For SPY the private deterministic projection contains5 completed bars and47,453
R-screened quote observations. One endpoint bar is excluded as incomplete;
354 locked/crossed quotes are counted as rejections. There are962 quote timestamps
with distinct states. All variants are preserved with group sizes and raw/source
lineage; content ordering is serialization ONLY, not inferred event order. Strict
state selection still rejects ambiguity. Receipt/status and size-unit admission
remain unknown; observed2026 retrieval is never historical2025 receipt.

`native/Program.cs` is a small observation codec using the **unchanged pinned
LEAN public TradeBar/Tick types**. It uses an explicitly artificial diagnostic
symbol alias, not an admitted historical SPY identifier. The original nanoseconds
remain in every output; LEAN time rounds upward to100ns, with no causal sequencing
claim for collapsed clocks. Prices/volumes/sizes roundtrip as decimal values;
provider size units are not silently converted into executable shares.

**This is not AlgorithmManager, security-cache/datafeed, portfolio or execution
integration.** No QCAlgorithm, signals, positions, order or brokerage calls exist
in the codec. Source/state admission and a strategy mapping remain separate work.
The five-minute sample cannot supply IQ-P1's09:30–10:00 feature, a full session or
full2025 research panel. Original10-Q and unapproved IQ-P1 files are unchanged.

## Actual validation and resource evidence

Python projections ran twice from the complete original private archive and were
byte-identical:5097fa90a3080a60d20db230cc90849317654a37a3f5ce2ee6968dff7482f969.
Two fresh native processes returned byte-identical output:
b44a2ee949b4124c40f5201920779dd1da3d190a155b5026f5b1205444a0ff04.
Parent checked EVERY ordered input/output field for5 bars/47,453 quotes using
Decimal, source-ns preservation, expected100ns ceiling, bar ends and tie-group
sizes. Input hash+array index binds native outputs to preserved private lineage.
Both report zero orders and no admitted historical identity/receipt.

Pinned SDK image is the accepted PR28 digest
`mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`.
All71 original runtime-file bindings matched before use. Codec assembly hash is
6f718957d40b1f1f0bf51a48b3ca7c1f8b5708ea16a626bf3793c82c21d65b3a.
Native source/commands/receipts are bound in CHECKPOINT and private artifacts.
Containers: UID65534, networknone, read-only root, cap-dropALL,
no-new-privileges; private inputs/code streamed into container-local tmpfs.
No host permission changes, root build, image pull or dependency installation.

End-to-end container/stream/parse/serialize wall times:10.290304s and9.792893s;
cgroup peaks643,186,688 and645,697,536 bytes. These include .NET/JSON graphs,
streamed assemblies, tar, tmpfs and page cache, not native per-event latency or
isolated engine RSS. Two samples are not a percentile benchmark; no production
capacity or optimized-memory claim. Existing synthetic PR51 timings are not reused
as real-data latency evidence. External spend exactly$0.

Three SDK/NuGet startup/restore attempts failed on a named-mutex environment
limitation before compilation. All logs are retained. Automatic approval rejected
one proposed root+host-directory-mode777 retry; it was NOT EXECUTED. The safe
alternative used the SDK's installed local C# compiler and reference pack, with
no restore/package dependency. `native/build-local.sh` records that recipe for a
new container-local staging directory and read-only accepted/runtime mount.
Compiler warningCS1701 (accepted Newtonsoft net6 reference versus net10) remains
in the log; field/runtime validation passed without suppressing it. No old native
qualification cases were rerun. Parser failures/repairs are listed in CHECKPOINT.

9 focused fixture tests and full341-test suite+demo PASS on Python3.13.5.
Tests cover original preservation, missing/mutated blobs, binding failure,
page incompleteness/cycles/cross-symbol pagination, precision, ties, deterministic
projection and quote rejection. Final independent review/exact-head Ubuntu+Windows
CI receipts are posted on the draft PR; native tests are Linux-container evidence.

## Stop / next action

Technical observation compatibility is now demonstrated, rather than merely
planned. Do not present it as an admitted tradable dataset or completed strategy
replay. Source lineage, sessions/status/carry-in, share units, corrections and
coverage must be predeclared for the next mapping; no historical receipt invented.
IQ-P1 remains a separate unapproved proposal. Next owner decision is the finite
source/identity and engine-replay mandate, followed by explicit scientific
registration approval before any strategy performance access. Do not acquire data,
search agreements or start that experiment automatically. No scientific edits,
Paper/Live/orders/trading or merge; all budgets/stop limits persist in CHECKPOINT.
