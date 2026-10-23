# P0-A Canonical Visibility Contract 1.0.0

Contract ID: `p0a-canonical-visibility-1.0.0`. Date: 2026-10-23 UTC.
**Design only; implementation and one authentic replay require separate owner
authorization. NO-GO for implementation/replay readiness until composition rules
are qualified. Overall P0A_INCOMPLETE.** This specifies a canonical processing
view, not a reconstruction of any historical investor's display or knowledge.

Normative MUST/REJECT requirements below apply to the proposed finite semantic
profile. They do not assert that the current parser implements them. All referenced
V2 inventory artifacts are bound by SHA256 in `evidence.json`; none was regenerated.
Source and protected scientific registrations remain unchanged.

## 1. Purpose, boundary and determinism

Derive source-grounded Part I Item 2 MD&A from one provenance-verified original
10-Q representation, with explicit visibility outcomes and original-byte maps.
The original response, full source text and each derived version remain distinct.
Only the complete-submission path is a candidate for the next implementation.
The failed scripted direct primary remains preserved. Multiple representations
of accession `0000950170-25-067613` still count as one filing.

Determinism means equal raw bytes + source identity + contract/profile/policy/code
hashes produce equal classification records, normalized MD&A, maps and chunk
hashes. Run timestamps, durations and receipt IDs are excluded from that equality.
It does not mean pixel-identical output across browsers. No browser's implicit UA
styles, system theme, installed fonts or error recovery may supply hidden defaults.

## 2. Canonical environment: explicit processing assumptions

| Setting | Normative value/meaning |
| --- | --- |
| Canvas/backdrop | Opaque sRGB white `#ffffff`, including unpainted document regions |
| Initial foreground | Opaque sRGB black `#000000`; inherited until an admitted explicit color overrides it |
| Initial element background | Transparent; resolve contrast against the nearest admitted opaque ancestor background, then white canvas |
| View | Screen, light scheme, zoom 100%, device scale 1, CSS reference pixel 1/96 inch; 1pt = 4/3 CSS px |
| Nominal viewport | 1280 x 720 CSS px; continuous document with unlimited scrolling; viewport position never deletes text |
| Initial font/flow | Logical `Times New Roman`, 16 CSS px, normal weight/style; normal line-height is an uninterpreted annotation, never measured font height; document-order reading, LTR horizontal flow |
| UA structure/box defaults | Closed roles below; margin/padding/border=0, background transparent, position static, z-index auto, visibility visible, opacity1, no clipping/offset/order/transform; no platform stylesheet imports |
| Link state | Inert, unvisited; no hover/focus/visited/user stylesheet variation or URL activation |
| Fonts and glyph layout | Only the finite font-family vocabulary below; family names remain logical labels, not permission for platform font discovery or downloads |
| Dynamic/foreign content | No scripts, event handlers, frames, embedded objects, images, forms, SVG, MathML, animations, transitions, generated content, external CSS/fonts or network |

This finite view does **not** calculate glyph positions, line wrapping, pagination
or font-specific rasterization. It qualifies text visibility only where the
restricted flow/contrast predicates in section 5 make those quantities irrelevant.
Any decision requiring font metrics, clipping geometry, uncertain paint overlap,
glyph shaping or scroll-position observation is AMBIGUOUS and blocks admission.
A rendering backend would need its own exact engine/build/dependency/font/container
hashes; the logical font names above would not pin its physical rendering.

Document-supplied colors/backgrounds override defaults only through admitted
inline declarations. No stylesheet, media query, CSS variable, URL, downloaded
schema, UA import or system preference can alter the environment.

Closed roles for all38 observed kinds:

| Kinds | Structural role |
| --- | --- |
| html, body | One document root and one flow root respectively |
| div, p, h1, h2 | Ordered block boundaries; no implicit heading font or margins |
| span, a | Inline text; a inert |
| br, hr | Structural separator, no invented narrative; generated intervals null |
| table, tr, td | Table container, row, cell respectively; never equate row/cell semantics with ordinary blocks; positive integer colspan, source order |
| head, title, meta | Non-narrative head metadata; passive meta rules required |
| ix:nonnumeric, ix:nonfraction, ix:continuation | Inline facts/continuations unless qualified metadata ancestry hides them |
| ix:header, ix:hidden, ix:references, ix:resources | Typed metadata containers; section7 schema mandatory |
| link:schemaref | Passive nontext schema reference, never fetched |
| xbrli:context/entity/identifier/period/segment/startdate/enddate/instant | Typed context metadata under resources |
| xbrldi:explicitmember | Typed dimensional metadata under segment |
| xbrli:unit/divide/measure/unitnumerator/unitdenominator | Typed unit metadata under resources |

Legacy tags not in these38 kinds are not automatically in this submission profile.
Unknown roles reject/abstain; none is inherited from a browser. This table defines
source structure, not table-painting geometry. Actual rendering of untrusted
filings remains prohibited by ADR001 §8 lines296–298; a documentary comparison
does not authorize an exception.

## 3. Outcomes and whole-document admission

Every text run has exactly one outcome, plus a reason and provenance:

- **VISIBLE:** admitted structural text whose visibility is established under
  this contract. Eligible for MD&A boundary/normalization processing, not automatic
  assertion truth or materiality acceptance.
- **HIDDEN:** a proven exclusion, such as qualified metadata, display:none,
  visibility:hidden, qualified collapsed table row, or equal opaque foreground
  and resolved background. Preserve original text and spans in the exclusion
  ledger; do not silently erase it or substitute hidden fact values.
- **AMBIGUOUS:** unknown/unsupported/malformed/conflicting visibility or an
  unproved composition predicate. Retain evidence and reason. No text preparation
  is admitted, including when the ambiguity appears outside MD&A.

Active content, provenance failure, malformed identity, duplicate/invalid
attributes and malformed DOM are hard rejections, not harmless HIDDEN content.
All markup/CSS is validated even inside hidden subtrees. A script anywhere in the
selected 10-Q HTML causes rejection; it cannot be removed, skipped or executed.

Document admission requires zero AMBIGUOUS runs/constructs in the entire selected
document, no active/integrity failures, and complete classification accounting.
Unresolved materiality of an exclusion also blocks complete-extraction acceptance.
Do not relabel an abstention as successful partial extraction.

Evaluation precedence: hard rejection first; any unproved syntax/context/composition
then makes the final outcome AMBIGUOUS and blocks the document. Only after those
guards may proven HIDDEN or VISIBLE be assigned for admission. Local contrast
subresults may be recorded diagnostically; they cannot override unknown ancestor
painting or discard text from a failed document. Parent contrast hiding is not
a subtree flag; metadata/display hiding is, with all descendants still validated.

For every nonwhitespace HIDDEN run, distinguish typed non-narrative metadata from
possible narrative/heading/table content. Possible material MD&A text, or content
whose exclusion could affect section boundaries, requires independent source-grounded
review before any complete-extraction claim. A hidden material assertion or
unresolved classification remains a failed/incomplete filing; the new view cannot
make it disappear from the denominator. Whitespace-only structural rows/spacers
are separately recorded. Visible page headers/footers are not silently deleted.

## 4. Color, whitespace and hiding semantics

Foreground is inherited; backgrounds are not inherited CSS properties, but the
effective opaque backdrop is resolved through the qualified ancestor painting
chain. Supported foregrounds: black, blue `#0000ff`, white. Supported opaque
backgrounds: white, black, pale cyan `#cff0fc`. Explicit transparency, alpha text
colors, blend/filter rules, background images and unqualified colors are AMBIGUOUS.

Exact contrast oracle (foreground, resolved opaque backdrop):

| Pair | Outcome |
| --- | --- |
| Equal supported colors | HIDDEN_CONTRAST |
| Black/white, black/pale-cyan, blue/white, blue/pale-cyan, white/black | VISIBLE, subject to flow/other hiding predicates |
| White/pale-cyan or blue/black | AMBIGUOUS; do not equate low contrast with absence |
| Unresolved/other | AMBIGUOUS |

This is a finite conservative classification, not a calibrated legibility or WCAG
claim. No empirical contrast threshold is added to scientific acceptance.
Contrast hiding applies to text runs, not unconditionally to a whole subtree:
a child foreground/background override must be resolved independently. By contrast,
display:none hides its entire subtree; children cannot resurrect it.
visibility:hidden/collapse are accepted only where the profile models their
inheritance/context exactly; unsupported child visibility overrides are rejected.

collapse is permitted only on qualified table rows. Its text must be HIDDEN or
the construct rejected, including adversarial nonempty rows. The observed 81
empty rows are evidence, not a rule that all collapsed rows are empty. Header,
table-cell and nested-table context remains auditable after exclusion.

Text is decoded without replacement. Each entity expansion maps back to its exact
original entity byte interval. Retain canonical-visible text before normalization;
the existing whitespace-only normalization may then collapse whitespace with
recorded original/null generated spans. Preserve punctuation, case, words, numbers
and text order. No ligature/OCR/semantic rewrite, dehyphenation or hidden-fact
replacement is authorized. nowrap/pre-wrap do not permit source-word deletion.

## 5. Finite CSS/DOM profile and compositional restrictions

The V2 inventory is the measured vocabulary: 38 element kinds, 45 CSS properties,
370 property/value pairs, 54,365 style attributes. Its `css.json` and `nodes.json`
are a maximum observed vocabulary/context reference, **not an acceptance oracle**.
Every admitted declaration needs a tag/parent/context rule plus the predicates
below; observing a string in authentic bytes never makes it safe. Exact grammar,
context policy and structured exclusions must be frozen/hash-bound before any
future authentic replay. Unknown syntax/values/contexts abstain; no fallback.
The explicit palette adds black-background unit-oracle cases beyond observed
backgrounds; this grants no unqualified layout context.

| Property family | Required qualification |
| --- | --- |
| color/background-color | Section 4 palette, inherited foreground and resolved backdrop; no alpha text/background or image |
| display | none, inline, flex, inline-flex only in qualified contexts; no reordering, offset or clipping side effects; explicit hidden precedence |
| visibility | hidden or tr-only collapse with qualified inheritance; no implicit override assumptions |
| position/z-index | relative only; body z-index 0 and qualified div layers 2/5; no offsets, absolute/fixed/sticky positioning, transforms, floats, clipping or uncertain overlap |
| width/min-width | Positive finite percentages or qualified fit-content; widths never authorize viewport truncation; unresolved min-content/overflow interactions abstain |
| height/min-height | Height only as minimum table-row height in table layout; min-height only in proved normal-flow containers; no fixed/max-height clipping boxes |
| margin/padding/text-indent | Admitted nonnegative spacing and auto contexts; body padding8px and margin:auto!important exact; one qualified hanging-indent pattern only after proving no hidden/off-canvas text |
| font-size/family/style/weight/kerning | Positive finite sizes; observed 1pt only for whitespace-only runs, otherwise AMBIGUOUS; families Times New Roman, Arial Narrow, Calibri, Segoe UI Symbol plus sans-serif fallback; no downloaded fonts |
| text-align/decoration/vertical-align | Qualified source formatting; no semantic or text-order conversion |
| white-space/word-break | nowrap/pre-wrap and admitted breaking modes preserve source word order/content; metric-dependent visibility abstains |
| borders/border-spacing/collapse/box-sizing | Finite source table contexts; border alpha is not text alpha; no inference that arbitrary dimensions cannot occlude text |
| flex-direction/align-items/justify-content | Only qualified normal-flow column/baseline/start/end structures with invariant source order; no generic flex layout permission |
| page-break-after | Audit page-break annotation; no deletion, pagination-generated text or viewport clipping |
| -sec-ix-hidden/-sec-extract | Typed inert local annotation/reference rules in section 7; never executable or a generic hide directive |

Validate declaration tokens and delimiters, property identity, finite numeric
values, units, duplicates and priority. Reject duplicate properties/attributes,
CSS escapes/comments/functions/imports/custom variables, URL/expression constructs
and shorthand ambiguity outside explicitly expanded finite rules. !important is
not stripped: only the exact qualified margin:auto!important rule is admitted;
other priority uses abstain. Hex alpha border values require their own passive
border rule and cannot be generalized to foreground/background transparency.

Normal-flow proof is document-wide: relative positioning has no offsets; no
negative margins, clipping, reordering, opaque overlap of text or generated
content. Table minimum sizing, nonshrinking/fit-content text, spacing and stacking
contexts must compose without hiding/reordering source runs. Retain a predicate
receipt for each qualified context. If that proof needs a general layout engine,
stop this finite profile; do not declare the context cosmetic. The inventory shows
why a finite proof is plausible, not that every proof has already passed.

**Closed decision for version1.0.0:** complete finite decision procedures/witness
schemas for flex defaults/shrink/min-content, table painting, relative stacking,
hanging-indent geometry and interacting width/nowrap/background are not supplied
by this packet. Every such composition without a normative procedure is AMBIGUOUS;
an implementer cannot invent an acceptance rule and call it qualified. The authentic
source uses these cases, so this version cannot admit it. NO-GO for implementation
and replay until a reviewed next profile/design version supplies those bounded
procedures or an explicitly permitted alternative. This conservative abstention
defines a deterministic reference contract, not an implemented source-compatible
CSS profile.

## 6. Concrete white-period adjudication

Source element interval `[362751,362940)`; period itself `[362932,362933)` in the
original complete submission. It is a span with explicit white foreground and no
opaque background ancestor. Under **this contract's white canvas assumption**, its
resolved backdrop is white and its **local contrast oracle is HIDDEN_CONTRAST**. Keep `.` and
both intervals in the exclusion ledger, with this contract hash and assumption
label. Do not transform punctuation through whitespace normalization.

This is a generic color/backdrop rule, not an exception for an accession, span,
period or location outside MD&A. The V2 source still establishes only the white
foreground and lack of explicit background. Its historical visibility remains
UNKNOWN; no investor display, theme or publication/knowledge time is inferred.
This resolves the canvas-default design question, not unqualified ancestor
painting/layout. Final source-run/document admission remains AMBIGUOUS until those
separate composition predicates pass. Independent source review must confirm any
eventual exclusion's non-MD&A/nonmaterial
role before complete-extraction acceptance. Classification is a design adjudication;
no parser or authentic replay has implemented/verified it in this task.

## 7. Passive iXBRL and document isolation

Select exactly one original TYPE10-Q TEXT through existing accession/form/CIK and
provenance checks. Retain the complete SGML response, its document envelope manifest
and excluded-document hashes/spans. The 95 envelopes are not independent filings.
164 script start-tokens in 82 other envelopes are explicitly accounted, not silently
sanitized. No external link/exhibit/schema is followed; no claim that the complete
submission response is script-free. The selected HTML must itself be script-free.

XML namespace URIs must match declared supported prefixes. Permit ix:references
only directly under a qualified ix:header; permit link:schemaRef only there with
qualified xlink:type=simple and passive URI grammar. Never resolve or fetch it.
Permit ix:resources only under that header and validate supported XBRL context,
entity, identifier, period, segment, explicitMember and unit/divide structures by
tag/parent/attribute type. Suppress their metadata text without suppressing validation.
Misplaced/forged namespaces, active children or unknown resource markup reject.

IDs must be unique; contextref/unitref targets must have the correct local type;
continuedAt targets must be valid continuations with an acyclic bounded graph.
xsi:nil is a typed fact attribute, not permission for arbitrary attributes or
contradictory nonempty content. Visible iXBRL fact/continuation text stays exactly
once in document order with original spans; do not concatenate it again by graph.

-sec-ix-hidden on a qualified visible span references one existing fact inside
ix:hidden. Preserve the span's own text/bytes. The observed 15 references include
single/1, twenty/twenty years and labels/taxonomy URIs; none authorizes substitution,
fact promotion, conversion or hiding of the visible span. -sec-extract:exhibit is
an inert audit annotation on a qualified link, never a request to follow it.

### Closed passive metadata schema

Core namespace bindings are html=`http://www.w3.org/1999/xhtml`,
ix=`http://www.xbrl.org/2013/inlineXBRL`,
xbrli=`http://www.xbrl.org/2003/instance`,
xbrldi=`http://xbrl.org/2006/xbrldi`,
link=`http://www.xbrl.org/2003/linkbase`,
xlink=`http://www.w3.org/1999/xlink`,
xsi=`http://www.w3.org/2001/XMLSchema-instance`.
Other taxonomy bindings must match the root pairs in hash-bound V2 attributes.json;
new pairs need a reviewed profile version. No nested rebinding, arbitrary prefix
acceptance, DTD/entity resolution or namespace/schema fetch.

| Node | Exact metadata context/content/attribute schema |
| --- | --- |
| ix:header | At most one, under div with proven display:none; no attrs; children ix:hidden then ix:references then ix:resources, whitespace otherwise |
| ix:hidden | Header only, no attrs; typed nonnumeric/nonfraction facts only; hidden text still validated |
| ix:references | Header only, no attrs; one schemaRef, whitespace otherwise |
| link:schemaRef | references only; empty; exactly xlink:type=simple and xlink:href ASCII basename ending .xsd, <=128 chars, no slash/colon/percent/query/fragment/'..'; never fetched |
| ix:resources | Header only, no attrs; context/unit children, whitespace otherwise |
| xbrli:context | resources only; one unique id attribute; entity then period |
| xbrli:entity | context only, no attrs; identifier then optional segment |
| xbrli:identifier | entity only; scheme=http://www.sec.gov/CIK only; digit text equals verified filing CIK; no children |
| xbrli:segment | entity only, no attrs; one or more explicitMember children |
| xbrldi:explicitMember | segment only; dimension bound QName attribute; bound QName text, no children |
| xbrli:period | context only, no attrs; instant OR startDate then endDate; ISO dates and start<=end |
| xbrli:instant/startDate/endDate | period only, no attrs/children; one ISO date |
| xbrli:unit | resources only; one unique id; one measure OR one divide |
| xbrli:divide | unit only, no attrs; unitNumerator then unitDenominator |
| xbrli:unitNumerator/unitDenominator | divide only, no attrs; one measure |
| xbrli:measure | unit or numerator/denominator only, no attrs/children; one bound QName text |

Facts require unique id, bound-QName name and valid contextref. Optional unitref,
decimals, scale, sign, format, continuedAt, escape and xsi:nil require the typed
fact rule: decimals signed integer/INF; scale signed integer; sign '-' only;
format bound QName; escape/nil true/false. True nil forbids nonwhitespace content.
No other attrs. Continuations require unique id, optional continuedAt only, visible
flow ancestry (not resources). Each continuedAt has one target, no target has more
than one incoming continuation edge, the graph is acyclic and chain length<=128.
Context/unit references resolve to exact resource types; vendor refs resolve to
hidden facts. No suffix-name matching or hidden fact supplies missing provenance.
These are declarative design requirements, not implemented validators. Existing
40,000,000-byte input and2,000,000-codepoint text limits stay unchanged; any new
execution limits must be frozen before separately authorized processing.

## 8. Evidence, admission and next authorization

Before preparation persist a classification/exclusion ledger covering every
decoded text run and every unsupported/active construct, even for failed documents.
Each record binds original response SHA256, source observation/accession/representation,
node/text original byte intervals, tag/ancestor identity, decoded text hash,
VISIBLE/HIDDEN/AMBIGUOUS + reason, effective foreground/backdrop and defaults used,
visibility/layout predicate references and code/profile/contract hashes. Retain
original text in immutable objects; generated separators have null source intervals.
Whole-document and MD&A accounting must reconcile all runs without gaps/duplication.

Identity, parsing/classification, boundary extraction, normalization/chunking,
validation and persistence remain distinct stages. Inference fields stay null/
NOT_MEASURED without separate authorization. The filing is complete only after
independent canonical-view comparison, boundary/text/span/chunk checks and exclusion
materiality review; code or schema success cannot substitute for those checks.

This design recommendation does not spend/reset a repair cycle, authorize a
replay, waive ADR001's original 50-filing single-repair gate or qualify P0-A.
See CHANGE_CONTROL.md and TEST_MATRIX.md. Any behavior change requires a new
contract/profile version, retained old results and fresh review. No adaptation
using stock outcomes, no sample replacement and no alternative renderer on failure.
