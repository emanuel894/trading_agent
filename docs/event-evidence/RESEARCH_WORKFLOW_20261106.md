# Smallest offline readiness research workflow

Integration foundation: `5f8b850548e2f7786814086d5350a72a19d87459`.
Stack base: reviewed draft PR59, `f6dc61ad36596718fcd3b773021af5d26b5c5a43`.
Branch: `feat/synthetic-research-decision-workflow-20261106`. This focused draft is
stacked on PR59 without merging it; exact resulting head/review/CI are in the PR.

## Reuse map and precise gap

| Stage | Existing asset reused | Boundary preserved |
|---|---|---|
| Evidence semantics | PR16, docs/event-evidence/CONTRACT.md | Unknown clocks, separate immutable evidence/admission, no source qualification from shape/hash |
| Real-format input | PR59, agent/fed_statement_offline.py | Pinned M02 catalog facts; 2026 retrieval; unproved original edition/receipts; missing-prior abstentions |
| Synthetic input/features | PR36, agent/offline_chart_gov_demo.py; PR51, research/lean_intraday_integration_20261023/integration.py | Reuse scenarios() and decide(); no replacement formulas, clocks or strategy |
| Auditable storage | agent/audit_store.py, EvidenceStore | Existing canonical JSON, blobs, immutable records, transactions and verifier |
| Native engine/risk | Accepted PR51 LEAN packet, agent/risk.py and later draft PR56 observation replay | Reuse receipts; no engine launch, order/risk path or requalification needed here |
| Other draft research | PR55/56 IQ-P1 and PR45–57 SEC/P0-A | Separate protocols/source gates; no importing unresolved datasets or altering holdouts |

PR51 already computes four fixed feature outcomes, checks native fixture wiring
and retains oracle reviews. PR59 already extracts retained Fed facts with
quarantine. Neither supplies an executable research-packet → separately supplied
critique → sealed research-decision join in EvidenceStore. The development review
controller concerns code/CI rather than scientific conclusions. No existing
adapter, engine, storage implementation or risk control is rebuilt.

The only new code is `agent/research_workflow_offline.py`: two offline stages,
fixed H1, provenance links and decision gates. It exposes no provider, model,
broker, strategy or general orchestration API.

## Bounded question and interpretation

H1 asks whether **every** existing PR51 synthetic case has both market and
policy-change features ready strictly before its common cutoff. The population
is fixed to baseline, future_revision, missing_bar and equal_clock. Primary
measure is ready / all4 opportunities. All failures stay in the denominator.

The existing fixtures yield2/4 readiness: baseline/future_revision ready,
missing_bar lacks market features, equal_clock lacks the policy-change feature.
This is an expected property of existing technical cases, **not a newly discovered
economic result**. They are related scenarios, not independent announcements.
The new result is a reproducible, independently critiqued and auditable rejection
of H1. It proves a research-workflow boundary using synthetic inputs, not alpha,
predictive merit, real latency, source readiness or permission for another study.

The Fed mode reads the same existing pinned copy through PR59, preserves its
catalog snapshot and creates **no** hypothesis observations/measurement. Its
decision remains BLOCKED_SOURCE_QUARANTINE even if the reviewer accepts the
interpretation. It does not quietly substitute a synthetic input.

## Prepare → actual critique → finalize

From `trading_agent_starter`, using the existing dependency environment:

```text
python -m agent.research_workflow_offline prepare --root <new-run-directory> --input synthetic --author <author-id>
python -m agent.research_workflow_offline prepare --root <different-new-directory> --input fed-catalog --author <author-id>
```

Each command prints the immutable packet record ID and blob SHA. The store records
the fixed hypothesis **before** computing features, then input bytes and a packet
binding both hashes, actual code bytes, every observation and the measurement.
Prepare creates no final research decision. Existing output directories refuse.

A separate reviewer must inspect that exact packet, source scope and hypothesis,
then supply a JSON object with exactly these fields:

- `packet_sha256`: reviewed packet's blob SHA;
- `reviewer_id`: nonempty identity distinct from the packet author;
- `independent`: true only after an actual separate review;
- `independence_basis`: actual review context and its limits;
- `verdict`: ACCEPT_INTERPRETATION, REQUEST_CHANGES or REJECT_INTERPRETATION;
- `findings`: list of blocking findings, empty only if none;
- `rationale`: substantive interpretation, including synthetic/source limitations.

The code records these as **attestations**, not authenticated signatures. A JSON
flag cannot establish independence. In the delivered demonstration a fresh Codex
reviewer supplies the actual critique, separately from the implementer. Included
agent review is not cross-provider or formal GitHub approval. Unit-test critique
doubles are explicitly synthetic and are never reported as independent review.

```text
python -m agent.research_workflow_offline finalize --root <run-directory> --packet-id <id> --critique <reviewer-produced-json>
```

Finalize verifies the existing store/linked input/hypothesis, exact packet hash,
unchanged implementation and critique shape. Missing/stale/same-author critiques
cannot seal a decision. Reviewer objections block the conclusion. Valid critique
and decision are appended in one existing store transaction, with links/hashes;
repeat finalization refuses. No preceding evidence is overwritten. Exit0 means
the workflow operation succeeded, not that H1 or a source was approved.

All decisions retain source_admission=NOT_GRANTED and predictive_research=NOT_RUN.
No return labels, portfolio, economic controls or model fitting are evaluated.
Existing frozen protocols, broker flags and real-source boundaries are unchanged.

## Verification, usage and stop

Local Python3.12.14/Linux: 11 focused integration tests PASS; full355-test suite
PASS, no failures/errors/skips; required300-bar demo PASS. Generated performance
output was not opened. The existing isolated requirements environment was reused;
no installation or dependency change. No accepted native qualification/runtime,
archive restoration, source/entitlement probe or framework audit was rerun.
Required regression CI retains existing tests; it is not new source certification.

TDD evidence: initial9 tests failed for the missing module; two added regressions
then exposed stale implementation acceptance and malformed verdict TypeError.
Both were fixed before the final11-test pass. No assertions were weakened.
Full suite measurements: wall15.4979s, child CPU14.8988user/0.7371system seconds,
peak child RSS117,008KiB (Linux, suite measurement rather than workflow throughput).
External spend$0; included-model/token/CI metering unavailable. Final exact-head
independent code review, actual research critiques, demonstration decisions and
Ubuntu/Windows CI receipts are recorded in the PR/task report; pending receipts
at document creation do not imply success.

Critical path: one author plus one independent code/research reviewer, then
required CI. Reusing the fixed fixtures and store avoids platform work. Next
three steps within this mandate: prepare immutable packets, obtain actual bound
critique/seal decisions, publish the focused draft with required checks. Stop at
source/scientific boundaries; no automatic expansion to market research.

NEXT_ACTION: Review the focused draft for integration, keeping every real-source
research claim blocked until its separate source/protocol authorization exists.

RESUME_PROMPT: Read this checkpoint, canonical policy/skill and the draft's
exact-head review/CI and actual critique/decision receipts. Reuse PR59 and PR51
without requalification. Preserve synthetic-only H1, common four-case denominator,
Fed catalog quarantine, negative readiness result and absent real-source admission.
Do not acquire data, access holdouts, change frozen protocols or activate orders.
