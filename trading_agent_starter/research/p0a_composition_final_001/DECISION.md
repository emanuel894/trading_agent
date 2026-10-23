# Final bounded composition qualification 1.0.0

**B — ARCHITECTURAL BLOCKER. NO-GO for the proposed metric-free compatibility
implementation and authentic replay. Overall P0A_INCOMPLETE.**

This is the final focused decision on the five gaps in accepted design baseline
`p0a-canonical-visibility-1.0.0`, PR48 at
`2678ff551696adf9fe0524c9d1c89ec73bf304e8`. The baseline remains unchanged.
No application parser was changed or invoked. The new evaluation reads only the
nine hash-bound, completed V2 inventory artifacts; it neither discovers source
constructs again nor produces authentic extracted text.

## What closes, and what does not

| Gap | Exhaustive retained-instance evaluation | Conclusion |
| --- | --- | --- |
| Flex defaults, shrink, min-content | 140 containers: 56 column (55 nonempty), 42 row wrappers, 42 inline-flex markers; all direct element/anonymous text items recorded | Column main-size and empty-container obligations close locally. All84 row/marker contexts need ink/min-content bounds absent from the baseline. `display:inline` flex items are blockified; width100% remains relevant. |
| Table painting/visibility | All81 tables,1,178 rows,17,594 cells (18,853 records); each table's column sums agree, no nested tables/rowspan; all81 collapse rows empty without visibility overrides | Empty-collapse exclusion closes locally. The other18,772 records track unresolved table geometry/painting contexts, not18,772 indispensable ink certificates. Grid consistency and minimum row heights are insufficient. |
| Relative positioning/stacking | All169: body z0;112 divs z2;56 divs z5; no offsets or other displacement/clipping properties | Zero translation and finite paint ordering close locally. They do not certify disjoint painted text/background extents of the owned subtrees. |
| Width/nowrap/background | Every33,813 element with any width, min-width, whitespace or background declaration;1,244 width declarations,6,142 nowrap cells,1,065 row backgrounds; all17,931 fit-content spans are ordinary inline boxes | `min-width` does not constrain those ordinary inline spans. Auto tables may expand to content minima; no actual overflow is asserted. Their allocation, line/ink extents and painting remain unproved. |
| Hanging indent | The sole negative indent, node4996, original bytes[361570,362409), evaluated algebraically with its full ancestor context | First-line reference x=6.5464px is inside the canvas. The left ink bearing of its checkbox is unbounded by the logical font contract; whole-run containment does not close. |

52,976 gap-instance records cover37,080 distinct inventoried nodes. Memberships
overlap and are not independent samples or counts of actual hidden text. Empty
roles can affect sizing/painting without containing text; collapse proof covers
its descendants, even though their table-context records remain in the list. The
remaining nodes have none of these directly inventoried declarations/structural
roles; ancestors and all direct flex items are retained in the records. This is
exhaustive coverage of the five specified construct sets, not a new source audit
or a successful whole-document visibility classification.

## Why this is a blocker, rather than another missing allowlist

[PROCEDURES.md](PROCEDURES.md) supplies finite local decisions, explicit missing
premises and countermodels for each gap. [ORACLES.md](ORACLES.md) supplies positive
and adversarial expectations independently of the application parser. Local
proofs do remove uncertainty: collapse emptiness, table grids, default flex rules,
zero displacement, paint ordering and hanging-indent reference arithmetic are
now decided. What remains is a shared, concrete dependency: **bounds on text
advances, bearings, line boxes and their relationship to adjacent text, finite
table backdrops and other stacking contexts**.

V1 deliberately specifies logical font names and uninterpreted normal line height,
with no physical fonts, glyph metrics, wrapping or paint geometry. The inventory
does not contain these bounds. Its observed marker minima, inline fit-content
and percentage widths cannot supply them. Two metric completions consistent with
those unmeasured annotations can satisfy or violate the inequalities in the
oracles. Choosing the favorable completion would introduce an unsupported viewing
assumption; ignoring the inequalities would weaken V1's no-uncertain-overlap rule.
Consequently a sound decision from this evidence returns AMBIGUOUS, which rejects
the **whole selected document**, including ambiguities outside MD&A.

This is an information/qualification result under the frozen baseline, **not a
claim that CSS is undecidable, every actual run overlaps, browsers are necessary,
or no future finite proof with independently established metric bounds can exist**.
Those bounds are absent now. Building enough custom flex/table/text layout to
manufacture them would cross the current finite, metric-free design boundary.
No new research loop to search for a favorable bound is recommended.

## Smallest defensible alternative and exact control boundary

Recommend a maintained, deterministic **text-layout and paint-geometry component**
behind the existing immutable mapper/identity/security validators, rather than
another ad hoc CSS patch or a browser agent. It must establish pinned fonts and
shaping/line metrics, flex/blockification/min-content constraints, table grid and
layer painting, and conservative ink/occlusion bounds. Pixel rasterization and
browser automation are not inherently necessary; layout/paint semantics are.
The already inspected pinned WeasyPrint70.0 is a candidate, not an adopted or
qualified dependency. Reuse PR48's comparison; do not repeat broad research.

**Before processing authentic documents with such a component:**

1. Obtain an explicit reviewed amendment to **ADR001 §8, Untrusted documents,
   lines296–298** (currently “never execute, render or follow”), and consistent
   trusted security policy, defining whether bounded inert layout counts as a
   permitted rendering exception. Do not relabel rendering as parsing to evade
   that rule. Any exception must retain script/active-content rejection before
   the component, deny all fetches/DTD/schema/font downloads, prohibit executable
   document behavior, constrain resources, and fail on unsupported/recovered or
   untraceable content. This document proposes the boundary; it amends nothing.
2. Version the visibility contract to pin actual fonts/metrics, component/build/
   native dependencies, UA defaults, screen/continuous layout, rounding, shaping,
   whitespace, paint/occlusion policy and ambiguity rules. Qualify synthetic
   oracles and a source-span bridge first. A PDF/text dump alone cannot prove
   byte provenance or complete extraction. No scientific threshold needs lowering
   if the original semantics and denominators are actually preserved.
3. Separately authorize one bounded implementation and **one** immutable
   complete-submission replay only after reviewed qualification. No such authority
   is supplied here. Preserve the scripted direct-primary failure and all drafts.

The smaller *semantic* alternative is a separately registered source-order DOM
text experiment that does not claim rendered-visible completeness. That is a
different extraction target, **not an approved fallback**. It requires explicit
amendments to P0-A REGISTRATION's fixed visible-text/ambiguity/complete-MD&A,
hidden-iXBRL and zero-silent-loss evaluation contract, and, before scientific use,
ADR001 §1 original-MD&A interpretation, §3 evidence/derived lineage, §6 extraction
gate and §8 complete parsed/comparable sample rule, plus §5 equal inputs across
arms if affected. Specify independent reference text, all exclusions/uncertainties,
unchanged or explicitly revised denominators and old/new result separation before
evaluation. Accepting ambiguity, omitting material text or shrinking an oracle
cannot be introduced as an engineering configuration. No amendment is written.

**Shortest next action:** owner review of this blocker and an explicit, versioned
decision on the bounded inert-layout exception. If declined, stop this visibility
path; use a separately registered semantic-text experiment only if authorized.
Do not authorize another metric-free parser patch or immediate authentic replay.

## Evidence, counters and residual risk

- Independent filing coverage remains1/12, successful authentic MD&A0/1.
  No new extraction evidence exists; the last actual replay still failed
  UNSUPPORTED_CSS. Real inference, correctness, latency and memory remain
  NOT_MEASURED, with no inference authorization/configured qualified route.
- The white period at element[362751,362940), text[362932,362933), retains only
  the accepted local white-canvas HIDDEN_CONTRAST result. Historical display is
  UNKNOWN and whole-document qualification has not occurred.
- Original bytes, source order, offset maps, exclusion ledger, passive iXBRL
  restrictions, active-content rejection and materiality review remain mandatory.
  This JSON-only evaluation makes no new byte-map/extraction correctness claim.
  G4 physical-clock/source-clock/representation conflicts remain UNRESOLVED.
- PR47 used one P0-A engineering repair. V2 stopped before its authorized second
  implementation/replay; these two design tasks spend/reset none. The original
  scientific50-filing single-repair gate at **ADR001 §8 line277** is separate and
  unchanged. No engineering authorization waives it; no third attempt is granted.
- Residual risks: deterministic layout and provenance bridge are unqualified;
  an engine may recover/ignore unsupported content; metric pins alone do not prove
  complete extraction; hidden material needs independent adjudication; single-file
  format feasibility does not establish12-filing or scientific qualification.
- Source parsing/rendering/replay/inference/SEC requests/spending/merges: all0.
  Ten scalar synthetic-oracle arithmetic assertions passed; these are not CSS
  processor/security regression tests. Existing repository CI, if run, is ordinary
  regression evidence only, not this design's runtime qualification.

One author plus a fresh independent design/evidence reviewer. Requested reviewer
preset gpt-6.1-sol/high; actual serving model IDs/effort are unavailable. No human
or cross-provider qualification is claimed. Final review/CI receipts accompany
the draft documentation PR and evidence packet; implementation remains NO-GO.
