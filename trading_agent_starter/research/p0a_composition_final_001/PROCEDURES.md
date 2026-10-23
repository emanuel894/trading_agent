# Five finite decisions and the shared obstruction

Version1.0.0. Extend the **analysis** of V1; do not change its accepted text or
implement these procedures in the extraction processor. Input is the completed,
hash-verified V2 node graph, declaration records and existing baseline, not fresh
HTML parsing. Predicates are sufficient conditions, not a new CSS allowlist.

## Shared admission and certificate rule

First preserve V1's hard failure precedence: wrong source/document identity or
spans, scripts/active content even in hidden trees, unsupported syntax/DOM/CSS,
namespace/resource violations or malformed structure reject. Do not recover,
strip, fetch, execute or substitute hidden facts. Then evaluate the five context
sets, without skipping any because it lies outside MD&A or is already hidden.
All unknown context/visibility/paint decisions are AMBIGUOUS and reject the whole
document. A local closed predicate is never a document pass.

A geometry certificate, where required below, must give conservative bounds on
each source-run's ink/line boxes and each relevant background/border rectangle,
normal-flow allocation, owning stacking context and paint order. For every text
run, require either proven full containment in its admitted backdrop without
occlusion, or a proven HIDDEN reason with original-byte exclusion accounting.
Partial/unknown occlusion is AMBIGUOUS. Bounds must have an independently verified
derivation; declarations, font-family names or application output are not such a
derivation. Finite interval containment/intersection checks suffice **given** a
certificate; this task does not generate geometry or render source documents.

In a future implementation, preserve source-run order regardless of visual paint
order, each entity's exact original byte interval, null generated separators,
original and normalized hashes, visibility/exclusion reasons and context-version
lineage. No generated glyph or hidden iXBRL value can substitute for original text.
Independently review all possible material narrative exclusions; no denominator
shrinking. The accepted passive iXBRL schemas in V1 §7 remain unchanged.

## F — Flex defaults, shrink, min-content

1. Enumerate every flex/inline-flex container and its element children and
   nonwhitespace anonymous text items. Whitespace-only anonymous runs generate no
   flex items; retain them in source accounting. Default direction=row, wrap=nowrap,
   order=0, grow=0, shrink=1, basis=auto. Initial item min-width/min-height=auto
   unless explicitly overridden. Missing declarations are **not** flex:none.
2. Blockify direct element flex items. In particular, display:inline on the42
   right-hand divs does not neutralize width100%. Do not reorder content by visual
   position. Reject reverse/order/offset/clip/unqualified styles.
3. An empty container has no text sizing obligation. For a column with auto main
   size and only a minimum height (not a definite/max height), nonnegative spacing
   and auto child main sizes, content establishes the main-size floor; the minimum
   may add space but does not provide a shrink-to-fit clipping height. Close this
   **local main-sizing** obligation; do not assert ink containment globally.
4. Row/inline-flex cases require main-axis free-space allocation, the automatic
   content-based minimum (including specified-size clamps), explicit percentage
   minima, and the actual ink bounds of anonymous marker text. If certifiable,
   require ordered allocations and no intersecting/hidden ink after shrink;
   otherwise A. Overflow:visible/unlimited scrolling does not prove no collision
   with the next item or another painted context.

**Observed evaluation:** 1 empty column and55 nonempty auto-sized minimum-only
columns close step3 locally. The42 two-item rows each contain one inline-flex
marker plus a width100% blockified div. The42 marker containers each contain
anonymous text (32 bullets; four `1.`, four `2.`, two `3.`), explicit percentage
min-width, and default shrink1. All84 require an absent ink/min-content bound.
All items/defaults/spans are in the detailed records; there are194 direct element
items and42 nonwhitespace anonymous marker segments.

**Obstruction:** a percentage minimum on the marker is not a bound on a glyph's
advance/ink. Even if the next item's automatic minimum makes it overflow rather
than shrink, that is not a proof that marker ink fits its allocation. The positive
and adversarial completions F+/F− show why missing metrics cannot be replaced by
“list marker formatting.” No actual authentic overlap or failure from shrink is
asserted. This cannot close for the observed context from metric-free input alone.

## T — Table painting and visibility

1. Assign every table/tr/td to its table, validate ordered rows/cells and positive
   integer colspans, construct a column occupancy grid and reject unexpected
   nesting/rowspan/context unless explicitly modeled. All81 observed tables have
   equal column sums across their own rows and no nesting/rowspan.
2. Separate borders, zero border spacing, auto table layout and specified widths
   remain distinct from block flow. Row height is a **minimum**, not a clipping
   height. Auto tables may expand beyond a specified percentage to satisfy content
   minima; do not infer overflow or cropping solely from declared widths.
3. For tr collapse, require complete subtree inspection: no visibility override
   and no substantive content for the narrow empty-row proof. Record HIDDEN
   whitespace/spans; retain the collapsed row's sizing/grid influence. A nonempty
   collapse row may never leak into visible text or be silently counted complete;
   abstain under this narrow proof. All81 observed cases close this local predicate.
4. Paint table/column-group/column/row-group/row/cell layers in their defined order
   where present (observed source has table/row/cell only), then borders/content
   at their actual painting steps; transparency exposes lower layers. A row
   background is **not** an inherited CSS background or an infinite rectangle.
   For each run require an ink certificate within the appropriate cell/row
   backdrop and no subsequent layer occlusion, including neighboring rows/cells
   and outer stacking contexts. No certificate or partial coverage => A.

**Observed evaluation:** all18,853 roles inspected;81 local empty-collapse proofs;
remaining18,772 roles await containment.1,088 row height declarations and1,065
opaque row backgrounds (586 white/479 cyan) are covered. Repeated headings/values
in financial tables are not inferred to be MD&A; no boundaries extracted.

**Obstruction:** row minimum height and valid grids do not provide line/glyph ink
bounds relative to later painted row backgrounds. Normal line-height is explicitly
uninterpreted in V1. T− is a countermodel to “minimum height means no occlusion,”
not a claim that this source actually has such overflow. A sound finite interval
decision can verify supplied bounds without rasterizing; it cannot invent them.

## P — Relative position and stacking

1. Require relative positioning, auto offsets (no top/right/bottom/left/inset),
   no transform/float/clipping, source-order normal flow and admitted nonnegative
   spacing. Compute translation=(0,0). All169 observed positioned elements close.
2. Construct the finite stacking-context tree. Body z0 owns112 direct z2 and56
   direct z5 div contexts. Sort sibling contexts by z-index, then source order
   for ties; preserve source order for extraction. z-index has a painting effect
   even with zero offsets. No class name provides CSS or geometry.
3. For every pair of potentially intersecting text/paint owners require disjoint
   conservative ink/paint bounds, or exact qualified non-occlusion. Transparent
   positioned divs can still own opaque row painting. Unknown bounds => A.

**Observed evaluation:** all169 local no-displacement proofs;57 z2 divs have no
nonwhitespace descendant text,55 z2 footers do,56 z5 content containers do, body
does. Emptiness removes own text obligations, not validation or every descendant
paint consideration. Parentage and z-order are recorded for every context.

**Obstruction:** normal-flow border boxes and unchanged reference positions are
not a bound on all descendant ink/overflow. F/T/W/H feed step3. Ignoring z-index
or assuming “relative without offsets is inert” cannot discharge it. No independent
positioning engine is needed to close steps1–2; full closure needs the shared
layout/paint certificate, not an additional CSS-string exception.

## W — Width, nowrap and background interaction

1. Inspect the union of all declarations of width/min-width/white-space/
   background-color, carrying table/flex ancestry and inherited whitespace/color.
   Do not treat these properties independently. Ordinary non-replaced inline
   spans do not acquire a minimum layout width from min-width:fit-content.
   Distinguish blockified direct flex items and inline-flex containers.
2. Resolve percentages to the correct containing width, box-sizing/padding and
   formatting context. Table cell percentages are constraints, not automatically
   final used widths. nowrap contributes intrinsic constraints; pre-wrap preserves
   whitespace/break opportunities and source order. Neither authorizes deleting
   a word or cropping at the viewport. Honor inherited word-break semantics.
3. Verify intrinsic/used widths, permitted overflow, wrapping/line/ink bounds and
   opaque painted regions jointly. A valid proof needs that no source ink can
   cross into a different background or be occluded. Only then apply V1's contrast
   table per run; unknown allocation/ink => A, not automatic VISIBLE/HIDDEN.

**Observed evaluation:** all33,813 elements in this union evaluated and mapped to
original spans/context. This includes all1,244 width declarations,18,015 minima,
25,597 whitespace declarations,6,142 nowrap cells and1,065 row backgrounds.
All17,931 fit-content spans are ordinary inline contexts, including42 under the
right-hand inline divs; none obtains a fit-content width guarantee. All42 right
divs are direct flex items and blockified, however. The ineffective span property
is not stripped or generalized into accepted arbitrary CSS; its no-sizing-effect
semantics is recorded, while the containing composition still abstains.

**Obstruction:** equal palette colors can settle contrast only with a known
painted backdrop. Row backgrounds have finite painted regions, and another row
can paint over unbounded ink. Metrics/line allocation are absent. W− invalidates
an independent width/nowrap/bg allowlist; it does not assert that an auto table
uses the adversary's fixed cell allocation on this authentic source.

## H — The observed hanging indent

Node4996 is a cover-page p containing checkbox U+2610 (Segoe UI Symbol/sans-serif,
9pt) and transition-report text, not the white-period node. Ancestors are z5
div4968, body4 with padding8px, html0. No intervening width/offset/border declaration.
V1 nominal viewport1280 minus body horizontal padding16 gives containing width
W=1264px. Both percentage padding and text-indent resolve against this containing
width; they must not be subtracted as percentages of different boxes.

```
padding-left = 0.03333 W = 42.12912px
text-indent  = -0.03448 W = -43.58272px
first-line reference x = 8 + padding-left + text-indent = 6.54640px
```

1. Require exactly this independently characterized *pattern*, not a source-span
   whitelist: block p, nonnegative remaining spacing, no reordering/clipping,
   deterministic containing width and percentage resolution. Unknown ancestry => A.
2. Compute the signed reference position using exact decimal/rational arithmetic.
   If negative, do not silently clip; A unless separately proven retrievable
   with the admitted view. Here it is positive; that local arithmetic closes.
3. Require a lower bound on the leading glyph's ink bearing and bounds on all
   first/subsequent line ink and surrounding paint. If the left edge can cross
   x=0 or other paint/line containment is unknown => A. A positive reference point
   alone is not an ink bound. No glyph bound exists in V1/inventory, so this single
   observed pattern does not close.

H+ and H− differ only in supplied bearing, demonstrating the missing premise
numerically. The adverse bearing is a logical countermodel, **not a measured
property of Segoe UI Symbol or this historical filing**. Pinning a font later
would establish a new processing fact, not historical investor rendering truth.

## Common impossibility scope and alternative

The finite procedures above terminate and safely abstain when their premises
are missing. They cannot produce an admitting result for all observed contexts
under V1's metric-free/no-uncertain-overlap guarantees: the same declaration/tree
input has no discriminant between the metric completions in the oracles. This
does not prove no finite algorithm with more independently grounded inputs can
ever work. It proves why the *current* evidence/contract cannot qualify the
observed compositions without supplying layout/ink semantics or changing the
claimed extraction meaning. See DECISION.md for the single recommended alternative
and exact no-render/scientific change-control boundary. No further rescue loop.
