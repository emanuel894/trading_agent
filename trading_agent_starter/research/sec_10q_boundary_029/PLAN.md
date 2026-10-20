# SEC original 10-Q source-boundary qualification plan

> For agentic workers: execute this source review inline; one fresh independent final reviewer. Resume from PROGRESS.md and committed captures; do not duplicate accepted retrievals or audits.

**Goal:** Decide Issue 29's narrow original-10-Q provenance/publication-clock boundary without inventing receipt or amending science.

**Architecture:** Reuse registered contracts, Issue 12 source captures and committed FMBH metadata assertions first. Add only missing official documentation and one original accession's metadata/index/submission representation. The packet records evidence and falsifications; it is not an ingestion implementation.

**Tools:** GitHub authenticated REST, local raw-byte/hash verification, bounded official SEC HTTP documentation/metadata retrieval, Python standard library for offline packet checks.

**Spec:** issue_snapshot.json. Exact base d90f13035cf47e4d96ac8a33aed25d784dc589fe; branch research/issue-29-sec-10q-source-boundary.

## Global constraints

- Historical first observation/receipt remain null unless independently evidenced. Retrieval is a separate actual clock.
- Preserve ADR001, Amendments 003/004/005, registration bytes, provisional600 seconds, candidate order/ledger and all accepted evidence.
- No MD&A/return/performance inspection, alpha run, broad acquisition/build, cohort freeze, FMBH eligibility adjudication, candidate2, paid calls, credentials or broker actions.
- One source reviewer/implementer, then one independent final review. Existing checkout; dedicated branch; durable commits.
- Stop at exactly READY, INCOMPLETE or BLOCKER from Issue29; final-head checks/CI and draftPR only, no merge in this task.

## Review focus

Publication versus acceptance versus receipt; zone/DST/native precision; original versus amendment/distinct accession; later-retrieved byte identity versus historical availability; strict separation of the registered acquisition proxy and later performance/prospective admission.

### Task 1: Reconcile and inventory existing authority

- [ ] Record live foundation/Issue29/PR28 merge and existing owner/PR state.
- [ ] Read trusted project skill/policy, ADR001§8, Amendment004/action registration and Issue12 envelope semantics.
- [ ] Hash reusable official captures and identify which old issuer raw objects are locally present versus hash-referenced only. Preserve that distinction.
- [ ] Commit the inventory/checkpoint before new SEC retrieval.

### Task 2: Qualify the smallest missing source boundary

- [ ] Review official SEC documentation on access, submissions, acceptance/zone, version/index/feed/update semantics. Reuse current captures where sufficient; log bounded official-only retrievals/failures.
- [ ] Reconcile one known original accession against retained assertions and minimal current metadata/index/submission bytes; never inspect MD&A. Retain opaque bytes/hash where needed.
- [ ] Record amendment/distinct-accession rejection and at least one missing/disagreement fail-closed path, with evidence boundaries explicit.
- [ ] Commit source captures, clock/precedence contract, sample and provisional decision with exact missing facts if any.

### Task 3: Review and publish the exact decision

- [ ] Run offline packet/protected-artifact checks; fresh independent final review of the source-boundary decision (no duplicate acquisition).
- [ ] Commit final packet; run required final-head repository tests/demo and exact-head Ubuntu/Windows Foundation CI through a draft PR.
- [ ] Record exact decision/review/validation receipts on Issue29/PR without changing the validated head; stop. State dependency closed/open, Eric/FMBH boundary, further timing work, next3 tasks.
