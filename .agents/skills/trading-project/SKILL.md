---
name: trading-project
description: Use when planning, implementing, researching, reviewing, or resuming work in emanuel894/trading_agent, including milestones, blockers, parallel workers, and usage decisions.
---

# Trading project operating doctrine

Version **1.2.0 — 2026-10-18**, Asia/Jerusalem.

## Read this first

Read [AI_PROJECT_POLICY.md](../../../AI_PROJECT_POLICY.md) every task; read the
[state and source map](references/project-state.md) on startup/resume or when a
gate/architecture/workstream matters. Load only the linked detailed documents
needed for the task. This skill owns operating practice; policy and registrations
own science/safety. No instruction here grants spending, trading or merge rights.

Mission: falsify whether AI information adds incremental **net alpha after all
costs** over strong cheap controls; remove the LLM if it loses. Optimize the overall
system for durable scale, compounding economic value and eventual profitability,
but never substitute ambition for evidence or weaken scientific/risk gates. Preserve PIT clocks,
survivorship-safe identity/populations, raw provenance, untouched holdouts and all
failures/costs. FMBH/Amendment 005 boundaries are in the state map; never work around
an unresolved gate. Broker/vendor/engine IDs cannot redefine scientific truth.

## Plan by dependencies; prevent duplicate work

Treat owner suggestions, discovered product features and external examples as
**hypotheses to evaluate, not instructions to adopt**. Compare them against current
architecture, opportunity cost, reliability, lock-in, scientific impact and total
workflow efficiency. Adopt only when they improve the system; reject or defer them
when they do not. Proactively surface better alternatives even when the owner has
not suggested them.

At task start, milestones and blockers, proactively identify the critical path:
the dependency chain controlling the next admissible scientific decision. Separate
external waits from runnable work. Rank tasks by uncertainty removed per total
time/cost, not volume of output. Tell the owner when another worker helps or wastes
usage; do not wait for the owner to suggest parallelism.

Check GitHub issues, PRs, branches and checkpoints before claiming work. Reuse
completed research/source packets; reopen a question only for new evidence, a
changed requirement or an identified defect. Record that reason and bounded delta.
One owner per task/output; no competing writers or repeated broad framework audits.

| Workers, total | Use when |
| --- | --- |
| 1 | One runnable critical task, shared mutable scope, unsettled interface, scarce usage, or coordination costs exceed saved time. |
| 2 | Two ready independent outputs have stable boundaries and enough budget; one can advance while the other waits. |
| 3 | Three ready independent outputs each remove material uncertainty; ownership, budget and integration capacity are available. A blocked dependency is not a third runnable task. |

Recommend the count first. The owner granted standing authorization on 2026-10-18
for routine repository maintenance and bounded worker dispatch without repeated
confirmation. Use it for issues, branches, PR publication, CI reruns and routine
merges after the existing review/CI gates pass. Existing explicit gates for science,
cost-bearing activation, credentials and trading remain unchanged. These staffing
choices are **not** a change to Issue #5's global one-implementer/one-reviewer pilot
caps or its disabled activation.

Each worker mandate records: issue, exact base SHA/branch, dedicated branch,
allowed paths/output, dependencies, exclusions, acceptance evidence, model/effort,
budget and stop condition. Use separate existing checkouts; follow policy's
no-worktree-unless-requested rule. Shared-interface/policy edits have one owner;
dependent workers wait for the reviewed contract. Stop at the mandated deliverable,
scope conflict, missing required authority/evidence, or budget limit. Finish
independent authorized work and checkpoint the blocked dependency. Workers never
merge each other's branches or extend a design task into implementation.

## Use Plan and Goal modes deliberately

For risky, underspecified or multi-system work, use **Plan mode first** to propose
the path and boundaries before edits. For long work with a clear outcome but an
uncertain multi-step path, use **Goal mode** so Codex keeps the completion condition
across turns. A normal prompt remains preferable for small one-shot work.

Goal mode improves continuity but does not replace durable repository state.
Usage limits can still interrupt future turns, so checkpoints, branches, exact SHAs
and resume instructions remain mandatory. When the Codex client exposes scheduling
and a quota reset time is known, prefer one scheduled resume shortly after reset
for a checkpointed Goal instead of requiring manual relay. The scheduled prompt
must read the existing checkpoint, avoid repeated work and stop rather than loop if
usage is still unavailable or state has changed. Do not create retry storms or use
scheduling to bypass scientific, spend, credential or trading gates. No verified
**heartbeat** control is available in the owner's current workflow; do not depend
on heartbeat-based resume unless it is later observed and qualified.

## Adopt, route and spend deliberately

Before building generic plumbing, consult existing adoption decisions in the state
map. Record `ADOPT`, `INTEGRATE`, `BENCHMARK`, `KEEP_OURS` or `REJECT` with evidence
and a small contract test. Keep project-specific scientific admission/evaluation;
adopt maintained transport, models, engines and job tooling. Do not weaken the
contract to fit an upstream default or install the whole proposed stack at once.

Use the [routing policy](../../../automation/real/routing_policy.json): cheaper/
medium for GREEN, Sol-class/High for substantive YELLOW, Astra-class/High for a
documented RED architecture/science/security blocker. Issues #9/#11/#12 request
High. Use fresh independent review; Gemini is the intended first provider
challenger, Claude deferred. Record actual model/tool IDs and reasoning support;
class names are not API IDs. Missing qualification blocks automated routing;
never claim same-model or fixture review is cross-provider acceptance.

Prefer included usage, focused reads, batched independent retrievals, reused
evidence and targeted falsification probes. Avoid full-history reprompts, redundant
agents, constant polling and repeated passing checks without a new reason.

Paid API automation becomes worth proposing when a repeatable bounded backlog is
execution/relay-limited, its source contracts are stable, and measured maintainer
time/latency savings or confirmed defects exceed implementation, review, retries,
runner/storage and operating costs. Compare waiting for included usage. Pilot
5–10 bounded issues; measure cost per accepted PR/confirmed finding and owner
minutes saved. External-source waiting or one-off research alone is insufficient.

Value is separate from permission: explicit owner-approved spend scope, exact
prices/model routes, combined hard cap, per-run cost/token/time limits, durable
pre-call reservations and ambiguous-call reconciliation are required. Unknown cost
means `PAUSED_BUDGET`. Previously discussed illustrative API amounts or proposed
data ceilings are non-canonical and are not approvals. No fixed monthly API
commitment is approved. No paid fallback when included usage ends; no purchases,
subscriptions, provider contact or secret/environment changes without the relevant
explicit authorization. See [activation prerequisites](../../../automation/real/ISSUE_5_ACTIVATION.md).

## Persist, validate and integrate

GitHub code, registrations, issues/PRs and CI are durable authority; chat previews
are context. Confirm live issue/head state and human decisions. Do not infer that
a request was sent, a worker ran, a draft merged or a gate passed. Preserve private
licensed evidence separately and link hashes/approved locations, never secrets.

Proceed autonomously within the mandate. Before interruption/usage exhaustion,
persist a checkpoint in the task's existing progress location (otherwise one
issue-scoped progress file): issue/branch/base/head, source/policy/input hashes,
completed outputs, passed/failed/unrun checks, findings/unknowns, attempts/repairs/
usage/cost, pending side effects, stop state and exact next action. Link it from
the issue/PR when authorized. Resume by reconciling live state and verifying those
bindings; retain counters and reconcile ambiguous calls/publication before retry.
Never restart completed research or reset spend/repair caps under a new identity.

Use a small draft PR to the mandated base; preserve unrelated changes. Run policy's
full suite/demo plus task checks and protected-artifact comparison. Record exact
head, commands, results and limitations. Require fresh independent review, both
Foundation OS jobs and integration review of combined scopes/contracts. The owner's
standing authorization satisfies the human-approval requirement for routine merges
once these gates pass; do not ask again for those merges. Revalidate after head/base
changes. Protected science, cost-bearing activation, credentials and trading gates
still require their own explicit authorization.

Ubuntu success does not clear Windows failure. Preserve failed logs and exact
run/job/attempt/head, identify the failing test, compare environment/path/encoding/
timing causes, and reproduce or make one diagnostic same-head rerun. A green rerun
alone does not prove a flake. Document the cause and remaining uncertainty; an
unexplained failure blocks readiness. No retry-until-green, test suppression,
threshold weakening or automatic exception/merge. Report unrun Windows separately.

## Mandatory milestone/blocker checklist

Persist and report this compact decision record at every milestone or blocker:

1. **Critical path:** next admissible decision, dependency and blocker/owner.
2. **Parallelizable tasks:** ready outputs, 1/2/3 workers, scopes and cost rationale.
3. **Adopt vs build:** existing component/decision reused; smallest necessary gap.
4. **Waste/duplication:** work to stop, reuse or defer; check current owners/PRs.
5. **Usage/API ROI:** included usage, estimated/actual cost and automation value;
   authorization/budget status and stop state.
6. **Next 3 highest-information-value tasks:** rank, question falsified, dependency,
   owner, acceptance/stop rule and whether each can run before the external answer.
7. **Scale/economic leverage:** ask whether a newly discovered feature, workflow or
   maintained tool reduces recurring human work, compute/model cost, latency, error
   rate or future integration burden at scale; prefer multiplicative leverage over
   local convenience, without claiming future profit before evidence.
