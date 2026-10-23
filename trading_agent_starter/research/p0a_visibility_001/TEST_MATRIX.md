# Adversarial qualification matrix — proposed, NOT EXECUTED

V = visible, H = hidden with exclusion record, A = ambiguous and document blocked;
R = hard reject. Whole-document admission is separate from a run's classification.
All fixtures are synthetic or explicitly provenance-bound minimal source slices;
none counts as an additional authentic filing or actual LLM inference.

| ID | Case | Expected oracle/evidence |
| --- | --- | --- |
| E01 | Unstyled text with no body background | V black on assumed white; ledger records contract defaults, historical visibility UNKNOWN |
| E02 | Known white period pattern | H_CONTRAST, original '.' retained; element/text spans reproduce bytes; no punctuation normalization |
| E03 | White text on explicit supported black background | V; explicit source background overrides white canvas |
| E04 | Black child text inside white foreground parent on white | Child V; no subtree skip merely from parent contrast |
| E05 | White child inside explicit black backdrop ancestor | V through backdrop resolution; CSS background is not falsely inherited as a property |
| E06 | White on pale cyan / blue on black | A; low contrast is not classified as absent text |
| E07 | Unsupported/alpha text or background color, unresolved image | A/R; never approximate or fetch |
| E08 | Ambient dark theme/user stylesheet/font changes | No effect on finite contract outputs; backend-dependent effect fails determinism |
| E09 | Same raw/policy/code twice | Equal classifications/text/maps/chunks; receipts/time fields may differ |
| H01 | display:none subtree with nested/void tags | H; no descendant leak, all markup validated |
| H02 | Script/event handler inside hidden subtree | R; hiding cannot bypass active-content checks |
| H03 | Qualified tr visibility:collapse, blank cells | H; table row/cell structure and excluded intervals audited |
| H04 | Nonempty collapsed row in potential MD&A | H text preserved; complete-extraction admission blocked for material/unresolved omission |
| H05 | Descendant visibility:visible override under hidden/collapse | A/R unless a new reviewed rule models it exactly; no silent inherited suppression |
| H06 | collapse outside permitted table-row context | A/R |
| H07 | 1pt NBSP/whitespace-only spacer | Audited whitespace-only handling; no invented text or source span |
| H08 | Nonwhitespace glyph under 1pt, zero/negative font size | A/R; no assumption that tiny text is ignorable |
| H09 | Hidden narrative assertion/boundary heading | Exclusion remains evidence; independent materiality review required; unresolved case fails completeness |
| C01 | Exact body padding/margin!important/z0/relative tuple | Admitted only under frozen body/context/priority proof; no global !important rule |
| C02 | Duplicate property/attribute, malformed delimiter | R/A, never choose whichever value makes text visible |
| C03 | CSS comments, escapes, url/var/expression/import | R/A; no token stripping or resource access |
| C04 | Relative z2/z5 context with proven normal flow | Only qualified context admitted; predicate receipt links text and ancestor chain |
| C05 | Offsets, absolute/fixed/sticky, transform, negative margin, order | A/R; no visible-label fallback |
| C06 | tr height minimum vs div fixed/max-height box | Qualified row semantics; unmodeled generic box A/R, no claim all heights clip |
| C07 | Width/nowrap/flex composition that may occlude/reorder | A; retain full source, never truncate at viewport or assume fit |
| C08 | Qualified hanging indent vs negative offscreen movement | Prove restricted pattern or A; unrelated negative-indent values reject |
| C09 | Border alpha vs text/background alpha | Passive border rule only; alpha permission does not migrate to text |
| X01 | Correct ix:header/references/schemaRef/resources tree | Metadata H; namespace/parent/attribute/target types verified; schema fetch count0 |
| X02 | Same tag names under wrong namespace or visible parent | R/A; cannot exploit generic prefix/tag allowance |
| X03 | Missing/duplicate ID, wrong context/unit reference target | R |
| X04 | continuedAt cycle/missing target/duplicate rendering | R; valid graph must not duplicate visible text |
| X05 | -sec-ix-hidden visible 'single' / hidden '1' | V source 'single' with its own byte map; hidden '1' never substituted/appended |
| X06 | Visible label / hidden taxonomy URI or nil fact | Preserve label; nil grammar rejects contradictory content; no URI execution |
| X07 | Dangling/wrong-type/remote vendor hidden reference | R/A; no lookup or hidden-text promotion |
| X08 | Visible nested numeric iXBRL/table cells | Exact text once, correct cell separation and table/prose markers |
| P01 | Valid SGML submission and original observation binding | Accession/form/CIK/hash/size/role/URI/chain all match; exactly one10-Q TEXT |
| P02 | Wrong issuer, amended form, multiple candidates, tampered bytes | R; cannot qualify via SEC-like URL or contract flag |
| P03 | Scripted direct primary vs separately valid submission | Primary remains failed; submission independently checked; one filing denominator |
| P04 | Other scripted SGML report/exhibit envelopes | Original bytes preserved/accounted; never executed/followed/promoted into selected primary |
| M01 | Unicode/entities across inline boundaries | Every codepoint maps to original byte interval; entity expansion shares literal interval |
| M02 | Collapsed whitespace/generated separators | Whitespace-only rules; generated spans null; no punctuation/case/word rewrite |
| M03 | Unknown construct outside MD&A | Whole document blocked; no source-span/section-location exemption |
| M04 | TOC/body duplicates, missing end, table Item3 reference | Ambiguity fails; table reference cannot truncate actual MD&A tail |
| M05 | Missing/duplicated chunk, unclassified/dropped text run | R; ledger and source/text/chunk coverage reconciliation detects gap/duplication |
| M06 | Exclusion log failure or partial persistence | Failure preserved; no complete/admitted result or self-approved manual override |
| S01 | Change normalization/contrast/canvas/profile version | New lineage/hash/version, preserve old results; no automatic threshold/sample change |
| S02 | Material hidden claim or source-review disagreement | Failed/incomplete in original denominator; no reference-oracle shrink to rescue accuracy |

Future minimum acceptance: independent expected outputs for every row, original
byte reconstruction and classification/exclusion coverage checks, zero network/
script execution, all required full suite/demo and Ubuntu/Windows CI. Tests must
exercise parser/visibility rejection with otherwise valid provenance, not pass
only because the synthetic source failed an unrelated identity check.

After code/evidence review and explicit owner authority, one original complete
submission replay may attempt preparation. Persist its first failure or full
text/boundary/map/chunk evidence and stage/resource measurements. No second
authentic retry, direct-primary sanitization, inference or automatic renderer fallback.
