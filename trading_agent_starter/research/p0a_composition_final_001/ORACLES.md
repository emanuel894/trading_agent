# Independent oracle matrix 1.0.0

These expected results are declarative and independently checkable by inequalities,
CSS formatting roles and source-accounting assertions. They are **not** reference
outputs of the application parser or authentic extraction. Supplied rectangles/
metrics are synthetic premises, not results computed from authentic HTML. The
evaluation executes only the ten explicitly named scalar arithmetic assertions;
all CSS/DOM/security/runtime cases below remain PROPOSED / NOT_EXECUTED.

V means eligible only after every other V1 guard passes. A means whole-document
AMBIGUOUS rejection; R means hard rejection. Local closures never override A/R.

| ID | Positive premise and independent expected oracle | Adversarial mutation and independent expected oracle |
| --- | --- | --- |
| F | Row available100px; marker allocation/minimum3px, ink wholly inside0..3; content preferred100/min20; grow0/shrink1/basisauto, no reordering; final widths3+97=100 after freezing marker minimum. With supplied nonintersecting ink bounds: local fit closes. | Marker still allocated3 but ink extends to6; next run starts at3. Intersecting ink is not ruled out => A. Remove metric certificate => A. Set reverse/order/offset => R/A, never source reorder. |
| T | Two separate-border zero-spacing cells40/60px, row y0..12, all ink y1..11 within cells; adjacent-row ink y13..23; exact row/cell backdrop/paint premises. Empty collapsed row has no overrides and retains grid/spans => local background and collapse proofs close. | First run ink bound x0..10/y8..14, adjacent row run x0..10/y12..22:14>12; containment/nonintersection is unproved => A. This does not establish actual glyph intersection or assume the next row background paints above prior cell text. Nonempty collapsed narrative/heading => A under narrow empty proof; visible descendant override => A/R. Invalid colspan/grid/rowspan not modeled => R/A. |
| P | Text/paint owner extents y0..10 and20..30, zero translations, z5/z2, source-stable order.10<20 => no owner intersection regardless of layer order. | First owner's ink extends to23 against paint starting20:23>20 => A unless exact independently certified non-occlusion. A transparent parent with opaque descendant is not a no-paint certificate. Add left/top/transform or unsupported z-index => R/A. |
| W | nowrap advance30 and ink contained in cell width40, positive whitespace/box bounds, known opaque backdrop, no foreign overpaint.30<=40 closes local fit; source words/entities remain exact and ordered. | Same run width30 in an assigned20 region followed by opaque paint, or unknown used width/bearings => A. A fit-content declaration on an ordinary inline span supplies no width certificate; width100% on a blockified flex item cannot be ignored. Auto-table expansion must be evaluated, not assumed to crop or fit. |
| H | Observed-pattern algebra gives first reference6.5464px. **Supplied** leading ink bearing>=-2px gives left edge>=4.5464>0; with all remaining ink/paint bounds certified, local left-containment closes. | Bearing=-8px gives left edge=-1.4536<0 => A; omitted bearing => A. Wrong containing-width basis, negative ancestor offset or applying this proof to an arbitrary negative indent => A/R. Positive reference is never complete run-containment evidence. |

F's supplied numbers isolate flex shrink/freeze behavior; they do not model the
actual source's font. T/P/W's rectangles are counterexamples to unsound implications,
not demonstrations that the authentic auto table overlaps. H's differing metric
completions expose an unspecified input, not a historical font claim. A future
maintained layout component would need independently created fixtures with these
outcomes, supported by pinned metric/paint facts; reproducing its own output is
not an independent oracle.

## Cross-cutting security, identity, source maps and no-loss oracles

| Case | Expected independent result |
| --- | --- |
| Known source bytes with multibyte checkbox/entity, selected TEXT offset and ordered siblings | Every original character/entity interval within the original response; whole-source/selected-slice identity unchanged; source order preserved; generated separators null. Different byte offsets after normalization => failure, never inferred citations. |
| Same source/identity/contract/component pins repeated | Equal classifications/maps/normalized/chunk hashes; timings excluded. Different source accessor/selected accession or a matching filename with wrong hash => R. |
| White period on canonical white, with fully certified unoccluded ancestors | Local HIDDEN_CONTRAST; exact period/text/element spans retained in exclusion ledger; historical display UNKNOWN. Unknown ancestor paint => A for the whole document. |
| Hidden metadata containing script, event handler, CSS URL/expression, stylesheet, foreign active element or network/schema request attempt | R before any optional component. Never ignore/strip/execute/fetch, even under display:none or outside the selected MD&A section. |
| Passive ix:references/resources under the exact V1 schema, no network, locally bound IDs | Typed non-narrative exclusion with raw spans preserved; never replace visible label by hidden target text. Wrong ancestry/prefix rebind/cycle/unresolved ID/unknown attribute => R/A. |
| Mixed visible/hidden/ambiguous content, ambiguity only in cover or exhibit-selection boundary | Whole selected-document A; no partial MD&A admission. Explicit SGML selection is distinct from stripping a script in the selected document; direct-primary retained script remains R. |
| Hidden material narrative or heading; oracle built by simply deleting implementation-excluded text | Incomplete/failure pending independent source-grounded materiality/coverage judgment; cannot improve completeness or shrink fixed denominator. |
| Unsupported CSS added to otherwise valid F/T/P/W/H case, including clipping/negative margin/alpha text, malformed DOM or ignored declaration | R/A; never silently normalized or globally disabled CSS validation. |

No synthetic text is an authentic filing. No output here counts as authentic MD&A,
real inference, scientific acceptance,12-filing coverage or processor latency.
