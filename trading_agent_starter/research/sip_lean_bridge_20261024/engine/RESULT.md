# Genuine native engine replay: CP1–CP4 technical/plan result

The authentic source projection now passes through IDataFeed/SubscriptionData,
DataManager+UniverseSelection, SubscriptionSynchronizer/TimeSliceFactory,
**AlgorithmManager.Run**, and **QCAlgorithm.OnData/OnEndOfAlgorithm**. This closes
the previous data-type-only gap. No private/reflection API or LEAN core patch.
Existing OfflineData/OfflineApi/LocalResults from the unchanged accepted runtime
provide sticky provider denial, history/API guards and disabled result sampling.

## What ran and what was admitted

The accepted projection hash5097fa90… was reused without archive re-verification,
codec roundtrip, provider calls or agreement search. All47,458 source observations
(5 completed bars,47,453 screened quotes) reached46,473 OnData atomic batches.
Every callback recomputed the payload hash, checked native clock/index, counted
rows and extended a trace. Trace SHA256:
7cfadceb64eab00338cc1348f2d6661c8573603c95f23326c8ebe9c7850956d5.
Both final fresh real-data processes produced identical complete output SHA256:
8ce747b99940af91c0a9b8d1186a4ef5b387c5378b7c571fa6a59f30bc46dc40.
Initialized/end observed, provider calls0, native/open/submitted orders0.

These are **real observations admitted to a non-price, non-executable custom-data
stream**, not admitted historical trading quotes. SIPOBS is an archive alias,
not a historical listing/portfolio identity. Value0 is a diagnostic sentinel;
no raw quote becomes an executable price. Quote ties and native clock collisions
stay atomic with raw ns retained. Bars enter at completion, not their start;
actual historical publication/receipt stays unknown. Source-side session gating
uses an explicit documented observation premise, not a complete historical status
feed. Rights remain UNRESOLVED. Original10-Q and IQ-P1 remain unchanged/unapproved.

## Evidence versions, failures and exact limits

Original implementation30cc57a produced six exact pairs: positive/tie batching,
missing-bar gap, out-of-session rejection, forbidden execution mode, missing
session, and authentic sample. Original12process receipts are preserved in
CHECKPOINT_CP3.json under their original source/compiler hashes. Four preflight
negative processes rejected before initialization; they are not mislabeled as
completed engine runs. Native synthetic positives proved delivery; Python fixtures
also test aligned beyond-close bars, unknown state, invalid quotes, DST and
half-day-close conventions. None qualify a complete exchange/state calendar.

Independent review required pinning the two source config files in addition to
71 runtime artifacts and the accepted build-manifest SHA dbf01345…. Actual config
bytes matched the accepted bindings. Review also identified runtime failure
receipts defaulting to initialized=false; a deliberate wrong-trace case reproduced
that error after the engine had ended. That reproducer is retained and excluded
from accepted evidence. The fix now preserves initialized/end/delivery counters.

Final code4c93a7c compiled assembly SHA256:
1e35da101516572de6862dc60a06142b9e1e005b21e58430ae6495827481e679.
Two final post-end-failure processes truthfully record initialized/endtrue and
2batches/4events before DELIVERY_ORACLE; two final authentic processes pass.
Successful authentic outputs exactly match the original-bound pair. Total new
processes17:12original accepted +1excluded stage reproducer +4final accepted.
No previous LEAN qualification cases were rerun. Compilation failures from omitted
Results/Server imports are preserved; no failed build produced accepted runtime
evidence. Pinned local compilation required no NuGet, install, image pull, root,
host permission change or paid service. Existing Newtonsoft/runtime compatibility
warning is retained without suppression, as in prior observation work.

Final real process wall13.028799s /12.357707s; cgroup peaks808,988,672 /807,649,280
bytes. These include container/streaming, JSON objects, tmpfs, assemblies and cache;
they are not per-event or source-to-decision latency, isolatedRSS or an alpha
benchmark. Two samples do not define a latency distribution. Both were below the
requested2GiB/120s bounds. Containers request2CPUs,64pids,512MiB tmpfs and enforce
networknone/read-onlyroot/capdropALL/no-new-privileges/UID65534; parent checks
isolation, memory/pid limits, OOM state and all delivery oracles. Input26,622,815
bytes and47,458events remain below the frozen50MiB/50,000-event diagnostic limits.

The CLI's --resume was exercised on the final completed checkpoint: verified
source/code/compiled/config/output bindings, launched0 new processes and wrote0
checkpoint updates. Changed bindings or existing pending/failed directories block
before retries. All private packets/logs remain under /workspace/sip-native-engine-*
and /workspace/sip-engine-*. Only code, synthetic fixtures and sanitized receipts
are versioned. No raw licensed observations were published.

9 engine-focused tests, full350-test suite and300-bar synthetic demo PASS locally
on Python3.13.5. Final independent review and exact-head Ubuntu/Windows receipts
are posted on PR56 after this documentation commit; native engine evidence is
Linux-container evidence only. External spending exactly$0.

## Full study boundary and next action

CP4's IQ_P1_FULL_2025_PLAN.md preserves the complete SPY2025 Q1/Q2/H2 design and
provides the missing identity/session/action/status/unit/clock/coverage inventory,
entry/exit/resolution source windows and dataset/engine/science gates. Calendar
and storage arithmetic are planning assumptions, never claimed acquisition.
The50,000-event diagnostic cap is not a proposal to truncate the experiment;
a separately reviewed full-year stream can reuse this native lifecycle.

NEXT_ACTION: owner reviews this completed genuine engine checkpoint; if desired,
authorize only the predeclared missing-source qualification and later streaming/
tradable mapping. No data acquisition, source agreement search, scientific
registration, strategy/returns/hypothetical fills, Paper/Live/orders or merge
starts automatically. No ambition, period, control or holdout has been reduced.
