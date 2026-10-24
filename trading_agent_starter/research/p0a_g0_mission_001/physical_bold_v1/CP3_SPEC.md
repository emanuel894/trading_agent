# CP3 independent verification/isolation — specified only

ISOLATION_POLICY.proposed.json is a concrete inactive Linuxamd64 worker policy:
readonly private root/font/config/cache, no credentials/hostevidence/docker mounts,
network/PID/mount isolation, nonroot/caps0/no-new-privileges,16tasks/64FDs,
1GiB cgroup memory,512MiB private noexec tmp,128MiB combinedoutput and original
15sCPU/20swall. Trusted initialization precedes any document read. After it,
maintainedlibseccomp defaults to KILL_PROCESS; only reviewed syscalls/filtered
non-executable mappings and thread-onlyclone are admitted. clone3 is deniedENOSYS,
not permitted; unknown/latecalls fail without silent rule expansion. ActualBPF,
kernel/OCI/UID/mount/enforcement/profile hashes and denial results remain missing.
No custom nativecode or framework was created, and no policy/probe was executed.

DENIAL_MATRIX defines30 trustedN15/N16 probes, rendererinvocations0. Exact trusted
payloads still need serialization/hashreview before authorized preparation. These
results must be independently evidenced by kernel/cgroup/supervisor receipts,
not candidate success logs. Each is counted once in unchanged gate/variant/600s
worker accounting; failed denial/limit means stop, never weaken policy/retry.
Any attempted fetch/activecontent remains fatal; deny-all URLfetcher and original
preflight controls remain mandatory in addition to OS containment.

ORACLES.proposed.json supplies independent staticinput glyph facts and analytical
placement/visibility/source-byte definitions. Local glyphs are simple all-on-curve
polygons, so extrema/advance are independent of renderer output. Only aggregate
geometry facts are distributed, not font bytes/outlines. At16px the fontunits
map exactly to integerPangounits; other sizes/lineboxes/kerning/paint/rounding need
independent conservative expectations. Bounds are not solid ink; holes and partial
occlusion matter. Unknown/backdrop/overlap/materiality blocks whole-document admission.

The4 bold source/span strings are analytical suboracle templates, **not complete
execution-ready layout fixtures**. Full32-family fixturebytes, placement/linebox/
paint/boundary expectations and30trusteddenialpayloads still require complete
pre-execution freeze. Proposed allocation64variants stays within64 and adds no
family. Existing PR49 metric-case oracles/PR50 definitions are reused, not studied
again. No oracle is learned from component output, no expected denominator is
shrunk, and no synthetic result substitutes for authentic source evidence.

Original-byte authority and every excluded interval remain outside the engine.
Stage receipts must separately measure preflight/identity, DOM/sourcebridge,
native layout, geometry/classification, MD&A verification, normalization/chunking
and persistence using monotonic wall, worker-treeCPU, cgroup peakmemory, bytes,
limit hits and first failure. Real inference remains NOT_RUN and unmeasured.
None of these processing stages was executed by this specification task.

The next owner decision is the exact inactive V1.2 physical-font contract. Any
nonlayout preparation, package/font staging, containerbuild or denial probe needs
the separate bounded authorization request; actual syntheticlayoutgate needs a
further explicit authorization after fullG0. Authentic processing needs its own
later reviewed exception/authorization. No scientificamendment is applied here.

Staticreview correction: fatal forbidden syscalls now have separate freshworker
cases; no later-call coverage is inferred afterSIGSYS. Host exclusion requires
supervisor mount/namespace inventory and a known nonsecret outside canary; worker
ENOENT alone is not proof. No actual probe ran. All30payloads remain to be frozen.
