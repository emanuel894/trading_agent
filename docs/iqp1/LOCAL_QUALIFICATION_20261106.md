# IQ-P1 local continuation — offline qualification only

Owner mandate: continue PR61 locally, do the work directly; no Alpaca request,
merge or spend. Base/local starting HEAD d3fa9e19610f73fc6f92d64b6784091e3f515dfd,
branch local/iqp1-pilot. Remote draft PR61 independently confirmed open/unmerged,
head d3fa9e1, base feat/alpaca-paper-foundation. Its existing exact-head Ubuntu and
Windows success receipts are prior evidence, not validation of this new diff.

## Implemented

Credential fixtures in AlpacaConfigTests and StoreCase now patch load_dotenv in
setup with registered cleanup. Production credential behavior is unchanged. The
new regression runs those fixtures while dotenv discovery and socket connection
raise before reading any secret or making any request. Initial run failed five
nested cases; after fixture isolation it passes. No local .env value was read,
printed, copied or added to the build context.

New offline qualifier reuses existing suite/HTTP accounting. No collector, order
path, credentials, real ledger or online mode added. It runs an immutable image ID,
nonroot, read-only root, no host binds, no privileges/capabilities, no network,
2GiB RAM and no swap, one CPU, 64 PIDs and no Docker log storage. All ordinary
scratch (including temporary files/demo/backup/reserve) shares one 3GiB tmpfs;
64MiB reserve is physically allocated there, not a sparse file. /dev is Docker's
separate small tmpfs; /dev/shm disabled through ipc=none. tmpfs counts against RAM,
so OOM can occur before the storage limit: this is not persistent acquisition.

Build via tools/iqp1_build.py after committing: it exports exact Git HEAD source,
filters .env* and runtime/local-config paths before archiving, rejects links/special
files, and builds a temporary source packet. Untracked files never enter context.
Do not use the local checkout itself as a Docker build context. .dockerignore is
additional defense; tracked accepted .log fixtures are retained for hash tests.
The initial manual build likewise used a Git archive, never the local repository.
Base Python digest pinned in Dockerfile; transitive dependencies remain governed
by the existing requirements, not a new reproducibility/lockfile claim.

## Executed evidence

- Local Python3.13.16: credential regression RED→GREEN; runner tests RED for missing
  module, then GREEN. Disabled-tunnel regression RED→GREEN. Source-packet check
  RED when .env exclusion removed, GREEN restored.
- Docker29.9.2, aarch64, cgroup v2, VM4106805248bytes/6CPUs. Image built successfully.
- Final container: **353 tests PASS, zero skips/errors/failures**, 8.464s; required
  fixture demo PASS (performance artifact neither printed nor inspected).
- Kernel readings: memory.max2147483648, memory.swap.max0, scratch3221225472,
  physically allocated reserve67108864; root read-only, no active egress/routes.
- Actual offline quota probe: 4GiB allocation on 3GiB scratch rejected ENOSPC.
- Actual offline memory probe: Docker OOMKilled=true; worker SIGKILL propagated
  as exit247. Does not imply an accounting failure or successful data acquisition.
- Actual inner watchdog probe: stalled worker killed after stricter2s, exit124.
  Parent runs as container PID1; its exit destroys detached namespace descendants.
- Initial container suite failed six errors: missing Git(5), excluded accepted log
  fixture(1). Fixed by installing Git/Node and retaining tracked logs; final run
  passed all353. An overlapping check used the previous image and repeated those
  known errors; only the final completed-build run is acceptance evidence.
- Final qualified image size734576857bytes, below configured768MiB image ceiling.
- Fresh independent same-model review: fixture isolation/issued Docker flags had
  no blocking defect. Watchdog caveat below. Archive helper reviewed separately: P2 wildcard/pathspec exclusion bypass found in a synthetic repo, reproduced RED and fixed GREEN using literal pathspecs, one resolved commit SHA and defensive archive-member checks. No real .env was involved.
  Cross-provider acceptance and new-head hosted Ubuntu/Windows remain unrun.

## Unresolved — no launch readiness

DATA_BLOCKED. Actual Alpaca requests0, acquired bytes0, new sessions0, packets0.
128 attempts/2e9 retained-body limits remain the existing durable accounting tests;
no new actual pilot ledger was created. Existing accepted Jan15 data was not read,
restored or reacquired. All source/science/exit/holdout restrictions unchanged.

This deliberately has no credential or online switch. Persistent sole-ledger
storage, restart retention, packet/page/window bindings, and authenticated
GET-only allowlisted egress in a credential-separated context still need binding
and review before any acquisition. The disposable tmpfs is not a substitute for
that persistent ledger. The3GiB scratch quota/image ceiling does not establish a
4GiB host-wide actual-storage bound inclusive of Docker image snapshots/build
cache/VM metadata/backups. Host build preparation is outside this job envelope.

Independent review identified a timeout scope caveat: <=1800s is the supervised
worker bound, not total host/daemon/startup/cleanup elapsed time; outer wait allows
10s cleanup and Docker inspect/rm can block. Ruling: retain this worker-scoped
qualification, explicitly do not qualify the host-wide watchdog for acquisition.
Cost if misunderstood: a future real job could exceed total wall time; live use
therefore remains blocked. Do not treat green tests as permission to launch.

## Milestone decision record / next actions

Critical path: demonstrated persistent private quota/reserve + sole ledger and
restricted egress + total watchdog, then review, then explicit owner consent for
Alpaca. One implementer and one bounded reviewer; more workers add coordination
without removing the runtime dependency. Reuse EvidenceStore/ReadOnlyHTTP/budget;
stop framework, sample restoration, entitlement and scientific requalification.
Included tools only; no paid API use/spend; included token metering unavailable.

Next3: (1) qualify a persistent private filesystem and4GiB inclusive storage
accounting; (2) bind sole existing ledger, frozen12packets/page/window contracts,
GET-only egress and host-enforced deadline with adversarial offline tests;
(3) obtain final review/current-head Ubuntu+Windows CI before seeking launch
consent. All engineering preparation can run before Alpaca consent; data calls
cannot. Avoid resuming by resetting ledger identity or budgets. Source-only
exports reduce recurring secret exposure/manual terminal relay but establish no
alpha or profitability result. No merge authorized.
