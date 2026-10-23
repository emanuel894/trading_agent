# P0-A maintained-layout adoption decision 1.0.0

**ADOPTABLE WITH REVIEWED AMENDMENT — WeasyPrint70.0 is the single candidate for
one separately authorized synthetic feasibility gate. It is not qualified or
adopted for authentic processing. Overall P0A_INCOMPLETE.**

Accept PR49's architectural blocker and stop custom CSS/layout development. This
decision reuses the merged build-vs-adopt audits, PR48's component comparison and
PR49's final findings. It does not redo the five-gap analysis or source inventory.
Only three additional files at the already pinned WeasyPrint revision were read
to resolve the integration surface. No component was installed, executed or timed.

## 1. Smallest route and evidence

| Component | Bounded role and decision |
| --- | --- |
| WeasyPrint70.0, Kozea/WeasyPrint `7e2dda0d7833916d2698c35e707bc80ddea1ed24` | **BENCHMARK for conditional adoption:** maintained CSS layout, font shaping and paint-geometry evidence. It supplies no scientific admission or original-byte truth. |
| Existing immutable store, identity checks, byte mapper, boundary/extraction/chunk validators | **KEEP_OURS:** security admission, original-byte accounting, MD&A completeness and failure persistence. Adapt only at the component boundary; no new collector or general parser. |
| EdgarTools, previously audited revision `cb4f34cb42a9cdfb44e52e47067580e0b97daa69` | Complementary local accession/section/iXBRL crosscheck only. Existing audit supports parsing qualification, not CSS visibility. Exclude from the minimal layout gate to avoid another parser/transport dependency. No SEC fetching/cache substitution. |
| Arelle | Optional future independent typed-XBRL validation only if a specific unmet need remains. No pinned Arelle evidence in the reused audits establishes this integration or CSS visibility. Defer; do not install/research it to rescue this gate. Schema/taxonomy fetching remains prohibited. |

Existing source evidence shows eight direct Python dependencies plus native/font
dependencies, default print media/URL fetching and warnings for unsupported CSS.
The focused additional source check establishes:

- `HTML.render()` lays out **and paginates**; `Page._page_box` is a private
  geometry tree (`document.py`25–81), not a public original-character-map API.
- Boxes retain their DOM `element`, computed style and children (`boxes.py`109–114);
  TextBox retains text and can be copied with changed text (599–617). These are
  useful bridge anchors, **not** original UTF-8 offsets or complete ink accounting.
- The existing painter uses Pango glyph extents (`draw/text.py`232–235). Native
  metrics exist; no supported stable public per-source-character ink/paint-plan
  interface is established by this inspection. Merely reading box width is
  insufficient. A version-bound read-only adapter must prove access/reconciliation
  in the gate; it may not copy/reimplement layout or paint-order algorithms.

**Why pursue this route:** it removes ownership of flex/table/font layout from our
code and leaves a bounded provenance/qualification adapter. Maintaining a custom
layout engine is rejected, so it is not a parallel fallback. WeasyPrint enlarges
the dependency/attack surface; it is **not intrinsically safer**. A secretless,
no-network, OS-limited worker can bound impact while maintained semantics avoid
our own layout implementation. This is a defensible smaller *owned semantic*
surface and a testable security route, not measured LOC savings, runtime benefit
or a claim of demonstrated comparative safety. Conditional adoption fails if the
bounded adapter or enforcement cannot meet the gate below. There is no rescue loop.

## 2. Exact proposed ADR001 §8 addition — NOT AN AMENDMENT IN FORCE

Retain the current “Store original bytes; never execute, render or follow document
instructions/links” rule and all subsequent requirements. Propose appending only:

> **P0-A synthetic inert-layout qualification exception.** After explicit owner
> and independent security review of the exact component/dependency/font hashes,
> sandbox policy and fixture/oracle manifest, one bounded offline qualification
> may invoke the pinned WeasyPrint70.0 layout component on synthetic test documents
> only. This exception does not admit any authentic filing or authorize replay.
> All documents remain untrusted data. Reject scripts, handlers, executable URLs,
> active/foreign content and unsupported markup/CSS before component invocation,
> including inside hidden content; never strip, ignore or execute them. Prohibit
> all document-triggered code execution, subprocesses, external/local URL fetching,
> schema/DTD resolution, document-provided fonts and following links. Load only
> trusted, hash-listed runtime/font files installed before isolation. Enforce
> no network, no credentials/host evidence mounts, least privilege, read-only
> runtime and hard OS CPU/memory/time/storage/process limits. Any attempted fetch,
> unsupported/recovered content, missing map/geometry or exhausted limit fails
> closed with an immutable receipt. Do not truncate input to obtain success.
> Preserve original bytes, every text/exclusion span and whole-document ambiguity
> rejection; do not change scientific thresholds, sample selection or repair gates.
> Authentic processing, research inference, acquisition, spending and merging remain
> prohibited unless separately authorized through their existing gates.

This is deliberately narrower than a general rendering exception. Ordinary native
library operations are permitted only as trusted pinned runtime behavior; document
instructions may never select code, plugins, commands or modules. The current
task does **not** activate even this synthetic exception. An authentic-use
extension would require a further explicit reviewed amendment/activation scoped
to the qualified immutable representation and one replay. It is not hidden in
this proposal. Do not change ADR001 or trusted policy in this PR.

## 3. Original bytes, visibility and MD&A boundary

The engine receives only an isolated selected-document input and emits untrusted
diagnostic records; it never opens the evidence database or writes the archive.
The parent verifies accession/CIK/form/representation, full-response and selected
slice hashes and exact original offsets through the existing read-only evidence
path. No source rewriting, injected text/IDs, script removal or hidden-fact
substitution is part of the route.

**Bridge requirements, tested before adoption:**

1. Keep the existing source token/entity map authoritative. Bind engine DOM
   elements to that map through a side table and exact ordered structural/text
   comparison. No global substring matching, PDF text search or pointer identity
   across processes. Account explicitly for HTML5-implied nontext nodes such as
   tbody, assigning null original spans; only independently proven neutral insertion
   is allowed. Reject any unexplained reparenting/recovery, text change or mismatch.
   If implied nodes alter CSS/visibility, the bridge fails rather than bypassing it.
2. Reconcile every split/merged text fragment to unique original text-node character
   intervals, including mixed text/tails, repeated text, UTF-8 and entities. A glyph
   cluster/ligature may map to a union of original byte spans; it may not manufacture
   a new source character. Preserve source order even when paint traversal differs.
   Only registered whitespace normalization is allowed, with original/null maps.
3. Maintain a complete run ledger with exactly one VISIBLE/HIDDEN/AMBIGUOUS outcome,
   foreground/backdrop, reason, owning context and source/contract/runtime hashes.
   Account for text absent from the layout tree: known display/metadata suppression
   has explicit source-span exclusions; an unexplained absence is A. Partial
   occlusion or insufficient ink/paint evidence is A. Any A rejects the whole
   selected document, including outside MD&A; geometry boxes alone do not waive it.
4. Keep V1's closed passive iXBRL namespace/resource/reference checks and local
   identity/continuation graph outside the renderer. Validate all hidden markup.
   Let the admitted metadata subtree remain hidden; never obtain visible narrative
   from its facts. An engine-normalized QName/value is not original source truth.
5. Reuse the original Item2/body-vs-TOC/next-section boundary checks. The engine's
   section guess, PDF or EdgarTools extraction cannot supply the reference oracle.
   Retain tables as mapped content and headers/footers with audited decisions.
   Compare complete MD&A against an independently frozen reference and all
   exclusions; unresolved material hidden text or missing boundary remains failed.

**Paged engine versus accepted continuous view:** `media_type='screen'` is required
but does not turn WeasyPrint into a continuous browser. Do not simulate infinity
with a guessed huge page, override author page breaks, crop pages, or silently
substitute paged semantics for V1. The synthetic gate must prove source/run identity
and visibility invariant under fragmentation and expose any page-edge uncertainty.
Internal pages may be traversal artifacts only if every source run remains uniquely
accounted and the accepted visibility meaning is preserved. If that cannot be
certified using existing component facilities, fail this route. A changed viewing
meaning needs a separately versioned contract and scientific-consistency review;
it is not an authorized gate repair or default assumption.

The white period remains a processing-default local HIDDEN_CONTRAST result,
historical display UNKNOWN; it is not re-adjudicated here. No authentic MD&A or
byte-map correctness is established by this proposal.

Do not make CSS warnings nonfatal globally. The only candidate exception is an
exact version-bound diagnostic for an existing V1 typed passive SEC metadata
annotation (`-sec-ix-hidden`/`-sec-extract`), whose syntax, ancestry and local target
have already passed the independent metadata validator and have no layout effect.
Record its original declaration span and consumed meaning; retain the source
unchanged. Every other ignored/unsupported declaration, unexpected diagnostic or
unproved rendering effect fails the gate. This is a reviewed integration boundary,
not new custom CSS semantics or authorization to hide warnings.

## 4. One bounded synthetic-only gate — PROPOSED / NOT RUN

**Entry:** separately authorized implementation of a disposable qualification
harness, reviewed §8 exception and exact runtime/fixture manifest. No production
parser patch. Use the pinned candidate only; no alternative version/engine retry,
core fork, monkeypatch, native-code addition, custom layout/paint-order algorithm
or copied upstream algorithm. Maximum500 new nonblank adapter/supervisor lines
(excluding fixtures/tests); exceeding this stop budget is failure, not permission
to grow a framework. Existing evidence/security code is reused, not duplicated.

**Dependency pins:** WeasyPrint source commit above, declared70.0; proposed host
CPython3.13.16 (observed in existing CI), Linux x86_64 canonical OCI image. The
upstream's eight version ranges are **not a reproducible lock**. Before first
fixture, G0 must freeze every direct/transitive artifact and build dependency,
native package (Pango, HarfBuzz, FreeType, Fontconfig, GLib/libffi and all resolved
libraries), OS/image digest, architecture, font files/configuration/family aliases,
trusted UA stylesheet, locale, environment, supervisor and adapter by exact
version/content SHA256. Use no host font discovery/download/fallback. Clear font
license/availability at $0; unsupported glyphs/missing families fail. No versions,
image digest, fonts or hashes are invented here. `evidence.json` distinguishes
the exact source pin from the **UNRESOLVED / NOT_EXECUTABLE** runtime lock. G0's
mechanical lock assembly is part of the single future gate, not permission for
another architecture study; incompatibility/unavailable artifact stops it.

**Enforcement:** one disposable nonroot worker, no capabilities/host mounts,
isolated network/PID namespaces and denied socket/exec/fork operations after
trusted initialization; at most16 runtime threads,64 FDs; read-only image/fonts,
one fixture passed read-only and bounded output pipes; private512MiB temporary
space. Deny-all fetcher for every scheme (HTTP/HTTPS/file/data/FTP/unknown), no
base URL inference. Preflight active-content rejection remains mandatory even
though the engine is not a JavaScript interpreter. Worker output is schema/cap
validated by the supervisor. No PDF export, links/forms/attachments or plugins.

Hard per-fixture limits: input<=40,000,000 UTF-8 bytes, DOM<=100,000 nodes,
depth<=128, decoded text<=2,000,000 codepoints; wall<=20s, CPU<=15s,
whole-worker/cgroup memory<=1GiB, output<=128MiB, temporary space<=512MiB.
Canonical width1280px, white canvas/black initial foreground, pinned fonts/UA;
fragmentation probes use page heights720/1440/8192px with zero page margin.
These are predeclared **engineering resource ceilings**, not measured capacity,
authentic-latency targets, revised scientific thresholds or permission to truncate.

**Fixed manifest:** 16 positive and16 adversarial case families below, maximum64
serialized fixture/parameter variants total, each SHA-bound with independent
expected source/run/visibility/boundary outputs before first execution. Three
fresh worker repetitions per admitted positive case; deterministic map/ledger/
MD&A hashes must match100%, excluding clocks. Resource/denial probes have exact
failure expectations. Aggregate worker wall budget600s across all variants/runs;
external spend$0. No test oracle updates after observing component output, no
repair-and-rerun round. Any failure/limit/unknown => gate FAIL and stop.

| Positive families P01–P16 | Negative families N01–N16 |
| --- | --- |
| P01 plain ordered flow; P02 UTF-8/entities; P03 mixed text/tails; P04 repeated strings with distinct owners | N01 script including hidden ancestry; N02 event/executable URL; N03 deny-all fetcher probes for all six scheme classes; N04 unknown/malformed CSS |
| P05 nowrap/pre-wrap whitespace; P06 contrast/inherited child override; P07 passive iXBRL/visible label; P08 local continuation identity | N05 active foreign/DTD/resource markup; N06 wrong namespace/resource ancestry; N07 duplicate IDs/cyclic references; N08 malformed/reparented HTML |
| P09 bodyMD&A vsTOC; P10 mapped MD&A tables; P11–P15 reuse PR49 F/T/P/W/H positive supplied-metric oracles | N09 wrong source/document/hash; N10 ambiguous fragment mapping; N11 missing/duplicate boundaries; N12 nonempty collapse/visibility override |
| P16 pagination/fragmentation invariance against the independent continuous-view oracle, including forced page breaks and page-edge text | N13 reuse PR49 geometric ambiguity adversaries; N14 missing fonts/ignored CSS/warnings; N15 resource exhaustion; N16 OS isolation/escape probes |

Positive threshold:100% exact expected semantic text, byte-span maps and ledger
accounting, no A, no source losses/duplication/substitution and correct complete
synthetic MD&A. No numeric geometry tolerance can excuse a classification change;
conservative bounds must support the expected outcome. Geometry values/rounding
must be independently checked against pinned native metric/analytic fixture facts,
not copied from this engine's output. Every negative must fail at its specified
boundary; preflight negatives must invoke the component0 times. N03 also directly
probes the fetcher defense; N15/N16 directly test supervisor/OS enforcement using
trusted test probes, never allowing hostile scripts through the renderer.
Allowed extra runtime attempts are exactly those frozen manifest repetitions,
not retries after failure. All outcomes and costs remain in the receipt.

Record stages separately: preflight/identity; DOM bridge; native layout; geometry/
classification; MD&A verification; normalization/chunking; persistence. Measure
monotonic wall and worker-tree CPU, cgroup peak memory, input/output bytes, limit
hits and first failure at each stage. Human review time is separate; research
inference stays NOT_RUN. Report all individual measurements plus descriptive
median/p95/max; tiny synthetic samples are not authentic workload qualification.

Fresh independent reviewer must verify exact code/image/lock/oracle hashes,
containment enforcement, complete source maps and all32 families/parameter cases;
existing repository Ubuntu/Windows tests/demo remain required. Component execution
is qualified only in the canonical Linux image; Windows CI alone establishes no
native-render equivalence. No human/cross-provider review claim unless performed.

## 5. Owner action, stop state and scientific accounting

**Owner decision offered:** review this narrow proposed amendment and bounded
synthetic gate. No gate execution is initiated by this adoption packet. PASS
would establish only eligibility to consider separately authorized integration and
one authentic replay; FAIL ends this candidate without another architecture loop.
The critical unproven risks are the private geometry/ink/paint bridge, HTML5 tree
mapping, pagination equivalence, complete runtime/font lock and actual containment.

No scientific target is lowered:12 distinct accessions, complete MD&A>=90%,
traceability/hashes100%, real schema/support>=95%, zero silent loss/unexplained
integrity failures. Preserve all failures and denominators. If visibility meaning,
material exclusions, sample selection or completeness oracle would change, STOP
for explicit versioned P0-A registration and applicable ADR001§1/§3/§5/§6/§8
scientific review before use; the §8 security exception alone cannot waive these.

ADR001§8 line277's original50-filing **single parser/access repair gate** is
unchanged and separate from P0-A engineering accounting. PR47 used one engineering
repair; V2 stopped before its authorized second implementation/replay. Design,
adoption discussion or synthetic qualification does not reset/extend the scientific
gate or grant an additional authentic attempt.

Current evidence remains1/12 filings, authentic MD&A0/1, real inference and
component processing performance NOT_MEASURED, G4 clock/source/representation
conflicts UNRESOLVED. All original bytes/read-only modes, accepted design baselines,
protected registrations and PR47–49 are preserved. No SEC requests, source rewriting,
parser patches, authentic replay, inference, spending, broker action or merge.

One author and one independent reviewer; requested Sol-class/High, actual serving
IDs/effort unavailable; no qualified cross-provider/human claim. Stop after this
adoption decision. No new open-ended research task or custom layout work.
