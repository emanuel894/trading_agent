# Engineering versus scientific change control

This contract is proposed for P0-A engineering qualification only. Original
protected documents and P0-A REGISTRATION.md remain byte-identical. User authority
is the current design-only architectural request, including explicit distinction
between processing assumptions and historical facts; implementation/replay are
not authorized by this document or the design GO recommendation.

## Existing requirements and compatibility

| Governing source | Frozen requirement | Contract treatment |
| --- | --- | --- |
| AI_PROJECT_POLICY.md, Evidence/Experiments | Original bytes/spans/lineage; external text untrusted; no silent scientific changes | Retain raw, append classified derivatives; validate hidden markup; contract defaults labelled assumptions |
| P0-A REGISTRATION.md, sample rule | First12 provenance-verified distinct accessions; representations count once; no outcomes-based selection | Unchanged; current coverage1/12, failures/abstentions retained, no replacement by renderer/source convenience |
| P0-A REGISTRATION.md, targets | Identity100%; complete MD&A>=90%; material assertion traceability100%; reproducible hashes100%; real-schema>=95%; supported assertions>=95%; silent loss0; unexplained integrity failures0 | All values, denominators and required evidence unchanged; classify/exclude audit cannot redefine an incomplete filing as complete |
| P0-A REGISTRATION.md, normalization/review | Whitespace-only normalization; hidden iXBRL suppression; ambiguity abstention; independent grounding review | Keep original canonical-visible view plus normalized view; punctuation exclusions are visibility records, never normalization rewrites; unresolved material exclusion blocks acceptance |
| ADR001 §1, §3 | Original Part I Item2, comparable prior-year quarter; immutable processing/source/time distinction | Canvas is a processing assumption; preserve source/processing versions and unknown historical display/time |
| ADR001 §5 table, A/B/C; §6 extraction gate | Same documents/passages across arms; independent calibration accuracy/schema/time thresholds | No arm/feature/extraction gate change. Future use must process comparable inputs consistently; current architecture work neither qualifies nor activates those gates |
| ADR001 §8, line277, acquisition gate | Original50 filings/>=25 issuers; >=48 complete sets; unresolved cases retained; one documented parser/access repair cycle | Unchanged and distinct from P0-A12-case engineering. V2's extra engineering cycle does not amend/reset this scientific gate |
| Amendments003/004/005 | SIP liquidity/population/priority/identity/clock constraints | No change; canonical viewing does not establish historical source availability, identity eligibility or candidate progression |

**Assessment:** the proposed canonical environment can be an engineering
processing specification without changing the listed scientific criteria, **only
with the conservative admission guards below**. This is a bounded consistency
analysis, not authority to apply it to the confirmatory experiment.

1. Complete extraction is measured against an independently evaluated original
   MD&A and its canonical visibility classifications. Both classifications and
   exclusions are reviewable; reference expectations cannot be derived solely
   from the implementation under test.
2. Do not change the expected-reference denominator by removing hidden material
   assertions. If an exclusion contains possible material MD&A/heading content or
   has unresolved materiality, the filing stays incomplete/failed pending independent
   evaluation. A policy that hides text cannot supply its own completeness proof.
3. Preserve all failures and source representations; hidden/ambiguous cases do
   not disappear from the fixed sample. AMBIGUOUS anywhere blocks preparation.
4. White-period classification resolves the processing-default ambiguity only.
   It changes neither observed source bytes nor historical display truth; it does
   not prove that all MD&A is extracted, that assertions are supported, or that
   unseen filings are compatible. No accession/span-specific bypass is allowed.
5. Existing alpha population, arms, sample dates, controls, feature/tuning budgets,
   thresholds, availability clocks, deadlines and cost assumptions remain frozen.
   No returns or labels are inspected to select the environment/profile.

## Exact amendment triggers: stop before dependent changes

| Proposed departure | Required change control before use |
| --- | --- |
| Lower >=90% complete MD&A or permit known material omission/accepted partial extraction | New versioned P0-A engineering registration amending its fixed-contract targets, with owner approval and retained old results; if used in the scientific extraction gate, explicit amendment to ADR001 §6 Extraction and §8 acquisition completeness requirements, with human scientific review |
| Remove failed/ambiguous filings, replace accessions or count two representations twice | P0-A sample-rule amendment; for original scientific sample, amendment to ADR001 §8 and Amendment004 registered deterministic selection/no-replacement protocol before evaluation |
| Treat white-canvas output as historical investor-visible information or infer availability/actionability | Not admissible as a display-default inference. Requires new independent historical/source-time evidence; any changed scientific availability premise requires explicit ADR001 §3/§4 and applicable registered clock/causality amendment, not a processing note |
| Accept untraceable text, omit exclusion records or silently normalize nonwhitespace | No waiver in this contract; revises P0-A zero-loss/traceability requirements and scientific source-span/evidence contract in ADR001 §3. Stop for explicit versioned approval before any affected processing |
| Use additional engineering rounds to bypass original50-filing one-repair stopping rule | Explicit amendment to ADR001 §8 acquisition-gate row and linked execution registration, with human scientific review; V2 alone supplies no such amendment |
| Apply different visibility filters to comparator/LLM arms or tune them on outcomes | Explicit scientific amendment to ADR001 §5 arm/input fairness and relevant frozen transform/tuning registration before affected evaluation |

No listed departure is part of this design. If later independent review finds
that the conservative contract itself changes one of these scientific criteria,
return NO-GO and stop; do not edit the protected document as an implementation detail.

## Scope correction and counters

The earlier local adjudication searched retained scope attachments and P0-A
REGISTRATION.md without finding a separate single-cycle sentence. The actual
scientific single-repair sentence is in **ADR001 §8, line277**. Its location and
scope are now explicit; earlier evidence is preserved, not rewritten.

PR47 implemented one authentic engineering repair. V2 inventoried/reviewed and
stopped before a second implementation/replay. Current work is design only; no
new cycle, replay allowance, merge authority or scientific gate passes arise.
Any next request must explicitly authorize one bounded implementation and one
complete-submission replay, reconcile those counters, preserve PR47/dependencies,
and stop on any new blocker. No automatic third repair or scientific audit run.
