# Issue #12 checkpoint

Branch: `research/issue-12-event-evidence-contract`
Base: `feat/alpaca-paper-foundation` at `b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe`.
Reconciled target: `1a9014ef47accbea82fd086866bce114621a0d1f`, merged into this
dedicated branch before final verification; inherited target changes are not
issue edits. No runtime/tests/workflows changed between those two target commits.
Mandate: https://github.com/emanuel894/trading_agent/issues/12

## Resume safely

Read `AGENTS.md`, trusted-base `AI_PROJECT_POLICY.md`, this checkpoint and the
issue snapshot before continuing. Work only on this branch. PR #10 is context
only; never push its branch. No alpha, candidate #2, registrations/amendments,
paid/provider/model calls, secrets, broker actions or ingestion platform.

## Progress

- Read Issue #12, repository policy, ADR 001, Amendment 005 and PR #10 architecture
  context (remote PR head `4dd7703f429df01a6f7e67912294ec26e93b4ad0`).
- Created the dedicated branch from the fetched remote base. Existing checkout
  retained as required by repository policy; no worktree created.
- Design-only deliverable: portable envelope plus source matrix/admission,
  correction, entity and baseline rules; separately registered future experiment
  proposal. No production implementation is planned.
- Captured 43 public documentation/source responses (34 HTTP 200; nine failed
  paths preserved); retained bytes/hashes and 24 bounded source excerpts. An
  HTTP 200 app shell is not feed qualification. Two clients are pinned, not installed.
- Drafted all eight requested outputs under `docs/event-evidence/`. Proposed
  disposition: `EVENT_SOURCE_QUALIFICATION_NEEDED`. First future separate pilot:
  eight consecutive scheduled FOMC statements for evidence/control feasibility;
  predictive comparison requires another powered registration.
- Existing Python 3.13.5/Linux fixture suite: 240 tests, zero failures/errors;
  synthetic 300-bar demo completed, zero broker orders/model training. Logs are
  currently `/tmp/issue12-tests.log` and `/tmp/issue12-demo.log`.
- Initial design checkpoint `484659f` pushed to the dedicated remote branch.
- Independent review at that head found two P2 inconsistencies: embedded
  cutoff-specific admission in an immutable source envelope, and a synthetic
  correction carrying the original publication/vintage date. Both are corrected:
  assessments now have separate IDs/evidence hashes/arm/cutoff dependencies, and
  v2 publication/vintage stays on the correction date while v1 is unchanged.
- Final offline verifier passes two evidence examples, two separate assessments,
  13 rejected counterexamples, evidence reuse across cutoffs/arms, correction-date
  checks, 43 source hashes, 24 excerpts, local links and docs-only scope.
- Completed suite/demo/install logs retained in `verification/*.log.gz`; no
  repeated source capture, design research or full fixture-suite run on resume.
- Reviewer recheck at `332cd0e` resolved both P2s with no remaining material
  blocker. Source qualification is still needed, as documented.
- Read the newly accepted target operating skill and state map. Reconciled the
  target branch without repeating source capture/design or the passing suite.
- Next: final verification record and integration recheck; push and draft PR
  targeting the base, then inspect exact-head Ubuntu/Windows CI and report status.

## Milestone decision record

1. Critical path: final verified packet → draft PR → exact-head CI; no external
   source answer is needed to finish this design milestone.
2. Workers: one author plus one bounded independent reviewer; no competing writer
   or additional source work would help the remaining shared artifact scope.
3. Adopt/build: reuse JSON Schema/offline validation and existing scientific
   contracts; no collector, ingestion platform, evaluator or model framework.
4. Waste: stop captures/framework research and passing full-suite repeats; reuse
   retained evidence and completed logs. PR #10 was externally merged, not edited.
5. Usage/API ROI: included agent tools only; no external model/provider/data spend
   or calls. Usage/cost counters are not exposed; no paid fallback is authorized.
6. Next three actions: verify/review final bindings (author/reviewer; stop on
   material mismatch); publish draft (author; only dedicated branch and target);
   inspect both OS CI jobs (author; report failures/unrun separately). All can run
   before external source qualification, which remains a later workstream.

## Operational notes

- Initial shell fetch without network permission failed to reach the session
  proxy. Explicit network-enabled execution succeeded. Preserve proxy settings.
- FMBH remains UNRESOLVED. This design does not clear acquisition or qualify any
  historical event feed by mere API reachability.
- Authoring agent: Codex GPT-6, HIGH reasoning requested. No external model API
  will be called. Exact backend build is not exposed.


## Integration refresh

After Issue #11 / PR #15 was merged into `feat/alpaca-paper-foundation` as `110490c8f0d03ddc48b808a603bcade4fdbc945b`, this branch received this documentation-only synchronization commit solely to force fresh hosted PR validation against the advanced target. No event-contract content, source evidence, scientific registration, runtime code, provider access or trading boundary changed. Final merge requires both hosted OS jobs green on this new head.
