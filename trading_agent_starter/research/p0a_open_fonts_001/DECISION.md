# Bounded open-font decision 1.0.0

**OPEN_FONT_ROUTE_RECOMMENDED**, subject to the unapplied contract proposal and
remaining G0 below. This recommends a lawful, retrievable candidate bundle, not
approved equivalence, rendering qualification, cleared G0 or gate authorization.
P0A_INCOMPLETE. PR52 and all protected registrations remain unchanged.

Only the four owner-named candidates were evaluated. Sources are their upstream
Liberation release pages/licenses and Google Fonts' pinned distribution of Carlito
and Noto. Static fontTools inspection read Unicode cmaps, names and metric tables;
no font was installed, shaped or rendered, no WeasyPrint invoked, and no authentic
extraction processor run. Character requirements come only from the hash-verified
retained V2 node/style inventory, including hidden/metadata text; no SEC source was
rediscovered or fetched. No five-gap architectural analysis was repeated.

## Verified artifact and rights result

| Candidate | Exact artifact/version result | Rights and required handling |
| --- | --- | --- |
| Liberation Serif | Upstream binary archive2.1.5, four static faces, embedded Version2.1.5 | OFL1.1; preserve copyright/license and original binaries; no standalone font sale or modified Reserved Font Names. |
| Liberation Sans Narrow | Upstream binary/source archives1.07.6; four faces internally labelled Version1.07.5 | **GPLv2 with Liberation exceptions/additional terms**, not OFL. Preserve COPYING, License.txt, AUTHORS and Oracle copyright in binaries; accompany any redistributed binary bundle with the complete upstream corresponding source archive and required source/modification/reinstallation rights. No modification, renaming or relicensing is proposed. |
| Carlito | Four static1.104 faces at Google Fonts commit e7db6ca603fd4862010383ff17ffd6cc4ffac1c0 | OFL1.1, Carlito Reserved Font Name; preserve copyright/license and unmodified fonts. |
| Noto Sans Symbols / Symbols2 | Noto Sans Symbols v2.003 variable font inspected but lacks U+2610/U+2612; **select only Noto Sans Symbols 2 Regular v2.008** from the same Google Fonts commit | OFL1.1; preserve original copyright/license. No variable instance generation or font binary modification. Symbols2's native synthesis question below remains unresolved. |

The selected bundle has13 unmodified TTFs. FONT_ARTIFACTS.json records **every
individual font's SHA256, internal version, face and static metrics**, binary
archive/source URLs and SHA256, and licenses/notices. The evidence archive includes
all required notices and the Narrow source archive. No Microsoft binary, purchase,
proprietary extraction or unverified mirror was used. Fonts were retrieved through
HTTPS from publisher-controlled GitHub release links or pinned Google Fonts paths.
Hashes establish reproducible retrieval pins, not signed-build attestation or
proof of bit-reproducible source compilation. No compilation was attempted.

The Narrow release/internal-version discrepancy is preserved, not corrected.
Its upstream README notes a historical licensing distinction and that it is not
part of the later OFL2.x family; that is why its own GPL/exception text and source
are retained. Do not label the complete bundle OFL or infer that font licensing
establishes license compliance for all future container software. Ancillary
`upstream_info.md` commentary in Google Fonts is not used as license authority.

## Actual retained-inventory coverage

| Source family | Observed distinct codepoints | Result |
| --- | --- | --- |
| Times New Roman |90, across normal/bold/italic/bold-italic | Liberation Serif's corresponding physical faces cover every required noncontrol codepoint;78 required in bold,40 in bold-italic,86 in regular,1 in italic (overlapping sets). |
| Arial Narrow |1, U+0020, in bold and bold-italic | Both physical Narrow faces cover it. Whitespace still has advance/line-height effects; it is not ignored. |
| Calibri |3, U+000A/U+0020/U+00A0,418 direct text runs | Carlito Regular covers space/NBSP; LF remains a mapped structural control. |
| Segoe UI Symbol |2, U+2610/U+2612,14 runs | Symbols2 Regular maps both to real non-.notdef glyphs;12 runs request normal, **2 request bold**. Symbols2 has no physical bold face. |

COVERAGE.json contains all nine inherited family/weight/style groups, exact
codepoint sets, source inventory hashes and matching files. Tab/LF/CR are the only
non-glyph control exemptions; they remain source-mapped/accounted. This is cmap
availability, **not** shaping, native style coverage, legibility, correct layout or
authentic MD&A qualification. Hidden metadata was included conservatively; no
hidden facts were substituted into visible narrative.

## Deterministic mapping and metrics: feasible, not qualified

The four source family names can be mapped through an isolated Fontconfig
configuration to exact selected files/faces, with no system includes, host font
directories, downloads or implicit fallback. Verify the resolved file hash and
face index after each selection; an unexpected font/style/glyph is AMBIGUOUS and
blocks the whole document. Keep the source family/style unchanged in provenance.
The generic sans-serif suffix in the observed declarations does not authorize
another font if the named candidate is missing. No candidate Fontconfig selection
configuration was installed or executed in this design task.

For the two bold symbol requests the narrow proposal is **explicit native
emboldening of the pinned Symbols2 Regular**, never silent regular-for-bold
substitution. Its exact Fontconfig/Pango/FreeType mechanism, native implementation
hashes, chosen parameters and effect on glyph/advance/ink bounds must be reviewed
and independently qualified in G0/the already frozen synthetic cases before use.
This is a proposed canonical processing assumption, not a physical bold face or
a claim that setting an `embolden` flag is sufficient. If the pinned maintained
stack cannot expose and honor it deterministically without copied layout/native
code, the font route stops. No custom bold font or alternate font search is
authorized. The proposed contract must explicitly approve this policy; without
that approval the original font blocker remains.

Static metrics are now obtainable and hash-bound: each face's units-per-em,
ascender/descender/line-gap and relevant glyph data were read. Noto Symbols2 has
unitsPerEm1000, hhea ascent1069/descent-630; its two required ballot glyphs each
have advance821, xMin51/xMax770, yMin0/yMax719. These are unscaled font-table
values, not native rendered pixels or authentic-position measurements. All native
dependencies/ABIs, fontconfig rules/cache, hinting, synthesis, shaping features,
rounding and environment still need the exact G0 lock. Host fontTools is an audit
reader, not the intended CPython/native layout runtime.

## Materiality and change control

Metric-compatibility descriptions do not establish identical glyph outlines,
bearings, hinting, kerning, line metrics, shaping or wrap/baseline/paint behavior.
Symbols2 is especially not a metric-compatible Segoe UI clone. Even whitespace
and artificial bold can alter geometry, contrast backdrop/occlusion or section
layout. Differences could be material; no before/after Microsoft-font rendering
comparison is claimed or possible from absent licensed originals here.

CONTRACT_1_1_PROPOSED.md is a narrow **unapplied overlay** on V1, not a new runtime
implementation. It requires explicit open-font processing assumptions, exact file/
face mappings, honest synthetic styling, independent oracles, unchanged source
maps and whole-document ambiguity rejection. No inference about any historical
investor's fonts/display is permitted. Canvas, viewport, source order, hiding,
iXBRL, independent complete-MD&A denominator and scientific thresholds stay fixed.

Before use, owner plus independent scientific/security review must accept the
versioned contract and full artifacts/licenses/native manifest. The inactive
ADR001§8 exception proposed in PR52 must be revised by a **new reviewed proposal**
to reference that contract/font manifest; do not silently edit PR52 or bypass its
no-alternative-font prerequisite. Exact font substitutions approved through the
new contract become its named candidates, not a general fallback permission.
The versioned P0-A processing-registration/lineage note must record the new
dependency/font/view assumptions before affected evaluation; original p0a-v1
registration/results remain immutable.

Scientific review must verify consistency with ADR001§1/§3 source evidence,
§5 equal inputs across arms, §6 extraction criteria and §8 complete-sample/no-render
and single-repair rules. If the proposal changes a scientific extraction target,
material exclusion, denominator or acceptance criterion, **STOP for an explicit
versioned scientific amendment** before affected use. Do not lower criteria or
derive an oracle by deleting implementation-excluded material. Synthetic success
alone cannot supply this judgment or qualify an authentic filing.

## Remaining runtime/container/isolation prerequisites

These can be checked separately from layout and authentic text: artifact retrieval/
hash/license/SBOM checks, dependency ABI resolution, Fontconfig config review and
trusted OS-denial/resource probes require no SEC documents or WeasyPrint layout.
PR52 already distinguishes managed Docker capability from coding-sandbox failures;
that evidence is reused, not retested as a rendering experiment.

A new **read-only registry manifest** query found an obtainable Linux/amd64
descriptor for `python:3.13.16-slim-bookworm`:
`sha256:17cbbc787c42807b179b559a5356f87804f01812cbcabd57f2becd3605ce65cd`.
No image layers were pulled, no Python inside it was executed and no container was
created. This descriptor pins an available **base-image candidate**, not the
completed WeasyPrint runtime, verified installed interpreter, license lock or
working sandbox. MANIFESTS.json retains the raw manifest and status.

Remaining G0: independently verify exact CPython/base contents and licenses; freeze
all direct/transitive/native artifacts, OCI image, font/Fontconfig/UA files and
supervisor by digest; validate the proposed native symbol bold treatment; qualify
no-network/no-fetch/no-exec/no-host-evidence isolation and all PR50 hard limits;
freeze independent fixture/oracle manifests under the unchanged16+16/64-variant/
500-line/20s wall/15s CPU/1GiB/600s aggregate/no-repair contract. Do not confuse the
base-image availability or font cmap result with those passes. Lack of an enforced
worker or a style/visibility mismatch still stops the candidate without substitution.

**Next action:** owner review of the narrow V1.1 font/style assumption proposal
and associated scientific/security consistency review. If accepted, resume only
G0 locking/non-layout containment qualification, then seek the existing required
explicit authorization for the single synthetic gate. This task does not apply an
amendment, initiate G0 deployment, run that gate or open another font search.

PR52 remains intact. All15 original evidence files and protected registrations
remain unchanged/read-only. Authentic coverage1/12; authentic MD&A0/1; inference
NOT_MEASURED; G4 conflictsUNRESOLVED. Original scientific single-repair gate is
unchanged and separate from P0-A engineering cycles. No component layout, authentic
replay, custom CSS/layout, broker, license purchase, spending or merge. One author
and independent reviewer; actual serving model/effort unavailable, no qualified
human/cross-provider claim. Stop after this decision.
