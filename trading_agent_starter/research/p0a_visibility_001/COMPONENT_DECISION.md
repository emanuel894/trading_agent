# Component comparison and bounded complexity evidence

**Recommendation: qualify the finite semantic CSS/DOM profile first.** Reuse the
existing source mapper, strict document/provenance checks and EvidenceStore.
Consider a maintained CSS tokenizer behind the strict profile where it replaces
fragile lexical code. Do not implement a general CSS layout engine. WeasyPrint
is a maintained rendering challenger for a separately authorized comparison if
the finite profile's compositional proof fails; it is not an automatic fallback.

## Measured/static evidence and limits

The completed V2 inventory counted 62,084 elements of38 kinds,54,365 inline styles,
45 properties/370 property-value pairs,81 collapsed rows (all whitespace-only),
595 contexts,9 units and4,811 typed references. All1,088 heights occur on table
rows;55 one-point spans are whitespace-only; positions have no offsets; no
clip/overflow/transform/opacity/order/negative-margin property was inventoried.
These bounded structural facts make a finite profile plausible. They do not prove
all CSS compositions safe or quantify implementation LOC, runtime or maintenance.

The renderer comparison inspected **Kozea/WeasyPrint** pinned commit
`7e2dda0d7833916d2698c35e707bc80ddea1ed24` (commit date2026-10-22), declared
version70.0. `evidence.json` records exact public source/doc URLs and retained
content hashes; no package, dependency or native library was installed/executed.
This is a maintenance/source snapshot, not rendered-output determinism evidence.

The pinned pyproject declares8 direct Python dependencies: pydyf, cffi,
tinyhtml5, tinycss2, cssselect2, Pyphen, Pillow and fonttools. Installation docs
also require Pango and describe platform/native/font dependencies. The first-steps
docs and validation source explicitly describe warnings and ignored unsupported
CSS. HTML's inspected constructor defaults to media_type='print' and a URL fetcher.
Those defaults cannot be used unchanged for this screen/no-fetch/fail-closed contract.

| Criterion | Finite semantic profile | Pinned WeasyPrint rendering candidate |
| --- | --- | --- |
| Correctness | Transparent limited semantics; must abstain on unproved geometry/contrast/flow | Broader maintained layout/CSS implementation; supported behavior still must match contract, not merely produce a PDF |
| Security | Smaller accepted grammar; no JS/resource engine; active/hidden validation stays strict | Requires isolated resource/CPU/memory limits, deny-all fetch policy and strict front-end validation; upstream ignoring unsupported CSS cannot count as successful admission |
| Determinism | Source order, exact palette/defaults and versioned predicate policy can avoid platform font/GPU state | Must pin build/native libraries/fonts/UA settings; screen vs print/pagination differences require qualification; no determinism benchmark performed |
| Original bytes | Retains existing offsets and entity maps directly | Inspected public entry points do not establish original-byte-span fidelity; must keep original mapper and validate a bridge through any tree recovery/layout transformation |
| iXBRL | Typed context/resource suppression and local reference graph required | Renderer does not establish this project's hidden-fact/provenance/identity semantics; project validators still required |
| Maintenance | Own bounded semantic/context policy and adversarial tests; freeze/review rather than expand after each failure | Upstream maintains layout; project still owns pinning, patches/updates, sandbox, fetching policy, warnings-as-failure and source-map compatibility |
| Observed dependency surface | Existing parser/store; future tokenizer optional and must be qualified | 8 direct Python deps plus native text/font stack observed in pinned source/docs |
| Measured latency/memory | NOT_MEASURED for proposed profile | NOT_MEASURED; no render executed |
| Scope failure | Stop if source needs broader geometry/unknown CSS | Separate component qualification; no per-filing renderer selection to rescue failures |

This is an evidence-backed complexity comparison, **not** a claim that a45-property
profile is a45-line patch or that any renderer is deterministic/slow/unsafe by
definition. No estimated person-days, performance or cost numbers are presented
as measurements. Eight direct dependencies is not the full transitive/native
dependency count;370 source values is not the count of semantic proof obligations.

## Future choice gate

A separately authorized implementer should freeze the finite grammar/context
policy and demonstrate the matrix and document-wide composition predicates before
the single authentic replay. An established CSS tokenizer such as tinycss2 may
parse syntax; it cannot turn unsupported values into accepted semantics. No new
dependency is approved or installed by this design recommendation.

If sound finite classification cannot be demonstrated within that bounded scope,
stop and return NO-GO for that implementation. Then propose one maintained-engine
comparison with pinned environment/font/resource policies and original-byte-map
oracles. A renderer does not remove the need for the canonical viewing contract,
scientific change-control check or independent extraction validation.
